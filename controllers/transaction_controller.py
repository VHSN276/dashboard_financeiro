from database.operations import adicionar_nova_transacao, listar_transacoes, listar_categorias

def processar_nova_transacao(descricao, valor_str, data, tipo, categoria_id_str):
    """
    Controlador: Recebe os dados em texto da View, valida, formata e envia para o Model.
    Retorna uma tupla: (Sucesso (Booleano), Mnsagem (Stering))
    """
    try:
        # 1. Validação de campos vazios
        if not descricao or not valor_str or not tipo or not categoria_id_str:
            return False, "Por favor, preencha todos os campos obrigatórios."

        # 2. Formatação dos dados
        valor_formatado = float(valor_str.replace(",", "."))
        categoria_id = int(categoria_id_str)

        # 3. Comunicação com o Banco de Dados (Model)
        sucesso = adicionar_nova_transacao(descricao, valor_formatado, data, tipo, categoria_id)

        if sucesso:
            return True, "Transação salva com sucesso!"
        else:
            return False, "Erro ao salvar no banco de dados."

    except ValueError:
        return False, "Valor inválido. Digite apenas números (ex: 21.90 ou 21,90)."
    except Exception as e:
        return False, f"Erro inesperado: {str(e)}"

def obter_transacoes_formatadas():
    """
    Controller: Pede os dados ao Model e formata para a View exibir.
    """
    transacoes_brutas = listar_transacoes()
    transacoes_prontas = []
    
    for t in transacoes_brutas:
        # ATENÇÃO AQUI: Mudamos 'categoria_id' para 'categoria_nome'
        descricao, categoria_nome, data, valor, tipo = t
        
        eh_despesa = (tipo == "Despesa" or tipo == "DESPESA") # Garantindo que pegue maiúsculo ou minúsculo
        sinal = "-" if eh_despesa else "+"
        valor_texto = f"{sinal} R$ {valor:.2f}"
        
        transacoes_prontas.append({
            "descricao": descricao,
            "categoria": categoria_nome, # Passamos o texto direto para a tela!
            "data": str(data),
            "valor_texto": valor_texto,
            "eh_despesa": eh_despesa
        })
        
    return transacoes_prontas

def obter_opcoes_categorias():
    """
    Controller: Pede as categorias ao banco e formata para o Dropdown.
    """
    categorias_brutas = listar_categorias()
    opcoes = []
    
    for c in categorias_brutas:
        id_cat, nome_cat = c
        # O Flet exige que a chave (key) seja uma String
        opcoes.append({"key": str(id_cat), "text": nome_cat})
        
    return opcoes

def obter_resumo_financeiro():
    """
    Controller: Calcula os totais de ganhos, gastos e o saldo restante.
    Retorna uma tupla com os três valores formatados em texto.
    """
    transacoes = listar_transacoes() # Reutilizamos a função do Model!
    
    total_ganhos = 0.0
    total_gastos = 0.0
    
    for t in transacoes:
        valor = float(t[3]) # A posição 3 é o valor
        tipo = t[4].upper() # A posição 4 é o tipo (Receita/Despesa)
        
        if tipo == "RECEITA":
            total_ganhos += valor
        else:
            total_gastos += valor
            
    saldo_restante = total_ganhos - total_gastos
    
    # Formata para o padrão brasileiro (ex: 1200.50 -> 1.200,50)
    # Como formatação complexa de moeda pode ser chata no Python, vamos fazer uma formatação simples
    ganhos_str = f"R$ {total_ganhos:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    gastos_str = f"R$ {total_gastos:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    restante_str = f"R$ {saldo_restante:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    return ganhos_str, gastos_str, restante_str