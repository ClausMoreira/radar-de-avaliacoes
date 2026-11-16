"""Testes das métricas com uma tabela pequena e resultado conferido à mão."""

import pandas as pd
import pytest

from radar.metricas import (
    atraso_real_por_motivo, categorias_por_motivo, evolucao_do_motivo, evolucao_mensal, exemplos,
    filtrar, prioridades, ranking_motivos, resumo_geral,
)


@pytest.fixture
def tabela():
    # 10 avaliações: 4 atraso, 2 defeito, 1 não recebido, 2 elogios, 1 outro.
    return pd.DataFrame(
        {
            "review_id": [f"r{n}" for n in range(10)],
            "data_avaliacao": pd.to_datetime(
                ["2018-01-05", "2018-01-20", "2018-02-03", "2018-02-10", "2018-02-28",
                 "2018-03-01", "2018-03-15", "2018-03-20", "2018-03-31", "2018-01-10"]
            ),
            "nota": [1, 2, 1, 2, 1, 3, 1, 5, 5, 3],
            "categoria": ["Moveis", "Moveis", "Moveis", "Brinquedos", "Brinquedos",
                          "Brinquedos", "Moveis", "Moveis", "Brinquedos", "Moveis"],
            "atraso_dias": [5.0, 2.0, -1.0, 10.0, -3.0, 0.0, None, -5.0, -2.0, -1.0],
            "motivo": ["atraso", "atraso", "atraso", "atraso", "defeito_ou_qualidade",
                       "defeito_ou_qualidade", "nao_recebido", "elogio", "elogio", "outro"],
            "texto": ["Demorou", "Atrasou muito", "Chegou tarde", "Demora", "Quebrado",
                      "Veio QUEBRADO", "Não chegou", "Ótimo", "Adorei", "Hmm"],
        }
    )


def test_resumo_geral(tabela):
    resumo = resumo_geral(tabela)
    assert resumo["avaliacoes"] == 10
    assert resumo["reclamacoes"] == 7          # sem elogio e sem outro
    assert resumo["pct_reclamacoes"] == 70.0
    assert resumo["nota_media"] == 2.4


def test_resumo_de_tabela_vazia_nao_quebra(tabela):
    resumo = resumo_geral(tabela.iloc[0:0])
    assert resumo["avaliacoes"] == 0 and resumo["nota_media"] is None


def test_ranking_ordena_por_quantidade_e_ignora_elogio_e_outro(tabela):
    ranking = ranking_motivos(tabela)
    assert ranking["motivo"].tolist() == ["atraso", "defeito_ou_qualidade", "nao_recebido"]
    assert ranking["quantidade"].tolist() == [4, 2, 1]
    assert ranking["pct_reclamacoes"].tolist() == [57.1, 28.6, 14.3]
    assert ranking.loc[0, "nome"] == "Atraso ou problema na entrega"


def test_ranking_calcula_nota_media_e_atraso_real(tabela):
    atraso = ranking_motivos(tabela).set_index("motivo").loc["atraso"]
    assert atraso["nota_media"] == 1.5
    assert atraso["pct_atrasados"] == 75.0     # 3 dos 4 pedidos passaram do prazo


def test_motivo_sem_data_de_entrega_fica_sem_percentual_de_atraso(tabela):
    nao_recebido = ranking_motivos(tabela).set_index("motivo").loc["nao_recebido"]
    assert pd.isna(nao_recebido["pct_atrasados"])


def test_empate_segue_a_ordem_da_taxonomia():
    empate = pd.DataFrame(
        {
            "data_avaliacao": pd.to_datetime(["2018-01-01"] * 2), "nota": [1, 1],
            "categoria": ["c", "c"], "atraso_dias": [0.0, 0.0],
            "motivo": ["atraso", "nao_recebido"],
        }
    )
    assert ranking_motivos(empate)["motivo"].tolist() == ["nao_recebido", "atraso"]


def test_prioridades_sao_as_primeiras_do_ranking(tabela):
    assert prioridades(tabela, 2)["motivo"].tolist() == ["atraso", "defeito_ou_qualidade"]


def test_ranking_vazio_tem_as_colunas_certas(tabela):
    vazio = ranking_motivos(tabela[tabela["motivo"] == "elogio"])
    assert vazio.empty and "pct_reclamacoes" in vazio.columns


def test_filtrar_por_categoria_e_periodo(tabela):
    assert len(filtrar(tabela, categorias=["Brinquedos"])) == 4
    # O fim é inclusivo: 2018-02-28 entra.
    assert filtrar(tabela, inicio="2018-02-01", fim="2018-02-28")["review_id"].tolist() == ["r2", "r3", "r4"]
    assert len(filtrar(tabela)) == 10


def test_atraso_real_por_motivo(tabela):
    tabela_atraso = atraso_real_por_motivo(tabela).set_index("motivo")
    assert tabela_atraso.loc["atraso", "pct_atrasados"] == 75.0
    assert tabela_atraso.loc["elogio", "pct_atrasados"] == 0.0
    assert "nao_recebido" not in tabela_atraso.index   # nenhum pedido entregue


def test_evolucao_mensal(tabela):
    evolucao = evolucao_mensal(tabela)
    fevereiro = evolucao[evolucao["mes"] == pd.Timestamp("2018-02-01")].set_index("motivo")
    assert fevereiro.loc["atraso", "quantidade"] == 2
    assert fevereiro.loc["defeito_ou_qualidade", "quantidade"] == 1
    assert "elogio" not in set(evolucao["motivo"])


def test_evolucao_do_motivo_conta_e_calcula_a_parte_do_mes(tabela):
    # Reclamações por mês: janeiro 2 (2 de atraso), fevereiro 3 (2 de atraso), março 2 (0 de atraso).
    evolucao = evolucao_do_motivo(tabela, "atraso", minimo=3)
    assert evolucao["mes"].tolist() == list(pd.to_datetime(["2018-01-01", "2018-02-01", "2018-03-01"]))
    assert evolucao["quantidade"].tolist() == [2, 2, 0]
    assert evolucao["reclamacoes_no_mes"].tolist() == [2, 3, 2]
    assert evolucao["pct_reclamacoes"].tolist() == [100.0, 66.7, 0.0]
    assert evolucao["poucos_dados"].tolist() == [True, False, True]


def test_evolucao_do_motivo_mantem_mes_sem_reclamacao(tabela):
    # Sem as reclamações de fevereiro, o mês continua na série, sem percentual.
    sem_fevereiro = tabela[~tabela["review_id"].isin(["r2", "r3", "r4"])]
    sem_fevereiro = pd.concat(
        [sem_fevereiro, tabela[tabela["review_id"] == "r7"].assign(data_avaliacao=pd.Timestamp("2018-02-15"))]
    )
    evolucao = evolucao_do_motivo(sem_fevereiro, "atraso").set_index("mes")
    fevereiro = evolucao.loc[pd.Timestamp("2018-02-01")]
    assert fevereiro["quantidade"] == 0 and fevereiro["reclamacoes_no_mes"] == 0
    assert pd.isna(fevereiro["pct_reclamacoes"])
    assert bool(fevereiro["poucos_dados"])


def test_evolucao_do_motivo_respeita_o_filtro(tabela):
    evolucao = evolucao_do_motivo(filtrar(tabela, categorias=["Brinquedos"]), "atraso", minimo=1)
    # Brinquedos: fevereiro tem 1 atraso em 2 reclamações, março tem 0 em 1.
    assert evolucao["quantidade"].tolist() == [1, 0]
    assert evolucao["pct_reclamacoes"].tolist() == [50.0, 0.0]


def test_evolucao_do_motivo_vazia_e_motivo_invalido(tabela):
    assert evolucao_do_motivo(tabela.iloc[0:0], "atraso").empty
    with pytest.raises(ValueError):
        evolucao_do_motivo(tabela, "elogio")


def test_categorias_por_motivo_usa_proporcao(tabela):
    resultado = categorias_por_motivo(tabela, "atraso", minimo=1)
    # Moveis: 3 atrasos em 6 avaliações (50%). Brinquedos: 1 em 4 (25%).
    assert resultado["categoria"].tolist() == ["Moveis", "Brinquedos"]
    assert resultado["pct"].tolist() == [50.0, 25.0]


def test_categorias_pequenas_ficam_fora(tabela):
    assert categorias_por_motivo(tabela, "atraso", minimo=5)["categoria"].tolist() == ["Moveis"]


def test_categorias_por_motivo_recusa_motivo_desconhecido(tabela):
    with pytest.raises(ValueError):
        categorias_por_motivo(tabela, "preco")


def test_exemplos_mais_recentes_primeiro_e_busca_sem_maiusculas(tabela):
    assert exemplos(tabela, "atraso", 2)["texto"].tolist() == ["Demora", "Chegou tarde"]
    assert exemplos(tabela, "defeito_ou_qualidade", busca="quebrado")["texto"].tolist() == [
        "Veio QUEBRADO", "Quebrado"
    ]
