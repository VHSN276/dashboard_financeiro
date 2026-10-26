"""Conversão e validação de valores, datas e meses digitados pelo usuário."""

import re
from datetime import datetime
from decimal import Decimal

ANO_MINIMO = 1900
ANO_MAXIMO = 2100
LIMITE_CENTAVOS = 99_999_999_999  # R$ 999.999.999,99


class ErroDeValidacao(Exception):
    """Entrada inválida; a mensagem é exibida ao usuário."""


def converter_valor_para_centavos(texto) -> int:
    """Converte '1.234,56', '1234.56', '50' ou 'R$ 10,5' em centavos (inteiro)."""
    bruto = (texto or "").replace("R$", "").replace(" ", "").strip()
    if not bruto:
        raise ErroDeValidacao("Informe o valor.")

    if "," in bruto:
        # Vírgula é o separador decimal; pontos são separadores de milhar.
        normalizado = bruto.replace(".", "")
        if normalizado.count(",") != 1:
            raise ErroDeValidacao("Valor inválido. Use o formato 1234,56.")
        normalizado = normalizado.replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", bruto):
        normalizado = bruto.replace(".", "")
    else:
        normalizado = bruto

    if not re.fullmatch(r"\d+(\.\d{1,2})?", normalizado):
        raise ErroDeValidacao("Valor inválido. Use o formato 1234,56.")

    centavos = int((Decimal(normalizado) * 100).to_integral_value())
    if centavos <= 0:
        raise ErroDeValidacao("O valor deve ser maior que zero.")
    if centavos > LIMITE_CENTAVOS:
        raise ErroDeValidacao("Valor acima do limite permitido.")
    return centavos


def formatar_brl(centavos: int) -> str:
    """123456 -> 'R$ 1.234,56'; valores negativos -> '-R$ 50,00'."""
    sinal = "-" if centavos < 0 else ""
    reais, resto = divmod(abs(centavos), 100)
    return f"{sinal}R$ {reais:,}".replace(",", ".") + f",{resto:02d}"


def formatar_valor_para_edicao(centavos: int) -> str:
    """123456 -> '1234,56' (formato aceito de volta pelo campo de valor)."""
    reais, resto = divmod(abs(centavos), 100)
    return f"{reais},{resto:02d}"


def validar_data(texto) -> str:
    """Valida AAAA-MM-DD e devolve a data normalizada."""
    try:
        data = datetime.strptime((texto or "").strip(), "%Y-%m-%d")
    except ValueError:
        raise ErroDeValidacao(
            "Data inválida. Use o formato AAAA-MM-DD (ex.: 2026-08-15)."
        ) from None
    if not ANO_MINIMO <= data.year <= ANO_MAXIMO:
        raise ErroDeValidacao(f"Informe um ano entre {ANO_MINIMO} e {ANO_MAXIMO}.")
    return data.strftime("%Y-%m-%d")


def validar_mes(texto) -> str:
    """Valida AAAA-MM e devolve o mês normalizado."""
    bruto = (texto or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}", bruto):
        raise ErroDeValidacao("Informe o mês no formato AAAA-MM (ex.: 2026-08).")
    ano, mes = int(bruto[:4]), int(bruto[5:])
    if not 1 <= mes <= 12:
        raise ErroDeValidacao("Mês inválido: use um valor de 01 a 12.")
    if not ANO_MINIMO <= ano <= ANO_MAXIMO:
        raise ErroDeValidacao(f"Informe um ano entre {ANO_MINIMO} e {ANO_MAXIMO}.")
    return bruto
