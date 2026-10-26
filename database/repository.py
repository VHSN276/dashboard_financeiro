"""Consultas SQL. Recebem uma conexão aberta e não validam regras de negócio."""

import sqlite3


def _dicts(cursor: sqlite3.Cursor) -> list[dict]:
    return [dict(linha) for linha in cursor.fetchall()]


def _um(cursor: sqlite3.Cursor) -> dict | None:
    linha = cursor.fetchone()
    return dict(linha) if linha else None


# --- Categorias -------------------------------------------------------------

def listar_categorias(con):
    return _dicts(
        con.execute(
            "SELECT id, nome, tipo FROM categorias "
            "ORDER BY CASE tipo WHEN 'RECEITA' THEN 0 ELSE 1 END, nome"
        )
    )


def obter_categoria(con, categoria_id):
    return _um(
        con.execute(
            "SELECT id, nome, tipo FROM categorias WHERE id = ?", (categoria_id,)
        )
    )


def buscar_categoria_por_nome(con, nome):
    return _um(
        con.execute("SELECT id, nome, tipo FROM categorias WHERE nome = ?", (nome,))
    )


def inserir_categoria(con, nome, tipo):
    cursor = con.execute(
        "INSERT INTO categorias (nome, tipo) VALUES (?, ?)", (nome, tipo)
    )
    return cursor.lastrowid


def atualizar_categoria(con, categoria_id, nome, tipo):
    con.execute(
        "UPDATE categorias SET nome = ?, tipo = ? WHERE id = ?",
        (nome, tipo, categoria_id),
    )


def excluir_categoria(con, categoria_id):
    con.execute("DELETE FROM categorias WHERE id = ?", (categoria_id,))


def contar_transacoes_da_categoria(con, categoria_id):
    return con.execute(
        "SELECT COUNT(*) FROM transacoes WHERE categoria_id = ?", (categoria_id,)
    ).fetchone()[0]


# --- Transações -------------------------------------------------------------

def _filtros(nomes_categorias, mes):
    condicoes, parametros = [], []
    if nomes_categorias:
        marcadores = ", ".join("?" * len(nomes_categorias))
        condicoes.append(f"c.nome IN ({marcadores})")
        parametros.extend(nomes_categorias)
    if mes:
        condicoes.append("t.mes = ?")
        parametros.append(mes)
    where = f"WHERE {' AND '.join(condicoes)}" if condicoes else ""
    return where, parametros


def listar_transacoes(con, nomes_categorias=None, mes=None):
    where, parametros = _filtros(nomes_categorias, mes)
    return _dicts(
        con.execute(
            "SELECT t.id, t.descricao, t.valor_centavos, t.data, t.mes, "
            "       c.id AS categoria_id, c.nome AS categoria, c.tipo "
            "FROM transacoes t JOIN categorias c ON c.id = t.categoria_id "
            f"{where} ORDER BY t.data DESC, t.id DESC",
            parametros,
        )
    )


def somar_por_tipo(con, nomes_categorias=None, mes=None):
    where, parametros = _filtros(nomes_categorias, mes)
    linhas = con.execute(
        "SELECT c.tipo, COALESCE(SUM(t.valor_centavos), 0) AS total "
        "FROM transacoes t JOIN categorias c ON c.id = t.categoria_id "
        f"{where} GROUP BY c.tipo",
        parametros,
    ).fetchall()
    return {linha["tipo"]: linha["total"] for linha in linhas}


def inserir_transacao(con, descricao, valor_centavos, data, mes, categoria_id):
    cursor = con.execute(
        "INSERT INTO transacoes (descricao, valor_centavos, data, mes, categoria_id) "
        "VALUES (?, ?, ?, ?, ?)",
        (descricao, valor_centavos, data, mes, categoria_id),
    )
    return cursor.lastrowid


def atualizar_transacao(
    con, transacao_id, descricao, valor_centavos, data, mes, categoria_id
):
    cursor = con.execute(
        "UPDATE transacoes SET descricao = ?, valor_centavos = ?, data = ?, "
        "mes = ?, categoria_id = ? WHERE id = ?",
        (descricao, valor_centavos, data, mes, categoria_id, transacao_id),
    )
    return cursor.rowcount


def excluir_transacao(con, transacao_id):
    return con.execute(
        "DELETE FROM transacoes WHERE id = ?", (transacao_id,)
    ).rowcount


# --- Meses ------------------------------------------------------------------

def listar_meses(con):
    return [
        linha["nome"]
        for linha in con.execute("SELECT nome FROM meses ORDER BY nome DESC")
    ]


def existe_mes(con, nome):
    return con.execute("SELECT 1 FROM meses WHERE nome = ?", (nome,)).fetchone() is not None


def inserir_mes(con, nome):
    con.execute("INSERT INTO meses (nome) VALUES (?)", (nome,))


def renomear_mes(con, nome_antigo, nome_novo):
    return con.execute(
        "UPDATE meses SET nome = ? WHERE nome = ?", (nome_novo, nome_antigo)
    ).rowcount


def mover_transacoes_de_mes(con, mes_antigo, mes_novo):
    return con.execute(
        "UPDATE transacoes SET mes = ? WHERE mes = ?", (mes_novo, mes_antigo)
    ).rowcount


def excluir_mes(con, nome):
    return con.execute("DELETE FROM meses WHERE nome = ?", (nome,)).rowcount


def excluir_transacoes_do_mes(con, nome):
    return con.execute("DELETE FROM transacoes WHERE mes = ?", (nome,)).rowcount
