"""Exemplos reais de cada motivo, para o lojista ler o que os clientes escrevem."""

import html

import streamlit as st

import comum as c
from radar.metricas import MOTIVOS_DE_RECLAMACAO, exemplos, ranking_motivos

tabela = c.filtros_na_barra_lateral()
st.title("O que os clientes escrevem")

ranking = ranking_motivos(tabela)
if ranking.empty:
    st.info("Nenhuma reclamação com esses filtros.")
    st.stop()

quantidades = dict(zip(ranking["motivo"], ranking["quantidade"]))
opcoes = [m for m in ranking["motivo"]] + [m for m in ("elogio", "outro") if (tabela["motivo"] == m).any()]
contagem = tabela["motivo"].value_counts()

motivo = st.pills(
    "Motivo",
    opcoes,
    default=opcoes[0],
    format_func=lambda m: f"{c.nome(m)} ({c.numero(contagem.get(m, 0))})",
    key="motivo_escolhido",
)
motivo = motivo or opcoes[0]
busca = st.text_input("Buscar no texto", placeholder="Por exemplo: troca, quebrado, correios")

lista = exemplos(tabela, motivo, quantos=30, busca=busca)
total = int((tabela["motivo"] == motivo).sum())
if busca.strip():
    st.caption(f"{c.numero(len(lista))} avaliações com “{busca.strip()}” (mostrando até 30).")
else:
    st.caption(f"As {c.numero(len(lista))} mais recentes de {c.numero(total)} avaliações com este motivo.")

if lista.empty:
    st.info("Nenhuma avaliação encontrada.")
for item in lista.itertuples():
    st.markdown(
        f"""
        <div style="border:1px solid #e4e2dc;border-left:4px solid {c.COR_DO_MOTIVO[motivo]};
                    border-radius:8px;padding:10px 14px;margin-bottom:8px;background:#ffffff">
          <div style="font-size:0.8rem;color:{c.TEXTO_SECUNDARIO}">
            <span aria-label="{item.nota} de 5 estrelas">{c.estrelas(item.nota)}</span>
            &nbsp;·&nbsp;{c.data_curta(item.data_avaliacao)}&nbsp;·&nbsp;{html.escape(item.categoria)}
          </div>
          <div style="margin-top:4px">{html.escape(item.texto)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if motivo in MOTIVOS_DE_RECLAMACAO:
    st.caption("O motivo de cada avaliação foi atribuído por IA e pode ter erros. Veja a taxa de acerto em “Como sabemos que funciona”.")
