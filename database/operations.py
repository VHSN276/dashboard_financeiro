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

def listar_transacoes():
    """Model: Busca as transações cruzando com a tabela de categorias para pegar o nome."""
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        
        # O JOIN conecta 't' (transacoes) e 'c' (categorias) através do categoria_id
        query = """
            SELECT t.descricao, c.nome, t.data, t.valor, t.tipo 
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