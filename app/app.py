"""Ponto de entrada do app: python -m streamlit run app/app.py"""

import streamlit as st

st.set_page_config(page_title="Radar de Avaliações", page_icon="📡", layout="wide")

paginas = st.navigation(
    [
        st.Page("paginas/prioridades.py", title="Prioridades", icon=":material/flag:", default=True),
        st.Page("paginas/avaliacoes.py", title="Avaliações", icon=":material/chat:"),
        st.Page("paginas/como_sabemos.py", title="Como sabemos que funciona", icon=":material/fact_check:"),
    ]
)
paginas.run()
