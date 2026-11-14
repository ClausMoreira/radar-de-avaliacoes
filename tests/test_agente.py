"""Testes do agente sem rede: as ferramentas com dados pequenos e a conversa simulada."""

from types import SimpleNamespace

import pandas as pd
import pytest

from radar.agente import (
    FERRAMENTAS, MAXIMO_DE_RODADAS, _EXECUTORES, buscar_avaliacoes, carregar_instrucao,
    categorias_mais_afetadas, executar, resolver_categoria, responder, resumo_dos_motivos,
)
from radar.config import CATEGORIAS
from radar.llm import Conversa, Passo
from radar.metricas import ranking_motivos


@pytest.fixture
def tabela():
    linhas = []
    for n in range(30):
        linhas.append(("Cama mesa banho", "nao_recebido" if n < 12 else "elogio", "Não chegou ainda" if n < 12 else "Ótimo"))
    for n in range(25):
        linhas.append(("Relógios presentes", "defeito_ou_qualidade" if n < 10 else "elogio", "Veio quebrado" if n < 10 else "Bom"))
    for n in range(5):
        linhas.append(("Relógios de parede", "atraso", "Demorou"))
    return pd.DataFrame(
        {
            "review_id": [f"r{i}" for i in range(len(linhas))],
            "data_avaliacao": pd.date_range("2018-01-01", periods=len(linhas), freq="D"),
            "nota": [1 if motivo != "elogio" else 5 for _, motivo, _ in linhas],
            "categoria": [c for c, _, _ in linhas],
            "atraso_dias": [3.0 if motivo == "atraso" else -1.0 for _, motivo, _ in linhas],
            "motivo": [m for _, m, _ in linhas],
            "texto": [t for _, _, t in linhas],
        }
    )


# --- Ferramentas -----------------------------------------------------------------

def test_cada_ferramenta_declarada_tem_executor_e_motivos_da_taxonomia():
    assert {f["nome"] for f in FERRAMENTAS} == set(_EXECUTORES)
    for ferramenta in FERRAMENTAS:
        motivo = ferramenta["parametros"]["properties"].get("motivo")
        if motivo:
            assert motivo["enum"] == list(CATEGORIAS)


def test_resumo_usa_os_mesmos_numeros_do_painel(tabela):
    resumo = resumo_dos_motivos(tabela)
    painel = ranking_motivos(tabela)
    assert [r["quantidade"] for r in resumo["ranking"]] == painel["quantidade"].tolist()
    assert [r["pct_das_reclamacoes"] for r in resumo["ranking"]] == painel["pct_reclamacoes"].tolist()
    assert resumo["ranking"][0]["motivo"] == "Não recebido"
    assert resumo["avaliacoes"] == 60 and resumo["reclamacoes"] == 27


def test_categoria_sem_acento_e_sem_maiusculas(tabela):
    assert resolver_categoria(tabela, "cama mesa") == ("Cama mesa banho", None)
    assert resolver_categoria(tabela, "RELOGIOS PRESENTES") == ("Relógios presentes", None)
    assert resolver_categoria(tabela, None) == (None, None)


def test_categoria_ambigua_ou_inexistente_vira_erro_para_o_modelo(tabela):
    _, erro = resolver_categoria(tabela, "relógios")
    assert sorted(erro["opcoes"]) == ["Relógios de parede", "Relógios presentes"]
    _, erro = resolver_categoria(tabela, "bicicletas")
    assert "erro" in erro


def test_resumo_filtrado_por_categoria(tabela):
    resumo = resumo_dos_motivos(tabela, categoria="cama")
    assert resumo["categoria"] == "Cama mesa banho"
    assert resumo["avaliacoes"] == 30
    assert [r["motivo"] for r in resumo["ranking"]] == ["Não recebido"]


def test_categorias_mais_afetadas(tabela):
    resultado = categorias_mais_afetadas(tabela, "defeito_ou_qualidade")
    assert resultado["categorias"] == [
        {"categoria": "Relógios presentes", "avaliacoes_da_categoria": 25, "com_este_motivo": 10, "pct": 40.0}
    ]


def test_buscar_avaliacoes_limita_a_quantidade_e_conta_o_total(tabela):
    resultado = buscar_avaliacoes(tabela, "nao_recebido", quantas=50)
    assert resultado["total_encontrado"] == 12
    assert len(resultado["avaliacoes"]) == 8                 # máximo permitido
    assert resultado["avaliacoes"][0]["data"] == "12/01/2018"  # a mais recente primeiro


def test_motivo_invalido_e_argumento_estranho_viram_erro(tabela):
    assert "erro" in executar(tabela, "buscar_avaliacoes", {"motivo": "preco"})
    assert "erro" in executar(tabela, "resumo_dos_motivos", {"cidade": "SP"})
    assert "erro" in executar(tabela, "ferramenta_que_nao_existe", {})


def test_instrucao_do_agente_existe_e_proibe_inventar_numeros():
    texto = carregar_instrucao()
    assert "Não calcule, não estime e não invente números" in texto
    assert "mostre também a contagem" in texto


# --- Conversa simulada -----------------------------------------------------------

class ConversaRoteirizada:
    """Imita a Conversa: devolve passos combinados e registra o que recebeu."""

    roteiro = []

    def __init__(self, gemini, instrucao, ferramentas):
        self.gemini, self.recebido = gemini, []
        self.passos = list(self.roteiro)

    def perguntar(self, texto):
        self.gemini.requisicoes += 1
        return self.passos.pop(0)

    def devolver_resultados(self, resultados):
        self.gemini.requisicoes += 1
        self.recebido.append(resultados)
        return self.passos.pop(0)


def test_agente_consulta_a_ferramenta_e_devolve_o_texto(tabela):
    ConversaRoteirizada.roteiro = [
        Passo(chamadas=[{"nome": "resumo_dos_motivos", "argumentos": {}}]),
        Passo(texto="O principal problema é Não recebido."),
    ]
    gemini = SimpleNamespace(requisicoes=10)
    resposta = responder("Qual o principal problema?", tabela, gemini, nova_conversa=ConversaRoteirizada)
    assert resposta.texto == "O principal problema é Não recebido."
    assert [c["nome"] for c in resposta.consultas] == ["resumo_dos_motivos"]
    assert resposta.consultas[0]["resultado"]["ranking"][0]["quantidade"] == 12
    assert resposta.requisicoes == 2


def test_agente_para_depois_do_maximo_de_rodadas(tabela):
    chamada = Passo(chamadas=[{"nome": "listar_categorias", "argumentos": {}}])
    ConversaRoteirizada.roteiro = [chamada] * (MAXIMO_DE_RODADAS + 1)
    resposta = responder("?", tabela, SimpleNamespace(requisicoes=0), nova_conversa=ConversaRoteirizada)
    assert len(resposta.consultas) == MAXIMO_DE_RODADAS
    assert resposta.texto.startswith("Não consegui concluir")


# --- Conversa real com um Gemini simulado ----------------------------------------

def test_conversa_le_chamadas_e_texto_e_guarda_o_historico():
    conteudo_modelo = SimpleNamespace(role="model")
    respostas = [
        SimpleNamespace(
            candidates=[SimpleNamespace(content=conteudo_modelo)],
            function_calls=[SimpleNamespace(name="resumo_dos_motivos", args={"categoria": "cama"})],
            text=None,
        ),
        SimpleNamespace(candidates=[SimpleNamespace(content=conteudo_modelo)], function_calls=None, text=" Pronto. "),
    ]
    gemini = SimpleNamespace(_chamar=lambda conteudo, configuracao: respostas.pop(0))
    conversa = Conversa(gemini, "instrução", FERRAMENTAS)

    passo = conversa.perguntar("pergunta")
    assert passo.chamadas == [{"nome": "resumo_dos_motivos", "argumentos": {"categoria": "cama"}}]
    passo = conversa.devolver_resultados([{"nome": "resumo_dos_motivos", "resultado": {"ok": True}}])
    assert passo.texto == "Pronto."
    # pergunta, pedido do modelo, resultado da ferramenta, resposta do modelo
    assert len(conversa.historico) == 4
    assert conversa.historico[2].parts[0].function_response.name == "resumo_dos_motivos"


# --- Conferência dos números -------------------------------------------------------

from radar.agente import numeros_sem_fonte

CONSULTAS = [{"nome": "resumo_dos_motivos", "argumentos": {}, "resultado": {
    "avaliacoes": 3000, "ranking": [{"motivo": "Não recebido", "quantidade": 342, "pct_das_reclamacoes": 26.3}],
    "periodo": "10/2016 a 07/2018",
}}]


def test_numeros_que_vieram_das_consultas_passam():
    texto = "Em 3.000 avaliações, Não recebido teve 342 casos (26,3% das reclamações), de 10/2016 a 07/2018."
    assert numeros_sem_fonte(texto, CONSULTAS) == []


def test_numero_inventado_e_apontado():
    assert numeros_sem_fonte("Não recebido é 27,5% das reclamações e custa 1.200 reais.", CONSULTAS) == ["27,5", "1.200"]


def test_numero_arredondado_tambem_e_apontado():
    assert numeros_sem_fonte("Cerca de 26% das reclamações.", CONSULTAS) == ["26"]


def test_inteiros_pequenos_e_numeros_da_pergunta_sao_aceitos():
    assert numeros_sem_fonte("As 3 prioridades e o top 5.", CONSULTAS) == []
    assert numeros_sem_fonte("Você citou 2017.", CONSULTAS, pergunta="E em 2017?") == []
