"""Regras de negócio e formatação de dados das transações."""

import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation

from database.operations import (
    adicionar_nova_transacao,
    atualizar_transacao_db,
    deletar_transacao_db,
    listar_categorias,
    listar_transacoes,
)


logger = logging.getLogger(__name__)
TIPOS_TRANSACAO = {
    "RECEITA": "RECEITA",
    "GANHO": "RECEITA",
    "DESPESA": "DESPESA",
}


def _validar_dados(descricao, valor, data, tipo, categoria_id):
    descricao = (descricao or "").strip()
    if not descricao or not valor or not tipo or not categoria_id:
        raise ValueError("Preencha todos os campos obrigatórios.")

    try:
        valor_formatado = Decimal(str(valor).strip().replace(",", "."))
    except InvalidOperation as erro:
        raise ValueError("Valor inválido. Use um número, como 21,90.") from erro
    if not valor_formatado.is_finite():
        raise ValueError("Valor inválido. Use um número, como 21,90.")

    tipo_formatado = TIPOS_TRANSACAO.get(str(tipo).strip().upper())
    if tipo_formatado is None:
        raise ValueError("Selecione Receita ou Despesa.")

    try:
        data_formatada = datetime.strptime(str(data).strip(), "%Y-%m-%d").date()
        categoria_formatada = int(categoria_id)
    except (TypeError, ValueError) as erro:
        raise ValueError("Confira a data e a categoria selecionadas.") from erro

    return descricao, valor_formatado, data_formatada, tipo_formatado, categoria_formatada


def _formatar_moeda(valor):
    valor = Decimal(str(valor)).quantize(Decimal("0.01"))
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def _obter_transacoes():
    try:
        return listar_transacoes()
    except Exception:
        logger.exception("Não foi possível listar as transações.")
        return []


def _mensagem_erro(acao):
    logger.exception("Falha ao %s transação.", acao)
    return False, f"Não foi possível {acao} a transação. Verifique o banco de dados."


def processar_nova_transacao(descricao, valor_str, data, tipo, categoria_id_str):
    try:
        dados = _validar_dados(descricao, valor_str, data, tipo, categoria_id_str)
        if adicionar_nova_transacao(*dados):
            return True, "Transação salva com sucesso!"
        return False, "Banco de dados indisponível. Tente novamente."
    except ValueError as erro:
        return False, str(erro)
    except Exception:
        return _mensagem_erro("salvar")


def obter_transacoes_formatadas(filtros_ativos=None):
    filtros = set(filtros_ativos or [])
    transacoes_prontas = []

    for transacao in _obter_transacoes():
        id_transacao, descricao, categoria, data, valor, tipo, categoria_id = transacao
        if filtros and categoria not in filtros:
            continue

        eh_despesa = str(tipo).upper() == "DESPESA"
        sinal = "-" if eh_despesa else "+"
        transacoes_prontas.append(
            {
                "id": id_transacao,
                "descricao": descricao,
                "categoria": categoria,
                "data": str(data),
                "valor_texto": f"{sinal} {_formatar_moeda(valor)}",
                "eh_despesa": eh_despesa,
                "valor_puro": str(valor),
                "tipo_puro": tipo,
                "categoria_id": str(categoria_id) if categoria_id is not None else None,
            }
        )

    return transacoes_prontas


def obter_opcoes_categorias():
    try:
        categorias = listar_categorias()
    except Exception:
        logger.exception("Não foi possível carregar as categorias.")
        return []

    return [{"key": str(id_categoria), "text": nome} for id_categoria, nome in categorias]


def obter_resumo_financeiro(filtros_ativos=None):
    filtros = set(filtros_ativos or [])
    total_ganhos = Decimal("0.00")
    total_gastos = Decimal("0.00")
    nomes_ganhos = set()
    nomes_gastos = set()

    for transacao in _obter_transacoes():
        categoria = transacao[2]
        valor = Decimal(str(transacao[4]))
        tipo = str(transacao[5]).upper()

        if filtros and categoria not in filtros:
            continue

        if tipo in {"RECEITA", "GANHO"}:
            total_ganhos += valor
            if categoria in filtros:
                nomes_ganhos.add(categoria)
        else:
            total_gastos += valor
            if categoria in filtros:
                nomes_gastos.add(categoria)

    restante = total_ganhos - total_gastos
    return (
        _formatar_moeda(total_ganhos),
        _formatar_moeda(total_gastos),
        _formatar_moeda(restante),
        sorted(nomes_ganhos),
        sorted(nomes_gastos),
    )


def processar_exclusao(id_transacao):
    try:
        if deletar_transacao_db(id_transacao):
            return True, "Transação apagada com sucesso!"
        return False, "Transação não encontrada ou banco indisponível."
    except Exception:
        return _mensagem_erro("excluir")


def processar_edicao(
    id_transacao, descricao, valor_str, data, tipo, categoria_id_str
):
    try:
        dados = _validar_dados(descricao, valor_str, data, tipo, categoria_id_str)
        if atualizar_transacao_db(id_transacao, *dados):
            return True, "Transação atualizada com sucesso!"
        return False, "Banco de dados indisponível. Tente novamente."
    except ValueError as erro:
        return False, str(erro)
    except Exception:
        return _mensagem_erro("atualizar")
