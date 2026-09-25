"""Configuração e inicialização do banco MySQL."""

import ast
import os
from pathlib import Path

import mysql.connector
from mysql.connector import Error

from database import queries


try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        """Carrega o formato simples do .env mesmo sem python-dotenv instalado."""
        arquivo_env = Path(__file__).resolve().parents[1] / ".env"
        if not arquivo_env.exists():
            return

        for linha in arquivo_env.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            chave, valor = linha.split("=", 1)
            valor = valor.strip()
            if valor.startswith(("'", '"')):
                try:
                    valor = ast.literal_eval(valor)
                except (SyntaxError, ValueError):
                    continue
            else:
                valor = valor.split(" #", 1)[0].strip()
            os.environ.setdefault(chave.strip(), str(valor))


load_dotenv()

DB_CONFIG = {
    "host": os.getenv("FINANCE_DB_HOST", "localhost"),
    "user": os.getenv("FINANCE_DB_USER", "root"),
    "password": os.getenv("FINANCE_DB_PASSWORD", ""),
}


def get_connection(db_name="finance_db"):
    """Abre uma conexão ativa com o banco configurado."""
    try:
        return mysql.connector.connect(**DB_CONFIG, database=db_name)
    except Error as erro:
        print(f"Erro ao conectar ao MySQL: {erro}")
        return None


def inicializar_banco():
    """Cria o banco e as tabelas caso ainda não existam."""
    conexao = None
    cursor = None
    try:
        conexao = mysql.connector.connect(**DB_CONFIG)
        cursor = conexao.cursor()
        cursor.execute(queries.CRIAR_BANCO)
        cursor.close()
        conexao.close()
        cursor = None
        conexao = None

        conexao = get_connection()
        if conexao is None:
            return False

        cursor = conexao.cursor()
        cursor.execute(queries.CRIAR_TABELA_CATEGORIAS)
        cursor.execute(queries.CRIAR_TABELA_TRANSACOES)
        cursor.execute(queries.CRIAR_TABELA_METAS)
        cursor.execute(queries.CRIAR_TABELA_MESES)

        cursor.execute("SELECT COUNT(*) FROM categorias")
        if cursor.fetchone()[0] == 0:
            categorias_padrao = [
                ("Salário", "RECEITA"),
                ("Bônus/Extra", "RECEITA"),
                ("Alimentação", "DESPESA"),
                ("Moradia", "DESPESA"),
                ("Cartão de Crédito", "DESPESA"),
                ("Lazer", "DESPESA"),
            ]
            cursor.executemany(
                "INSERT INTO categorias (nome, tipo) VALUES (%s, %s)",
                categorias_padrao,
            )

        conexao.commit()
        print("Banco de dados e tabelas inicializados com sucesso.")
        return True
    except Error as erro:
        print(f"Erro ao inicializar o banco: {erro}")
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if conexao is not None:
            conexao.close()


if __name__ == "__main__":
    inicializar_banco()
