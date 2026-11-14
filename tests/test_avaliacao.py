import pandas as pd

from radar.avaliacao import acerto_geral, acerto_por_motivo, confusoes

GABARITO = pd.Series(["atraso", "atraso", "atraso", "elogio", "elogio", "outro"])
PREVISTO = pd.Series(["atraso", "nao_recebido", "nao_recebido", "elogio", "outro", "outro"])


def test_acerto_geral():
    assert acerto_geral(GABARITO, PREVISTO) == {"total": 6, "acertos": 3, "acerto": 0.5}


def test_acerto_geral_sem_linhas_nao_quebra():
    vazio = pd.Series([], dtype=str)
    assert acerto_geral(vazio, vazio) == {"total": 0, "acertos": 0, "acerto": 0.0}


def test_acerto_por_motivo_segue_a_ordem_da_taxonomia():
    tabela = acerto_por_motivo(GABARITO, PREVISTO).set_index("motivo")
    assert tabela.index.tolist() == ["atraso", "elogio", "outro"]
    assert tabela.loc["atraso", ["total", "acertos"]].tolist() == [3, 1]
    assert tabela.loc["atraso", "acerto"] == 0.3333
    assert tabela.loc["outro", "acerto"] == 1.0


def test_confusoes_lista_as_trocas_da_mais_comum_para_a_menos():
    tabela = confusoes(GABARITO, PREVISTO)
    assert tabela.to_dict("records") == [
        {"gabarito": "atraso", "previsto": "nao_recebido", "quantidade": 2},
        {"gabarito": "elogio", "previsto": "outro", "quantidade": 1},
    ]


def test_confusoes_vazia_quando_nao_ha_erro():
    assert len(confusoes(GABARITO, GABARITO)) == 0


from radar.avaliacao import intervalo_de_confianca


def test_intervalo_de_confianca_de_wilson():
    # Valores de referência do intervalo de Wilson com 95% de confiança.
    assert intervalo_de_confianca(54, 60) == (0.7985, 0.9534)
    assert intervalo_de_confianca(0, 10) == (0.0, 0.2775)
    assert intervalo_de_confianca(10, 10) == (0.7225, 1.0)
    assert intervalo_de_confianca(0, 0) == (0.0, 0.0)
