import pandas as pd
import pytest

from radar.dados import carregar_avaliacoes, sortear_amostra


@pytest.fixture
def pasta_raw(tmp_path):
    avaliacoes = pd.DataFrame(
        {
            "review_id": ["r1", "r1", "r2", "r3", "r4"],
            "order_id": ["o1", "o9", "o2", "o3", "o4"],
            "review_score": [1, 1, 5, 3, 4],
            "review_comment_title": [None] * 5,
            "review_comment_message": [
                "Produto não chegou\r\naté hoje, péssimo",
                "Produto não chegou\r\naté hoje, péssimo",
                "Chegou antes do prazo, recomendo muito",
                "ok",
                None,
            ],
            "review_creation_date": ["2018-01-10"] * 5,
            "review_answer_timestamp": ["2018-01-11"] * 5,
        }
    )
    pedidos = pd.DataFrame(
        {
            "order_id": ["o1", "o2", "o3", "o4", "o9"],
            "customer_id": ["c"] * 5,
            "order_status": ["shipped", "delivered", "delivered", "delivered", "shipped"],
            "order_purchase_timestamp": ["2018-01-01"] * 5,
            "order_approved_at": ["2018-01-01"] * 5,
            "order_delivered_carrier_date": ["2018-01-02"] * 5,
            "order_delivered_customer_date": [None, "2018-01-05 12:00:00", "2018-01-12 00:00:00", "2018-01-05 00:00:00", None],
            "order_estimated_delivery_date": ["2018-01-08 00:00:00"] * 5,
        }
    )
    avaliacoes.to_csv(tmp_path / "olist_order_reviews_dataset.csv", index=False)
    pedidos.to_csv(tmp_path / "olist_orders_dataset.csv", index=False)
    return tmp_path


def test_remove_textos_curtos_vazios_e_duplicados(pasta_raw):
    tabela = carregar_avaliacoes(pasta_raw, tamanho_minimo=20)
    assert sorted(tabela["review_id"]) == ["r1", "r2"]


def test_limpa_quebras_de_linha(pasta_raw):
    tabela = carregar_avaliacoes(pasta_raw, tamanho_minimo=20)
    texto = tabela.loc[tabela["review_id"] == "r1", "texto"].iloc[0]
    assert texto == "Produto não chegou até hoje, péssimo"


def test_atraso_em_dias(pasta_raw):
    tabela = carregar_avaliacoes(pasta_raw, tamanho_minimo=20).set_index("review_id")
    assert tabela.loc["r2", "atraso_dias"] == -2.5  # entregue 2,5 dias antes do prazo
    assert pd.isna(tabela.loc["r1", "atraso_dias"])  # pedido sem data de entrega


def test_amostra_tem_mesma_quantidade_por_nota():
    tabela = pd.DataFrame({"review_id": range(40), "nota": [1, 2, 3, 4] * 10})
    amostra = sortear_amostra(tabela, por_nota=5, semente=1)
    assert amostra["nota"].value_counts().tolist() == [5, 5, 5, 5]
    assert amostra["review_id"].is_unique


def test_amostra_e_reproduzivel():
    tabela = pd.DataFrame({"review_id": range(40), "nota": [1, 2, 3, 4] * 10})
    a = sortear_amostra(tabela, por_nota=5, semente=1)
    b = sortear_amostra(tabela, por_nota=5, semente=1)
    assert a["review_id"].tolist() == b["review_id"].tolist()


def test_amostra_falha_se_faltam_avaliacoes():
    tabela = pd.DataFrame({"review_id": range(3), "nota": [1, 1, 2]})
    with pytest.raises(ValueError):
        sortear_amostra(tabela, por_nota=2, semente=1)


# --- Categoria do produto e separação entre painel e avaliações novas ---

from radar.dados import adicionar_categoria, nome_legivel, separar_painel_e_novas


@pytest.fixture
def pasta_com_itens(pasta_raw):
    pd.DataFrame(
        {
            "order_id": ["o1", "o1", "o2"],
            "product_id": ["p_barato", "p_caro", "p_sem_categoria"],
            "price": [10.0, 99.0, 50.0],
        }
    ).to_csv(pasta_raw / "olist_order_items_dataset.csv", index=False)
    pd.DataFrame(
        {
            "product_id": ["p_barato", "p_caro", "p_sem_categoria"],
            "product_category_name": ["brinquedos", "cama_mesa_banho", None],
        }
    ).to_csv(pasta_raw / "olist_products_dataset.csv", index=False)
    return pasta_raw


def test_nome_legivel():
    assert nome_legivel("cama_mesa_banho") == "Cama mesa banho"
    assert nome_legivel(None) == "Sem categoria"


def test_categoria_e_a_do_item_mais_caro(pasta_com_itens):
    tabela = carregar_avaliacoes(pasta_com_itens, tamanho_minimo=20)
    tabela = adicionar_categoria(tabela, pasta_com_itens).set_index("review_id")
    assert tabela.loc["r1", "categoria"] == "Cama mesa banho"   # o1: item de 99 ganha do de 10
    assert tabela.loc["r2", "categoria"] == "Sem categoria"     # o2: produto sem categoria
    assert len(tabela) == 2                                     # a junção não duplica linhas


def tabela_com_datas():
    datas = ["2018-06-01", "2018-07-15", "2018-07-31", "2018-08-01", "2018-08-20", "2018-07-01"]
    return pd.DataFrame(
        {
            "review_id": [f"r{n}" for n in range(6)],
            "order_id": "o", "nota": 5, "texto": "t", "categoria": "c",
            "status_pedido": "delivered", "atraso_dias": 0.0,
            "data_avaliacao": datas,
        }
    )


def test_painel_e_novas_separados_pela_data_de_corte():
    painel, novas = separar_painel_e_novas(tabela_com_datas(), set(), "2018-08-01", 10, 10, 1)
    assert sorted(painel["review_id"]) == ["r0", "r1", "r2", "r5"]
    assert sorted(novas["review_id"]) == ["r3", "r4"]


def test_gabarito_fica_fora_das_duas_partes():
    painel, novas = separar_painel_e_novas(tabela_com_datas(), {"r1", "r4"}, "2018-08-01", 10, 10, 1)
    assert "r1" not in set(painel["review_id"]) and "r4" not in set(novas["review_id"])


def test_tamanho_da_amostra_e_reprodutivel():
    a, _ = separar_painel_e_novas(tabela_com_datas(), set(), "2018-08-01", 2, 1, 7)
    b, _ = separar_painel_e_novas(tabela_com_datas(), set(), "2018-08-01", 2, 1, 7)
    assert len(a) == 2 and a["review_id"].tolist() == b["review_id"].tolist()
