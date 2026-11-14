"""O fluxo do n8n versionado precisa usar os mesmos prompts, a mesma lista de
motivos e a mesma regra do código, e não pode carregar dados pessoais."""

import json

import pytest

from radar.classificador import MARCA_AVALIACOES
from radar.config import (
    CATEGORIAS, MODELO_AGENTE, MODELO_CLASSIFICACAO, NOMES_EXIBICAO, NOTA_MAXIMA_CRITICA,
    PASTA_PROMPTS, RAIZ, VERSAO_PROMPT_PRODUCAO,
)

ARQUIVO = RAIZ / "automacao" / "fluxo_radar.json"


@pytest.fixture(scope="module")
def nos():
    fluxo = json.loads(ARQUIVO.read_text(encoding="utf-8"))
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
    codigo = nos["Montar registro"]["parameters"]["jsCode"]
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


def test_arquivo_versionado_nao_tem_dados_pessoais(nos):
    assert nos["Enviar alerta"]["parameters"]["sendTo"] == "SEU_EMAIL@exemplo.com"
    for no in nos.values():
        assert "credentials" not in no, f"{no['name']} traz uma credencial"
    for nome in ("Registrar na planilha", "Guardar rascunho"):
        assert nos[nome]["parameters"]["documentId"]["value"] == ""
