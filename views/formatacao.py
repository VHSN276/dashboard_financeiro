"""Formatação de rótulos usados apenas na interface."""


_ABREVIACOES_MESES = (
    "JAN",
    "FEV",
    "MAR",
    "ABR",
    "MAI",
    "JUN",
    "JUL",
    "AGO",
    "SET",
    "OUT",
    "NOV",
    "DEZ",
)


def formatar_rotulo_mes(mes):
    """Acrescenta a abreviação em português sem alterar o valor armazenado."""
    if not isinstance(mes, str) or len(mes) != 7 or mes[4] != "-":
        return mes

    ano, numero_mes = mes[:4], mes[5:]
    if not ano.isdigit() or not numero_mes.isdigit():
        return mes

    numero_mes = int(numero_mes)
    if not 1 <= numero_mes <= 12:
        return mes

    return f"{mes} ({_ABREVIACOES_MESES[numero_mes - 1]})"
