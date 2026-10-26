"""Conexão com o banco SQLite local."""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from database.errors import BancoIndisponivelError
from database.schema import inicializar

VARIAVEL_CAMINHO = "CONTROLE_FINANCEIRO_DB"


def caminho_banco() -> Path:
    """Arquivo do banco; pode ser trocado pela variável CONTROLE_FINANCEIRO_DB."""
    personalizado = os.environ.get(VARIAVEL_CAMINHO)
    if personalizado:
        return Path(personalizado).expanduser()
    return Path.home() / ".controle_financeiro" / "financas.db"


@contextmanager
def conexao():
    """Abre a conexão, confirma a transação ao final e desfaz em caso de erro.

    Falhas do SQLite viram BancoIndisponivelError; violações de integridade
    seguem como sqlite3.IntegrityError para o controller decidir a mensagem.
    """
    con = None
    try:
        caminho = caminho_banco()
        caminho.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(caminho, timeout=5)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        inicializar(con)
    except (OSError, sqlite3.Error) as erro:
        if con is not None:
            con.close()
        raise BancoIndisponivelError(str(erro)) from erro

    try:
        yield con
        con.commit()
    except sqlite3.IntegrityError:
        con.rollback()
        raise
    except sqlite3.Error as erro:
        con.rollback()
        raise BancoIndisponivelError(str(erro)) from erro
    except BaseException:
        con.rollback()
        raise
    finally:
        con.close()
