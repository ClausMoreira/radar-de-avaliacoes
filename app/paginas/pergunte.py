"""Página do agente: o lojista pergunta em português e o Radar responde com os dados."""

import os

import streamlit as st

import comum as c
from radar.agente import criar_gemini_do_agente, numeros_sem_fonte, responder
from radar.config import PERGUNTAS_POR_SESSAO
from radar.llm import ChaveAusente, ErroDaAPI

PERGUNTAS_EXEMPLO = [
    "Qual é o principal problema da loja e o que os clientes dizem sobre ele?",
    "Em quais categorias o defeito ou qualidade pesa mais?",
    "Escreva um rascunho de resposta para um cliente que ainda não recebeu o pedido.",
]

NOMES_DAS_CONSULTAS = {
    "resumo_dos_motivos": "Resumo dos motivos",
    "categorias_mais_afetadas": "Categorias mais afetadas",
    "buscar_avaliacoes": "Busca de avaliações",
    "listar_categorias": "Lista de categorias",
}


def _chave_dos_segredos() -> None:
    """No app publicado, a chave fica nos segredos do Streamlit, nunca no código."""
    try:
        chave = st.secrets.get("GEMINI_API_KEY")
    except Exception:  # sem arquivo de segredos (computador local usa o .env)
        chave = None
    if chave and not os.getenv("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = chave


@st.cache_resource(show_spinner=False)
def _gemini():
    # Um só cliente para todas as sessões: o intervalo entre requisições vale
    # para o app inteiro, não para cada visitante.
    _chave_dos_segredos()
    return criar_gemini_do_agente()


@st.cache_data(show_spinner=False, max_entries=200)
def _responder(pergunta: str) -> dict:
    # Mesma pergunta, mesma resposta, sem gastar cota de novo. Erros não
    # entram no cache, então uma pergunta que falhou pode ser repetida.
    resposta = responder(pergunta, c.dados(), _gemini())
    return {
        "texto": resposta.texto,
        "consultas": resposta.consultas,
        "requisicoes": resposta.requisicoes,
        "sem_fonte": numeros_sem_fonte(resposta.texto, resposta.consultas, pergunta),
    }


def _mostrar(item: dict) -> None:
    with st.chat_message("user"):
        st.markdown(item["pergunta"])
    with st.chat_message("assistant", avatar=":material/radar:"):
        if "erro" in item:
            st.warning(item["erro"])
            return
        resposta = item["resposta"]
        st.markdown(resposta["texto"])
        if resposta["consultas"] and not resposta["sem_fonte"]:
            st.caption(":material/check_circle: Todos os números da resposta aparecem nas consultas abaixo.")
        elif resposta["sem_fonte"]:
            st.caption(
                ":material/warning: Estes números não aparecem nas consultas e podem estar errados: "
                + ", ".join(resposta["sem_fonte"])
            )
        if resposta["consultas"]:
            with st.expander(f"Consultas feitas ({len(resposta['consultas'])})"):
                for consulta in resposta["consultas"]:
                    argumentos = ", ".join(f"{k}: {v}" for k, v in consulta["argumentos"].items()) or "sem filtros"
                    st.markdown(f"**{NOMES_DAS_CONSULTAS.get(consulta['nome'], consulta['nome'])}** ({argumentos})")
                    st.json(consulta["resultado"], expanded=False)


def _perguntar(pergunta: str, livre: bool) -> None:
    item = {"pergunta": pergunta}
    if livre and st.session_state.perguntas_livres >= PERGUNTAS_POR_SESSAO:
        item["erro"] = "Você atingiu o limite de perguntas livres desta sessão. As perguntas de exemplo continuam disponíveis."
        st.session_state.historico.append(item)
        return
    try:
        with st.spinner("Consultando os dados..."):
            item["resposta"] = _responder(pergunta)
        if livre:
            st.session_state.perguntas_livres += 1
    except ChaveAusente:
        item["erro"] = "O agente está desligado nesta instalação: falta a chave da API."
    except ErroDaAPI as erro:
        if erro.code == 429:
            item["erro"] = (
                "A cota gratuita da API acabou por agora. Tente mais tarde. "
                "As perguntas de exemplo já respondidas continuam funcionando."
            )
        else:
            item["erro"] = "Não foi possível responder agora. Tente de novo em instantes."
    st.session_state.historico.append(item)


st.session_state.setdefault("historico", [])
st.session_state.setdefault("perguntas_livres", 0)

st.title("Pergunte ao Radar")
st.markdown(
    "Faça uma pergunta sobre as avaliações. O agente escolhe quais consultas fazer, as consultas "
    "calculam os números com as **mesmas funções do painel**, e a IA só redige a resposta. "
    "Cada pergunta é respondida separadamente e usa toda a amostra, sem os filtros das outras páginas."
)

st.markdown("**Experimente:**")
colunas = st.columns(len(PERGUNTAS_EXEMPLO))
for coluna, pergunta in zip(colunas, PERGUNTAS_EXEMPLO):
    if coluna.button(pergunta, width="stretch"):
        _perguntar(pergunta, livre=False)

restantes = PERGUNTAS_POR_SESSAO - st.session_state.perguntas_livres
pergunta = st.chat_input(
    "Escreva sua pergunta" if restantes > 0 else "Limite de perguntas desta sessão atingido",
    disabled=restantes <= 0,
)
if pergunta:
    _perguntar(pergunta.strip()[:500], livre=True)

for item in reversed(st.session_state.historico):
    _mostrar(item)

restantes = PERGUNTAS_POR_SESSAO - st.session_state.perguntas_livres
st.caption(
    f"Perguntas livres restantes nesta sessão: {max(restantes, 0)} de {PERGUNTAS_POR_SESSAO}. "
    "O limite existe porque o app usa a camada gratuita da API. "
    "Rascunhos de resposta a clientes precisam de revisão e aprovação de uma pessoa antes do envio."
)
