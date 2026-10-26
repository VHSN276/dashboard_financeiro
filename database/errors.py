"""Erros e mensagens do acesso ao banco de dados."""

MENSAGEM_BANCO_INDISPONIVEL = (
    "Não foi possível acessar o banco de dados. Tente novamente."
)


class BancoIndisponivelError(Exception):
    """O banco de dados não pôde ser aberto, lido ou gravado."""
