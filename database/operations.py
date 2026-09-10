from database.connection_bd import get_connection
import database.queries as query

def adicionar_nova_transacao(descricao, valor, data, tipo, categoria_id):
    "Função que será chamada no botão de salvar do Flet (View)"
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        valores = (descricao, valor, data, tipo, categoria_id)

        # Executa a query importada passando os valores do usuario
        cursor.execute(query.inserir_transacao, valores)
        conn.commit()

        cursor.close()
        conn.close()
        return True
    return False

def adicionar_mes(nome_mes):
    """Model: Adiciona um novo mês no banco de dados."""
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO finance_db.meses (nome) VALUES (%s)", (nome_mes,))
        conn.commit()
        
        cursor.close()
        conn.close()
        return True
    return False

def listar_transacoes():
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        # Adicionamos o t.categoria_id no final da lista!
        query = """
            SELECT t.id, t.descricao, c.nome, t.data, t.valor, t.tipo, t.categoria_id 
            FROM finance_db.transacoes t
            JOIN finance_db.categorias c ON t.categoria_id = c.id
            ORDER BY t.data DESC
        """
        cursor.execute(query)
        linhas = cursor.fetchall()
        cursor.close()
        conn.close()
        return linhas
    return []

def listar_meses():
    """Model: Busca todos os meses disponíveis no banco."""
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM finance_db.meses ORDER BY nome ASC")
        linhas = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return linhas
    return []

def listar_categorias():
    """Model: Busca todas as categorias disponíveis no banco."""
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        # Busca o ID e o Nome, ordenando alfabeticamente
        cursor.execute("SELECT id, nome FROM finance_db.categorias ORDER BY nome")
        linhas = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return linhas
    return []

def obter_saldo_atual():
    """Função que será chamada para exibir no Card principal do Dashboard."""
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(query.buscar_saldo)
        resultado = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # Retorna o saldo (ou 0 se for None)
        return resultado[0] if resultado[0] else 0
    return 0

def deletar_transacao_db(id_transacao):
    """Model: Apaga uma transação específica pelo ID."""
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM finance_db.transacoes WHERE id = %s", (id_transacao,))
        conn.commit()
        
        cursor.close()
        conn.close()
        return True
    return False

def atualizar_transacao_db(id_transacao, descricao, valor, data, tipo, categoria_id):
    """Model: Atualiza uma transação existente."""
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        query = """
            UPDATE finance_db.transacoes 
            SET descricao = %s, valor = %s, data = %s, tipo = %s, categoria_id = %s
            WHERE id = %s
        """
        # A ordem dos valores tem que bater exatamente com os %s da query acima
        cursor.execute(query, (descricao, valor, data, tipo, categoria_id, id_transacao))
        conn.commit()
        
        cursor.close()
        conn.close()
        return True
    return False

def atualizar_mes(nome_antigo, nome_novo):
    """Model: Atualiza o nome de um mês na base de dados."""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            nome_antigo = str(nome_antigo).strip()
            nome_novo = str(nome_novo).strip()
            
            cursor.execute("UPDATE finance_db.meses SET nome = %s WHERE nome = %s", (nome_novo, nome_antigo))
            conn.commit()
            
            linhas = cursor.rowcount
            cursor.close()
            conn.close()
            return linhas > 0
        except Exception as e:
            print(f"Erro ao atualizar mês no banco: {e}")
            return False
    return False