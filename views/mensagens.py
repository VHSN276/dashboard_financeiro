"""Mensagens rápidas (snackbar) compartilhadas pelas views."""

import flet as ft


def mostrar_mensagem(page, mensagem, sucesso):
    """Exibe um snackbar verde (sucesso) ou vermelho (erro).

    Usa page.show_dialog: atribuir page.snack_bar não exibe nada no Flet 0.80+.
    """
    page.show_dialog(
        ft.SnackBar(
            ft.Text(mensagem),
            bgcolor=ft.Colors.GREEN if sucesso else ft.Colors.RED,
        )
    )
