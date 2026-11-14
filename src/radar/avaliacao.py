"""Compara a classificação do modelo com o gabarito rotulado à mão.

Todas as funções recebem duas colunas alinhadas: o motivo do gabarito e o
motivo previsto pelo modelo. Nenhuma delas chama a IA.
"""

import math

import pandas as pd

from radar.config import CATEGORIAS


def acerto_geral(gabarito: pd.Series, previsto: pd.Series) -> dict:
    """Quantas avaliações o modelo classificou igual ao gabarito."""
    total = len(gabarito)
    acertos = int((gabarito.values == previsto.values).sum())
    return {
        "total": total,
        "acertos": acertos,
        "acerto": round(acertos / total, 4) if total else 0.0,
    }


def acerto_por_motivo(gabarito: pd.Series, previsto: pd.Series) -> pd.DataFrame:
    """Para cada motivo do gabarito, quantas o modelo acertou.

    Motivos com poucas avaliações têm um percentual instável. Por isso a
    tabela mostra sempre a quantidade ao lado do percentual.
    """
    tabela = pd.DataFrame({"gabarito": gabarito.values, "previsto": previsto.values})
    tabela["acertou"] = tabela["gabarito"] == tabela["previsto"]
    resumo = (
        tabela.groupby("gabarito")["acertou"]
        .agg(total="size", acertos="sum")
        .reindex(list(CATEGORIAS))
        .dropna()
        .astype(int)
    )
    resumo["acerto"] = (resumo["acertos"] / resumo["total"]).round(4)
    return resumo.rename_axis("motivo").reset_index()


def confusoes(gabarito: pd.Series, previsto: pd.Series) -> pd.DataFrame:
    """Os erros agrupados por par (gabarito, previsto), do mais ao menos comum.

    É a tabela que orienta a próxima versão do prompt: mostra quais motivos
    o modelo troca entre si.
    """
    tabela = pd.DataFrame({"gabarito": gabarito.values, "previsto": previsto.values})
    erros = tabela[tabela["gabarito"] != tabela["previsto"]]
    return (
        erros.groupby(["gabarito", "previsto"])
        .size()
        .reset_index(name="quantidade")
        .sort_values(["quantidade", "gabarito", "previsto"], ascending=[False, True, True])
        .reset_index(drop=True)
    )


def intervalo_de_confianca(acertos: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalo de Wilson com 95% de confiança para uma taxa de acerto.

    Em amostras pequenas, o acerto observado varia bastante de uma amostra
    para outra. O intervalo mostra essa incerteza: com 60 avaliações, um
    acerto de 90% é compatível com valores reais de cerca de 80% a 95%.
    """
    if total == 0:
        return (0.0, 0.0)
    p = acertos / total
    denominador = 1 + z**2 / total
    centro = (p + z**2 / (2 * total)) / denominador
    margem = z * math.sqrt(p * (1 - p) / total + z**2 / (4 * total**2)) / denominador
    return (round(max(0.0, centro - margem), 4), round(min(1.0, centro + margem), 4))
