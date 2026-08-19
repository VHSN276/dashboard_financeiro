import mysql.connector
from mysql.connector import Error
from database.user_crendences import user
#config do banco
DB_CONFIG = {
    "host": "localhost",
    "user": user.user,
    "password": user.password
}

def get_connection(db_name="finance_db"):
    """Faz uma conexão ativa com o banco de dados finance_db"""
    try:
        connection = mysql.connector.connect(
            **DB_CONFIG,
            database=db_name
        )
        return connection
    except Error as e:
        print(f"Erro ao conectar ao mysql: {e}")
        return None

#Rodar uma vez
def inicializar_banco():
    """Criar o banco de dados e as tabelas, caso ainda não existam"""
    try:
        # 1. Conecta sem especificar o banco para criar o 'finance_db'
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS finance_db")
        conn.close()

        #2. Conecta diretamente no banco finance_db para criar as tabelas
        conn = get_connection()
        if conn and conn.is_connected():
            cursor = conn.cursor()

            # Tabela de Categoria
            cursor.execute("""CREATE TABLE IF NOT EXISTS categorias (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(50) NOT NULL,
                tipo ENUM('RECEITA', 'DESPESA') NOT NULL);""")
            
            #Tabela de transações
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS transacoes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                descricao VARCHAR(100) NOT NULL,
                valor DECIMAL(10, 2) NOT NULL,
                data DATE NOT NULL,
                tipo ENUM('RECEITA', 'DESPESA') NOT NULL,
                categoria_id INT,
                FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL);""")
            
            #Tabela de Metas
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS metas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                descricao VARCHAR(100) NOT NULL,
                valor_objetivo DECIMAL(10, 2) NOT NULL,
                valor_atual DECIMAL(10, 2) DEFAULT 0.00,
                data_limite DATE);""")
            
            # Inserir algumas categorias padrão se a tabela estiver vazia
            cursor.execute("SELECT COUNT(*) FROM categorias;")
            if cursor.fetchone()[0] == 0:
                categorias_padrao = [
                    ('Salário', 'RECEITA'),
                    ('Bônus/Extra', 'RECEITA'),
                    ('Alimentação', 'DESPESA'),
                    ('Moradia', 'DESPESA'),
                    ('Cartão de Crédito', 'DESPESA'),
                    ('Lazer', 'DESPESA')
                ]
                cursor.executemany("INSERT INTO categorias (nome, tipo) VALUES (%s, %s)", categorias_padrao)
            
            conn.commit()
            print("✅ Banco de dados e tabelas inicializados com sucesso!")
            cursor.close()
            conn.close()

    except Error as e:
        print(f"❌ Erro ao inicializar o banco: {e}")

#python3 database/connection_bd.py
##if __name__ == "__main__":
##    inicializar_banco()