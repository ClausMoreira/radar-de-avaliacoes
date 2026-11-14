"""Peças compartilhadas pelas páginas: dados, filtros, formatação e gráficos.

As páginas não calculam nada: todo número vem de radar.metricas ou de
radar.avaliacao. Este arquivo só carrega, filtra e desenha.
"""

import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ / "src") not in sys.path:
    sys.path.insert(0, str(RAIZ / "src"))

import altair as alt  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from radar.config import CATEGORIAS, CLASSIFICADAS_CSV, NOMES_EXIBICAO, PASTA_RESULTADOS  # noqa: E402
from radar.metricas import carregar, filtrar  # noqa: E402

# Variável de ambiente usada só no desenvolvimento, para testar com outro arquivo.
ARQUIVO_DADOS = Path(os.getenv("RADAR_CLASSIFICADAS", CLASSIFICADAS_CSV))

# Cores (paleta de referência validada para daltonismo). Cada motivo tem a sua
# cor fixa, pela ordem da taxonomia: a cor acompanha o motivo, não a posição
# no ranking, então um filtro nunca troca a cor de um motivo.
COR_PRINCIPAL = "#2a78d6"
COR_NEUTRA = "#b5b3ab"
TEXTO_SECUNDARIO = "#52514e"
CORES_SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
COR_DO_MOTIVO = {motivo: CORES_SERIES[i] for i, motivo in enumerate(CATEGORIAS)}

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


# --- Formatação no padrão brasileiro -----------------------------------------

def numero(valor) -> str:
    return f"{int(valor):,}".replace(",", ".")


def pct(valor) -> str:
    if valor is None or pd.isna(valor):
        return "sem dado"
    return f"{valor:.1f}%".replace(".", ",")


def decimal(valor, casas: int = 1) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def mes_ano(data) -> str:
    data = pd.Timestamp(data)
    return f"{MESES[data.month - 1]}/{data.year}"


def data_curta(data) -> str:
    return pd.Timestamp(data).strftime("%d/%m/%Y")


def estrelas(nota: int) -> str:
    return "★" * int(nota) + "☆" * (5 - int(nota))


# --- Dados ---------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def dados() -> pd.DataFrame:
    return carregar(ARQUIVO_DADOS)


@st.cache_data(show_spinner=False)
def medicao(versao: str) -> pd.DataFrame | None:
    arquivo = PASTA_RESULTADOS / f"medicao_{versao}.csv"
    if not arquivo.exists():
        return None
    return pd.read_csv(arquivo, dtype=str, keep_default_na=False)


def filtros_na_barra_lateral() -> pd.DataFrame:
    """Desenha os filtros (categoria e período) e devolve a tabela filtrada.

    Os filtros ficam na barra lateral e valem para todas as páginas.
    """
    tabela = dados()
    with st.sidebar:
        st.markdown("**Filtros**")
        categorias = sorted(tabela["categoria"].unique())
        escolhidas = st.multiselect(
            "Categoria do produto",
            categorias,
            key="filtro_categorias",
            placeholder="Todas as categorias",
        )
        meses = pd.period_range(
            tabela["data_avaliacao"].min(), tabela["data_avaliacao"].max(), freq="M"
        )
        rotulos = [mes_ano(m.to_timestamp()) for m in meses]
        inicio, fim = st.select_slider(
            "Período",
            options=list(range(len(meses))),
            value=(0, len(meses) - 1),
            format_func=lambda i: rotulos[i],
            key="filtro_periodo",
        )
        st.caption(
            "Dados públicos e anonimizados da Olist, de um marketplace brasileiro. "
            "Cada avaliação foi classificada por IA em um motivo principal."
        )
    return filtrar(
        tabela,
        categorias=escolhidas or None,
        inicio=meses[inicio].start_time,
        fim=meses[fim].end_time.normalize(),
    )


# --- Gráficos ------------------------------------------------------------------

def _base(grafico: alt.Chart) -> alt.Chart:
    return (
        grafico.configure_view(stroke=None)
        .configure_axis(
            labelColor=TEXTO_SECUNDARIO, titleColor=TEXTO_SECUNDARIO,
            labelFontSize=12, titleFontSize=12, domain=False, tickColor="#e4e2dc",
        )
        .configure(background="transparent")
    )


def barras_horizontais(
    tabela: pd.DataFrame,
    valor: str,
    rotulo_valor: str,
    titulo_valor: str,
    dica: list,
    cor: str = COR_PRINCIPAL,
    cores_por_linha: str | None = None,
) -> alt.Chart:
    """Barras horizontais finas, com o valor escrito no fim de cada barra.

    `tabela` precisa ter as colunas "nome", `valor` e `rotulo_valor` (o texto
    já formatado). A ordem das linhas da tabela é a ordem das barras.
    """
    ordem = tabela["nome"].tolist()
    altura = max(120, 38 * len(tabela))
    base = alt.Chart(tabela).encode(
        y=alt.Y("nome:N", sort=ordem, title=None, axis=alt.Axis(labelLimit=260, ticks=False)),
        x=alt.X(f"{valor}:Q", title=titulo_valor, axis=alt.Axis(grid=False, labels=False, ticks=False)),
        tooltip=dica,
    )
    if cores_por_linha:
        cor_barra = alt.Color(f"{cores_por_linha}:N", scale=None, legend=None)
    else:
        cor_barra = alt.value(cor)
    barras = base.mark_bar(size=18, cornerRadiusEnd=4).encode(color=cor_barra)
    textos = base.mark_text(align="left", dx=6, fontSize=12, color="#0b0b0b").encode(
        text=f"{rotulo_valor}:N"
    )
    return _base((barras + textos).properties(height=altura))


def cartao(titulo: str, destaque: str, linhas: list[str], cor: str) -> None:
    """Cartão de prioridade: título, número em destaque e linhas de apoio."""
    detalhes = "".join(f"<div style='margin-top:4px'>{linha}</div>" for linha in linhas)
    st.markdown(
        f"""
        <div style="border:1px solid #e4e2dc;border-top:4px solid {cor};border-radius:8px;
                    padding:14px 16px;background:#ffffff;height:100%">
          <div style="font-size:0.95rem;font-weight:600;color:#0b0b0b">{titulo}</div>
          <div style="font-size:2rem;font-weight:700;color:#0b0b0b;line-height:1.2;margin-top:6px">{destaque}</div>
          <div style="font-size:0.85rem;color:{TEXTO_SECUNDARIO}">{detalhes}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def nome(motivo: str) -> str:
    return NOMES_EXIBICAO.get(motivo, motivo)
