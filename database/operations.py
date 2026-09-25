"""Acesso ao banco de dados para as operações da aplicação."""

from database import queries
from database.connection_bd import get_connection


def _executar(sql, parametros=(), *, buscar=None, confirmar=False):
    """Executa uma consulta e sempre fecha o cursor e a conexão."""
    conexao = get_connection()
    if conexao is None:
        return None

    cursor = None
    try:
        cursor = conexao.cursor()
        cursor.execute(sql, parametros)
        if confirmar:
            conexao.commit()

        if buscar == "todos":
            return cursor.fetchall()
        if buscar == "um":
            return cursor.fetchone()
        return cursor.rowcount
    finally:
        try:
            if cursor is not None:
                cursor.close()
        finally:
            conexao.close()


def adicionar_nova_transacao(descricao, valor, data, tipo, categoria_id):
    resultado = _executar(
        queries.INSERIR_TRANSACAO,
        (descricao, valor, data, tipo, categoria_id),
        confirmar=True,
    )
    return resultado is not None


def listar_transacoes():
    return _executar(queries.LISTAR_TRANSACOES, buscar="todos") or []


def listar_categorias():
    return _executar(queries.LISTAR_CATEGORIAS, buscar="todos") or []


def deletar_transacao_db(id_transacao):
    resultado = _executar(
        queries.EXCLUIR_TRANSACAO,
        (id_transacao,),
        confirmar=True,
    )
    return resultado is not None and resultado > 0


def atualizar_transacao_db(
    id_transacao, descricao, valor, data, tipo, categoria_id
):
    resultado = _executar(
        queries.ATUALIZAR_TRANSACAO,
        (descricao, valor, data, tipo, categoria_id, id_transacao),
        confirmar=True,
    )
    return resultado is not None


def adicionar_mes(nome_mes):
    resultado = _executar(
        queries.INSERIR_MES,
        (nome_mes,),
        confirmar=True,
    )
    return resultado is not None


def listar_meses():
    return _executar(queries.LISTAR_MESES, buscar="todos") or []


def atualizar_mes(nome_antigo, nome_novo):
    resultado = _executar(
        queries.ATUALIZAR_MES,
        (nome_novo, nome_antigo),
        confirmar=True,
    )
    return resultado is not None
