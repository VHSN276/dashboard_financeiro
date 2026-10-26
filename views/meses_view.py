"""Seletor e formulários de gerenciamento dos meses do dashboard."""

import logging

import flet as ft

from controllers.transaction_controller import (
    obter_meses_disponiveis,
    processar_edicao_mes,
    processar_exclusao_mes,
    processar_exclusao_mes_e_transacoes,
    processar_novo_mes,
)
from database.errors import MENSAGEM_BANCO_INDISPONIVEL
from views.formatacao import formatar_rotulo_mes
from views.mensagens import mostrar_mensagem


logger = logging.getLogger(__name__)


class MesesView:
    def __init__(self, page, ao_selecionar_mes):
        self.page = page
        self.ao_selecionar_mes = ao_selecionar_mes
        self.mes_atual = None
        self.mes_em_edicao = None
        self.linha_meses = ft.Row(
            scroll=ft.ScrollMode.AUTO,
            alignment=ft.MainAxisAlignment.START,
        )
        self.erro_carregamento = ft.Text(
            visible=False,
            color=ft.Colors.RED_300,
            size=13,
        )

        self.nome_mes_input = ft.TextField(
            label="Nome do mês (ex.: 2026-08)", width=300
        )
        self.novo_nome_mes_input = ft.TextField(
            label="Novo nome do mês", width=300
        )
        self.modal_novo_mes = ft.AlertDialog(
            title=ft.Text("Adicionar mês"),
            content=ft.Column([self.nome_mes_input], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=self._fechar_modal_novo_mes),
                ft.ElevatedButton(
                    "Salvar",
                    on_click=self._salvar_novo_mes,
                    bgcolor=ft.Colors.GREEN_600,
                    color=ft.Colors.WHITE,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.modal_gerenciar_mes = ft.AlertDialog(
            title=ft.Text("Gerenciar mês"),
            content=ft.Container(),
            actions=[],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.overlay.extend([self.modal_novo_mes, self.modal_gerenciar_mes])

        self.control = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            "+ Mês",
                            bgcolor=ft.Colors.GREEN_600,
                            color=ft.Colors.WHITE,
                            on_click=self._abrir_modal_novo_mes,
                        ),
                        ft.Container(expand=True, content=self.linha_meses),
                    ],
                    spacing=16,
                ),
                self.erro_carregamento,
            ],
            spacing=4,
        )

    def atualizar(self):
        try:
            meses = obter_meses_disponiveis()
        except Exception:
            logger.exception("Não foi possível carregar os meses na interface.")
            self.erro_carregamento.value = MENSAGEM_BANCO_INDISPONIVEL
            self.erro_carregamento.visible = True
            self.page.update()
            self.ao_selecionar_mes(self.mes_atual)
            return

        self.erro_carregamento.value = ""
        self.erro_carregamento.visible = False
        if self.mes_atual not in meses:
            self.mes_atual = meses[0] if meses else None

        self.linha_meses.controls = [
            ft.GestureDetector(
                content=ft.TextButton(
                    ft.Text(formatar_rotulo_mes(mes), data=mes),
                    data=mes,
                    style=ft.ButtonStyle(
                        color=(
                            ft.Colors.GREEN_400
                            if mes == self.mes_atual
                            else ft.Colors.WHITE54
                        )
                    ),
                    on_click=self._selecionar_mes,
                ),
                data=mes,
                on_secondary_tap=self._abrir_opcoes_mes,
            )
            for mes in meses
        ]
        self.page.update()
        self.ao_selecionar_mes(self.mes_atual)

    def _selecionar_mes(self, evento):
        self.mes_atual = evento.control.data
        self.atualizar()

    def _abrir_modal_novo_mes(self, _evento):
        self.nome_mes_input.value = ""
        self.modal_novo_mes.open = True
        self.page.update()

    def _fechar_modal_novo_mes(self, _evento):
        self.modal_novo_mes.open = False
        self.page.update()

    def _salvar_novo_mes(self, _evento):
        sucesso, mensagem = processar_novo_mes(self.nome_mes_input.value)
        self._mostrar_mensagem(mensagem, sucesso)
        if sucesso:
            self.modal_novo_mes.open = False
            self.atualizar()
        else:
            self.page.update()

    def _abrir_opcoes_mes(self, evento):
        self.mes_em_edicao = evento.control.data
        self.modal_gerenciar_mes.title = ft.Text(
            f"Opções: {formatar_rotulo_mes(self.mes_em_edicao)}"
        )
        self.modal_gerenciar_mes.content = ft.Column(
            [
                ft.ElevatedButton(
                    "Editar mês",
                    icon=ft.Icons.EDIT,
                    bgcolor=ft.Colors.BLUE_600,
                    color=ft.Colors.WHITE,
                    on_click=self._mostrar_formulario_edicao,
                ),
                ft.ElevatedButton(
                    "Excluir mês",
                    icon=ft.Icons.DELETE_OUTLINE,
                    bgcolor=ft.Colors.RED_700,
                    color=ft.Colors.WHITE,
                    on_click=self._mostrar_confirmacao_exclusao,
                ),
                ft.ElevatedButton(
                    "Excluir mês e transações",
                    icon=ft.Icons.DELETE_OUTLINE,
                    bgcolor=ft.Colors.RED_900,
                    color=ft.Colors.WHITE,
                    on_click=self._mostrar_confirmacao_exclusao_com_transacoes,
                ),
            ],
            tight=True,
        )
        self.modal_gerenciar_mes.actions = [
            ft.TextButton("Cancelar", on_click=self._fechar_modal_gerenciar)
        ]
        self.modal_gerenciar_mes.open = True
        self.page.update()

    def _mostrar_confirmacao_exclusao(self, _evento):
        self.modal_gerenciar_mes.title = ft.Text(
            f"Excluir mês: {formatar_rotulo_mes(self.mes_em_edicao)}?"
        )
        self.modal_gerenciar_mes.content = ft.Text(
            "O mês será removido da lista. As transações registradas nesse período "
            "serão mantidas."
        )
        self.modal_gerenciar_mes.actions = [
            ft.TextButton("Cancelar", on_click=self._fechar_modal_gerenciar),
            ft.ElevatedButton(
                "Excluir mês",
                icon=ft.Icons.DELETE_OUTLINE,
                on_click=self._excluir_mes,
                bgcolor=ft.Colors.RED_700,
                color=ft.Colors.WHITE,
            ),
        ]
        self.page.update()

    def _mostrar_confirmacao_exclusao_com_transacoes(self, _evento):
        mes = formatar_rotulo_mes(self.mes_em_edicao)
        self.modal_gerenciar_mes.title = ft.Text(
            f"Excluir {mes} e todas as transações?"
        )
        self.modal_gerenciar_mes.content = ft.Text(
            "O mês e todas as transações registradas nele serão excluídos "
            "permanentemente. Essa ação não pode ser desfeita."
        )
        self.modal_gerenciar_mes.actions = [
            ft.TextButton("Cancelar", on_click=self._fechar_modal_gerenciar),
            ft.ElevatedButton(
                "Excluir tudo",
                icon=ft.Icons.DELETE_OUTLINE,
                on_click=self._excluir_mes_e_transacoes,
                bgcolor=ft.Colors.RED_900,
                color=ft.Colors.WHITE,
            ),
        ]
        self.page.update()

    def _excluir_mes(self, _evento):
        nome_mes = self.mes_em_edicao
        sucesso, mensagem = processar_exclusao_mes(nome_mes)
        self._mostrar_mensagem(mensagem, sucesso)
        if sucesso:
            if self.mes_atual == nome_mes:
                self.mes_atual = None
            self.modal_gerenciar_mes.open = False
            self.atualizar()
        else:
            self.page.update()

    def _excluir_mes_e_transacoes(self, _evento):
        nome_mes = self.mes_em_edicao
        sucesso, mensagem = processar_exclusao_mes_e_transacoes(nome_mes)
        self._mostrar_mensagem(mensagem, sucesso)
        if sucesso:
            if self.mes_atual == nome_mes:
                self.mes_atual = None
            self.modal_gerenciar_mes.open = False
            self.atualizar()
        else:
            self.page.update()

    def _mostrar_formulario_edicao(self, _evento):
        self.novo_nome_mes_input.value = self.mes_em_edicao
        self.modal_gerenciar_mes.title = ft.Text(
            f"Editar mês: {formatar_rotulo_mes(self.mes_em_edicao)}"
        )
        self.modal_gerenciar_mes.content = ft.Column(
            [self.novo_nome_mes_input], tight=True
        )
        self.modal_gerenciar_mes.actions = [
            ft.TextButton("Cancelar", on_click=self._fechar_modal_gerenciar),
            ft.ElevatedButton(
                "Salvar alteração",
                on_click=self._salvar_edicao_mes,
                bgcolor=ft.Colors.BLUE_600,
                color=ft.Colors.WHITE,
            ),
        ]
        self.page.update()

    def _salvar_edicao_mes(self, _evento):
        nome_antigo = self.mes_em_edicao
        nome_novo = (self.novo_nome_mes_input.value or "").strip()
        sucesso, mensagem = processar_edicao_mes(nome_antigo, nome_novo)
        self._mostrar_mensagem(mensagem, sucesso)
        if sucesso:
            if self.mes_atual == nome_antigo:
                self.mes_atual = nome_novo
            self.modal_gerenciar_mes.open = False
            self.atualizar()
        else:
            self.page.update()

    def _fechar_modal_gerenciar(self, _evento):
        self.modal_gerenciar_mes.open = False
        self.page.update()

    def _mostrar_mensagem(self, mensagem, sucesso):
        mostrar_mensagem(self.page, mensagem, sucesso)
