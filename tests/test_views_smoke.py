"""Smoke test: as views do protótipo, sem alterações, conversam com o backend real.

Usa uma página falsa (sem abrir janela) e dispara os handlers como a interface faria.
"""

from types import SimpleNamespace

import flet as ft

from controllers import transaction_controller as c
from views.categorias_view import CategoriasView
from views.dashboard_view import DashboardView
from views.meses_view import MesesView
from views.transacoes_view import TransacoesView


class PaginaFalsa:
    def __init__(self):
        self.overlay = []
        self.dialogos = []  # o que foi exibido via page.show_dialog (snackbars)
        self.atualizacoes = 0

    def update(self):
        self.atualizacoes += 1

    def show_dialog(self, dialogo):
        dialogo.open = True
        self.dialogos.append(dialogo)

    def pop_dialog(self):
        for dialogo in reversed(self.dialogos):
            if dialogo.open:
                dialogo.open = False
                return dialogo
        return None

    @property
    def mensagens(self):
        return [d for d in self.dialogos if isinstance(d, ft.SnackBar)]

    @property
    def ultima_mensagem(self):
        return self.mensagens[-1]


def _evento(**atributos):
    return SimpleNamespace(**atributos)


def _montar():
    pagina = PaginaFalsa()
    dashboard = DashboardView()
    transacoes = TransacoesView(pagina, lambda f, m: dashboard.atualizar(f, m))
    meses = MesesView(pagina, transacoes.selecionar_mes)
    categorias = CategoriasView(pagina, transacoes.atualizar_categorias)
    meses.atualizar()
    return pagina, dashboard, transacoes, meses, categorias


def _id(nome):
    return next(cat["id"] for cat in c.obter_categorias() if cat["nome"] == nome)


def test_abertura_mostra_mes_atual_categorias_e_dashboard_zerado():
    _, dashboard, transacoes, meses, _ = _montar()
    assert len(meses.linha_meses.controls) == 1
    assert meses.mes_atual is not None
    assert len(transacoes.linha_filtros.controls) == len(c.obter_categorias())
    assert dashboard.texto_ganhos.value == "R$ 0,00"
    assert transacoes.tabela.rows == []


def test_fluxo_nova_transacao_atualiza_tabela_e_dashboard():
    pagina, dashboard, transacoes, meses, _ = _montar()
    transacoes._abrir_nova_transacao(None)
    transacoes.descricao_input.value = "Mercado"
    transacoes.valor_input.value = "250,75"
    transacoes.tipo_dropdown.value = "DESPESA"
    transacoes.categoria_dropdown.value = str(_id("Alimentação"))
    # a data padrão é hoje, que está no mês cadastrado na carga inicial
    transacoes._salvar_transacao(None)

    assert transacoes.modal.open is False
    assert len(transacoes.tabela.rows) == 1
    assert dashboard.texto_gastos.value == "R$ 250,75"
    assert dashboard.texto_restante.value == "-R$ 250,75"
    assert pagina.ultima_mensagem.bgcolor == ft.Colors.GREEN


def test_erro_de_validacao_fica_visivel_dentro_do_modal_e_nada_e_gravado():
    pagina, _, transacoes, _, _ = _montar()
    transacoes._abrir_nova_transacao(None)
    transacoes.descricao_input.value = ""
    transacoes._salvar_transacao(None)
    assert transacoes.modal.open is True
    assert transacoes.erro_modal.visible is True
    assert "descrição" in transacoes.erro_modal.value.lower()
    assert transacoes.tabela.rows == []
    assert pagina.mensagens == []


def _preencher(transacoes, descricao, valor, tipo, categoria, mes=None):
    transacoes._abrir_nova_transacao(None)
    transacoes.descricao_input.value = descricao
    transacoes.valor_input.value = valor
    transacoes.tipo_dropdown.value = tipo
    transacoes.categoria_dropdown.value = str(_id(categoria))
    if mes:
        transacoes.mes_dropdown.value = mes
    transacoes._salvar_transacao(None)


def test_regressao_adicionar_varias_transacoes_em_sequencia():
    """Bug reportado: depois da 1ª transação o fluxo de adicionar parava de funcionar."""
    _, _, transacoes, _, _ = _montar()
    _preencher(transacoes, "Mercado", "50", "DESPESA", "Alimentação")
    assert len(transacoes.tabela.rows) == 1

    # Ao reabrir, o formulário é novo: nada de Tipo/Categoria "fantasma".
    tipo_antigo = transacoes.tipo_dropdown
    categoria_antiga = transacoes.categoria_dropdown
    transacoes._abrir_nova_transacao(None)
    assert transacoes.tipo_dropdown is not tipo_antigo
    assert transacoes.categoria_dropdown is not categoria_antiga
    assert transacoes.tipo_dropdown.value is None
    assert transacoes.categoria_dropdown.value is None
    assert transacoes.descricao_input.value == ""
    assert transacoes.valor_input.value == ""
    assert transacoes.erro_modal.visible is False

    for numero in range(2, 5):
        _preencher(transacoes, f"Item {numero}", "10", "DESPESA", "Lazer")
        assert transacoes.modal.open is False
        assert len(transacoes.tabela.rows) == numero


def test_modal_abre_com_foco_na_descricao():
    _, _, transacoes, _, _ = _montar()
    transacoes._abrir_nova_transacao(None)
    assert transacoes.descricao_input.autofocus is True
    transacoes._editar_transacao(_evento(control=SimpleNamespace(data={
        "id": 1, "descricao": "x", "valor_puro": "1,00", "data": "2026-10-01",
        "mes": "2026-10", "tipo_puro": "DESPESA", "categoria_id": "1",
    })))
    assert transacoes.descricao_input.autofocus is True


def test_dropdown_de_mes_acompanha_os_meses_cadastrados():
    _, _, transacoes, meses, _ = _montar()
    transacoes._abrir_nova_transacao(None)
    antes = [o.key for o in transacoes.mes_dropdown.options]
    assert antes == [m for m in c.obter_meses_disponiveis()]
    assert transacoes.mes_dropdown.value == meses.mes_atual  # mês em exibição vem marcado

    transacoes._fechar_modal(None)
    meses._abrir_modal_novo_mes(None)
    meses.nome_mes_input.value = "2099-01"
    meses._salvar_novo_mes(None)

    transacoes._abrir_nova_transacao(None)
    assert "2099-01" in [o.key for o in transacoes.mes_dropdown.options]
    assert len(transacoes.mes_dropdown.options) == len(antes) + 1


def test_transacao_so_aparece_no_mes_escolhido():
    pagina, _, transacoes, meses, _ = _montar()
    meses._abrir_modal_novo_mes(None)
    meses.nome_mes_input.value = "2099-01"
    meses._salvar_novo_mes(None)
    mes_exibido = meses.mes_atual  # mantém o mês corrente em exibição
    assert mes_exibido != "2099-01"

    _preencher(transacoes, "Viagem", "900", "DESPESA", "Lazer", mes="2099-01")
    assert transacoes.tabela.rows == []  # mês em exibição não mostra
    assert "2099-01" in pagina.ultima_mensagem.content.value  # e o aviso diz onde ela está

    meses._selecionar_mes(_evento(control=SimpleNamespace(data="2099-01")))
    assert len(transacoes.tabela.rows) == 1


def test_escolher_outro_mes_leva_a_data_junto():
    _, _, transacoes, meses, _ = _montar()
    meses._abrir_modal_novo_mes(None)
    meses.nome_mes_input.value = "2099-02"
    meses._salvar_novo_mes(None)

    transacoes._abrir_nova_transacao(None)
    transacoes.data_input.value = "2026-10-31"
    transacoes.mes_dropdown.value = "2099-02"
    transacoes._ao_selecionar_mes(None)
    assert transacoes.data_input.value == "2099-02-28"  # dia ajustado ao tamanho do mês

    transacoes.data_input.value = "2099-02-10"
    transacoes._ao_selecionar_mes(None)
    assert transacoes.data_input.value == "2099-02-10"  # já no mês: não mexe


def test_filtro_por_chip_e_edicao_e_exclusao():
    _, dashboard, transacoes, _, _ = _montar()
    for descricao, valor, tipo, categoria in [
        ("Salário", "3000", "RECEITA", "Salário"),
        ("Cinema", "40", "DESPESA", "Lazer"),
    ]:
        transacoes._abrir_nova_transacao(None)
        transacoes.descricao_input.value = descricao
        transacoes.valor_input.value = valor
        transacoes.tipo_dropdown.value = tipo
        transacoes.categoria_dropdown.value = str(_id(categoria))
        transacoes._salvar_transacao(None)
    assert len(transacoes.tabela.rows) == 2

    chip_lazer = next(ch for ch in transacoes.linha_filtros.controls if ch.label.value == "Lazer")
    transacoes._alternar_filtro(_evento(control=chip_lazer, data="true"))
    assert len(transacoes.tabela.rows) == 1
    assert dashboard.titulo_gastos.value == "Gastos (Lazer)"
    assert dashboard.texto_gastos.value == "R$ 40,00"

    botoes = transacoes.tabela.rows[0].cells[4].content.controls
    transacoes._editar_transacao(_evento(control=botoes[0]))
    assert transacoes.descricao_input.value == "Cinema"
    assert transacoes.valor_input.value == "40,00"
    transacoes.valor_input.value = "45"
    transacoes._salvar_transacao(None)
    assert transacoes.modal.open is False
    assert dashboard.texto_gastos.value == "R$ 45,00"

    botoes = transacoes.tabela.rows[0].cells[4].content.controls
    transacoes._excluir_transacao(_evento(control=botoes[1]))
    assert transacoes.tabela.rows == []


def test_fluxo_de_categorias_atualiza_chips_e_dropdown():
    _, _, transacoes, _, categorias = _montar()
    antes = len(transacoes.linha_filtros.controls)

    categorias._abrir(None)
    categorias._nova_categoria(None)
    categorias.nome_input.value = "Pets"
    categorias.tipo_dropdown.value = "DESPESA"
    categorias._salvar_categoria(None)

    assert len(transacoes.linha_filtros.controls) == antes + 1
    categorias._fechar(None)
    transacoes._abrir_nova_transacao(None)  # o dropdown é montado a cada abertura
    assert "Pets" in [o.text for o in transacoes.categoria_dropdown.options]
    transacoes._fechar_modal(None)

    # duplicada: erro dentro do modal, sem mexer nos chips
    categorias._nova_categoria(None)
    categorias.nome_input.value = "pets"
    categorias.tipo_dropdown.value = "DESPESA"
    categorias._salvar_categoria(None)
    assert categorias.erro.visible is True and "Já existe" in categorias.erro.value
    assert len(transacoes.linha_filtros.controls) == antes + 1


def test_fluxo_de_meses():
    _, _, transacoes, meses, _ = _montar()
    meses._abrir_modal_novo_mes(None)
    meses.nome_mes_input.value = "2099-01"
    meses._salvar_novo_mes(None)
    assert meses.modal_novo_mes.open is False
    assert [b.content.data for b in meses.linha_meses.controls] == ["2099-01", meses.linha_meses.controls[1].content.data]

    meses._abrir_modal_novo_mes(None)
    meses.nome_mes_input.value = "2099-13"
    meses._salvar_novo_mes(None)
    assert meses.modal_novo_mes.open is True  # permanece aberto com erro

    meses._abrir_opcoes_mes(_evento(control=meses.linha_meses.controls[0]))
    meses._excluir_mes(None)
    assert len(meses.linha_meses.controls) == 1


def test_banco_indisponivel_nas_views_mostra_aviso_sem_quebrar(tmp_path, monkeypatch):
    monkeypatch.setenv("CONTROLE_FINANCEIRO_DB", str(tmp_path))  # diretório: não abre
    pagina = PaginaFalsa()
    dashboard = DashboardView()
    dashboard.atualizar()
    assert dashboard.aviso.visible is True and dashboard.texto_ganhos.value == "—"

    transacoes = TransacoesView(pagina, lambda f, m: None)
    assert transacoes.erro_categorias.visible is True
    transacoes.atualizar_tabela()
    assert transacoes.erro_tabela.visible is True

    meses = MesesView(pagina, transacoes.selecionar_mes)
    meses.atualizar()
    assert meses.erro_carregamento.visible is True
