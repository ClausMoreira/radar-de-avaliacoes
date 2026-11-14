"""Testes da automação: regra da avaliação crítica, escolha, envio e conferência. Sem rede."""

import pandas as pd
import pytest

from radar import automacao
from radar.automacao import (
    COLUNAS_DO_REGISTRO, conferir_registro, eh_critica, eh_endereco_de_teste, enviar_todas,
    escolher, ler_webhook, montar_envio, resumo_do_registro,
)
from radar.config import CATEGORIAS


@pytest.fixture
def novas():
    return pd.DataFrame(
        {
            "review_id": [f"r{n}" for n in range(10)],
            "data_avaliacao": pd.to_datetime(["2018-08-01"] * 10),
            "nota": [1, 1, 2, 3, 4, 5, 5, 5, 1, 2],
            "texto": [f"texto {n}" for n in range(10)],
            "categoria": ["Moveis"] * 10,
            "atraso_dias": [0.0] * 10,
        }
    )


def linha_do_registro(review_id, nota, motivo, critica, rascunho=""):
    valores = dict.fromkeys(COLUNAS_DO_REGISTRO, "")
    valores.update(review_id=review_id, nota=str(nota), motivo=motivo, critica=critica, rascunho=rascunho)
    return valores


# --- Regra -------------------------------------------------------------------

@pytest.mark.parametrize("nota, motivo, esperado", [
    (1, "nao_recebido", True),
    (2, "atendimento_e_pos_venda", True),
    (3, "nao_recebido", False),       # nota 3 não gera alerta
    (5, "defeito_ou_qualidade", False),
    (1, "elogio", False),             # nota baixa sem motivo de reclamação
    (1, "outro", False),
])
def test_regra_da_avaliacao_critica(nota, motivo, esperado):
    assert eh_critica(nota, motivo) is esperado


def test_todo_motivo_da_taxonomia_tem_resposta_na_regra():
    for motivo in CATEGORIAS:
        assert eh_critica(1, motivo) is (motivo not in ("elogio", "outro"))


# --- Escolha -----------------------------------------------------------------

def test_escolher_repete_a_mesma_ordem_e_continua_de_onde_parou(novas):
    primeiras = escolher(novas, 4, semente=7)
    assert escolher(novas, 4, semente=7)["review_id"].tolist() == primeiras["review_id"].tolist()
    seguintes = escolher(novas, 4, semente=7, inicio=4)
    assert not set(primeiras["review_id"]) & set(seguintes["review_id"])


def test_escolher_por_nota_e_por_review_id(novas):
    assert set(escolher(novas, 10, semente=7, nota=1)["nota"]) == {1}
    assert escolher(novas, 1, semente=7, review_id="r3")["review_id"].tolist() == ["r3"]
    with pytest.raises(ValueError):
        escolher(novas, 1, semente=7, review_id="nao_existe")


def test_montar_envio_manda_so_o_que_o_marketplace_mandaria(novas):
    envio = montar_envio(novas.iloc[0])
    assert envio == {
        "review_id": "r0", "data_avaliacao": "2018-08-01", "nota": 1,
        "categoria": "Moveis", "texto": "texto 0",
    }
    assert isinstance(envio["nota"], int)


# --- Envio -------------------------------------------------------------------

def test_enviar_todas_respeita_o_intervalo_e_a_ordem():
    enviados, esperas = [], []
    total = enviar_todas(
        "https://exemplo/webhook/x", [{"review_id": "a"}, {"review_id": "b"}, {"review_id": "c"}],
        intervalo=8, enviar_uma=lambda endereco, envio: enviados.append(envio["review_id"]),
        esperar=esperas.append,
    )
    assert total == 3
    assert enviados == ["a", "b", "c"]
    assert esperas == [8, 8]          # espera entre os envios, não antes do primeiro


def test_endereco_de_teste_e_de_producao():
    assert eh_endereco_de_teste("https://x.app.n8n.cloud/webhook-test/abc")
    assert not eh_endereco_de_teste("https://x.app.n8n.cloud/webhook/abc")


def test_ler_webhook_exige_endereco_https(monkeypatch):
    monkeypatch.setattr(automacao, "load_dotenv", lambda *a, **k: None)
    monkeypatch.delenv("N8N_WEBHOOK_URL", raising=False)
    with pytest.raises(automacao.WebhookAusente):
        ler_webhook()
    monkeypatch.setenv("N8N_WEBHOOK_URL", "http://sem-https/webhook/x")
    with pytest.raises(automacao.WebhookAusente):
        ler_webhook()
    monkeypatch.setenv("N8N_WEBHOOK_URL", "https://x.app.n8n.cloud/webhook/abc")
    assert ler_webhook().startswith("https://")


# --- Conferência -------------------------------------------------------------

def test_conferir_registro_correto_nao_aponta_problemas(novas):
    registro = pd.DataFrame([
        linha_do_registro("r0", 1, "nao_recebido", "TRUE", "Olá, sentimos muito..."),
        linha_do_registro("r5", 5, "elogio", "FALSE"),
        linha_do_registro("r3", 3, "atraso", "FALSO"),          # planilha em português
    ])
    assert conferir_registro(registro, novas) == []
    assert resumo_do_registro(registro)["criticas"] == 1


def test_conferir_registro_aponta_cada_tipo_de_problema(novas):
    registro = pd.DataFrame([
        linha_do_registro("r0", 1, "nao_recebido", "FALSE", "rascunho"),   # regra diferente
        linha_do_registro("r1", 1, "defeito_ou_qualidade", "TRUE"),        # crítica sem rascunho
        linha_do_registro("r5", 5, "elogio", "FALSE", "rascunho"),         # rascunho indevido
        linha_do_registro("r2", 5, "elogio", "FALSE"),                     # nota alterada
        linha_do_registro("r4", 4, "preco", "FALSE"),                      # motivo fora da lista
        linha_do_registro("zz", 1, "atraso", "TRUE", "rascunho"),          # não enviada por nós
        linha_do_registro("r5", 5, "elogio", "FALSE"),                     # repetida
    ])
    problemas = "\n".join(conferir_registro(registro, novas))
    for trecho in ["r0: a regra daria crítica=True", "r1: avaliação crítica sem rascunho",
                   "r5: avaliação não crítica com rascunho", "r2: a nota do registro difere",
                   "r4: motivo fora da lista", "zz: não está entre as avaliações novas",
                   "r5: registrada mais de uma vez"]:
        assert trecho in problemas


def test_conferir_registro_exige_as_colunas(novas):
    problemas = conferir_registro(pd.DataFrame({"review_id": ["r0"]}), novas)
    assert len(problemas) == 1 and problemas[0].startswith("Colunas faltando")
