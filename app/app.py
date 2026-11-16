"""Ponto de entrada do app: python -m streamlit run app/app.py"""

import streamlit as st

st.set_page_config(page_title="Radar de Avaliações: qual problema da loja priorizar", page_icon="📡", layout="wide")

# Entrada animada, sugerida por quem abriu o app pelo celular. Aparece uma vez
# por visita e some sozinha em cerca de 1,4 segundo. É só CSS: os dados carregam
# por baixo dela, deixa os cliques passarem e não aparece para quem
# pediu menos animações no aparelho. Para desligar, basta apagar este bloco.
ENTRADA = """
<style>
div[data-testid="stElementContainer"]:has(.radar-entrada) { position: absolute; }
.radar-entrada { position: fixed; inset: 0; z-index: 999999; background: #fcfcfb; display: flex;
  flex-direction: column; align-items: center; justify-content: center; gap: 18px; pointer-events: none;
  animation: radar-sair 0.4s ease 1s forwards; }
.radar-sinal { position: relative; width: 96px; height: 96px; }
.radar-sinal span { position: absolute; inset: 0; border: 3px solid #2a78d6; border-radius: 50%; opacity: 0;
  animation: radar-onda 1s ease-out infinite; }
.radar-sinal span:nth-child(2) { animation-delay: 0.2s; }
.radar-sinal span:nth-child(3) { animation-delay: 0.4s; }
.radar-sinal i { position: absolute; left: 50%; top: 50%; width: 18px; height: 18px; margin: -9px 0 0 -9px;
  border-radius: 50%; background: #2a78d6; }
.radar-nome { font-size: 1.6rem; font-weight: 700; color: #0b0b0b; }
.radar-frase { font-size: 0.95rem; color: #52514e; margin-top: -12px; }
@keyframes radar-onda { 0% { transform: scale(0.2); opacity: 0.9; } 100% { transform: scale(1); opacity: 0; } }
@keyframes radar-sair { to { opacity: 0; visibility: hidden; } }
@media (prefers-reduced-motion: reduce) { .radar-entrada { display: none; } }
</style>
<div class="radar-entrada" aria-hidden="true">
<div class="radar-sinal"><span></span><span></span><span></span><i></i></div>
<div class="radar-nome">Radar de Avaliações</div>
<div class="radar-frase">Qual problema priorizar?</div>
</div>
"""
if "entrada_exibida" not in st.session_state:
    st.session_state["entrada_exibida"] = True
    st.markdown(ENTRADA, unsafe_allow_html=True)

paginas = st.navigation(
    [
        st.Page("paginas/prioridades.py", title="Prioridades", icon=":material/flag:", default=True),
        st.Page("paginas/avaliacoes.py", title="Avaliações", icon=":material/chat:"),
        st.Page("paginas/pergunte.py", title="Pergunte ao Radar", icon=":material/forum:"),
        st.Page("paginas/como_sabemos.py", title="Como sabemos que funciona", icon=":material/fact_check:"),
    ]
)
paginas.run()
