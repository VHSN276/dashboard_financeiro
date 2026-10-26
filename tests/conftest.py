import pytest


@pytest.fixture(autouse=True)
def banco_temporario(tmp_path, monkeypatch):
    """Cada teste usa um banco SQLite novo e isolado."""
    monkeypatch.setenv("CONTROLE_FINANCEIRO_DB", str(tmp_path / "teste.db"))
