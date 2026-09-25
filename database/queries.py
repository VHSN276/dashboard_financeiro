"""SQL usado pelo model e pela inicialização do banco."""

CRIAR_BANCO = "CREATE DATABASE IF NOT EXISTS finance_db"

CRIAR_TABELA_CATEGORIAS = """CREATE TABLE IF NOT EXISTS categorias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(50) NOT NULL,
    tipo ENUM('RECEITA', 'DESPESA') NOT NULL
)"""

CRIAR_TABELA_TRANSACOES = """CREATE TABLE IF NOT EXISTS transacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    descricao VARCHAR(100) NOT NULL,
    valor DECIMAL(10, 2) NOT NULL,
    data DATE NOT NULL,
    tipo ENUM('RECEITA', 'DESPESA') NOT NULL,
    categoria_id INT,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL
)"""

CRIAR_TABELA_METAS = """CREATE TABLE IF NOT EXISTS metas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    descricao VARCHAR(100) NOT NULL,
    valor_objetivo DECIMAL(10, 2) NOT NULL,
    valor_atual DECIMAL(10, 2) DEFAULT 0.00,
    data_limite DATE
)"""

CRIAR_TABELA_MESES = """CREATE TABLE IF NOT EXISTS meses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(50) NOT NULL UNIQUE
)"""

INSERIR_TRANSACAO = """INSERT INTO finance_db.transacoes
    (descricao, valor, data, tipo, categoria_id)
    VALUES (%s, %s, %s, %s, %s)"""

LISTAR_TRANSACOES = """SELECT
    t.id,
    t.descricao,
    COALESCE(c.nome, 'Sem categoria') AS categoria,
    t.data,
    t.valor,
    t.tipo,
    t.categoria_id
FROM finance_db.transacoes AS t
LEFT JOIN finance_db.categorias AS c ON t.categoria_id = c.id
ORDER BY t.data DESC, t.id DESC"""

LISTAR_CATEGORIAS = """SELECT id, nome
FROM finance_db.categorias
ORDER BY nome"""

EXCLUIR_TRANSACAO = "DELETE FROM finance_db.transacoes WHERE id = %s"

ATUALIZAR_TRANSACAO = """UPDATE finance_db.transacoes
SET descricao = %s, valor = %s, data = %s, tipo = %s, categoria_id = %s
WHERE id = %s"""

INSERIR_MES = "INSERT INTO finance_db.meses (nome) VALUES (%s)"

LISTAR_MESES = "SELECT id, nome FROM finance_db.meses ORDER BY nome"

ATUALIZAR_MES = "UPDATE finance_db.meses SET nome = %s WHERE nome = %s"
