import flet as ft

def main(page: ft.Page):
    # 1. Configurações da Janela
    page.title = "Controle Financeiro"
    page.window_width = 900
    page.window_height = 700
    page.theme_mode = ft.ThemeMode.DARK 
    page.padding = 30

    # 2. Criando a Seleção de Meses (Baseado no topo do seu desenho)
    linha_meses = ft.Row(
        controls=[
            ft.TextButton("Mês 1", style=ft.ButtonStyle(color=ft.Colors.WHITE54)),
            ft.TextButton("Mês 2", style=ft.ButtonStyle(color=ft.Colors.WHITE54)),
            ft.TextButton("Mês 3", style=ft.ButtonStyle(color=ft.Colors.GREEN_400)), # Exemplo de mês "Ativo"
            ft.TextButton("Mês 4", style=ft.ButtonStyle(color=ft.Colors.WHITE54)),
            ft.TextButton("Mês 5", style=ft.ButtonStyle(color=ft.Colors.WHITE54)),
        ],
        scroll=ft.ScrollMode.AUTO, # Permite rolar para o lado se tiverem muitos meses
        alignment=ft.MainAxisAlignment.START
    )

    # 3. Criando os Cards de Resumo
    def criar_card(titulo, valor, cor_texto):
        return ft.Card(
            elevation=5,
            content=ft.Container(
                padding=20,
                width=260, # Ajustado levemente para caber bem na tela
                content=ft.Column([
                    ft.Text(titulo, size=16, weight=ft.FontWeight.W_500, color=cor_texto),
                    ft.Text(f"R$ {valor}", size=28, weight=ft.FontWeight.BOLD)
                ])
            )
        )

    card_ganhos = criar_card("Ganhos", "1.200", ft.Colors.GREEN_400)
    card_gastos = criar_card("Gastos", "21,90", ft.Colors.RED_400)
    card_restante = criar_card("Restante", "1.178,10", ft.Colors.BLUE_400)

    linha_resumo = ft.Row(
        controls=[card_ganhos, card_gastos, card_restante],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    # 4. A Linha de Ações: Botão + NEW e os Filtros (Bolhas)
    def criar_linha_acoes():
        botao_add = ft.ElevatedButton(
            ft.Text("New", weight=ft.FontWeight.BOLD),
            height=40,
            bgcolor=ft.Colors.GREEN_600,
            color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)) # Deixa menos arredondado
        )
        
        # O ft.Chip é perfeito para desenhar essas pílulas ovais do seu rascunho
        filtros = ft.Row([
            ft.Chip(label=ft.Text("Todos")),
            ft.Chip(label=ft.Text("Fixos")),
            ft.Chip(label=ft.Text("Lazer")),
            ft.Chip(label=ft.Text("Streamings")),
        ])
        
        return ft.Row(
            controls=[botao_add, filtros], 
            alignment=ft.MainAxisAlignment.START, 
            spacing=30 # Dá um espaço entre o botão e os filtros
        )

    # 5. A Tabela de Transações
    def visualizar_despesas():
        return ft.DataTable(
            width=float("inf"), # Faz a tabela esticar até o fim da tela
            columns=[
                ft.DataColumn(ft.Text("Descrição", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Categoria", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Data", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Valor", weight=ft.FontWeight.BOLD)),
            ],
            rows=[
                # Linha de exemplo simulando o Spotify do seu caderno
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text("Spotify")),
                        ft.DataCell(ft.Text("Streaming")),
                        ft.DataCell(ft.Text("12/10/2023")),
                        ft.DataCell(ft.Text("- R$ 21,90", color=ft.Colors.RED_400)),
                    ],
                ),
            ],
        )

    # 6. Adicionando tudo na tela (Na ordem exata do seu desenho)
    page.add(
        linha_meses,
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        
        linha_resumo,
        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        
        criar_linha_acoes(),
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        
        visualizar_despesas()
    )

if __name__ == "__main__":
    ft.run(main) # Atualizado para o comando moderno do Flet