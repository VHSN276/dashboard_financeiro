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