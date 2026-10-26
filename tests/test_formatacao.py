import pytest

from controllers.formatacao import (
    ErroDeValidacao,
    converter_valor_para_centavos,
    formatar_brl,
    formatar_valor_para_edicao,
    validar_data,
    validar_mes,
)


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("50", 5000),
        ("50,5", 5050),
        ("50,50", 5050),
        ("1.234,56", 123456),
        ("1234.56", 123456),
        ("1.234", 123400),
        ("1.234.567,89", 123456789),
        ("R$ 10,00", 1000),
        ("  0,01 ", 1),
    ],
)
def test_converte_valores_validos(texto, esperado):
    assert converter_valor_para_centavos(texto) == esperado


@pytest.mark.parametrize(
    "texto",
    ["", None, "   ", "abc", "0", "0,00", "-5", "1,234,5", "10,999", "1e3", "99999999999,99"],
)
def test_rejeita_valores_invalidos(texto):
    with pytest.raises(ErroDeValidacao):
        converter_valor_para_centavos(texto)


def test_formatar_brl():
    assert formatar_brl(123456) == "R$ 1.234,56"
    assert formatar_brl(0) == "R$ 0,00"
    assert formatar_brl(5) == "R$ 0,05"
    assert formatar_brl(-5000) == "-R$ 50,00"
    assert formatar_brl(100000000) == "R$ 1.000.000,00"


def test_valor_para_edicao_volta_para_o_mesmo_valor():
    for centavos in (1, 99, 100, 123456, 100000000):
        assert converter_valor_para_centavos(formatar_valor_para_edicao(centavos)) == centavos


def test_validar_data():
    assert validar_data("2026-08-01") == "2026-08-01"
    assert validar_data("2026-8-1") == "2026-08-01"
    for invalida in ("2026-02-30", "01/08/2026", "", None, "2026-13-01", "0999-01-01"):
        with pytest.raises(ErroDeValidacao):
            validar_data(invalida)


def test_validar_mes():
    assert validar_mes(" 2026-08 ") == "2026-08"
    for invalido in ("2026-13", "2026-00", "2026-8", "26-08", "agosto", "", None):
        with pytest.raises(ErroDeValidacao):
            validar_mes(invalido)
