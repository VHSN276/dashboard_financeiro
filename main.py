"""Ponto de entrada e composição das views da aplicação."""

import flet as ft

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

    page.add(
        meses.control,
        ft.Divider(height=12, color=ft.Colors.TRANSPARENT),
        dashboard.control,
        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        transacoes.control,
    )

    meses.atualizar()


if __name__ == "__main__":
    ft.run(main)
