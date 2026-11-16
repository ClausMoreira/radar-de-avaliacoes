"""Todos os números do painel e do agente.

O painel e o agente chamam as mesmas funções. Assim os dois mostram sempre o
mesmo valor, e o agente nunca calcula nada sozinho: ele consulta estas funções
e só redige a resposta.

Entrada de todas as funções: a tabela de data/processado/avaliacoes_classificadas.csv
(uma linha por avaliação, com as colunas motivo, nota, categoria, data_avaliacao
e atraso_dias). Nenhuma função altera a tabela recebida.
"""

import pandas as pd

from radar.config import CATEGORIAS, NOMES_EXIBICAO

# Motivos que indicam algo a resolver. "elogio" não é problema, e "outro"
# não diz o que resolver, por isso ficam fora do ranking de prioridades.
MOTIVOS_DE_RECLAMACAO = [m for m in CATEGORIAS if m not in ("elogio", "outro")]


def carregar(caminho) -> pd.DataFrame:
    """Lê o CSV processado com os tipos certos."""
    tabela = pd.read_csv(caminho, parse_dates=["data_avaliacao"])
    tabela["nota"] = tabela["nota"].astype(int)
    return tabela


def filtrar(
    tabela: pd.DataFrame,
    categorias: list[str] | None = None,
    inicio=None,
    fim=None,
) -> pd.DataFrame:
    """Filtra por categoria e por período (datas inclusivas). None não filtra."""
    filtro = pd.Series(True, index=tabela.index)
    if categorias:
        filtro &= tabela["categoria"].isin(categorias)
    if inicio is not None:
        filtro &= tabela["data_avaliacao"] >= pd.Timestamp(inicio)
    if fim is not None:
        filtro &= tabela["data_avaliacao"] < pd.Timestamp(fim) + pd.Timedelta(days=1)
    return tabela[filtro]


def _reclamacoes(tabela: pd.DataFrame) -> pd.DataFrame:
    return tabela[tabela["motivo"].isin(MOTIVOS_DE_RECLAMACAO)]


def _percentual(parte: int, total: int) -> float:
    return round(100 * parte / total, 1) if total else 0.0


def resumo_geral(tabela: pd.DataFrame) -> dict:
    """Totais do período e dos filtros escolhidos."""
    total = len(tabela)
    reclamacoes = len(_reclamacoes(tabela))
    return {
        "avaliacoes": total,
        "reclamacoes": reclamacoes,
        "pct_reclamacoes": _percentual(reclamacoes, total),
        "nota_media": round(float(tabela["nota"].mean()), 2) if total else None,
        "inicio": tabela["data_avaliacao"].min() if total else None,
        "fim": tabela["data_avaliacao"].max() if total else None,
    }


def ranking_motivos(tabela: pd.DataFrame) -> pd.DataFrame:
    """Motivos de reclamação, do mais frequente para o menos frequente.

    Colunas:
        motivo, nome, quantidade,
        pct_reclamacoes   parte das reclamações que tem este motivo,
        nota_media        nota média dessas avaliações,
        pct_atrasados     parte dos pedidos com entrega registrada que chegou
                          depois do prazo prometido (dado real do pedido, não
                          da IA). Vazio quando nenhum pedido tem data de entrega.

    Motivos sem nenhuma avaliação não aparecem. Empates são ordenados pela
    ordem da taxonomia, para o ranking não mudar entre execuções.
    """
    reclamacoes = _reclamacoes(tabela)
    total = len(reclamacoes)
    linhas = []
    for ordem, motivo in enumerate(MOTIVOS_DE_RECLAMACAO):
        grupo = reclamacoes[reclamacoes["motivo"] == motivo]
        if grupo.empty:
            continue
        entregues = grupo["atraso_dias"].dropna()
        linhas.append(
            {
                "motivo": motivo,
                "nome": NOMES_EXIBICAO[motivo],
                "quantidade": len(grupo),
                "pct_reclamacoes": _percentual(len(grupo), total),
                "nota_media": round(float(grupo["nota"].mean()), 2),
                "pct_atrasados": _percentual(int((entregues > 0).sum()), len(entregues)) if len(entregues) else None,
                "_ordem": ordem,
            }
        )
    colunas = ["motivo", "nome", "quantidade", "pct_reclamacoes", "nota_media", "pct_atrasados"]
    if not linhas:
        return pd.DataFrame(columns=colunas)
    ranking = pd.DataFrame(linhas).sort_values(["quantidade", "_ordem"], ascending=[False, True])
    return ranking[colunas].reset_index(drop=True)


def prioridades(tabela: pd.DataFrame, quantas: int = 3) -> pd.DataFrame:
    """As primeiras linhas do ranking: o que resolver primeiro."""
    return ranking_motivos(tabela).head(quantas).reset_index(drop=True)


def atraso_real_por_motivo(tabela: pd.DataFrame) -> pd.DataFrame:
    """Para cada motivo (inclusive elogio), quanto os pedidos realmente atrasaram.

    Serve para conferir a IA com um dado que ela não viu: se a classificação
    faz sentido, quem reclama de atraso deve ter tido mais entregas atrasadas
    do que quem elogia.
    """
    entregues = tabela.dropna(subset=["atraso_dias"])
    linhas = []
    for motivo in CATEGORIAS:
        grupo = entregues[entregues["motivo"] == motivo]
        if grupo.empty:
            continue
        linhas.append(
            {
                "motivo": motivo,
                "nome": NOMES_EXIBICAO[motivo],
                "pedidos_entregues": len(grupo),
                "pct_atrasados": _percentual(int((grupo["atraso_dias"] > 0).sum()), len(grupo)),
                "atraso_mediano_dias": round(float(grupo["atraso_dias"].median()), 1),
            }
        )
    return pd.DataFrame(linhas)


def evolucao_mensal(tabela: pd.DataFrame) -> pd.DataFrame:
    """Reclamações por mês e motivo. Colunas: mes, motivo, nome, quantidade."""
    reclamacoes = _reclamacoes(tabela)
    if reclamacoes.empty:
        return pd.DataFrame(columns=["mes", "motivo", "nome", "quantidade"])
    mes = reclamacoes["data_avaliacao"].dt.to_period("M").dt.to_timestamp()
    contagem = reclamacoes.groupby([mes, "motivo"]).size().reset_index(name="quantidade")
    contagem.columns = ["mes", "motivo", "quantidade"]
    contagem["nome"] = contagem["motivo"].map(NOMES_EXIBICAO)
    return contagem[["mes", "motivo", "nome", "quantidade"]]


# Abaixo disso, poucos casos mudam muito o percentual do mês. O painel mostra
# o mês mesmo assim, mas sinalizado, para ninguém ler ruído como tendência.
MINIMO_DE_RECLAMACOES_NO_MES = 30


def evolucao_do_motivo(
    tabela: pd.DataFrame, motivo: str, minimo: int = MINIMO_DE_RECLAMACOES_NO_MES
) -> pd.DataFrame:
    """Um motivo de reclamação, mês a mês, pelas datas reais das avaliações.

    Uma linha por mês, do primeiro ao último mês da tabela recebida, inclusive
    os meses em que o motivo não apareceu. Colunas:
        mes                 primeiro dia do mês,
        quantidade          reclamações com este motivo no mês,
        reclamacoes_no_mes  reclamações de todos os motivos no mês,
        pct_reclamacoes     parte das reclamações do mês que tem este motivo
                            (vazio quando o mês não tem nenhuma reclamação),
        poucos_dados        True quando o mês tem menos de `minimo` reclamações.

    Mostramos a parte das reclamações, e não só a quantidade, porque a
    quantidade também sobe quando o mês simplesmente tem mais avaliações.
    Não há previsão: a função só conta o que já aconteceu.
    """
    if motivo not in MOTIVOS_DE_RECLAMACAO:
        raise ValueError(f"Motivo de reclamação desconhecido: {motivo}")
    colunas = ["mes", "quantidade", "reclamacoes_no_mes", "pct_reclamacoes", "poucos_dados"]
    if tabela.empty:
        return pd.DataFrame(columns=colunas)
    meses = pd.period_range(tabela["data_avaliacao"].min(), tabela["data_avaliacao"].max(), freq="M")
    reclamacoes = _reclamacoes(tabela)
    mes = reclamacoes["data_avaliacao"].dt.to_period("M")
    no_mes = mes.value_counts().reindex(meses, fill_value=0)
    do_motivo = mes[reclamacoes["motivo"] == motivo].value_counts().reindex(meses, fill_value=0)
    return pd.DataFrame(
        {
            "mes": meses.to_timestamp(),
            "quantidade": do_motivo.to_numpy(dtype=int),
            "reclamacoes_no_mes": no_mes.to_numpy(dtype=int),
            "pct_reclamacoes": [
                _percentual(int(q), int(total)) if total else None for q, total in zip(do_motivo, no_mes)
            ],
            "poucos_dados": (no_mes < minimo).to_numpy(dtype=bool),
        },
        columns=colunas,
    )


def categorias_por_motivo(tabela: pd.DataFrame, motivo: str, minimo: int = 20, quantas: int = 5) -> pd.DataFrame:
    """Categorias onde um motivo pesa mais, em proporção às avaliações da categoria.

    Usamos proporção, e não quantidade, porque categorias grandes teriam mais
    reclamações só por venderem mais. Categorias com menos de `minimo`
    avaliações ficam fora, porque nelas um único caso muda muito o percentual.
    Colunas: categoria, avaliacoes, com_motivo, pct.
    """
    if motivo not in CATEGORIAS:
        raise ValueError(f"Motivo desconhecido: {motivo}")
    por_categoria = tabela.groupby("categoria").agg(
        avaliacoes=("motivo", "size"),
        com_motivo=("motivo", lambda serie: int((serie == motivo).sum())),
    )
    por_categoria = por_categoria[por_categoria["avaliacoes"] >= minimo].copy()
    por_categoria["pct"] = (100 * por_categoria["com_motivo"] / por_categoria["avaliacoes"]).round(1)
    por_categoria = por_categoria[por_categoria["com_motivo"] > 0]
    return (
        por_categoria.reset_index()
        .sort_values(["pct", "com_motivo", "categoria"], ascending=[False, False, True])
        .head(quantas)
        .reset_index(drop=True)
    )


def exemplos(tabela: pd.DataFrame, motivo: str, quantos: int = 5, busca: str = "") -> pd.DataFrame:
    """Avaliações reais de um motivo, das mais recentes para as mais antigas.

    `busca` filtra por um trecho do texto, sem diferenciar maiúsculas.
    Colunas: data_avaliacao, nota, categoria, texto.
    """
    grupo = tabela[tabela["motivo"] == motivo]
    if busca.strip():
        grupo = grupo[grupo["texto"].str.contains(busca.strip(), case=False, regex=False)]
    grupo = grupo.sort_values(["data_avaliacao", "review_id"], ascending=[False, True])
    return grupo[["data_avaliacao", "nota", "categoria", "texto"]].head(quantos).reset_index(drop=True)
