"""Testes do acesso ao Gemini que não dependem de rede nem de chave."""

import pytest

from radar.llm import ChaveAusente, escolher_modelo, ler_chave

NOMES = [
    "gemini-3.1-flash-lite",
    "gemini-3.1-flash-lite-image",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash-lite-preview-09-2026",
    "gemini-3.8-flash",
    "gemma-4-31b-it",
]


def test_escolhe_o_primeiro_candidato_disponivel():
    assert escolher_modelo(NOMES, ("3.5-flash-lite", "3.1-flash-lite")) == "gemini-3.5-flash-lite"


def test_usa_o_segundo_candidato_quando_o_primeiro_nao_existe():
    assert escolher_modelo(NOMES, ("9.9-flash-lite", "3.1-flash-lite")) == "gemini-3.1-flash-lite"


def test_ignora_modelos_de_imagem():
    nomes = ["gemini-3.1-flash-lite-image", "gemini-3.1-flash-lite-preview"]
    assert escolher_modelo(nomes, ("3.1-flash-lite",)) == "gemini-3.1-flash-lite-preview"


def test_devolve_none_quando_nada_corresponde():
    assert escolher_modelo(NOMES, ("modelo-inexistente",)) is None


def test_chave_ausente_gera_erro_claro(monkeypatch):
    # Variável vazia no ambiente tem prioridade sobre o arquivo .env.
    monkeypatch.setenv("GEMINI_API_KEY", "")
    with pytest.raises(ChaveAusente):
        ler_chave()
