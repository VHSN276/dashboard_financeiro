from database.connection_bd import get_connection
import database.queries

def adicionar_nova_transacao(descricao, valor, data, tipo, categoria_id):
    "Função que será chamada no botão de salvar do Flet (View)"
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        valores = (descricao, valor, data, tipo, categoria_id)

        cursor.execute()