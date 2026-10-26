"""Interface de gerenciamento das categorias de transação."""

import logging

import flet as ft

from controllers.transaction_controller import (
    obter_categorias,
    processar_edicao_categoria,
    processar_exclusao_categoria,
    processar_nova_categoria,
)
from database.errors import MENSAGEM_BANCO_INDISPONIVEL
from views.mensagens import mostrar_mensagem


logger = logging.getLogger(__name__)


class CategoriasView:
    def __init__(self, page, ao_alterar):
        self.page = page
        self.ao_alterar = ao_alterar
        self.categoria_em_edicao = None

        self.erro = ft.Text(color=ft.Colors.RED_300, size=13, visible=False)
        self.nome_input = ft.TextField(label="Nome", width=420, max_length=50)
        self.tipo_dropdown = ft.Dropdown(
            label="Tipo",
            width=420,
            options=[
                ft.dropdown.Option(key="RECEITA", text="Receita"),
                ft.dropdown.Option(key="DESPESA", text="Despesa"),
            ],
        )
        self.tabela = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Categoria")),
                ft.DataColumn(ft.Text("Tipo")),
                ft.DataColumn(ft.Text("Ações")),
            ],
            rows=[],
        )
        self.modal = ft.AlertDialog(
            title=ft.Text("Categorias"),
            content=ft.Container(width=520),
            actions=[],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.overlay.append(self.modal)
        self.control = ft.ElevatedButton(
            "Categorias",
            icon=ft.Icons.CATEGORY_OUTLINED,
            on_click=self._abrir,
        )

    def _abrir(self, _evento):
        self._mostrar_lista()
        self.modal.open = True
        self.page.update()

    def _mostrar_lista(self, mensagem=None, sucesso=False):
        self.categoria_em_edicao = None
        self.modal.title = ft.Text("Categorias")
        self.erro.value = mensagem or ""
        self.erro.visible = bool(mensagem) and not sucesso
        self._recarregar_tabela()
        self.modal.content = ft.Container(
            width=520,
            content=ft.Column(
                controls=[
                    self.erro,
                    ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                "Nova categoria",
                                icon=ft.Icons.ADD,
                                on_click=self._nova_categoria,
                                bgcolor=ft.Colors.GREEN_600,
                                color=ft.Colors.WHITE,
                            )
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                    self.tabela,
                ],
                tight=True,
                scroll=ft.ScrollMode.AUTO,
            ),
        )
        self.modal.actions = [
            ft.TextButton("Fechar", on_click=self._fechar),
        ]
        if mensagem and sucesso:
            self._mostrar_mensagem(mensagem, True)

    def _recarregar_tabela(self):
        try:
            categorias = obter_categorias()
        except Exception:
            logger.exception("Não foi possível carregar categorias na interface.")
            categorias = None
            self.erro.value = MENSAGEM_BANCO_INDISPONIVEL
            self.erro.visible = True

        linhas = [
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(categoria["nome"])),
                    ft.DataCell(
                        ft.Text(
                            "Receita"
                            if categoria["tipo"] == "RECEITA"
                            else "Despesa"
                        )
                    ),
                    ft.DataCell(
                        ft.Row(
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.EDIT_OUTLINED,
                                    tooltip="Editar",
                                    data=categoria,
                                    on_click=self._editar_categoria,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_color=ft.Colors.RED_400,
                                    tooltip="Excluir",
                                    data=categoria["id"],
                                    on_click=self._confirmar_exclusao,
                                ),
                            ],
                            spacing=0,
                        )
                    ),
                ]
            )
            for categoria in (categorias or [])
        ]
        if categorias == []:
            linhas.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text("Nenhuma categoria cadastrada.")),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                    ]
                )
            )
        self.tabela.rows = linhas

    def _nova_categoria(self, _evento):
        self._mostrar_formulario()

    def _editar_categoria(self, evento):
        categoria = evento.control.data
        self._mostrar_formulario(categoria)

    def _mostrar_formulario(self, categoria=None):
        self.categoria_em_edicao = categoria["id"] if categoria else None
        self.erro.value = ""
        self.erro.visible = False
        self.nome_input.value = categoria["nome"] if categoria else ""
        self.tipo_dropdown.value = categoria["tipo"] if categoria else None
        self.modal.title = ft.Text(
            "Editar categoria" if categoria else "Nova categoria"
        )
        self.modal.content = ft.Container(
            width=460,
            content=ft.Column(
                [self.nome_input, self.tipo_dropdown, self.erro],
                tight=True,
            ),
        )
        self.modal.actions = [
            ft.TextButton("Cancelar", on_click=self._voltar_para_lista),
            ft.ElevatedButton(
                "Salvar",
                on_click=self._salvar_categoria,
                bgcolor=ft.Colors.GREEN_600,
                color=ft.Colors.WHITE,
            ),
        ]
        self.page.update()

    def _salvar_categoria(self, _evento):
        if self.categoria_em_edicao is None:
            sucesso, mensagem = processar_nova_categoria(
                self.nome_input.value,
                self.tipo_dropdown.value,
            )
        else:
            sucesso, mensagem = processar_edicao_categoria(
                self.categoria_em_edicao,
                self.nome_input.value,
                self.tipo_dropdown.value,
            )

        if sucesso:
            self._dados_alterados(mensagem)
        else:
            self.erro.value = mensagem
            self.erro.visible = True
            self.page.update()

    def _confirmar_exclusao(self, evento):
        self.categoria_em_edicao = evento.control.data
        self.erro.value = ""
        self.erro.visible = False
        self.modal.title = ft.Text("Excluir categoria?")
        self.modal.content = ft.Container(
            width=460,
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Categorias vinculadas a transações não podem ser excluídas. "
                        "Reclassifique essas transações primeiro."
                    ),
                    self.erro,
                ],
                tight=True,
            ),
        )
        self.modal.actions = [
            ft.TextButton("Cancelar", on_click=self._voltar_para_lista),
            ft.ElevatedButton(
                "Excluir",
                icon=ft.Icons.DELETE_OUTLINE,
                on_click=self._excluir_categoria,
                bgcolor=ft.Colors.RED_700,
                color=ft.Colors.WHITE,
            ),
        ]
        self.page.update()

    def _excluir_categoria(self, _evento):
        sucesso, mensagem = processar_exclusao_categoria(
            self.categoria_em_edicao
        )
        if sucesso:
            self._dados_alterados(mensagem)
        else:
            self._mostrar_lista(mensagem)
            self.page.update()

    def _dados_alterados(self, mensagem):
        self.ao_alterar()
        self._mostrar_lista(mensagem, sucesso=True)
        self.page.update()

    def _voltar_para_lista(self, _evento):
        self._mostrar_lista()
        self.page.update()

    def _fechar(self, _evento):
        self.modal.open = False
        self.page.update()

    def _mostrar_mensagem(self, mensagem, sucesso):
        mostrar_mensagem(self.page, mensagem, sucesso)
