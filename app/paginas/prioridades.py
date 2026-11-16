"""Primeira tela: as três prioridades aparecem sem nenhum clique."""

import streamlit as st

import comum as c
from radar.metricas import (
    MINIMO_DE_RECLAMACOES_NO_MES, atraso_real_por_motivo, evolucao_do_motivo, exemplos, prioridades,
    ranking_motivos, resumo_geral,
)

tabela = c.filtros_na_barra_lateral()
resumo = resumo_geral(tabela)

# Topo da página. O nome do app é o título, e a frase abaixo diz em linguagem
# simples o que ele faz. Quatro pessoas que abriram o app pediram isso de
# formas diferentes: as duas primeiras sentiram falta de uma apresentação, e a
# quarta, pelo celular, pediu um título que se explicasse sozinho.
base_inteira = c.dados()
st.title("Radar de Avaliações")
st.markdown(
    "<div style='font-size:1.15rem;color:#0b0b0b;margin:-10px 0 8px'>Descubra, pelo que os clientes escrevem, "
    "<b>qual problema da loja priorizar</b>.</div>",
    unsafe_allow_html=True,
)

# Contexto sempre visível, em três linhas curtas. Três pessoas pediram contexto
# antes dos números, e a quarta achou a tela com texto demais. Por isso o bloco
# ficou com cerca de metade do texto, sem esconder o que é preciso para ler os
# números: de onde vêm os dados, quem aponta o motivo e o que o percentual mede.
c.bloco_de_contexto(
    [
        (
            "Dados:",
            f"{c.numero(len(base_inteira))} avaliações reais e públicas de um marketplace brasileiro (Olist), "
            f"de {base_inteira['data_avaliacao'].min().year} a {base_inteira['data_avaliacao'].max().year}.",
        ),
        (
            "Motivo:",
            "apontado por IA a partir do texto de cada avaliação. O acerto medido está na página "
            "“Como sabemos que funciona”.",
        ),
        (
            "Percentual:",
            "parte das reclamações com aquele motivo. Elogios e textos vagos não contam.",
        ),
    ]
)

st.subheader("As 3 dores mais citadas pelos clientes")

if resumo["avaliacoes"] == 0:
    st.info("Nenhuma avaliação com esses filtros. Amplie o período ou escolha outra categoria.")
    st.stop()

st.markdown(
    f"Das **{c.numero(resumo['avaliacoes'])} avaliações** de {c.mes_ano(resumo['inicio'])} "
    f"a {c.mes_ano(resumo['fim'])}, **{c.numero(resumo['reclamacoes'])}** "
    f"({c.pct(resumo['pct_reclamacoes'])}) são reclamações. Os três motivos mais citados:"
)

top = prioridades(tabela, 3)
colunas = st.columns(3)
for posicao, (coluna, linha) in enumerate(zip(colunas, top.itertuples()), start=1):
    # O cartão fica com o essencial. A comparação com as datas de entrega
    # saiu daqui e continua na última seção da página.
    linhas = [
        f"{c.numero(linha.quantidade)} avaliações · nota média {c.decimal(linha.nota_media)} de 5",
    ]
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

# Atalho para o agente. No celular o menu lateral começa fechado, então sem
# este botão o visitante pode sair sem saber que dá para perguntar.
convite, botao, teste = st.columns([2, 1, 1], vertical_alignment="center")
convite.markdown(
    "**Quer ir além do ranking?** Pergunte em português, por exemplo: "
    "“em quais categorias o principal problema pesa mais?”, ou teste uma avaliação sua."
)
if botao.button("Pergunte ao Radar", icon=":material/forum:", type="primary", width="stretch"):
    st.switch_page("paginas/pergunte.py")
if teste.button("Testar uma avaliação", icon=":material/rate_review:", width="stretch"):
    st.switch_page("paginas/testar.py")

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
        f"Meses em cinza têm poucas reclamações (menos de {MINIMO_DE_RECLAMACOES_NO_MES}) e ficam fora da linha."
    )
    with st.expander("Como ler estes gráficos"):
        st.markdown(
            "- Nos meses em cinza, poucos casos mudam muito o percentual. Por isso eles não entram na linha.\n"
            "- A quantidade também sobe quando o mês tem mais avaliações. A tendência se lê pelo primeiro gráfico.\n"
            "- Usamos as datas reais das avaliações. Não há previsão."
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
