"""Ponto de entrada e composição das views da aplicação."""

import flet as ft

from views.dashboard_view import DashboardView
from views.transacoes_view import TransacoesView


def main(page: ft.Page):
    page.title = "Controle Financeiro"
    page.window_width = 1100
    page.window_height = 760
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 24

    dashboard = DashboardView()

    def atualizar_dashboard(filtros_ativos):
        dashboard.atualizar(filtros_ativos)
        page.update()

    transacoes = TransacoesView(page, atualizar_dashboard)

    page.add(
        dashboard.control,
        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        transacoes.control,
    )

    transacoes.atualizar_tabela()
    atualizar_dashboard(transacoes.filtros_ativos)


if __name__ == "__main__":
    ft.run(main)
