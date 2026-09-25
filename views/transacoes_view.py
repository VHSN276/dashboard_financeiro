"""Formulário, filtros e tabela de transações."""

from datetime import datetime

import flet as ft

from controllers.transaction_controller import (
    obter_opcoes_categorias,
    obter_transacoes_formatadas,
    processar_edicao,
    processar_exclusao,
    processar_nova_transacao,
)


class TransacoesView:
    def __init__(self, page, ao_alterar_dados):
        self.page = page
        self.ao_alterar_dados = ao_alterar_dados
        self.filtros_ativos = []
        self.mes_atual = None
        self.id_edicao = None

        self.descricao_input = ft.TextField(label="Descrição", width=300)
        self.valor_input = ft.TextField(
            label="Valor (R$)", width=300, keyboard_type=ft.KeyboardType.NUMBER
        )
        self.data_input = ft.TextField(
            label="Data (AAAA-MM-DD)",
            width=300,
            value=datetime.today().strftime("%Y-%m-%d"),
        )
        self.tipo_dropdown = ft.Dropdown(
            label="Tipo",
            width=300,
            options=[
                ft.dropdown.Option(key="RECEITA", text="Receita"),
                ft.dropdown.Option(key="DESPESA", text="Despesa"),
            ],
        )
        self.categorias = obter_opcoes_categorias()
        self.categoria_dropdown = ft.Dropdown(
            label="Categoria",
            width=300,
            options=[
                ft.dropdown.Option(key=opcao["key"], text=opcao["text"])
                for opcao in self.categorias
            ],
        )
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

        self.modal = ft.AlertDialog(
            title=ft.Text("Nova transação"),
            content=ft.Column(
                [
                    self.descricao_input,
                    self.valor_input,
                    self.data_input,
                    self.tipo_dropdown,
                    self.categoria_dropdown,
                ],
                tight=True,
            ),
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
        self.page.overlay.append(self.modal)

        self.control = ft.Column(
            controls=[self._criar_linha_acoes(), self.tabela],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _criar_linha_acoes(self):
        chips = [
            ft.Chip(
                label=ft.Text(opcao["text"]),
                on_select=self._alternar_filtro,
                selected_color=ft.Colors.GREEN_600,
            )
            for opcao in self.categorias
        ]
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
                ft.Row(controls=chips, scroll=ft.ScrollMode.AUTO, expand=True),
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=20,
        )

    def atualizar_tabela(self):
        linhas = []
        for transacao in obter_transacoes_formatadas(
            self.filtros_ativos, self.mes_atual
        ):
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
        self.modal.title = ft.Text("Nova transação")
        self.descricao_input.value = ""
        self.valor_input.value = ""
        self.data_input.value = datetime.today().strftime("%Y-%m-%d")
        self.tipo_dropdown.value = None
        self.categoria_dropdown.value = None
        self.modal.open = True
        self.page.update()

    def _editar_transacao(self, evento):
        dados = evento.control.data
        self.id_edicao = dados["id"]
        self.modal.title = ft.Text("Editar transação")
        self.descricao_input.value = dados["descricao"]
        self.valor_input.value = dados["valor_puro"]
        self.data_input.value = dados["data"]
        self.tipo_dropdown.value = dados["tipo_puro"]
        self.categoria_dropdown.value = dados["categoria_id"]
        self.modal.open = True
        self.page.update()

    def _salvar_transacao(self, _evento):
        argumentos = (
            self.descricao_input.value,
            self.valor_input.value,
            self.data_input.value,
            self.tipo_dropdown.value,
            self.categoria_dropdown.value,
        )
        if self.id_edicao is None:
            sucesso, mensagem = processar_nova_transacao(*argumentos)
        else:
            sucesso, mensagem = processar_edicao(self.id_edicao, *argumentos)

        self._mostrar_mensagem(mensagem, sucesso)
        if sucesso:
            self.modal.open = False
            self.atualizar_tabela()
            self.ao_alterar_dados(self.filtros_ativos, self.mes_atual)
        self.page.update()

    def _excluir_transacao(self, evento):
        sucesso, mensagem = processar_exclusao(evento.control.data)
        self._mostrar_mensagem(mensagem, sucesso)
        if sucesso:
            self.atualizar_tabela()
            self.ao_alterar_dados(self.filtros_ativos, self.mes_atual)
        self.page.update()

    def _fechar_modal(self, _evento):
        self.modal.open = False
        self.page.update()

    def _mostrar_mensagem(self, mensagem, sucesso):
        self.page.snack_bar = ft.SnackBar(
            ft.Text(mensagem),
            bgcolor=ft.Colors.GREEN if sucesso else ft.Colors.RED,
        )
        self.page.snack_bar.open = True
