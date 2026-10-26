"""Migração do banco v1 (sem coluna mes) para o v2, usada por quem já rodou o app."""

import sqlite3
from contextlib import closing

from controllers import transaction_controller as c
from database.connection import caminho_banco, conexao

DDL_V1 = """
CREATE TABLE categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE COLLATE NOCASE CHECK (length(trim(nome)) > 0),
    tipo TEXT NOT NULL CHECK (tipo IN ('RECEITA', 'DESPESA'))
);
CREATE TABLE transacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao TEXT NOT NULL CHECK (length(trim(descricao)) > 0),
    valor_centavos INTEGER NOT NULL CHECK (valor_centavos > 0),
    data TEXT NOT NULL CHECK (data GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    categoria_id INTEGER NOT NULL REFERENCES categorias (id) ON DELETE RESTRICT
);
CREATE INDEX idx_transacoes_data ON transacoes (data);
CREATE INDEX idx_transacoes_categoria ON transacoes (categoria_id);
CREATE TABLE meses (nome TEXT PRIMARY KEY CHECK (nome GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]'));
INSERT INTO categorias (nome, tipo) VALUES ('Salário', 'RECEITA'), ('Lazer', 'DESPESA');
INSERT INTO meses (nome) VALUES ('2026-09'), ('2026-10');
INSERT INTO transacoes (descricao, valor_centavos, data, categoria_id) VALUES
    ('Salário', 500000, '2026-10-05', 1),
    ('Cinema', 4000, '2026-10-12', 2),
    ('Show', 15000, '2026-09-20', 2);
PRAGMA user_version = 1;
"""


def _criar_banco_v1():
    caminho = caminho_banco()
    with closing(sqlite3.connect(caminho)) as con:
        con.executescript(DDL_V1)
    return caminho


def test_migra_preenchendo_o_mes_pela_data_sem_perder_transacoes():
    _criar_banco_v1()

    assert [(t["descricao"], t["mes"]) for t in c.obter_transacoes_formatadas()] == [
        ("Cinema", "2026-10"), ("Salário", "2026-10"), ("Show", "2026-09"),
    ]
    assert len(c.obter_transacoes_formatadas(mes_atual="2026-10")) == 2
    assert c.obter_resumo_financeiro(None, "2026-09")[1] == "R$ 150,00"
    assert c.obter_meses_disponiveis() == ["2026-10", "2026-09"]


def test_migra_com_backup_do_banco_antigo():
    caminho = _criar_banco_v1()
    c.obter_categorias()  # dispara a migração

    backup = caminho.with_name(caminho.name + ".v1.bak")
    assert backup.exists()
    with closing(sqlite3.connect(backup)) as con:
        colunas = [linha[1] for linha in con.execute("PRAGMA table_info(transacoes)")]
        assert "mes" not in colunas
        assert con.execute("SELECT COUNT(*) FROM transacoes").fetchone()[0] == 3
        assert con.execute("PRAGMA user_version").fetchone()[0] == 1


def test_esquema_migrado_tem_indices_restricoes_e_versao_2():
    _criar_banco_v1()
    with conexao() as con:
        assert con.execute("PRAGMA user_version").fetchone()[0] == 2
        indices = {l[1] for l in con.execute("PRAGMA index_list(transacoes)")}
        assert {"idx_transacoes_data", "idx_transacoes_categoria", "idx_transacoes_mes"} <= indices
        assert con.execute("PRAGMA foreign_key_check").fetchall() == []
        try:
            con.execute(
                "INSERT INTO transacoes (descricao, valor_centavos, data, categoria_id, mes) "
                "VALUES ('x', 1, '2026-10-01', 1, 'outubro')"
            )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("mes inválido deveria violar o CHECK")


def test_migracao_so_roda_uma_vez_e_novas_transacoes_funcionam():
    caminho = _criar_banco_v1()
    c.obter_categorias()
    backup = caminho.with_name(caminho.name + ".v1.bak")
    backup.unlink()

    c.obter_categorias()  # segunda abertura: não migra nem refaz o backup
    assert not backup.exists()

    lazer = next(x["id"] for x in c.obter_categorias() if x["nome"] == "Lazer")
    assert c.processar_nova_transacao("Parque", "20", "2026-10-20", "2026-10", "DESPESA", str(lazer))[0]
    assert len(c.obter_transacoes_formatadas(mes_atual="2026-10")) == 3


def test_banco_novo_ja_nasce_na_versao_2_sem_backup():
    c.obter_categorias()
    caminho = caminho_banco()
    assert not caminho.with_name(caminho.name + ".v1.bak").exists()
    with conexao() as con:
        assert con.execute("PRAGMA user_version").fetchone()[0] == 2
        colunas = [l[1] for l in con.execute("PRAGMA table_info(transacoes)")]
        assert "mes" in colunas
