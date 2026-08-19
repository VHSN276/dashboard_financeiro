import flet as ft
from datetime import datetime
# Importe a sua função do banco aqui (ajuste o caminho se necessário)
from database.operations import adicionar_nova_transacao 

def main(page: ft.Page):
    # 1. Configurações da Janela
    page.title = "Controle Financeiro"
    page.window_width = 900
    page.window_height = 700
    page.theme_mode = ft.ThemeMode.DARK 
    page.padding = 30

    # 2. Criando a Seleção de Meses
    linha_meses = ft.Row(
        controls=[
            ft.TextButton("Mês 1", style=ft.ButtonStyle(color=ft.Colors.WHITE54)),
            ft.TextButton("Mês 2", style=ft.ButtonStyle(color=ft.Colors.WHITE54)),
            ft.TextButton("Mês 3", style=ft.ButtonStyle(color=ft.Colors.GREEN_400)), 
            ft.TextButton("Mês 4", style=ft.ButtonStyle(color=ft.Colors.WHITE54)),
            ft.TextButton("Mês 5", style=ft.ButtonStyle(color=ft.Colors.WHITE54)),
        ],
        scroll=ft.ScrollMode.AUTO, 
        alignment=ft.MainAxisAlignment.START
    )

    # 3. Criando os Cards de Resumo
    def criar_card(titulo, valor, cor_texto):
        return ft.Card(
            elevation=5,
            content=ft.Container(
                padding=20,
                width=260,
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


    # =====================================================================
    # 4. SESSÃO DO FORMULÁRIO (MODAL) E BANCO DE DADOS
    # =====================================================================
    
    # 4.1 Campos de entrada
    descricao_input = ft.TextField(label="Descrição", width=300)
    valor_input = ft.TextField(label="Valor (R$)", width=300, keyboard_type=ft.KeyboardType.NUMBER)
    data_input = ft.TextField(label="Data (AAAA-MM-DD)", width=300, value=datetime.today().strftime('%Y-%m-%d'))
    tipo_dropdown = ft.Dropdown(label="Tipo", width=300, options=[ft.dropdown.Option("Receita"), ft.dropdown.Option("Despesa")])
    categoria_dropdown = ft.Dropdown(label="Categoria", width=300, options=[
        ft.dropdown.Option(key="1", text="Alimentação"),
        ft.dropdown.Option(key="2", text="Salário"),
        ft.dropdown.Option(key="3", text="Moradia"),
        ft.dropdown.Option(key="4", text="Streaming"),
    ])

    # 4.2 Lógica dos botões do Modal
    def fechar_modal(e):
        modal_novo.open = False
        page.update()

    def salvar_transacao(e):
        try:
            # Substitui vírgula por ponto para o banco aceitar
            valor_formatado = float(valor_input.value.replace(",", "."))
            
            # Envia para o MySQL
            sucesso = adicionar_nova_transacao(
                descricao=descricao_input.value,
                valor=valor_formatado,
                data=data_input.value,
                tipo=tipo_dropdown.value,
                categoria_id=int(categoria_dropdown.value)
            )

            if sucesso:
                # Mostra aviso de sucesso
                page.snack_bar = ft.SnackBar(ft.Text("Transação salva com sucesso!"), bgcolor=ft.Colors.GREEN)
                page.snack_bar.open = True
                
                # Limpa os campos para a próxima
                descricao_input.value = ""
                valor_input.value = ""
                tipo_dropdown.value = None
                categoria_dropdown.value = None
                
                modal_novo.open = False # <-- Ajuste aqui
                page.update()
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Erro ao salvar no banco de dados."), bgcolor=ft.Colors.RED)
                page.snack_bar.open = True
                page.update()

        except Exception as erro:
            # Caso o usuário deixe algo em branco ou digite letras no valor
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro: Verifique os campos preenchidos. Detalhe: {erro}"), bgcolor=ft.Colors.RED)
            page.snack_bar.open = True
            page.update()

    # 4.3 Criação da janela Modal
    modal_novo = ft.AlertDialog(
        title=ft.Text("Nova Transação"),
        content=ft.Column([descricao_input, valor_input, data_input, tipo_dropdown, categoria_dropdown], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=fechar_modal),
            ft.ElevatedButton("Salvar", on_click=salvar_transacao, bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def abrir_modal(e):
        page.overlay.append(modal_novo) 
        modal_novo.open = True
        page.update()
        
    # =====================================================================


    # 5. A Linha de Ações: Botão + NEW e os Filtros (Bolhas)
    def criar_linha_acoes():
        botao_add = ft.ElevatedButton(
            ft.Text("New", weight=ft.FontWeight.BOLD),
            height=40,
            bgcolor=ft.Colors.GREEN_600,
            color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            on_click=abrir_modal # <-- CONECTAMOS O MODAL AQUI!
        )
        
        filtros = ft.Row([
            ft.Chip(label=ft.Text("Todos")),
            ft.Chip(label=ft.Text("Fixos")),
            ft.Chip(label=ft.Text("Lazer")),
            ft.Chip(label=ft.Text("Streamings")),
        ])
        
        return ft.Row(
            controls=[botao_add, filtros], 
            alignment=ft.MainAxisAlignment.START, 
            spacing=30
        )

    # 6. A Tabela de Transações
    def visualizar_despesas():
        return ft.DataTable(
            width=float("inf"), 
            columns=[
                ft.DataColumn(ft.Text("Descrição", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Categoria", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Data", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Valor", weight=ft.FontWeight.BOLD)),
            ],
            rows=[
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

    # 7. Adicionando tudo na tela
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
    ft.run(main)