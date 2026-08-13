banco_finance_db = """CREATE DATABASE IF NOT EXISTS finance_db;
USE finance_db;"""

tabela_categorias = """CREATE TABLE IF NOT EXISTS categorias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(50) NOT NULL,
    tipo ENUM('RECEITA', 'DESPESA') NOT NULL
);"""

tabela_transacoes = """CREATE TABLE IF NOT EXISTS transacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    descricao VARCHAR(100) NOT NULL,
    valor DECIMAL(10, 2) NOT NULL,
    data DATE NOT NULL,
    tipo ENUM('RECEITA', 'DESPESA') NOT NULL,
    categoria_id INT,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL
);"""

tabela_metas = """CREATE TABLE IF NOT EXISTS metas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    descricao VARCHAR(100) NOT NULL,
    valor_objetivo DECIMAL(10, 2) NOT NULL,
    valor_atual DECIMAL(10, 2) DEFAULT 0.00,
    data_limite DATE
);"""

# AÇÕES - INSERT

## Inserindo Transações
inserir_transacao = """INSERT INTO finance_db.transacoes
        (descricao, valor, data, tipo, categoria_id)
        VALUES (%s, %s, %s, %s, %s)
    """

# CONSULTAS - SELECT

## Buscar saldo
buscar_saldo = """
        SELECT SUM(CASE WHEN tipo = 'RECEITA' THEN valor ELSE 0 END) - 
        SUM(CASE WHEN tipo = 'DESPESA' THEN valor ELSE 0 END) AS saldo_restante
        FROM transacoes
    """