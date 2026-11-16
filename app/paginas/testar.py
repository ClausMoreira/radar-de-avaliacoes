"""Tela de teste da API, feita no v0 e publicada na Vercel, dentro do app.

O app continua sendo a porta de entrada única: quem chega pelo link do
painel encontra aqui a tela que chama a API do Radar no n8n.
"""

import streamlit as st

ENDERECO = "https://radar-de-avaliacoes.vercel.app"
RESULTADO = "https://github.com/ClausMoreira/radar-de-avaliacoes/blob/main/docs/resultados/api_medicao.md"

st.title("Testar uma avaliação")
st.markdown(
    "Cole uma avaliação de cliente e veja, em poucos segundos, qual problema ela aponta e, "
    "se for crítica, um rascunho de resposta para revisar."
)
# O botão vem antes da tela embutida: se o navegador não mostrar a tela aqui
# dentro, o visitante ainda chega a ela com um toque.
st.link_button("Abrir em tela cheia", ENDERECO, icon=":material/open_in_new:")

# st.iframe só existe nas versões mais novas do Streamlit. O servidor publicado
# pode estar em uma versão anterior, então mantemos as duas formas.
if hasattr(st, "iframe"):
    st.iframe(ENDERECO, height=1150)
else:
    import streamlit.components.v1 as componentes

    componentes.iframe(ENDERECO, height=1150, scrolling=True)

with st.expander("Como esta tela funciona"):
    st.markdown(
        "- A tela foi gerada com o v0 e está publicada na Vercel.\n"
        "- Ela chama a API do Radar: um fluxo do n8n, sem servidor próprio, que usa o mesmo prompt "
        "e a mesma regra da avaliação crítica deste painel.\n"
        f"- O acerto e o tempo de resposta da API foram medidos com as 60 avaliações da validação às cegas. "
        f"[Ver a medição]({RESULTADO}).\n"
        "- A API roda no teste gratuito do n8n Cloud. Se ela estiver fora do ar, a própria tela avisa."
    )
