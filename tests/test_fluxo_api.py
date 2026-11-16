"""O fluxo da API precisa usar o mesmo prompt, a mesma lista de motivos, a
mesma regra e os mesmos modelos do fluxo da automação e do código, e não pode
carregar credenciais."""

import json

import pytest

from radar.classificador import MARCA_AVALIACOES
from radar.config import (
    CATEGORIAS, MODELO_AGENTE, MODELO_CLASSIFICACAO, NOMES_EXIBICAO, NOTA_MAXIMA_CRITICA,
    PASTA_PROMPTS, RAIZ, VERSAO_PROMPT_PRODUCAO,
)

ARQUIVO = RAIZ / "automacao" / "fluxo_api.json"


@pytest.fixture(scope="module")
def fluxo():
    return json.loads(ARQUIVO.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def nos(fluxo):
    return {no["name"]: no for no in fluxo["nodes"]}


def test_classificacao_usa_o_prompt_de_producao_sem_alteracao(nos):
    prompt = (PASTA_PROMPTS / f"classificacao_{VERSAO_PROMPT_PRODUCAO}.md").read_text(encoding="utf-8")
    antes, depois = prompt.rstrip("\n").split(MARCA_AVALIACOES)
    texto = nos["Classificar motivo"]["parameters"]["text"]
    assert texto.startswith("=" + antes)
    assert texto.endswith(depois)
    assert "JSON.stringify" in texto[len(antes):]      # a avaliação entra como dado


def test_formato_da_resposta_aceita_so_os_motivos_da_taxonomia(nos):
    esquema = json.loads(nos["Formato da resposta"]["parameters"]["inputSchema"])
    motivos = esquema["properties"]["classificacoes"]["items"]["properties"]["motivo"]["enum"]
    assert motivos == list(CATEGORIAS)


def test_regra_da_avaliacao_critica_e_a_mesma_do_codigo(nos):
    codigo = nos["Montar resposta"]["parameters"]["jsCode"]
    assert f"nota <= {NOTA_MAXIMA_CRITICA} && !['elogio', 'outro'].includes(motivo)" in codigo
    for motivo, nome in NOMES_EXIBICAO.items():
        assert f"{motivo}: '{nome}'" in codigo


def test_rascunho_usa_o_prompt_versionado(nos):
    prompt = (PASTA_PROMPTS / "rascunho_v1.md").read_text(encoding="utf-8")
    regras = prompt.split("## Avaliação")[0]
    assert nos["Rascunhar resposta"]["parameters"]["text"].startswith("=" + regras)


def test_modelos_sao_os_do_projeto(nos):
    assert nos["Gemini (classificação)"]["parameters"]["modelName"] == f"models/{MODELO_CLASSIFICACAO}"
    assert nos["Gemini (rascunho)"]["parameters"]["modelName"] == f"models/{MODELO_AGENTE}"
    assert nos["Gemini (classificação)"]["parameters"]["options"]["temperature"] == 0


def test_webhook_responde_pelo_fluxo_e_aceita_chamadas_do_navegador(nos):
    parametros = nos["Pedido (API)"]["parameters"]
    assert parametros["responseMode"] == "responseNode"
    assert parametros["options"]["allowedOrigins"] == "*"


def test_pedido_invalido_nao_chega_na_ia(fluxo):
    saidas = fluxo["connections"]["Pedido válido?"]["main"]
    assert [c["node"] for c in saidas[0]] == ["Classificar motivo"]
    assert [c["node"] for c in saidas[1]] == ["Responder erro"]


def test_toda_saida_termina_em_uma_resposta(fluxo, nos):
    respostas = {nome for nome, no in nos.items() if no["type"] == "n8n-nodes-base.respondToWebhook"}
    assert respostas == {"Responder erro", "Responder com rascunho", "Responder sem rascunho"}
    destinos = {c["node"] for saida in fluxo["connections"].values() for lista in saida.get("main", []) for c in lista}
    assert respostas <= destinos


def test_api_nao_grava_nada_nem_traz_credenciais(nos):
    tipos = {no["type"] for no in nos.values()}
    assert "n8n-nodes-base.googleSheets" not in tipos
    assert "n8n-nodes-base.gmail" not in tipos
    for no in nos.values():
        assert "credentials" not in no, f"{no['name']} traz uma credencial"
