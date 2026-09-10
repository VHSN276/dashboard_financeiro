import flet as ft
import time
from datetime import datetime

# Importações limpas (apenas o que realmente está a ser usado)
from controllers.transaction_controller import (
    processar_nova_transacao, obter_transacoes_formatadas, 
    obter_opcoes_categorias, obter_resumo_financeiro, 
    processar_exclusao, processar_edicao, obter_meses_disponiveis, 
    processar_novo_mes, processar_edicao_mes
)

def main(page: ft.Page):
    # =====================================================================
    # 1. CONFIGURAÇÕES DA JANELA E ESTADO
    # =====================================================================
    page.title = "Controle Financeiro"
    page.window_width = 900
    page.window_height = 700
    page.theme_mode = ft.ThemeMode.DARK 
    page.padding = 30

    estado_app = {
        "id_edicao": None,
        "filtros_ativos": [],
        "mes_atual": None,
        "mes_alvo_opcoes": None 
    }

    # =====================================================================
    # 2. INTERFACE BASE: CARDS DE RESUMO, TABELA E MESES
    # =====================================================================
    texto_ganhos = ft.Text("R$ 0,00", size=28, weight=ft.FontWeight.BOLD)
    texto_gastos = ft.Text("R$ 0,00", size=28, weight=ft.FontWeight.BOLD)
    texto_restante = ft.Text("R$ 0,00", size=28, weight=ft.FontWeight.BOLD)
    
    titulo_ganhos = ft.Text("Ganhos", size=16, weight=ft.FontWeight.W_500, color=ft.Colors.GREEN_400, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
    titulo_gastos = ft.Text("Gastos", size=16, weight=ft.FontWeight.W_500, color=ft.Colors.RED_400, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)

    def criar_card(titulo_dinamico, texto_dinamico, cor_texto):
        if isinstance(titulo_dinamico, str):
            titulo_dinamico = ft.Text(titulo_dinamico, size=16, weight=ft.FontWeight.W_500, color=cor_texto)
            
        return ft.Card(
            elevation=5,
            content=ft.Container(
                padding=20,
                width=260,
                content=ft.Column([titulo_dinamico, texto_dinamico])
            )
        )

    card_ganhos = criar_card(titulo_ganhos, texto_ganhos, ft.Colors.GREEN_400)
    card_gastos = criar_card(titulo_gastos, texto_gastos, ft.Colors.RED_400) 
    card_restante = criar_card("Restante", texto_restante, ft.Colors.BLUE_400)

    linha_resumo = ft.Row(
        controls=[card_ganhos, card_gastos, card_restante],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    linha_meses = ft.Row(scroll=ft.ScrollMode.AUTO, alignment=ft.MainAxisAlignment.START)
    
    tabela_despesas = ft.DataTable(
        width=float("inf"),
        columns=[
            ft.DataColumn(ft.Text("Descrição", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Categoria", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Data", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Valor", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Ações", weight=ft.FontWeight.BOLD)),
        ],
        rows=[]
    )

    # =====================================================================
    # 3. FUNÇÕES DE ATUALIZAÇÃO GERAIS (CORE)
    # =====================================================================
    def atualizar_cards_resumo():
        filtros = estado_app["filtros_ativos"]
        mes = estado_app["mes_atual"]
        
        ganhos, gastos, restante, nomes_ganhos, nomes_gastos = obter_resumo_financeiro(filtros, mes)
        
        texto_ganhos.value = ganhos
        texto_gastos.value = gastos
        texto_restante.value = restante
        
        if len(nomes_ganhos) > 0:
            titulo_ganhos.value = f"Ganhos ({'/'.join(nomes_ganhos)})"
        else:
            titulo_ganhos.value = "Ganhos"

        if len(nomes_gastos) > 0:
            titulo_gastos.value = f"Gastos ({'/'.join(nomes_gastos)})"
        else:
            titulo_gastos.value = "Gastos"
            
        page.update()

    def atualizar_tabela():
        tabela_despesas.rows.clear()
        filtros = estado_app["filtros_ativos"]
        mes = estado_app["mes_atual"]
        transacoes = obter_transacoes_formatadas(filtros, mes)
        
        for t in transacoes:
            cor_texto = ft.Colors.RED_400 if t["eh_despesa"] else ft.Colors.GREEN_400

            btn_excluir = ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE, 
                icon_color=ft.Colors.RED_400,
                data=t["id"],
                on_click=clicar_lixeira
            )

            btn_editar = ft.IconButton(
                icon=ft.Icons.EDIT_OUTLINED,
                icon_color=ft.Colors.BLUE_400,
                data=t,
                on_click=clicar_lapis
            )

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

    def clicar_mes(e):
        estado_app["mes_atual"] = e.control.data
        atualizar_linha_meses()
        atualizar_tabela()
        atualizar_cards_resumo()

    def atualizar_linha_meses():
        linha_meses.controls.clear()
        meses_db = obter_meses_disponiveis()
        
        if estado_app["mes_atual"] is None and len(meses_db) > 0:
            estado_app["mes_atual"] = meses_db[0]
            
        for mes in meses_db:
            eh_selecionado = (mes == estado_app["mes_atual"])
            cor = ft.Colors.GREEN_400 if eh_selecionado else ft.Colors.WHITE54
            
            botao = ft.TextButton(
                ft.Text(mes), 
                data=mes, 
                style=ft.ButtonStyle(color=cor),
                on_click=clicar_mes 
            )
            
            detector = ft.GestureDetector(
                content=botao,
                data=mes,
                on_secondary_tap=abrir_opcoes_mes 
            )
            
            linha_meses.controls.append(detector)
        page.update()


    # =====================================================================
    # 4. MODAL 1: CRIAR NOVO MÊS
    # =====================================================================
    nome_mes_input = ft.TextField(label="Nome do Mês (Ex: 2026-08)", width=300)

    def abrir_modal_mes(e):
        nome_mes_input.value = ""
        nome_mes_input.update()
        modal_mes.open = True
        page.update()

    def fechar_modal_mes(e):
        modal_mes.open = False
        page.update()

    def salvar_novo_mes(e):
        sucesso, mensagem = processar_novo_mes(nome_mes_input.value)
        
        cor_aviso = ft.Colors.GREEN if sucesso else ft.Colors.RED
        page.snack_bar = ft.SnackBar(ft.Text(mensagem), bgcolor=cor_aviso)
        page.snack_bar.open = True
        
        if sucesso:
            fechar_modal_mes(e)
            atualizar_linha_meses() 
        else:
            page.update() 

    modal_mes = ft.AlertDialog(
        title=ft.Text("Novo Mês"),
        content=ft.Column([nome_mes_input], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=fechar_modal_mes),
            ft.ElevatedButton("Salvar", on_click=salvar_novo_mes, bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    btn_novo_mes = ft.ElevatedButton(
        ft.Text("+ Mês"),
        bgcolor=ft.Colors.GREEN_600,
        color=ft.Colors.WHITE,
        on_click=abrir_modal_mes 
    )

    barra_superior_meses = ft.Row(
        controls=[btn_novo_mes, linha_meses],
        alignment=ft.MainAxisAlignment.START
    )

    # =====================================================================
    # 5. MODAL 2: GERENCIAR MÊS (EDITAR / EXCLUIR)
    # =====================================================================
    novo_nome_mes_input = ft.TextField(label="Novo Nome do Mês", width=300)

    def fechar_modal_gerenciar_mes(e):
        modal_gerenciar_mes.open = False
        page.update()

    def acao_excluir_mes(e):
        mes = estado_app["mes_alvo_opcoes"]
        fechar_modal_gerenciar_mes(e)
        print(f"Pronto para excluir: {mes}")
        # A lógica do banco virá aqui depois!

    def salvar_edicao_mes(e):
        mes_antigo = estado_app["mes_alvo_opcoes"]
        mes_novo = novo_nome_mes_input.value.strip()
        
        sucesso, mensagem = processar_edicao_mes(mes_antigo, mes_novo)
        
        cor_aviso = ft.Colors.GREEN if sucesso else ft.Colors.RED
        page.snack_bar = ft.SnackBar(ft.Text(mensagem), bgcolor=cor_aviso)
        page.snack_bar.open = True
        
        if sucesso:
            modal_gerenciar_mes.open = False
            
            if estado_app["mes_atual"] == mes_antigo:
                estado_app["mes_atual"] = mes_novo
            estado_app["mes_alvo_opcoes"] = mes_novo
            
            atualizar_linha_meses()
            atualizar_tabela()
            atualizar_cards_resumo()
        
        page.update()

    def mostrar_form_edicao(e):
        mes_atual = estado_app["mes_alvo_opcoes"]
        novo_nome_mes_input.value = mes_atual
        
        modal_gerenciar_mes.title = ft.Text(f"Editar Mês: {mes_atual}")
        modal_gerenciar_mes.content = ft.Column([novo_nome_mes_input], tight=True)
        modal_gerenciar_mes.actions = [
            ft.TextButton("Cancelar", on_click=fechar_modal_gerenciar_mes),
            ft.ElevatedButton("Salvar Alteração", on_click=salvar_edicao_mes, bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE)
        ]
        page.update()

    def abrir_opcoes_mes(e):
        mes_clicado = e.control.data
        estado_app["mes_alvo_opcoes"] = mes_clicado
        
        modal_gerenciar_mes.title = ft.Text(f"Opções: {mes_clicado}")
        modal_gerenciar_mes.content = ft.Column([
            ft.ElevatedButton("Editar Mês", on_click=mostrar_form_edicao, icon=ft.Icons.EDIT, bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE, width=200),
            ft.ElevatedButton("Excluir Mês", on_click=acao_excluir_mes, icon=ft.Icons.DELETE, bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE, width=200),
        ], tight=True)
        modal_gerenciar_mes.actions = [
            ft.TextButton("Cancelar", on_click=fechar_modal_gerenciar_mes)
        ]
        modal_gerenciar_mes.open = True
        page.update()

    modal_gerenciar_mes = ft.AlertDialog(
        title=ft.Text("Gerenciar Mês"),
        content=ft.Container(),
        actions=[],
        actions_alignment=ft.MainAxisAlignment.END,
    )


    # =====================================================================
    # 6. MODAL 3: TRANSAÇÕES (NOVA E EDITAR) E FILTROS
    # =====================================================================
    descricao_input = ft.TextField(label="Descrição", width=300)
    valor_input = ft.TextField(label="Valor (R$)", width=300, keyboard_type=ft.KeyboardType.NUMBER)
    data_input = ft.TextField(label="Data (AAAA-MM-DD)", width=300, value=datetime.today().strftime('%Y-%m-%d'))
    tipo_dropdown = ft.Dropdown(label="Tipo", width=300, options=[ft.dropdown.Option("Receita"), ft.dropdown.Option("Despesa")])
    
    lista_categorias_db = obter_opcoes_categorias()
    opcoes_dropdown = [ft.dropdown.Option(key=cat["key"], text=ft.Text(cat["text"])) for cat in lista_categorias_db]
    categoria_dropdown = ft.Dropdown(label="Categoria", width=300, options=opcoes_dropdown)

    def fechar_modal_transacao(e):
        modal_novo.open = False
        page.update()

    def salvar_transacao(e):
        id_atual = estado_app["id_edicao"]
        
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

    modal_novo = ft.AlertDialog(
        title=ft.Text("Nova Transação"),
        content=ft.Column([descricao_input, valor_input, data_input, tipo_dropdown, categoria_dropdown], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=fechar_modal_transacao),
            ft.ElevatedButton("Salvar", on_click=salvar_transacao, bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def abrir_modal_transacao(e):
        estado_app["id_edicao"] = None 
        modal_novo.title = ft.Text("Nova Transação")
        
        descricao_input.value = ""
        valor_input.value = ""
        data_input.value = datetime.today().strftime('%Y-%m-%d')
        tipo_dropdown.value = ""
        categoria_dropdown.value = ""
        
        modal_novo.open = True
        page.update()

    def clicar_lapis(e):
        dados = e.control.data 
        estado_app["id_edicao"] = dados["id"]
        modal_novo.title = ft.Text("Editar Transação")
        
        descricao_input.value = dados["descricao"]
        valor_input.value = dados["valor_puro"]
        data_input.value = dados["data"]
        tipo_dropdown.value = dados["tipo_puro"]
        categoria_dropdown.value = dados["categoria_id"]
        
        modal_novo.open = True
        page.update()

    def clicar_lixeira(e):
        id_para_apagar = e.control.data 
        sucesso, mensagem = processar_exclusao(id_para_apagar)
        
        cor_aviso = ft.Colors.GREEN if sucesso else ft.Colors.RED
        page.snack_bar = ft.SnackBar(ft.Text(mensagem), bgcolor=cor_aviso)
        page.snack_bar.open = True
        
        if sucesso:
            atualizar_tabela()
            atualizar_cards_resumo()
        page.update()

    def clicar_filtro(e):
        nome_filtro = e.control.label.value
        foi_selecionado = (str(e.data).lower() == "true")
        
        e.control.selected = foi_selecionado
        e.control.update()
        
        if foi_selecionado:
            if nome_filtro not in estado_app["filtros_ativos"]:
                estado_app["filtros_ativos"].append(nome_filtro)
        else:
            if nome_filtro in estado_app["filtros_ativos"]:
                estado_app["filtros_ativos"].remove(nome_filtro)
        
        atualizar_tabela()
        atualizar_cards_resumo()

    def criar_linha_acoes():
        botao_add = ft.ElevatedButton(
            ft.Text("New"),
            height=40,
            bgcolor=ft.Colors.GREEN_600,
            color=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
            on_click=abrir_modal_transacao 
        )

        chips_filtros = []
        for cat in obter_opcoes_categorias():
            chips_filtros.append(
                ft.Chip(label=ft.Text(cat["text"]), on_select=clicar_filtro, selected_color=ft.Colors.GREEN_600)
            )

        filtros = ft.Row(controls=chips_filtros, scroll=ft.ScrollMode.AUTO)
        
        return ft.Row(controls=[botao_add, filtros], alignment=ft.MainAxisAlignment.START, spacing=30)

    # =====================================================================
    # 7. ADICIONANDO TUDO NO ECRÃ E INICIANDO
    # =====================================================================
    page.add(
        barra_superior_meses,
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        linha_resumo,
        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        
        criar_linha_acoes(),
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        tabela_despesas
    )

    # Apenas os 3 Modais finais necessários!
    page.overlay.append(modal_novo)
    page.overlay.append(modal_mes)
    page.overlay.append(modal_gerenciar_mes)

    # Atualizações iniciais
    atualizar_linha_meses()
    atualizar_tabela()
    atualizar_cards_resumo()

if __name__ == "__main__":
    ft.run(main)