"""Casos de uso do controle financeiro, consumidos pelas views.

Funções obter_*: leitura; propagam erros de banco (as views já os tratam).
Funções processar_*: escrita; devolvem (sucesso, mensagem) e nunca lançam
exceção para a interface.
"""

import logging
import sqlite3

from controllers.formatacao import (
    ErroDeValidacao,
    converter_valor_para_centavos,
    formatar_brl,
    formatar_valor_para_edicao,
    validar_data,
    validar_mes,
)
from database import repository
from database.connection import conexao
from database.errors import BancoIndisponivelError, MENSAGEM_BANCO_INDISPONIVEL

logger = logging.getLogger(__name__)

MENSAGEM_ERRO_INESPERADO = "Ocorreu um erro inesperado. Tente novamente."
ROTULO_TIPO = {"RECEITA": "receita", "DESPESA": "despesa"}
LIMITE_NOME_CATEGORIA = 50
LIMITE_DESCRICAO = 120


def _processar(operacao):
    """Executa a operação e converte qualquer desfecho em (sucesso, mensagem)."""
    try:
        return True, operacao()
    except ErroDeValidacao as erro:
        return False, str(erro)
    except sqlite3.IntegrityError:
        logger.exception("Violação de integridade ao gravar dados.")
        return False, "Os dados informados violam uma regra de integridade."
    except BancoIndisponivelError:
        logger.exception("Banco de dados indisponível.")
        return False, MENSAGEM_BANCO_INDISPONIVEL
    except Exception:
        logger.exception("Falha inesperada ao processar a operação.")
        return False, MENSAGEM_ERRO_INESPERADO


def _converter_id(valor, mensagem):
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise ErroDeValidacao(mensagem) from None


# --- Categorias -------------------------------------------------------------

def obter_categorias():
    with conexao() as con:
        return repository.listar_categorias(con)


def obter_opcoes_categorias():
    """Opções para dropdown e chips: key = id (texto), text = nome."""
    return [
        {"key": str(categoria["id"]), "text": categoria["nome"]}
        for categoria in obter_categorias()
    ]


def _validar_nome_categoria(nome):
    limpo = " ".join((nome or "").split())
    if not limpo:
        raise ErroDeValidacao("Informe o nome da categoria.")
    if len(limpo) > LIMITE_NOME_CATEGORIA:
        raise ErroDeValidacao(
            f"O nome deve ter no máximo {LIMITE_NOME_CATEGORIA} caracteres."
        )
    return limpo


def _validar_tipo(tipo, mensagem):
    if tipo not in ROTULO_TIPO:
        raise ErroDeValidacao(mensagem)
    return tipo


def processar_nova_categoria(nome, tipo):
    def operacao():
        nome_ok = _validar_nome_categoria(nome)
        tipo_ok = _validar_tipo(tipo, "Selecione o tipo da categoria.")
        with conexao() as con:
            if repository.buscar_categoria_por_nome(con, nome_ok):
                raise ErroDeValidacao("Já existe uma categoria com esse nome.")
            repository.inserir_categoria(con, nome_ok, tipo_ok)
        return "Categoria criada com sucesso."

    return _processar(operacao)


def processar_edicao_categoria(categoria_id, nome, tipo):
    def operacao():
        nome_ok = _validar_nome_categoria(nome)
        tipo_ok = _validar_tipo(tipo, "Selecione o tipo da categoria.")
        with conexao() as con:
            atual = repository.obter_categoria(con, categoria_id)
            if atual is None:
                raise ErroDeValidacao("Categoria não encontrada.")
            existente = repository.buscar_categoria_por_nome(con, nome_ok)
            if existente is not None and existente["id"] != atual["id"]:
                raise ErroDeValidacao("Já existe uma categoria com esse nome.")
            if (
                tipo_ok != atual["tipo"]
                and repository.contar_transacoes_da_categoria(con, atual["id"]) > 0
            ):
                raise ErroDeValidacao(
                    "Não é possível alterar o tipo de uma categoria que já tem "
                    "transações."
                )
            repository.atualizar_categoria(con, atual["id"], nome_ok, tipo_ok)
        return "Categoria atualizada com sucesso."

    return _processar(operacao)


def processar_exclusao_categoria(categoria_id):
    def operacao():
        with conexao() as con:
            if repository.obter_categoria(con, categoria_id) is None:
                raise ErroDeValidacao("Categoria não encontrada.")
            if repository.contar_transacoes_da_categoria(con, categoria_id) > 0:
                raise ErroDeValidacao(
                    "Esta categoria está vinculada a transações e não pode ser "
                    "excluída. Reclassifique essas transações primeiro."
                )
            repository.excluir_categoria(con, categoria_id)
        return "Categoria excluída com sucesso."

    return _processar(operacao)


# --- Transações -------------------------------------------------------------

def _validar_transacao(con, descricao, valor, data, mes, tipo, categoria_id):
    """Valida o formulário e devolve (descricao, centavos, data, mes, categoria_id)."""
    descricao_ok = " ".join((descricao or "").split())
    if not descricao_ok:
        raise ErroDeValidacao("Informe a descrição.")
    if len(descricao_ok) > LIMITE_DESCRICAO:
        raise ErroDeValidacao(
            f"A descrição deve ter no máximo {LIMITE_DESCRICAO} caracteres."
        )
    centavos = converter_valor_para_centavos(valor)
    data_ok = validar_data(data)
    if not mes:
        raise ErroDeValidacao(
            "Selecione o mês da transação (cadastre um em \"+ Mês\" se a lista "
            "estiver vazia)."
        )
    mes_ok = validar_mes(mes)
    if not repository.existe_mes(con, mes_ok):
        raise ErroDeValidacao("O mês selecionado não está mais na lista. Escolha outro.")
    tipo_ok = _validar_tipo(tipo, "Selecione o tipo da transação.")

    id_categoria = _converter_id(categoria_id, "Selecione uma categoria.")
    categoria = repository.obter_categoria(con, id_categoria)
    if categoria is None:
        raise ErroDeValidacao("Categoria não encontrada. Selecione outra.")
    if categoria["tipo"] != tipo_ok:
        raise ErroDeValidacao(
            f"A categoria \"{categoria['nome']}\" é de "
            f"{ROTULO_TIPO[categoria['tipo']]}; escolha o tipo correspondente."
        )
    return descricao_ok, centavos, data_ok, mes_ok, id_categoria


def obter_transacoes_formatadas(filtros_ativos=None, mes_atual=None):
    with conexao() as con:
        linhas = repository.listar_transacoes(con, list(filtros_ativos or []), mes_atual)

    transacoes = []
    for linha in linhas:
        eh_despesa = linha["tipo"] == "DESPESA"
        valor = formatar_brl(linha["valor_centavos"])
        transacoes.append(
            {
                "id": linha["id"],
                "descricao": linha["descricao"],
                "categoria": linha["categoria"],
                "categoria_id": str(linha["categoria_id"]),
                "data": linha["data"],
                "mes": linha["mes"],
                "valor_texto": f"- {valor}" if eh_despesa else f"+ {valor}",
                "valor_puro": formatar_valor_para_edicao(linha["valor_centavos"]),
                "tipo_puro": linha["tipo"],
                "eh_despesa": eh_despesa,
            }
        )
    return transacoes


def obter_resumo_financeiro(filtros_ativos=None, mes_filtro=None):
    """Devolve (ganhos, gastos, restante, nomes_ganhos, nomes_gastos).

    Os três primeiros já formatados em reais; os nomes são das categorias
    filtradas, separadas por tipo (usadas no título dos cards).
    """
    nomes = list(filtros_ativos or [])
    with conexao() as con:
        totais = repository.somar_por_tipo(con, nomes, mes_filtro)
        categorias = repository.listar_categorias(con)

    ganhos = totais.get("RECEITA", 0)
    gastos = totais.get("DESPESA", 0)
    selecionadas = set(nomes)
    nomes_ganhos = [
        c["nome"] for c in categorias if c["tipo"] == "RECEITA" and c["nome"] in selecionadas
    ]
    nomes_gastos = [
        c["nome"] for c in categorias if c["tipo"] == "DESPESA" and c["nome"] in selecionadas
    ]
    return (
        formatar_brl(ganhos),
        formatar_brl(gastos),
        formatar_brl(ganhos - gastos),
        nomes_ganhos,
        nomes_gastos,
    )


def processar_nova_transacao(descricao, valor, data, mes, tipo, categoria_id):
    def operacao():
        with conexao() as con:
            dados = _validar_transacao(con, descricao, valor, data, mes, tipo, categoria_id)
            repository.inserir_transacao(con, *dados)
        return "Transação salva com sucesso."

    return _processar(operacao)


def processar_edicao(transacao_id, descricao, valor, data, mes, tipo, categoria_id):
    def operacao():
        with conexao() as con:
            dados = _validar_transacao(con, descricao, valor, data, mes, tipo, categoria_id)
            if repository.atualizar_transacao(con, transacao_id, *dados) == 0:
                raise ErroDeValidacao("Transação não encontrada.")
        return "Transação atualizada com sucesso."

    return _processar(operacao)


def processar_exclusao(transacao_id):
    def operacao():
        with conexao() as con:
            if repository.excluir_transacao(con, transacao_id) == 0:
                raise ErroDeValidacao("Transação não encontrada.")
        return "Transação excluída com sucesso."

    return _processar(operacao)


# --- Meses ------------------------------------------------------------------

def obter_meses_disponiveis():
    with conexao() as con:
        return repository.listar_meses(con)


def processar_novo_mes(nome):
    def operacao():
        mes = validar_mes(nome)
        with conexao() as con:
            if repository.existe_mes(con, mes):
                raise ErroDeValidacao("Esse mês já está cadastrado.")
            repository.inserir_mes(con, mes)
        return "Mês adicionado com sucesso."

    return _processar(operacao)


def processar_edicao_mes(nome_antigo, nome_novo):
    def operacao():
        mes = validar_mes(nome_novo)
        with conexao() as con:
            if not repository.existe_mes(con, nome_antigo):
                raise ErroDeValidacao("Mês não encontrado.")
            if mes != nome_antigo and repository.existe_mes(con, mes):
                raise ErroDeValidacao("Esse mês já está cadastrado.")
            repository.renomear_mes(con, nome_antigo, mes)
            repository.mover_transacoes_de_mes(con, nome_antigo, mes)
        return "Mês atualizado com sucesso."

    return _processar(operacao)


def processar_exclusao_mes(nome):
    def operacao():
        with conexao() as con:
            if repository.excluir_mes(con, nome) == 0:
                raise ErroDeValidacao("Mês não encontrado.")
        return "Mês excluído. As transações dele foram mantidas e voltam se você recriar o mês."

    return _processar(operacao)
