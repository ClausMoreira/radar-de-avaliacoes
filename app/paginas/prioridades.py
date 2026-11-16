"""Primeira tela: as três prioridades aparecem sem nenhum clique."""

import streamlit as st

import comum as c
from radar.metricas import (
    MINIMO_DE_RECLAMACOES_NO_MES, atraso_real_por_motivo, evolucao_do_motivo, exemplos, prioridades,
    ranking_motivos, resumo_geral,
)

tabela = c.filtros_na_barra_lateral()
resumo = resumo_geral(tabela)

# Identificação do app antes do título. Uma pessoa de fora da área apontou
# que a primeira tela não dizia o que é o app nem qual é o objetivo dele.
st.markdown(
    "**Radar de Avaliações** lê o que os clientes escrevem sobre uma loja de marketplace "
    "e mostra quais reclamações resolver primeiro."
)
st.title("O que resolver primeiro")

# Contexto antes dos números. As três pessoas que testaram o app pediram uma
# apresentação dos dados. Fica em um bloco curto, e não em uma página
# separada, para as prioridades continuarem aparecendo sem nenhum clique.
base_inteira = c.dados()
c.bloco_de_contexto(
    [
        (
            "De onde vêm os dados:",
            "avaliações públicas e anonimizadas da Olist, um marketplace brasileiro, escritas por clientes "
            f"entre {c.mes_ano(base_inteira['data_avaliacao'].min())} e "
            f"{c.mes_ano(base_inteira['data_avaliacao'].max())}.",
        ),
        (
            "O que conta como reclamação:",
            "a avaliação em que a IA identificou um motivo concreto, como produto não recebido ou com defeito. "
            "Elogios e textos vagos ficam fora.",
        ),
        (
            "Como ler os cartões:",
            "o número grande é a parte das reclamações com aquele motivo. Abaixo vêm a quantidade, "
            "a nota média e uma avaliação real.",
        ),
    ]
)

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

# Atalho para o agente. No celular o menu lateral começa fechado, então sem
# este botão o visitante pode sair sem saber que dá para perguntar.
convite, botao = st.columns([3, 1], vertical_alignment="center")
convite.markdown(
    "**Quer ir além do ranking?** Pergunte em português, por exemplo: "
    "“em quais categorias o principal problema pesa mais?”"
)
if botao.button("Pergunte ao Radar", icon=":material/forum:", type="primary", width="stretch"):
    st.switch_page("paginas/pergunte.py")

# Evolução no tempo, pedida por quem testou o app. Usa só as datas reais das
# avaliações, por mês. Não há previsão nem dado simulado.
# Sem nenhuma reclamação nos filtros, não há prioridade para acompanhar.
if not top.empty:
    st.subheader("Como cada prioridade evoluiu mês a mês")
    nomes_das_prioridades = dict(zip(top["motivo"], top["nome"]))
    escolhido = st.segmented_control(
        "Prioridade",
        list(nomes_das_prioridades),
        format_func=nomes_das_prioridades.get,
        default=top.loc[0, "motivo"],
        key="evolucao_motivo",
        label_visibility="collapsed",
    )
    if escolhido not in nomes_das_prioridades:
        # Nenhuma opção marcada, ou um filtro novo tirou o motivo das três prioridades.
        escolhido = top.loc[0, "motivo"]
    evolucao = evolucao_do_motivo(tabela, escolhido)
    com_volume = evolucao[~evolucao["poucos_dados"]]
    if com_volume.empty:
        st.markdown(
            f"Com esses filtros, nenhum mês chega a {MINIMO_DE_RECLAMACOES_NO_MES} reclamações. "
            "Os pontos abaixo mostram o que aconteceu, mas são poucos casos para falar em tendência."
        )
    else:
        maior = com_volume.loc[com_volume["pct_reclamacoes"].idxmax()]
        menor = com_volume.loc[com_volume["pct_reclamacoes"].idxmin()]
        st.markdown(
            f"Nos meses com pelo menos {MINIMO_DE_RECLAMACOES_NO_MES} reclamações, "
            f"**{nomes_das_prioridades[escolhido].lower()}** ficou entre **{c.pct(menor['pct_reclamacoes'])}** "
            f"({c.mes_ano(menor['mes'])}) e **{c.pct(maior['pct_reclamacoes'])}** ({c.mes_ano(maior['mes'])}) "
            "das reclamações do mês."
        )
    grafico_da_parte, grafico_da_quantidade = c.evolucao_mensal(
        evolucao, c.COR_DO_MOTIVO[escolhido], MINIMO_DE_RECLAMACOES_NO_MES
    )
    st.markdown("**Parte das reclamações de cada mês que tem este motivo**")
    st.altair_chart(grafico_da_parte, width="stretch")
    st.markdown("**Quantidade de reclamações com este motivo**")
    st.altair_chart(grafico_da_quantidade, width="stretch")
    st.caption(
        f"Meses em cinza têm menos de {MINIMO_DE_RECLAMACOES_NO_MES} reclamações no total: neles, poucos casos "
        "mudam muito o percentual, por isso ficam fora da linha. A quantidade também sobe quando o mês tem mais "
        "avaliações, então a tendência se lê pelo primeiro gráfico. Usamos as datas reais das avaliações, "
        "sem previsão."
    )

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
