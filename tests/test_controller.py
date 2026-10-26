import sqlite3

import pytest

from controllers import transaction_controller as c
from database.connection import VARIAVEL_CAMINHO, caminho_banco
from database.errors import BancoIndisponivelError, MENSAGEM_BANCO_INDISPONIVEL


def _id_categoria(nome):
    return next(cat["id"] for cat in c.obter_categorias() if cat["nome"] == nome)


def _nova(descricao="Mercado", valor="50,00", data="2026-08-10", tipo="DESPESA",
          categoria="Alimentação", mes=None):
    mes = mes or data[:7]
    c.processar_novo_mes(mes)  # ignora "já cadastrado"
    return c.processar_nova_transacao(
        descricao, valor, data, mes, tipo, str(_id_categoria(categoria))
    )


# --- primeira execução -------------------------------------------------------

def test_primeira_execucao_cria_categorias_e_mes_atual():
    categorias = c.obter_categorias()
    assert {"Salário", "Alimentação"} <= {cat["nome"] for cat in categorias}
    assert categorias[0]["tipo"] == "RECEITA"  # receitas primeiro
    assert len(c.obter_meses_disponiveis()) == 1


def test_categorias_removidas_nao_reaparecem():
    for cat in c.obter_categorias():
        assert c.processar_exclusao_categoria(cat["id"])[0]
    assert c.obter_categorias() == []  # carga inicial só roda no banco novo


# --- categorias --------------------------------------------------------------

def test_categoria_duplicada_ignora_maiusculas_e_espacos():
    assert c.processar_nova_categoria("Pets", "DESPESA") == (True, "Categoria criada com sucesso.")
    sucesso, mensagem = c.processar_nova_categoria("  pets ", "DESPESA")
    assert not sucesso and "Já existe" in mensagem


def test_categoria_exige_nome_e_tipo():
    assert not c.processar_nova_categoria("   ", "DESPESA")[0]
    assert not c.processar_nova_categoria("Pets", None)[0]
    assert not c.processar_nova_categoria("x" * 51, "DESPESA")[0]


def test_editar_categoria_para_nome_de_outra_falha():
    sucesso, mensagem = c.processar_edicao_categoria(_id_categoria("Lazer"), "Saúde", "DESPESA")
    assert not sucesso and "Já existe" in mensagem


def test_editar_categoria_mantendo_o_proprio_nome_funciona():
    assert c.processar_edicao_categoria(_id_categoria("Lazer"), "Lazer", "DESPESA")[0]


def test_nao_altera_tipo_de_categoria_com_transacoes():
    assert _nova()[0]
    sucesso, mensagem = c.processar_edicao_categoria(_id_categoria("Alimentação"), "Alimentação", "RECEITA")
    assert not sucesso and "alterar o tipo" in mensagem


def test_nao_exclui_categoria_vinculada_e_exclui_depois_de_liberar():
    assert _nova()[0]
    categoria_id = _id_categoria("Alimentação")
    sucesso, mensagem = c.processar_exclusao_categoria(categoria_id)
    assert not sucesso and "Reclassifique" in mensagem

    transacao = c.obter_transacoes_formatadas()[0]
    assert c.processar_exclusao(transacao["id"])[0]
    assert c.processar_exclusao_categoria(categoria_id)[0]


def test_excluir_categoria_inexistente():
    assert c.processar_exclusao_categoria(9999) == (False, "Categoria não encontrada.")


# --- transações --------------------------------------------------------------

def test_criar_transacao_e_formatar_para_a_tabela():
    assert _nova(valor="1.234,56")[0]
    (t,) = c.obter_transacoes_formatadas()
    assert t["descricao"] == "Mercado"
    assert t["categoria"] == "Alimentação"
    assert t["data"] == "2026-08-10"
    assert t["mes"] == "2026-08"
    assert t["valor_texto"] == "- R$ 1.234,56"
    assert t["valor_puro"] == "1234,56"
    assert t["tipo_puro"] == "DESPESA" and t["eh_despesa"] is True
    assert t["categoria_id"] == str(_id_categoria("Alimentação"))


def test_receita_formata_com_sinal_positivo():
    _nova("Salário", "5000", "2026-08-05", "RECEITA", "Salário")
    assert c.obter_transacoes_formatadas()[0]["valor_texto"] == "+ R$ 5.000,00"


@pytest.mark.parametrize(
    "campo, valor",
    [
        ("descricao", "  "),
        ("valor", "abc"),
        ("valor", "0"),
        ("data", "10/08/2026"),
        ("mes", None),
        ("mes", "2099-12"),
        ("tipo", None),
        ("categoria", None),
    ],
)
def test_transacao_invalida_nao_e_gravada(campo, valor):
    c.processar_novo_mes("2026-08")
    argumentos = dict(
        descricao="Mercado", valor="50", data="2026-08-10", mes="2026-08",
        tipo="DESPESA", categoria=str(_id_categoria("Alimentação")),
    )
    argumentos[campo] = valor
    sucesso, _ = c.processar_nova_transacao(
        argumentos["descricao"], argumentos["valor"], argumentos["data"],
        argumentos["mes"], argumentos["tipo"], argumentos["categoria"],
    )
    assert not sucesso
    assert c.obter_transacoes_formatadas() == []


def test_tipo_diferente_do_tipo_da_categoria_e_rejeitado():
    sucesso, mensagem = _nova(tipo="RECEITA", categoria="Alimentação")
    assert not sucesso and "é de despesa" in mensagem


def test_editar_e_excluir_transacao():
    _nova()
    transacao_id = c.obter_transacoes_formatadas()[0]["id"]
    assert c.processar_edicao(
        transacao_id, "Feira", "20", "2026-08-11", "2026-08", "DESPESA",
        str(_id_categoria("Alimentação")),
    )[0]
    assert c.obter_transacoes_formatadas()[0]["descricao"] == "Feira"
    assert c.processar_exclusao(transacao_id)[0]
    assert c.processar_exclusao(transacao_id) == (False, "Transação não encontrada.")
    assert c.processar_edicao(
        transacao_id, "x", "1", "2026-08-11", "2026-08", "DESPESA",
        str(_id_categoria("Alimentação")),
    ) == (False, "Transação não encontrada.")


def test_ordenacao_mais_recente_primeiro():
    _nova("A", data="2026-08-01")
    _nova("B", data="2026-08-20")
    _nova("C", data="2026-08-20")
    assert [t["descricao"] for t in c.obter_transacoes_formatadas()] == ["C", "B", "A"]


def test_mes_da_transacao_e_independente_da_data_e_define_onde_ela_aparece():
    assert _nova("Fatura", "100", data="2026-08-31", mes="2026-09")[0]
    assert [x["descricao"] for x in c.obter_transacoes_formatadas(mes_atual="2026-09")] == ["Fatura"]
    assert c.obter_transacoes_formatadas(mes_atual="2026-08") == []
    assert c.obter_resumo_financeiro(None, "2026-09")[1] == "R$ 100,00"
    assert c.obter_resumo_financeiro(None, "2026-08")[1] == "R$ 0,00"


def test_editar_transacao_para_outro_mes_move_ela_de_aba():
    _nova("A", data="2026-08-10")
    c.processar_novo_mes("2026-09")
    transacao = c.obter_transacoes_formatadas()[0]
    assert c.processar_edicao(
        transacao["id"], "A", "50", "2026-08-10", "2026-09", "DESPESA",
        transacao["categoria_id"],
    )[0]
    assert c.obter_transacoes_formatadas(mes_atual="2026-08") == []
    assert len(c.obter_transacoes_formatadas(mes_atual="2026-09")) == 1


def test_mes_obrigatorio_com_mensagem_orientando_a_cadastrar():
    sucesso, mensagem = c.processar_nova_transacao(
        "Mercado", "50", "2026-08-10", None, "DESPESA", str(_id_categoria("Alimentação"))
    )
    assert not sucesso and "Selecione o mês" in mensagem


# --- filtros e resumo --------------------------------------------------------

def _massa():
    _nova("Salário", "5000", "2026-08-05", "RECEITA", "Salário")
    _nova("Mercado", "300,10", "2026-08-10", "DESPESA", "Alimentação")
    _nova("Cinema", "50", "2026-08-12", "DESPESA", "Lazer")
    _nova("Mercado set", "100", "2026-09-02", "DESPESA", "Alimentação")


def test_filtro_por_mes_e_categoria():
    _massa()
    assert len(c.obter_transacoes_formatadas()) == 4
    assert len(c.obter_transacoes_formatadas(mes_atual="2026-08")) == 3
    assert [t["descricao"] for t in c.obter_transacoes_formatadas(["Alimentação"], "2026-08")] == ["Mercado"]
    assert len(c.obter_transacoes_formatadas(["Alimentação", "Lazer"])) == 3


def test_resumo_financeiro_sem_filtros():
    _massa()
    assert c.obter_resumo_financeiro(None, "2026-08") == (
        "R$ 5.000,00", "R$ 350,10", "R$ 4.649,90", [], [],
    )


def test_resumo_financeiro_com_filtros_traz_nomes_por_tipo():
    _massa()
    ganhos, gastos, restante, nomes_ganhos, nomes_gastos = c.obter_resumo_financeiro(
        ["Salário", "Lazer"], "2026-08"
    )
    assert (ganhos, gastos, restante) == ("R$ 5.000,00", "R$ 50,00", "R$ 4.950,00")
    assert nomes_ganhos == ["Salário"] and nomes_gastos == ["Lazer"]


def test_resumo_negativo_e_vazio():
    assert c.obter_resumo_financeiro() == ("R$ 0,00", "R$ 0,00", "R$ 0,00", [], [])
    _nova("Mercado", "10")
    assert c.obter_resumo_financeiro()[2] == "-R$ 10,00"


def test_soma_em_centavos_nao_acumula_erro_de_ponto_flutuante():
    _nova("a", "0,10")
    _nova("b", "0,20")
    assert c.obter_resumo_financeiro()[1] == "R$ 0,30"


# --- meses -------------------------------------------------------------------

def test_meses_crud_e_transacoes_sao_mantidas():
    assert c.processar_novo_mes("2026-08")[0]
    assert c.processar_novo_mes("2026-08") == (False, "Esse mês já está cadastrado.")
    assert not c.processar_novo_mes("2026-13")[0]

    _nova(data="2026-08-10")
    assert c.processar_edicao_mes("2026-08", "2026-07")[0]
    assert c.processar_edicao_mes("2026-08", "2026-06") == (False, "Mês não encontrado.")
    # renomear o mês leva as transações dele junto
    assert len(c.obter_transacoes_formatadas(mes_atual="2026-07")) == 1
    assert c.obter_transacoes_formatadas(mes_atual="2026-08") == []

    c.processar_novo_mes("2026-09")
    assert c.processar_edicao_mes("2026-09", "2026-07") == (False, "Esse mês já está cadastrado.")

    assert c.processar_exclusao_mes("2026-07")[0]
    assert c.processar_exclusao_mes("2026-07") == (False, "Mês não encontrado.")
    # a transação continua no banco e volta quando o mês é recriado
    assert len(c.obter_transacoes_formatadas()) == 1
    assert c.processar_novo_mes("2026-07")[0]
    assert len(c.obter_transacoes_formatadas(mes_atual="2026-07")) == 1


def test_meses_em_ordem_decrescente():
    for mes in ("2026-01", "2026-03", "2025-12"):
        c.processar_novo_mes(mes)
    meses = c.obter_meses_disponiveis()
    assert meses == sorted(meses, reverse=True)


# --- banco indisponível ------------------------------------------------------

def test_banco_indisponivel(tmp_path, monkeypatch):
    monkeypatch.setenv(VARIAVEL_CAMINHO, str(tmp_path))  # um diretório não abre como banco
    with pytest.raises(BancoIndisponivelError):
        c.obter_categorias()
    assert c.processar_nova_categoria("Pets", "DESPESA") == (False, MENSAGEM_BANCO_INDISPONIVEL)
    assert c.processar_exclusao(1) == (False, MENSAGEM_BANCO_INDISPONIVEL)


def test_chaves_estrangeiras_ativas_no_banco():
    from database.connection import conexao

    with conexao() as con:
        assert con.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError):
            con.execute(
                "INSERT INTO transacoes (descricao, valor_centavos, data, categoria_id) "
                "VALUES ('x', 100, '2026-08-01', 9999)"
            )


def test_caminho_padrao_fica_na_pasta_do_usuario(monkeypatch):
    monkeypatch.delenv(VARIAVEL_CAMINHO)
    assert caminho_banco().name == "financas.db"
