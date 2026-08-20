from database.operations import adicionar_nova_transacao, listar_transacoes, listar_categorias, deletar_transacao_db, atualizar_transacao_db

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
    transacoes_brutas = listar_transacoes()
    transacoes_prontas = []
    
    for t in transacoes_brutas:
        # Agora desempacotamos 7 itens (o categoria_id é o t[6])
        id_transacao, descricao, categoria_nome, data, valor, tipo, categoria_id = t
        
        eh_despesa = (tipo == "Despesa" or tipo == "DESPESA") 
        sinal = "-" if eh_despesa else "+"
        valor_texto = f"{sinal} R$ {valor:.2f}"
        
        transacoes_prontas.append({
            "id": id_transacao, 
            "descricao": descricao,
            "categoria": categoria_nome,
            "data": str(data),
            "valor_texto": valor_texto,
            "eh_despesa": eh_despesa,
            # Guardamos os dados puros para conseguir jogar de volta no formulário
            "valor_puro": str(valor),
            "tipo_puro": tipo,
            "categoria_id": str(categoria_id) 
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
        valor = float(t[4]) # A posição 4 é o valor
        tipo = t[5].upper() # A posição 5 é o tipo (Receita/Despesa)
        
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

def processar_exclusao(id_transacao):
    """Controller: Pede ao Model para apagar e retorna o status."""
    sucesso = deletar_transacao_db(id_transacao)
    if sucesso:
        return True, "Transação apagada com sucesso!"
    return False, "Erro ao tentar apagar a transação."

def processar_edicao(id_transacao, descricao, valor_str, data, tipo, categoria_id_str):
    """Controller: Valida e envia a atualização pro Model."""
    try:
        if not descricao or not valor_str or not tipo or not categoria_id_str:
            return False, "Por favor, preencha todos os campos obrigatórios."

        valor_formatado = float(valor_str.replace(",", "."))
        categoria_id = int(categoria_id_str)

        sucesso = atualizar_transacao_db(id_transacao, descricao, valor_formatado, data, tipo, categoria_id)

        if sucesso:
            return True, "Transação atualizada com sucesso!"
        return False, "Erro ao atualizar no banco."

    except ValueError:
        return False, "Valor inválido. Digite apenas números."
    except Exception as e:
        return False, f"Erro inesperado: {str(e)}"