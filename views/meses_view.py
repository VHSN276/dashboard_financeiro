"""Seletor e formulários de gerenciamento dos meses do dashboard."""

import flet as ft

from controllers.transaction_controller import (
    obter_meses_disponiveis,
    processar_edicao_mes,
    processar_novo_mes,
)


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

        self.control = ft.Row(
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
        )

    def atualizar(self):
        meses = obter_meses_disponiveis()
        if self.mes_atual not in meses:
            self.mes_atual = meses[0] if meses else None

        self.linha_meses.controls = [
            ft.GestureDetector(
                content=ft.TextButton(
                    ft.Text(mes),
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
            f"Opções: {self.mes_em_edicao}"
        )
        self.modal_gerenciar_mes.content = ft.Column(
            [
                ft.ElevatedButton(
                    "Editar mês",
                    icon=ft.Icons.EDIT,
                    bgcolor=ft.Colors.BLUE_600,
                    color=ft.Colors.WHITE,
                    on_click=self._mostrar_formulario_edicao,
                )
            ],
            tight=True,
        )
        self.modal_gerenciar_mes.actions = [
            ft.TextButton("Cancelar", on_click=self._fechar_modal_gerenciar)
        ]
        self.modal_gerenciar_mes.open = True
        self.page.update()

    def _mostrar_formulario_edicao(self, _evento):
        self.novo_nome_mes_input.value = self.mes_em_edicao
        self.modal_gerenciar_mes.title = ft.Text(
            f"Editar mês: {self.mes_em_edicao}"
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
        self.page.snack_bar = ft.SnackBar(
            ft.Text(mensagem),
            bgcolor=ft.Colors.GREEN if sucesso else ft.Colors.RED,
        )
        self.page.snack_bar.open = True
