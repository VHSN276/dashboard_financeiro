from database.operations import adicionar_nova_transacao

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