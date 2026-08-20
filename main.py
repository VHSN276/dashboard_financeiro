import flet as ft
from datetime import datetime
# Importe a sua função do banco aqui (ajuste o caminho se necessário)
from database.operations import adicionar_nova_transacao
from controllers.transaction_controller import processar_nova_transacao, obter_transacoes_formatadas, obter_opcoes_categorias, obter_resumo_financeiro, processar_exclusao, processar_edicao
def main(page: ft.Page):
    # 1. Configurações da Janela
    page.title = "Controle Financeiro"
    page.window_width = 900
    page.window_height = 700
    page.theme_mode = ft.ThemeMode.DARK 
    page.padding = 30

    estado_app = {
        "id_edicao": None,
        "filtros_ativos": [] # <-- Mudamos para uma lista!
    }

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
    texto_ganhos = ft.Text("R$ 0,00", size=28, weight=ft.FontWeight.BOLD)
    texto_gastos = ft.Text("R$ 0,00", size=28, weight=ft.FontWeight.BOLD)
    texto_restante = ft.Text("R$ 0,00", size=28, weight=ft.FontWeight.BOLD)
    
    # Transformamos o Ganhos em variável dinâmica também!
    titulo_ganhos = ft.Text("Ganhos", size=16, weight=ft.FontWeight.W_500, color=ft.Colors.GREEN_400, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
    titulo_gastos = ft.Text("Gastos", size=16, weight=ft.FontWeight.W_500, color=ft.Colors.RED_400, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)

    def criar_card(titulo_dinamico, texto_dinamico, cor_texto):
        # Se você passar um texto simples (string), ele cria o componente na hora
        if isinstance(titulo_dinamico, str):
            titulo_dinamico = ft.Text(titulo_dinamico, size=16, weight=ft.FontWeight.W_500, color=cor_texto)
            
        return ft.Card(
            elevation=5,
            content=ft.Container(
                padding=20,
                width=260,
                content=ft.Column([
                    titulo_dinamico, # Agora recebe a variável aqui!
                    texto_dinamico 
                ])
            )
        )

    card_ganhos = criar_card(titulo_ganhos, texto_ganhos, ft.Colors.GREEN_400)
    # Aqui a gente passa a nova variável para o card de Gastos!
    card_gastos = criar_card(titulo_gastos, texto_gastos, ft.Colors.RED_400) 
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
        filtros = estado_app["filtros_ativos"]
        
        # Agora recebemos os 5 itens que o controlador mandou!
        ganhos, gastos, restante, nomes_ganhos, nomes_gastos = obter_resumo_financeiro(filtros)
        
        texto_ganhos.value = ganhos
        texto_gastos.value = gastos
        texto_restante.value = restante
        
        # Regra para o título de Ganhos
        if len(nomes_ganhos) > 0:
            titulo_ganhos.value = f"Ganhos ({'/'.join(nomes_ganhos)})"
        else:
            titulo_ganhos.value = "Ganhos"

        # Regra para o título de Gastos
        if len(nomes_gastos) > 0:
            titulo_gastos.value = f"Gastos ({'/'.join(nomes_gastos)})"
        else:
            titulo_gastos.value = "Gastos"
            
        page.update()
        
    # Chama a função para carregar os números ao abrir o app
    atualizar_cards_resumo()

    def salvar_transacao(e):
        id_atual = estado_app["id_edicao"]
        
        # Se for None, é transação nova. Se tiver ID, é edição!
        if id_atual is None:
            sucesso, mensagem = processar_nova_transacao(
                descricao=descricao_input.value,
                valor_str=valor_input.value,
                data=data_input.value,
                tipo=tipo_dropdown.value,
                categoria_id_str=categoria_dropdown.value
            )
        else:
            sucesso, mensagem = processar_edicao(
                id_transacao=id_atual,
                descricao=descricao_input.value,
                valor_str=valor_input.value,
                data=data_input.value,
                tipo=tipo_dropdown.value,
                categoria_id_str=categoria_dropdown.value
            )

        cor_aviso = ft.Colors.GREEN if sucesso else ft.Colors.RED
        page.snack_bar = ft.SnackBar(ft.Text(mensagem), bgcolor=cor_aviso)
        page.snack_bar.open = True

        if sucesso:
            modal_novo.open = False
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
        estado_app["id_edicao"] = None # Garante que é modo de CRIAÇÃO
        modal_novo.title = ft.Text("Nova Transação")
        
        # Limpa os campos
        descricao_input.value = ""
        valor_input.value = ""
        # Definindo a data de hoje como padrão para novos registros!
        data_input.value = datetime.today().strftime('%Y-%m-%d')
        tipo_dropdown.value = ""
        categoria_dropdown.value = ""
        
        # 3. Abre o modal
        modal_novo.open = True
        page.update()

    def fechar_modal(e):
        modal_novo.open = False
        page.update()

    def clicar_lapis(e):
        # Captura todos os dados da linha clicada
        dados = e.control.data 
        
        # Muda o estado para modo de EDIÇÃO e troca o título do modal
        estado_app["id_edicao"] = dados["id"]
        modal_novo.title = ft.Text("Editar Transação")
        
        # Preenche os campos com os valores puros que guardamos no Controller
        descricao_input.value = dados["descricao"]
        valor_input.value = dados["valor_puro"]
        data_input.value = dados["data"]
        tipo_dropdown.value = dados["tipo_puro"]
        categoria_dropdown.value = dados["categoria_id"]
        
        modal_novo.open = True
        page.update(),
        
    # =====================================================================

    def clicar_filtro(e):
        nome_filtro = e.control.label.value
        
        # Converte qualquer coisa que o Flet mandar (True, "True", "true") para texto minúsculo
        foi_selecionado = (str(e.data).lower() == "true")
        
        # 1. Garante que a bolha mude de cor visualmente
        e.control.selected = foi_selecionado
        e.control.update()
        
        # 2. Atualiza a nossa lista de forma segura
        if foi_selecionado:
            if nome_filtro not in estado_app["filtros_ativos"]:
                estado_app["filtros_ativos"].append(nome_filtro)
        else:
            if nome_filtro in estado_app["filtros_ativos"]:
                estado_app["filtros_ativos"].remove(nome_filtro)
        
        # 3. PRINT DE DEBUG: Vai aparecer no seu terminal (VS Code, CMD, etc)
        print(f"Filtros clicados agora: {estado_app['filtros_ativos']}")
        
        atualizar_tabela()
        atualizar_cards_resumo()

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

        # 1. Puxa as categorias do banco (reaproveitando o Controller!)
        lista_categorias_db = obter_opcoes_categorias()

        # 2. A lista começa VAZIA (sem o chip "Todos")
        chips_filtros = []

        # 3. Adiciona as categorias
        for cat in lista_categorias_db:
            chips_filtros.append(
                ft.Chip(label=ft.Text(cat["text"]), on_select=clicar_filtro, selected_color=ft.Colors.GREEN_600)
            )

        # 4. Coloca os chips numa Row (com scroll, caso você tenha muitas categorias!)
        filtros = ft.Row(
            controls=chips_filtros, 
            scroll=ft.ScrollMode.AUTO
        )
        
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
            ft.DataColumn(ft.Text("Ações", weight=ft.FontWeight.BOLD)),
        ],
        rows=[] # Começa vazia
    )

    def clicar_lixeira(e):
        # O ID da transação estará guardado na propriedade 'data' do botão
        id_para_apagar = e.control.data 
        
        sucesso, mensagem = processar_exclusao(id_para_apagar)
        
        # Mostra o aviso
        cor_aviso = ft.Colors.GREEN if sucesso else ft.Colors.RED
        page.snack_bar = ft.SnackBar(ft.Text(mensagem), bgcolor=cor_aviso)
        page.snack_bar.open = True
        
        # Se deu certo, atualiza tudo!
        if sucesso:
            atualizar_tabela()
            atualizar_cards_resumo()
        
        page.update()

    def atualizar_tabela():
        """Pede os dados ao Controller e recria as linhas da tabela."""
        tabela_despesas.rows.clear()
        # Agora passamos o filtro que está salvo no estado!
        filtros = estado_app["filtros_ativos"]
        transacoes = obter_transacoes_formatadas(filtros)
        
        for t in transacoes:
            # Define a cor baseada no tipo (Despesa = Vermelho, Receita = Verde)
            cor_texto = ft.Colors.RED_400 if t["eh_despesa"] else ft.Colors.GREEN_400

            # Criamos o botão da lixeira, guardando o ID no parâmetro 'data'
            btn_excluir = ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE, 
                icon_color=ft.Colors.RED_400,
                data=t["id"], # <-- O Flet esconde o ID aqui dentro!
                on_click=clicar_lixeira
            )

            # NOVO: Botão de Lápis
            btn_editar = ft.IconButton(
                icon=ft.Icons.EDIT_OUTLINED,
                icon_color=ft.Colors.BLUE_400,
                data=t, # <-- Passamos o DICIONÁRIO INTEIRO para o botão!
                on_click=clicar_lapis
            )

            # Agrupa os dois botões na mesma célula
            acoes = ft.Row([btn_editar, btn_excluir], spacing=0)

            tabela_despesas.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(t["descricao"])),
                        ft.DataCell(ft.Text(t["categoria"])),
                        ft.DataCell(ft.Text(t["data"])),
                        ft.DataCell(ft.Text(t["valor_texto"], color=cor_texto)),
                        ft.DataCell(acoes),
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

    # CADASTRA O MODAL AQUI (Garante que ele exista na tela, mas invisível)
    page.overlay.append(modal_novo)

    # Atualizações iniciais
    atualizar_tabela()
    atualizar_cards_resumo()

if __name__ == "__main__":
    ft.run(main)