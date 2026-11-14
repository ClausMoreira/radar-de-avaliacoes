"""Primeira tela: as três prioridades aparecem sem nenhum clique."""

import streamlit as st

import comum as c
from radar.metricas import atraso_real_por_motivo, exemplos, prioridades, ranking_motivos, resumo_geral

tabela = c.filtros_na_barra_lateral()
resumo = resumo_geral(tabela)

st.title("O que consertar primeiro")

if resumo["avaliacoes"] == 0:
    st.info("Nenhuma avaliação com esses filtros. Amplie o período ou escolha outra categoria.")
    st.stop()

st.markdown(
    f"Em **{c.numero(resumo['avaliacoes'])} avaliações** de {c.mes_ano(resumo['inicio'])} "
    f"a {c.mes_ano(resumo['fim'])}, **{c.numero(resumo['reclamacoes'])}** "
    f"({c.pct(resumo['pct_reclamacoes'])}) trazem uma reclamação com motivo identificado. "
    "Estas são as três mais frequentes:"
)

top = prioridades(tabela, 3)
colunas = st.columns(3)
for posicao, (coluna, linha) in enumerate(zip(colunas, top.itertuples()), start=1):
    linhas = [
        f"{c.numero(linha.quantidade)} avaliações · nota média {c.decimal(linha.nota_media)}",
    ]
    if linha.pct_atrasados is not None and linha.pct_atrasados == linha.pct_atrasados:
        linhas.append(f"dos pedidos que foram entregues, {c.pct(linha.pct_atrasados)} chegaram depois do prazo")
    exemplo = exemplos(tabela, linha.motivo, 1)
    if not exemplo.empty:
        texto = exemplo.loc[0, "texto"]
        texto = texto if len(texto) <= 110 else texto[:107].rstrip() + "..."
        linhas.append(f"<i>“{texto}”</i>")
    with coluna:
        c.cartao(
            f"{posicao}º · {linha.nome}",
            f"{c.pct(linha.pct_reclamacoes)}",
            ["das reclamações"] + linhas,
            c.COR_DO_MOTIVO[linha.motivo],
        )

st.write("")
st.caption("Ranking pela quantidade de avaliações com cada motivo. Elogios e textos vagos ficam fora.")

st.subheader("Todos os motivos de reclamação")
ranking = ranking_motivos(tabela)
ranking["rotulo"] = [
    f"{c.numero(q)} ({c.pct(p)})" for q, p in zip(ranking["quantidade"], ranking["pct_reclamacoes"])
]
ranking["cor"] = ranking["motivo"].map(c.COR_DO_MOTIVO)
ranking["nota"] = ranking["nota_media"].map(c.decimal)
st.altair_chart(
    c.barras_horizontais(
        ranking, "quantidade", "rotulo", "Avaliações",
        dica=[
            {"field": "nome", "title": "Motivo"},
            {"field": "quantidade", "title": "Avaliações"},
            {"field": "rotulo", "title": "Quantidade (parte das reclamações)"},
            {"field": "nota", "title": "Nota média"},
        ],
        cores_por_linha="cor",
    ),
    width="stretch",
)

st.subheader("A classificação bate com as datas de entrega?")
atraso = atraso_real_por_motivo(tabela)
if not atraso.empty:
    atraso = atraso.sort_values("pct_atrasados", ascending=False).reset_index(drop=True)
    atraso["rotulo"] = atraso["pct_atrasados"].map(c.pct)
    atraso["pedidos"] = atraso["pedidos_entregues"].map(c.numero)
    indice = atraso.set_index("motivo")
    if {"atraso", "elogio"} <= set(indice.index):
        st.markdown(
            f"A IA leu só o texto das avaliações. As datas de entrega vêm do pedido. Entre as "
            f"avaliações classificadas como **{c.nome('atraso').lower()}**, "
            f"**{c.pct(indice.loc['atraso', 'pct_atrasados'])}** dos pedidos chegaram depois do prazo "
            f"prometido. Entre os **elogios**, foram **{c.pct(indice.loc['elogio', 'pct_atrasados'])}**."
        )
    st.altair_chart(
        c.barras_horizontais(
            atraso, "pct_atrasados", "rotulo", "Pedidos entregues depois do prazo",
            dica=[
                {"field": "nome", "title": "Motivo"},
                {"field": "rotulo", "title": "Entregues depois do prazo"},
                {"field": "pedidos", "title": "Pedidos com data de entrega"},
            ],
            cor=c.COR_NEUTRA,
        ),
        width="stretch",
    )
    st.caption("Considera só pedidos com data de entrega registrada. Pedidos não entregues ficam de fora.")
