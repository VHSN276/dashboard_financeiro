"""Formulário, filtros e tabela de transações."""

import calendar
import logging
from datetime import datetime

import flet as ft

from controllers.transaction_controller import (
    obter_meses_disponiveis,
    obter_opcoes_categorias,
    obter_transacoes_formatadas,
    processar_edicao,
    processar_exclusao,
    processar_nova_transacao,
)
from database.errors import MENSAGEM_BANCO_INDISPONIVEL
from views.mensagens import mostrar_mensagem


logger = logging.getLogger(__name__)


class TransacoesView:
    def __init__(self, page, ao_alterar_dados):
        self.page = page
        self.ao_alterar_dados = ao_alterar_dados
        self.filtros_ativos = []
        self.mes_atual = None
        self.id_edicao = None

        self.erro_categorias = ft.Text(
            visible=False,
            color=ft.Colors.RED_300,
            size=13,
        )
        try:
            self.categorias = obter_opcoes_categorias()
        except Exception:
            logger.exception("Não foi possível carregar as opções de categoria.")
            self.categorias = []
            self.erro_categorias.value = MENSAGEM_BANCO_INDISPONIVEL
            self.erro_categorias.visible = True
        self.tabela = ft.DataTable(
            width=float("inf"),
            columns=[
                ft.DataColumn(ft.Text("Descrição", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Categoria", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Data", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Valor", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Ações", weight=ft.FontWeight.BOLD)),
            ],
            rows=[],
        )
        self.erro_tabela = ft.Text(
            visible=False,
            color=ft.Colors.RED_300,
            size=13,
        )
        self.linha_filtros = ft.Row(
            controls=self._criar_chips_filtro(),
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        self.modal = None  # criado a cada abertura, em _abrir_modal

        self.control = ft.Column(
            controls=[
                self._criar_linha_acoes(),
                self.erro_categorias,
                self.erro_tabela,
                self.tabela,
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _carregar_meses(self):
        try:
            return obter_meses_disponiveis(), ""
        except Exception:
            logger.exception("Não foi possível carregar os meses do formulário.")
            return [], MENSAGEM_BANCO_INDISPONIVEL

    def _montar_formulario(self, dados=None):
        """Cria os campos do modal do zero a cada abertura.

        Campos novos evitam que o Flet continue exibindo a seleção anterior nos
        dropdowns (limpar o valor no Python não limpava o texto na tela, e o
        formulário parecia preenchido sem estar). A lista de meses é lida aqui,
        então meses criados ou removidos aparecem automaticamente.
        """
        meses, erro = self._carregar_meses()
        if dados is not None:
            mes_inicial = dados["mes"] if dados["mes"] in meses else None
        elif self.mes_atual in meses:
            mes_inicial = self.mes_atual
        else:
            mes_inicial = meses[0] if meses else None

        hoje = datetime.today().strftime("%Y-%m-%d")
        if dados is not None:
            data_inicial = dados["data"]
        elif mes_inicial and mes_inicial != hoje[:7]:
            data_inicial = f"{mes_inicial}-01"
        else:
            data_inicial = hoje

        self.erro_modal = ft.Text(
            value=erro,
            visible=bool(erro),
            color=ft.Colors.RED_300,
            size=13,
        )
        self.descricao_input = ft.TextField(
            label="Descrição",
            width=300,
            autofocus=True,
            value=dados["descricao"] if dados else "",
        )
        self.valor_input = ft.TextField(
            label="Valor (R$)",
            width=300,
            keyboard_type=ft.KeyboardType.NUMBER,
            value=dados["valor_puro"] if dados else "",
        )
        self.data_input = ft.TextField(
            label="Data (AAAA-MM-DD)", width=300, value=data_inicial
        )
        self.mes_dropdown = ft.Dropdown(
            label="Mês",
            width=300,
            options=[ft.dropdown.Option(key=mes, text=mes) for mes in meses],
            value=mes_inicial,
            on_select=self._ao_selecionar_mes,
        )
        self.tipo_dropdown = ft.Dropdown(
            label="Tipo",
            width=300,
            options=[
                ft.dropdown.Option(key="RECEITA", text="Receita"),
                ft.dropdown.Option(key="DESPESA", text="Despesa"),
            ],
            value=dados["tipo_puro"] if dados else None,
        )
        self.categoria_dropdown = ft.Dropdown(
            label="Categoria",
            width=300,
            options=[
                ft.dropdown.Option(key=opcao["key"], text=opcao["text"])
                for opcao in self.categorias
            ],
            value=dados["categoria_id"] if dados else None,
        )
        self._formulario = ft.Column(
            [
                self.descricao_input,
                self.valor_input,
                self.data_input,
                self.mes_dropdown,
                self.tipo_dropdown,
                self.categoria_dropdown,
                self.erro_modal,
            ],
            tight=True,
        )

    def _abrir_modal(self, titulo, dados=None):
        """Cria um diálogo novo, com campos novos, e o exibe.

        Reaproveitar um diálogo do overlay trocando o conteúdo fazia os campos
        recriados não sincronizarem com o Python (valores e erros se perdiam).
        """
        self._montar_formulario(dados)
        self.modal = ft.AlertDialog(
            title=ft.Text(titulo),
            content=self._formulario,
            actions=[
                ft.TextButton("Cancelar", on_click=self._fechar_modal),
                ft.ElevatedButton(
                    "Salvar",
                    on_click=self._salvar_transacao,
                    bgcolor=ft.Colors.GREEN_600,
                    color=ft.Colors.WHITE,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(self.modal)

    def _ao_selecionar_mes(self, _evento):
        """Leva a data para o mês escolhido, mantendo o dia (ajustado ao mês)."""
        mes = self.mes_dropdown.value
        try:
            data = datetime.strptime((self.data_input.value or "").strip(), "%Y-%m-%d")
        except ValueError:
            return
        if not mes or data.strftime("%Y-%m") == mes:
            return
        ultimo_dia = calendar.monthrange(int(mes[:4]), int(mes[5:]))[1]
        self.data_input.value = f"{mes}-{min(data.day, ultimo_dia):02d}"
        self.page.update()

    def _criar_linha_acoes(self):
        return ft.Row(
            controls=[
                ft.ElevatedButton(
                    ft.Text("Nova transação", weight=ft.FontWeight.BOLD),
                    height=40,
                    bgcolor=ft.Colors.GREEN_600,
                    color=ft.Colors.WHITE,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8)
                    ),
                    on_click=self._abrir_nova_transacao,
                ),
                self.linha_filtros,
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=20,
        )

    def _criar_chips_filtro(self):
        return [
            ft.Chip(
                label=ft.Text(opcao["text"]),
                on_select=self._alternar_filtro,
                selected_color=ft.Colors.GREEN_600,
                selected=opcao["text"] in self.filtros_ativos,
            )
            for opcao in self.categorias
        ]

    def atualizar_categorias(self):
        try:
            categorias = obter_opcoes_categorias()
        except Exception:
            logger.exception("Não foi possível atualizar as categorias.")
            self.erro_categorias.value = MENSAGEM_BANCO_INDISPONIVEL
            self.erro_categorias.visible = True
            self.page.update()
            return False

        self.categorias = categorias
        self.erro_categorias.value = ""
        self.erro_categorias.visible = False
        nomes_validos = {opcao["text"] for opcao in categorias}
        self.filtros_ativos = [
            nome for nome in self.filtros_ativos if nome in nomes_validos
        ]
        self.linha_filtros.controls = self._criar_chips_filtro()
        self.atualizar_tabela()
        self.ao_alterar_dados(self.filtros_ativos, self.mes_atual)
        return True

    def atualizar_tabela(self):
        linhas = []
        try:
            transacoes = obter_transacoes_formatadas(
                self.filtros_ativos, self.mes_atual
            )
        except Exception:
            logger.exception("Não foi possível carregar as transações na tabela.")
            self.tabela.rows = []
            self.erro_tabela.value = MENSAGEM_BANCO_INDISPONIVEL
            self.erro_tabela.visible = True
            self.page.update()
            return

        self.erro_tabela.value = ""
        self.erro_tabela.visible = False
        for transacao in transacoes:
            cor = (
                ft.Colors.RED_400
                if transacao["eh_despesa"]
                else ft.Colors.GREEN_400
            )
            acoes = ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.EDIT_OUTLINED,
                        icon_color=ft.Colors.BLUE_400,
                        data=transacao,
                        on_click=self._editar_transacao,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_color=ft.Colors.RED_400,
                        data=transacao["id"],
                        on_click=self._excluir_transacao,
                    ),
                ],
                spacing=0,
            )
            linhas.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(transacao["descricao"])),
                        ft.DataCell(ft.Text(transacao["categoria"])),
                        ft.DataCell(ft.Text(transacao["data"])),
                        ft.DataCell(ft.Text(transacao["valor_texto"], color=cor)),
                        ft.DataCell(acoes),
                    ]
                )
            )

        self.tabela.rows = linhas
        self.page.update()

    def _alternar_filtro(self, evento):
        nome = evento.control.label.value
        selecionado = str(evento.data).lower() == "true"
        evento.control.selected = selecionado

        if selecionado and nome not in self.filtros_ativos:
            self.filtros_ativos.append(nome)
        elif not selecionado and nome in self.filtros_ativos:
            self.filtros_ativos.remove(nome)

        self.atualizar_tabela()
        self.ao_alterar_dados(self.filtros_ativos, self.mes_atual)

    def selecionar_mes(self, mes):
        self.mes_atual = mes
        self.atualizar_tabela()
        self.ao_alterar_dados(self.filtros_ativos, self.mes_atual)

    def _abrir_nova_transacao(self, _evento):
        self.id_edicao = None
        self._abrir_modal("Nova transação")

    def _editar_transacao(self, evento):
        dados = evento.control.data
        self.id_edicao = dados["id"]
        self._abrir_modal("Editar transação", dados)

    def _salvar_transacao(self, _evento):
        argumentos = (
            self.descricao_input.value,
            self.valor_input.value,
            self.data_input.value,
            self.mes_dropdown.value,
            self.tipo_dropdown.value,
            self.categoria_dropdown.value,
        )
        if self.id_edicao is None:
            sucesso, mensagem = processar_nova_transacao(*argumentos)
        else:
            sucesso, mensagem = processar_edicao(self.id_edicao, *argumentos)

        if not sucesso:
            # erro dentro do modal: o snackbar ficaria escurecido sob a janela
            self.erro_modal.value = mensagem
            self.erro_modal.visible = True
            self.page.update()
            return

        self.page.pop_dialog()
        self.atualizar_tabela()
        self.ao_alterar_dados(self.filtros_ativos, self.mes_atual)
        mes_salvo = argumentos[3]
        if self.mes_atual and mes_salvo != self.mes_atual:
            mensagem += f" Ela aparece no mês {mes_salvo}."
        self._mostrar_mensagem(mensagem, True)
        self.page.update()

    def _excluir_transacao(self, evento):
        sucesso, mensagem = processar_exclusao(evento.control.data)
        self._mostrar_mensagem(mensagem, sucesso)
        if sucesso:
            self.atualizar_tabela()
            self.ao_alterar_dados(self.filtros_ativos, self.mes_atual)
        self.page.update()

    def _fechar_modal(self, _evento):
        self.page.pop_dialog()

    def _mostrar_mensagem(self, mensagem, sucesso):
        mostrar_mensagem(self.page, mensagem, sucesso)
