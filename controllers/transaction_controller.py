from database.operations import adicionar_nova_transacao, listar_transacoes, listar_categorias, deletar_transacao_db, atualizar_transacao_db, adicionar_mes, listar_meses

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

def obter_transacoes_formatadas(filtros_ativos=None, mes_filtro=None):
    if filtros_ativos is None:
        filtros_ativos = []

    if mes_filtro is None:
        mes_filtro = ""

    transacoes_brutas = listar_transacoes()
    transacoes_prontas = []
    
    for t in transacoes_brutas:
        id_transacao, descricao, categoria_nome, data, valor, tipo, categoria_id = t
        data_transacao = str(data)[:7]  # Pega a data e corta para "YYYY-MM"

        if mes_filtro and data_transacao != mes_filtro:
            continue

        # A MÁGICA DO MULTI-SELECT:
        # Se tem algo na lista de filtros E a categoria não está lá dentro, ignoramos essa linha!
        if len(filtros_ativos) > 0 and categoria_nome not in filtros_ativos:
            continue
        
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

def obter_resumo_financeiro(filtros_ativos=None, mes_filtro=None):
    if filtros_ativos is None:
        filtros_ativos = []

    if mes_filtro is None:
        mes_filtro = ""

    transacoes_brutas = listar_transacoes()
    total_ganhos = 0.0
    total_gastos = 0.0
    
    # Criamos dois 'conjuntos' (sets) para guardar os nomes sem repeti-los
    nomes_ganhos = set()
    nomes_gastos = set()
    
    for t in transacoes_brutas:
        # Pega a data e corta para "YYYY-MM"
        data_transacao = str(t[3])[:7]
        categoria_nome = t[2]
        valor = float(t[4])
        tipo = t[5].upper()

        # Se o filtro de mês está ativo, ignoramos transações de outros meses
        if mes_filtro and data_transacao != mes_filtro:
            continue

        # Se a categoria está marcada no filtro, nós descobrimos de qual lado ela é!
        if categoria_nome in filtros_ativos:
            if tipo == "RECEITA" or tipo == "GANHO": # Ajuste para a palavra exata do seu banco
                nomes_ganhos.add(categoria_nome)
            else:
                nomes_gastos.add(categoria_nome)
                
        # Continua a lógica matemática normal
        if len(filtros_ativos) > 0 and categoria_nome not in filtros_ativos:
            continue
            
        if tipo == "RECEITA" or tipo == "GANHO":
            total_ganhos += valor
        else:
            total_gastos += valor
            
    restante = total_ganhos - total_gastos
    
    # Agora a função devolve 5 coisas! Os 3 valores, e as 2 listas de nomes.
    return (
        f"R$ {total_ganhos:,.2f}", 
        f"R$ {total_gastos:,.2f}", 
        f"R$ {restante:,.2f}",
        list(nomes_ganhos), 
        list(nomes_gastos)
    )

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

def obter_meses_disponiveis():
    """Lê os meses do banco e retorna em ordem cronológica real."""
    meses_brutos = listar_meses()
    meses_nomes = [mes[1] for mes in meses_brutos]
    
    # 1. Criamos um "gabarito" ensinando a ordem correta para o Python
    ordem_meses = {
        "Janeiro": 1, 
        "Fevereiro": 2, 
        "Março": 3, 
        "Abril": 4,
        "Maio": 5, 
        "Junho": 6, 
        "Julho": 7, 
        "Agosto": 8,
        "Setembro": 9, 
        "Outubro": 10, 
        "Novembro": 11, 
        "Dezembro": 12
    }
    
    # 2. Ensinamos a função sorted a usar o nosso gabarito
    # Se o usuário digitar algo diferente (ex: "Ano Todo"), jogamos para o final (peso 99)
    meses_ordenados = sorted(meses_nomes, key=lambda mes: ordem_meses.get(mes, 99))
    
    return meses_ordenados

def processar_novo_mes(nome_mes):
    """Regra de negócio para salvar o mês."""
    if not nome_mes.strip():
        return False, "O nome do mês não pode estar vazio."
        
    try:
        sucesso = adicionar_mes(nome_mes)
        if sucesso:
            return True, "Mês adicionado com sucesso!"
        return False, "Erro ao salvar no banco."
    except Exception as e:
        # Se você tentar cadastrar '2026-08' duas vezes, o MySQL vai dar erro por causa do UNIQUE
        return False, "Este mês já está cadastrado!"