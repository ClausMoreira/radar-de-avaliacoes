"""Testes do acesso ao Gemini que não dependem de rede nem de chave."""

import json
from types import SimpleNamespace

import pytest

from radar.llm import (
    ChaveAusente, ErroDaAPI, Gemini, RespostaInvalida, escolher_modelo, ler_chave,
)

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


# --- Classe Gemini: cache, intervalo e novas tentativas, sem rede ---

ESQUEMA = {"type": "object"}


class ClienteDeMentira:
    """Imita o cliente do Google: devolve, em ordem, as respostas combinadas."""

    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.chamadas = 0
        self.models = SimpleNamespace(generate_content=self._gerar)

    def _gerar(self, model, contents, config):
        self.chamadas += 1
        resposta = self.respostas.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return SimpleNamespace(text=resposta)


class Relogio:
    """Tempo de mentira: dormir só avança o relógio e anota a espera."""

    def __init__(self):
        self.agora = 0.0
        self.esperas = []

    def dormir(self, segundos):
        self.esperas.append(segundos)
        self.agora += segundos

    def ler(self):
        return self.agora


def criar_gemini(tmp_path, respostas, intervalo=0):
    cliente, relogio = ClienteDeMentira(respostas), Relogio()
    gemini = Gemini(
        cliente, "modelo-teste", pasta_cache=tmp_path / "cache",
        intervalo=intervalo, dormir=relogio.dormir, relogio=relogio.ler,
    )
    return gemini, cliente, relogio


def erro_da_api(codigo):
    return ErroDaAPI(codigo, {"error": {"message": "erro simulado"}})


def test_segunda_pergunta_igual_vem_do_cache(tmp_path):
    gemini, cliente, _ = criar_gemini(tmp_path, ['{"ok": true}'])
    assert gemini.gerar_json("pergunta", ESQUEMA) == {"ok": True}
    assert gemini.gerar_json("pergunta", ESQUEMA) == {"ok": True}
    assert cliente.chamadas == 1
    assert (gemini.requisicoes, gemini.respostas_do_cache) == (1, 1)


def test_pergunta_diferente_nao_usa_o_cache(tmp_path):
    gemini, cliente, _ = criar_gemini(tmp_path, ['{"n": 1}', '{"n": 2}'])
    assert gemini.gerar_json("pergunta A", ESQUEMA) == {"n": 1}
    assert gemini.gerar_json("pergunta B", ESQUEMA) == {"n": 2}
    assert cliente.chamadas == 2


def test_espera_o_intervalo_entre_requisicoes(tmp_path):
    gemini, _, relogio = criar_gemini(tmp_path, ['{"n": 1}', '{"n": 2}'], intervalo=4.5)
    gemini.gerar_json("pergunta A", ESQUEMA)
    gemini.gerar_json("pergunta B", ESQUEMA)
    assert relogio.esperas == [4.5]  # só antes da segunda


def test_tenta_de_novo_quando_o_limite_por_minuto_estoura(tmp_path):
    gemini, cliente, relogio = criar_gemini(tmp_path, [erro_da_api(429), '{"ok": true}'])
    assert gemini.gerar_json("pergunta", ESQUEMA) == {"ok": True}
    assert cliente.chamadas == 2
    assert relogio.esperas == [20]
    assert gemini.requisicoes == 2  # a tentativa recusada também conta


def test_desiste_depois_de_tres_recusas_seguidas(tmp_path):
    gemini, cliente, _ = criar_gemini(tmp_path, [erro_da_api(429)] * 3)
    with pytest.raises(ErroDaAPI):
        gemini.gerar_json("pergunta", ESQUEMA)
    assert cliente.chamadas == 3


def test_erro_que_nao_passa_sozinho_nao_e_repetido(tmp_path):
    gemini, cliente, _ = criar_gemini(tmp_path, [erro_da_api(400)])
    with pytest.raises(ErroDaAPI):
        gemini.gerar_json("pergunta", ESQUEMA)
    assert cliente.chamadas == 1


def test_resposta_que_nao_e_json_gera_nova_requisicao(tmp_path):
    gemini, cliente, _ = criar_gemini(tmp_path, ["isto não é JSON", '{"ok": true}'])
    assert gemini.gerar_json("pergunta", ESQUEMA) == {"ok": True}
    assert cliente.chamadas == 2


def test_resposta_reprovada_nao_entra_no_cache(tmp_path):
    def reprovar(dados):
        raise RespostaInvalida("faltou avaliação")

    gemini, cliente, _ = criar_gemini(tmp_path, ['{"n": 1}', '{"n": 2}'])
    with pytest.raises(RespostaInvalida):
        gemini.gerar_json("pergunta", ESQUEMA, validar=reprovar)
    assert cliente.chamadas == 2
    assert not list((tmp_path / "cache").glob("*.json"))


def test_cache_nao_guarda_o_prompt_nem_a_chave(tmp_path):
    gemini, _, _ = criar_gemini(tmp_path, ['{"ok": true}'])
    gemini.gerar_json("pergunta secreta", ESQUEMA)
    (arquivo,) = (tmp_path / "cache").glob("*.json")
    guardado = json.loads(arquivo.read_text(encoding="utf-8"))
    assert guardado == {"modelo": "modelo-teste", "resposta": {"ok": True}}
