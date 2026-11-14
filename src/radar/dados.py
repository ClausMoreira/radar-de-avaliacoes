"""Leitura e limpeza dos dados da Olist.

Entrada: dois CSVs brutos (avaliações e pedidos).
Saída: uma tabela com uma linha por avaliação escrita, já com o atraso real
da entrega calculado a partir das datas do pedido.
"""

from pathlib import Path

import pandas as pd

from radar.config import ARQUIVO_AVALIACOES, ARQUIVO_PEDIDOS, TAMANHO_MINIMO_TEXTO


def limpar_texto(serie: pd.Series) -> pd.Series:
    """Troca quebras de linha e espaços repetidos por um espaço só."""
    return serie.fillna("").str.replace(r"\s+", " ", regex=True).str.strip()


def carregar_avaliacoes(pasta_raw: Path, tamanho_minimo: int = TAMANHO_MINIMO_TEXTO) -> pd.DataFrame:
    """Carrega as avaliações com comentário e junta os dados do pedido.

    Colunas devolvidas:
        review_id, order_id, nota, texto, data_avaliacao, status_pedido,
        data_entrega, data_estimada, atraso_dias

    atraso_dias > 0 significa que a entrega passou do prazo prometido.
    Fica vazio quando o pedido não tem data de entrega registrada.
    """
    pasta_raw = Path(pasta_raw)
    avaliacoes = pd.read_csv(pasta_raw / ARQUIVO_AVALIACOES)
    pedidos = pd.read_csv(pasta_raw / ARQUIVO_PEDIDOS)
    for coluna in ["order_delivered_customer_date", "order_estimated_delivery_date"]:
        pedidos[coluna] = pd.to_datetime(pedidos[coluna], errors="coerce")

    avaliacoes["texto"] = limpar_texto(avaliacoes["review_comment_message"])
    avaliacoes = avaliacoes[avaliacoes["texto"].str.len() >= tamanho_minimo]

    # A mesma avaliação pode aparecer ligada a mais de um pedido. Mantemos uma.
    avaliacoes = avaliacoes.drop_duplicates(subset="review_id", keep="first")

    tabela = avaliacoes.merge(pedidos, on="order_id", how="left")
    atraso = tabela["order_delivered_customer_date"] - tabela["order_estimated_delivery_date"]
    tabela["atraso_dias"] = (atraso.dt.total_seconds() / 86400).round(1)

    tabela = tabela.rename(
        columns={
            "review_score": "nota",
            "review_creation_date": "data_avaliacao",
            "order_status": "status_pedido",
            "order_delivered_customer_date": "data_entrega",
            "order_estimated_delivery_date": "data_estimada",
        }
    )
    colunas = [
        "review_id", "order_id", "nota", "texto", "data_avaliacao",
        "status_pedido", "data_entrega", "data_estimada", "atraso_dias",
    ]
    return tabela[colunas].reset_index(drop=True)


def sortear_amostra(tabela: pd.DataFrame, por_nota: int, semente: int) -> pd.DataFrame:
    """Sorteia a mesma quantidade de avaliações para cada nota e embaralha."""
    partes = []
    for nota, grupo in tabela.groupby("nota"):
        if len(grupo) < por_nota:
            raise ValueError(f"A nota {nota} só tem {len(grupo)} avaliações; pedidas {por_nota}.")
        partes.append(grupo.sample(n=por_nota, random_state=semente))
    amostra = pd.concat(partes).sample(frac=1, random_state=semente)
    return amostra.reset_index(drop=True)
