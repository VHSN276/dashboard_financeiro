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