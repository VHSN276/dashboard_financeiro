import flet as ft
from datetime import datetime
# Importe a sua função do banco aqui (ajuste o caminho se necessário)
from database.operations import adicionar_nova_transacao
from controllers.transaction_controller import processar_nova_transacao, obter_transacoes_formatadas, obter_opcoes_categorias, obter_resumo_financeiro
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
    # Transformamos os textos em variáveis globais da tela para podermos atualizá-los
    texto_ganhos = ft.Text("R$ 0,00", size=28, weight=ft.FontWeight.BOLD)
    texto_gastos = ft.Text("R$ 0,00", size=28, weight=ft.FontWeight.BOLD)
    texto_restante = ft.Text("R$ 0,00", size=28, weight=ft.FontWeight.BOLD)

    def criar_card(titulo, texto_dinamico, cor_texto):
        return ft.Card(
            elevation=5,
            content=ft.Container(
                padding=20,
                width=260,
                content=ft.Column([
                    ft.Text(titulo, size=16, weight=ft.FontWeight.W_500, color=cor_texto),
                    texto_dinamico # Injeta a variável de texto aqui
                ])
            )
        )

    card_ganhos = criar_card("Ganhos", texto_ganhos, ft.Colors.GREEN_400)
    card_gastos = criar_card("Gastos", texto_gastos, ft.Colors.RED_400)
    card_restante = criar_card("Restante", texto_restante, ft.Colors.BLUE_400)

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
    # Carrega as categorias do banco via Controller
    lista_categorias_db = obter_opcoes_categorias()
    # Monta as opções do Flet dinamicamente
    opcoes_dropdown = []
    for cat in lista_categorias_db:
        opcoes_dropdown.append(ft.dropdown.Option(key=cat["key"], text=cat["text"]))
        
    categoria_dropdown = ft.Dropdown(label="Categoria", width=300, options=opcoes_dropdown)

    # 4.2 Lógica dos botões do Modal
    def fechar_modal(e):
        modal_novo.open = False
        page.update()

    def atualizar_cards_resumo():
        ganhos, gastos, restante = obter_resumo_financeiro()
        
        texto_ganhos.value = ganhos
        texto_gastos.value = gastos
        texto_restante.value = restante
        
        page.update()
        
    # Chama a função para carregar os números ao abrir o app
    atualizar_cards_resumo()

    def salvar_transacao(e):
        # Envia tudo como texto para o Controlador decidir o que fazer
        sucesso, mensagem = processar_nova_transacao(
            descricao=descricao_input.value,
            valor_str=valor_input.value,
            data=data_input.value,
            tipo=tipo_dropdown.value,
            categoria_id_str=categoria_dropdown.value
        )
        # Configura a cor do aviso baseado no sucesso ou erro
        cor_aviso = ft.Colors.GREEN if sucesso else ft.Colors.RED
        page.snack_bar = ft.SnackBar(ft.Text(mensagem), bgcolor=cor_aviso)
        page.snack_bar.open = True

        # Se deu certo, limpa os campos e fecha o modal
        if sucesso:
            descricao_input.value = ""
            valor_input.value = ""
            tipo_dropdown.value = None
            categoria_dropdown.value = None
            modal_novo.open = False

            # Atualiza a tabela com o novo registro!
            atualizar_tabela()
            atualizar_cards_resumo()
        
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
    # 5. A Tabela de Transações (Dinâmica)
    tabela_despesas = ft.DataTable(
        width=float("inf"),
        columns=[
            ft.DataColumn(ft.Text("Descrição", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Categoria", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Data", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Valor", weight=ft.FontWeight.BOLD)),
        ],
        rows=[] # Começa vazia
    )

    def atualizar_tabela():
        """Pede os dados ao Controller e recria as linhas da tabela."""
        tabela_despesas.rows.clear()
        
        transacoes = obter_transacoes_formatadas()
        
        for t in transacoes:
            # Define a cor baseada no tipo (Despesa = Vermelho, Receita = Verde)
            cor_texto = ft.Colors.RED_400 if t["eh_despesa"] else ft.Colors.GREEN_400
            
            tabela_despesas.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(t["descricao"])),
                        ft.DataCell(ft.Text(t["categoria"])),
                        ft.DataCell(ft.Text(t["data"])),
                        ft.DataCell(ft.Text(t["valor_texto"], color=cor_texto)),
                    ]
                )
            )
        page.update()

    # Chama a função para carregar os dados assim que o app abrir
    atualizar_tabela()

    # 7. Adicionando tudo na tela
    page.add(
        linha_meses,
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        linha_resumo,
        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        criar_linha_acoes(),
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        tabela_despesas
    )

if __name__ == "__main__":
    ft.run(main)