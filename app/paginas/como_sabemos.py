"""Como medimos a classificação e o que ela ainda erra."""

import html

import pandas as pd
import streamlit as st

import comum as c
from radar.avaliacao import acerto_geral, acerto_por_motivo, intervalo_de_confianca
from radar.config import MODELO_CLASSIFICACAO, VERSAO_PROMPT_PRODUCAO

st.title("Como sabemos que funciona")

st.markdown(
    "Antes de confiar na IA, rotulamos à mão **150 avaliações** (30 de cada nota, de 1 a 5) "
    "seguindo uma [taxonomia escrita](https://github.com/ClausMoreira/radar-de-avaliacoes/blob/main/docs/taxonomia.md). "
    "Depois comparamos a resposta do modelo com esse gabarito. A nota em estrelas não é mostrada "
    "nem a quem rotula nem ao modelo: os dois leem só o texto."
)

medicoes = {
    "v1, gabarito original": c.medicao("v1_gabarito_original"),
    "v1, gabarito revisado": c.medicao("v1"),
    "v2, gabarito revisado": c.medicao("v2"),
}
linhas = []
for nome, tabela in medicoes.items():
    if tabela is None:
        continue
    geral = acerto_geral(tabela["motivo"], tabela["previsto"])
    sem_duvida = tabela[tabela["duvida"].str.lower() != "true"]
    geral_sd = acerto_geral(sem_duvida["motivo"], sem_duvida["previsto"])
    linhas.append(
        {
            "Medição": nome,
            "Acerto": f"{geral['acertos']} de {geral['total']} ({c.pct(100 * geral['acerto'])})",
            "Sem as linhas de dúvida": f"{geral_sd['acertos']} de {geral_sd['total']} ({c.pct(100 * geral_sd['acerto'])})",
        }
    )

v2 = medicoes["v2, gabarito revisado"]
if v2 is not None:
    geral = acerto_geral(v2["motivo"], v2["previsto"])
    st.metric(
        f"Acerto do prompt em uso ({VERSAO_PROMPT_PRODUCAO}, {MODELO_CLASSIFICACAO})",
        c.pct(100 * geral["acerto"]),
        help="Avaliações em que o motivo dado pela IA é igual ao do gabarito.",
    )

st.subheader("Duas versões do prompt")
st.markdown(
    "O **v1** recebia só a definição de cada motivo. A análise dos erros mostrou que faltavam as regras "
    "de desempate, por exemplo \"se o cliente ainda não recebeu, não é atraso\". O **v2** recebe essas regras."
)
if linhas:
    st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch")
st.caption(
    "Depois da medição do v1, revisamos 10 rótulos do gabarito, com cada mudança registrada "
    "[aqui](https://github.com/ClausMoreira/radar-de-avaliacoes/blob/main/docs/revisao_gabarito.md). "
    "O v2 foi escrito olhando os erros nessas mesmas avaliações, por isso o número tende a ser otimista."
)

cega = c.medicao("cega")
if cega is not None:
    st.subheader("Validação às cegas")
    st.markdown(
        "O gabarito de 150 avaliações foi usado para ajustar o prompt, então ele tende a favorecer o v2. "
        "Para medir sem esse viés, sorteamos avaliações do próprio painel e as rotulamos à mão **sem ver "
        "a resposta do modelo**. Nenhuma delas foi usada para ajustar nada."
    )
    linhas_cega = []
    grupos = [("Todas as avaliações sorteadas", cega), ("Só as que não são elogio", cega[cega["motivo"] != "elogio"])]
    for nome_grupo, grupo in grupos:
        resultado = acerto_geral(grupo["motivo"], grupo["previsto"])
        minimo, maximo = intervalo_de_confianca(resultado["acertos"], resultado["total"])
        linhas_cega.append(
            {
                "Grupo": nome_grupo,
                "Acerto": f"{resultado['acertos']} de {resultado['total']} ({c.pct(100 * resultado['acerto'])})",
                "Intervalo de 95% de confiança": f"{c.pct(100 * minimo)} a {c.pct(100 * maximo)}",
            }
        )
    st.dataframe(pd.DataFrame(linhas_cega), hide_index=True, width="stretch")
    st.caption(
        "Os elogios são a maioria e são fáceis de acertar. Como o painel ranqueia reclamações, o acerto "
        "sem os elogios é o que mais importa para ele. Com poucas avaliações, o intervalo é largo. "
        "Revisando as discordâncias pela taxonomia, a maioria é erro do modelo e uma parte é rótulo "
        "ambíguo ou errado: veja a [revisão das discordâncias]"
        "(https://github.com/ClausMoreira/radar-de-avaliacoes/blob/main/docs/resultados/validacao_cega_revisao.md)."
    )

if v2 is not None:
    st.subheader("Acerto por motivo (v2)")
    por_motivo = acerto_por_motivo(v2["motivo"], v2["previsto"])
    por_motivo["Motivo"] = por_motivo["motivo"].map(c.nome)
    por_motivo["Acerto"] = [
        f"{a} de {t} ({c.pct(100 * p)})" for a, t, p in zip(por_motivo["acertos"], por_motivo["total"], por_motivo["acerto"])
    ]
    st.dataframe(por_motivo[["Motivo", "Acerto"]], hide_index=True, width="stretch")
    st.caption("Motivos com poucas avaliações no gabarito têm percentual instável: um erro muda muito o número.")

    st.subheader("Onde o v2 ainda erra")
    erros = v2[v2["motivo"] != v2["previsto"]]
    for item in erros.itertuples():
        st.markdown(
            f"""
            <div style="border:1px solid #e4e2dc;border-radius:8px;padding:10px 14px;margin-bottom:8px;background:#ffffff">
              <div style="font-size:0.8rem;color:{c.TEXTO_SECUNDARIO}">
                Gabarito: <b>{c.nome(item.motivo)}</b> &nbsp;·&nbsp; IA: <b>{c.nome(item.previsto)}</b>
              </div>
              <div style="margin-top:4px">{html.escape(item.texto)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.subheader("Limitações")
st.markdown(
    """
- Os dados são de 2016 a 2018 e de e-commerce em geral, não de delivery de comida.
- O painel mostra uma amostra de 3.000 avaliações, não a base inteira, por causa do limite gratuito da API.
- O gabarito foi rotulado por uma pessoa só. Um segundo rotulador ajudaria a medir o quanto os próprios rótulos concordam.
- Este app é uma demonstração com dados públicos, não uma ferramenta em uso em uma empresa.
"""
)
