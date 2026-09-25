"""Componentes visuais dos indicadores financeiros."""

import flet as ft

from controllers.transaction_controller import obter_resumo_financeiro


class DashboardView:
    def __init__(self):
        self.texto_ganhos = ft.Text("R$ 0,00", size=28, weight=ft.FontWeight.BOLD)
        self.texto_gastos = ft.Text("R$ 0,00", size=28, weight=ft.FontWeight.BOLD)
        self.texto_restante = ft.Text("R$ 0,00", size=28, weight=ft.FontWeight.BOLD)
        self.titulo_ganhos = ft.Text(
            "Ganhos",
            size=16,
            weight=ft.FontWeight.W_500,
            color=ft.Colors.GREEN_400,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self.titulo_gastos = ft.Text(
            "Gastos",
            size=16,
            weight=ft.FontWeight.W_500,
            color=ft.Colors.RED_400,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

        self.control = ft.Row(
            controls=[
                self._criar_card(self.titulo_ganhos, self.texto_ganhos),
                self._criar_card(self.titulo_gastos, self.texto_gastos),
                self._criar_card("Restante", self.texto_restante, ft.Colors.BLUE_400),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    @staticmethod
    def _criar_card(titulo, valor, cor=ft.Colors.WHITE):
        if isinstance(titulo, str):
            titulo = ft.Text(titulo, size=16, weight=ft.FontWeight.W_500, color=cor)

        return ft.Card(
            elevation=5,
            content=ft.Container(
                padding=20,
                width=260,
                content=ft.Column([titulo, valor]),
            ),
        )

    def atualizar(self, filtros_ativos=None, mes_filtro=None):
        ganhos, gastos, restante, nomes_ganhos, nomes_gastos = obter_resumo_financeiro(
            filtros_ativos, mes_filtro
        )
        self.texto_ganhos.value = ganhos
        self.texto_gastos.value = gastos
        self.texto_restante.value = restante
        self.titulo_ganhos.value = (
            f"Ganhos ({'/'.join(nomes_ganhos)})" if nomes_ganhos else "Ganhos"
        )
        self.titulo_gastos.value = (
            f"Gastos ({'/'.join(nomes_gastos)})" if nomes_gastos else "Gastos"
        )
