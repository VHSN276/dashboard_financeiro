"""Esquema do banco SQLite, carga inicial e migrações."""

import sqlite3
from contextlib import closing
from datetime import date

VERSAO_ESQUEMA = 2

_TABELA_TRANSACOES = """
CREATE TABLE {nome} (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao      TEXT NOT NULL CHECK (length(trim(descricao)) > 0),
    valor_centavos INTEGER NOT NULL CHECK (valor_centavos > 0),
    data           TEXT NOT NULL
        CHECK (data GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    categoria_id   INTEGER NOT NULL
        REFERENCES categorias (id) ON DELETE RESTRICT,
    mes            TEXT NOT NULL
        CHECK (mes GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]')
);
"""

_INDICES = """
CREATE INDEX IF NOT EXISTS idx_transacoes_data ON transacoes (data);
CREATE INDEX IF NOT EXISTS idx_transacoes_categoria ON transacoes (categoria_id);
CREATE INDEX IF NOT EXISTS idx_transacoes_mes ON transacoes (mes);
"""

_DDL = (
    """
CREATE TABLE IF NOT EXISTS categorias (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE COLLATE NOCASE CHECK (length(trim(nome)) > 0),
    tipo TEXT NOT NULL CHECK (tipo IN ('RECEITA', 'DESPESA'))
);

CREATE TABLE IF NOT EXISTS meses (
    nome TEXT PRIMARY KEY CHECK (nome GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]')
);
"""
    + _TABELA_TRANSACOES.format(nome="transacoes").replace(
        "CREATE TABLE", "CREATE TABLE IF NOT EXISTS", 1
    )
    + _INDICES
)

# v1 -> v2: cada transação ganha o mês em que aparece (início: o mês da data).
_MIGRACAO_V1_V2 = (
    "BEGIN;"
    + _TABELA_TRANSACOES.format(nome="transacoes_nova")
    + """
INSERT INTO transacoes_nova (id, descricao, valor_centavos, data, categoria_id, mes)
    SELECT id, descricao, valor_centavos, data, categoria_id, substr(data, 1, 7)
    FROM transacoes;
DROP TABLE transacoes;
ALTER TABLE transacoes_nova RENAME TO transacoes;
"""
    + _INDICES
    + """
PRAGMA user_version = 2;
COMMIT;
"""
)

CATEGORIAS_INICIAIS = (
    ("Salário", "RECEITA"),
    ("Outras receitas", "RECEITA"),
    ("Alimentação", "DESPESA"),
    ("Moradia", "DESPESA"),
    ("Transporte", "DESPESA"),
    ("Saúde", "DESPESA"),
    ("Lazer", "DESPESA"),
    ("Educação", "DESPESA"),
    ("Outras despesas", "DESPESA"),
)


def inicializar(con: sqlite3.Connection) -> None:
    """Cria o banco novo ou migra um banco antigo para a versão atual."""
    versao = con.execute("PRAGMA user_version").fetchone()[0]
    if versao >= VERSAO_ESQUEMA:
        return
    if versao == 0:
        _criar_banco_novo(con)
    else:
        _fazer_backup(con, versao)
        con.executescript(_MIGRACAO_V1_V2)


def _criar_banco_novo(con: sqlite3.Connection) -> None:
    con.executescript(_DDL)
    con.executemany(
        "INSERT OR IGNORE INTO categorias (nome, tipo) VALUES (?, ?)",
        CATEGORIAS_INICIAIS,
    )
    con.execute(
        "INSERT OR IGNORE INTO meses (nome) VALUES (?)",
        (date.today().strftime("%Y-%m"),),
    )
    con.execute(f"PRAGMA user_version = {VERSAO_ESQUEMA}")
    con.commit()


def _fazer_backup(con: sqlite3.Connection, versao: int) -> None:
    """Copia o banco para <arquivo>.v<versao>.bak antes de migrar."""
    arquivo = next(
        (linha[2] for linha in con.execute("PRAGMA database_list") if linha[1] == "main"),
        "",
    )
    if not arquivo:
        return
    with closing(sqlite3.connect(f"{arquivo}.v{versao}.bak")) as copia:
        con.backup(copia)
