"""Ponto de entrada e composição das views da aplicação."""

import os
import sys

# Algumas combinações de GTK/GNOME no Wayland falham ao consultar a chave
# antiga "antialiasing". Quando o XWayland está disponível, use o backend
# X11 para contornar esse problema antes de o Flet iniciar a janela nativa.
if (
    sys.platform == "linux"
    and os.environ.get("WAYLAND_DISPLAY")
    and os.environ.get("DISPLAY")
    and os.environ.get("GDK_BACKEND", "").strip().lower() in {"", "wayland"}
):
    os.environ["GDK_BACKEND"] = "x11"

import flet as ft

from views.categorias_view import CategoriasView
from views.dashboard_view import DashboardView
from views.meses_view import MesesView
from views.transacoes_view import TransacoesView


def main(page: ft.Page):
    page.title = "Controle Financeiro"
    page.window_width = 1100
    page.window_height = 760
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 24

    dashboard = DashboardView()

    def atualizar_dashboard(filtros_ativos, mes_filtro):
        dashboard.atualizar(filtros_ativos, mes_filtro)
        page.update()

    transacoes = TransacoesView(page, atualizar_dashboard)
    meses = MesesView(page, transacoes.selecionar_mes)

    def atualizar_categorias():
        transacoes.atualizar_categorias()

    categorias = CategoriasView(page, atualizar_categorias)

    page.add(
        ft.Row(
            controls=[
                ft.Container(content=meses.control, expand=True),
                categorias.control,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        ft.Divider(height=12, color=ft.Colors.TRANSPARENT),
        dashboard.control,
        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        transacoes.control,
    )

    meses.atualizar()


if __name__ == "__main__":
    ft.run(main)
