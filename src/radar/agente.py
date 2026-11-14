"""Agente "Pergunte ao Radar".

Divisão de trabalho:
- o Gemini lê a pergunta e escolhe quais ferramentas chamar;
- as ferramentas (este arquivo) consultam radar.metricas, as mesmas funções
  do painel, e devolvem os números;
- o Gemini só redige a resposta a partir do que as ferramentas devolveram.

Assim o agente não inventa números e mostra sempre os mesmos valores do painel.
Este arquivo não importa a biblioteca do Google: a conversa passa por llm.py.
"""

import re
import unicodedata
from dataclasses import dataclass, field

import pandas as pd

from radar.config import CATEGORIAS, INTERVALO_AGENTE, MODELO_AGENTE, NOMES_EXIBICAO, PASTA_PROMPTS
from radar.metricas import categorias_por_motivo, exemplos, filtrar, ranking_motivos, resumo_geral

# v1: primeira versão. v2: pede a contagem junto de cada percentual e proíbe
# "significativamente" (no teste da v1, a resposta sobre categorias omitia que
# os percentuais vinham de grupos de 21 a 47 avaliações).
VERSAO_INSTRUCAO = "v2"
MAXIMO_DE_RODADAS = 4  # rodadas de ferramentas por pergunta, para limitar o gasto de cota

_MOTIVO = {"type": "string", "enum": list(CATEGORIAS), "description": "Nome técnico do motivo."}
_CATEGORIA = {
    "type": "string",
    "description": "Nome (ou parte do nome) de uma categoria de produto. Omita para usar todas.",
}

FERRAMENTAS = [
    {
        "nome": "resumo_dos_motivos",
        "descricao": (
            "Ranking dos motivos de reclamação, do mais frequente ao menos frequente, com "
            "quantidade, parte das reclamações, nota média e parte dos pedidos entregues com "
            "atraso. Também devolve o total de avaliações e de reclamações. Use para perguntas "
            "sobre os principais problemas, prioridades ou comparação entre motivos."
        ),
        "parametros": {"type": "object", "properties": {"categoria": _CATEGORIA}},
    },
    {
        "nome": "categorias_mais_afetadas",
        "descricao": (
            "Categorias de produto em que um motivo pesa mais, em proporção às avaliações da "
            "categoria. Só considera categorias com pelo menos 20 avaliações."
        ),
        "parametros": {
            "type": "object",
            "properties": {
                "motivo": _MOTIVO,
                "quantas": {"type": "integer", "minimum": 1, "maximum": 10, "description": "Padrão: 5."},
            },
            "required": ["motivo"],
        },
    },
    {
        "nome": "buscar_avaliacoes",
        "descricao": (
            "Avaliações reais de um motivo, das mais recentes para as mais antigas. Pode filtrar "
            "por um trecho do texto e por categoria. Use para mostrar o que os clientes escrevem "
            "ou como base para um rascunho de resposta."
        ),
        "parametros": {
            "type": "object",
            "properties": {
                "motivo": _MOTIVO,
                "trecho": {"type": "string", "description": "Palavra ou trecho que o texto deve conter."},
                "categoria": _CATEGORIA,
                "quantas": {"type": "integer", "minimum": 1, "maximum": 8, "description": "Padrão: 5."},
            },
            "required": ["motivo"],
        },
    },
    {
        "nome": "listar_categorias",
        "descricao": "Lista as categorias de produto disponíveis, com a quantidade de avaliações de cada uma.",
        "parametros": {"type": "object", "properties": {}},
    },
]


@dataclass
class RespostaDoAgente:
    texto: str
    consultas: list = field(default_factory=list)   # [{"nome", "argumentos", "resultado"}]
    requisicoes: int = 0


def carregar_instrucao(versao: str = VERSAO_INSTRUCAO) -> str:
    return (PASTA_PROMPTS / f"agente_{versao}.md").read_text(encoding="utf-8")


# --- Ferramentas ---------------------------------------------------------------

def _sem_acento(texto: str) -> str:
    normal = unicodedata.normalize("NFKD", str(texto).lower().strip())
    return "".join(letra for letra in normal if not unicodedata.combining(letra))


def resolver_categoria(tabela: pd.DataFrame, pedido: str | None) -> tuple[str | None, dict | None]:
    """Encontra a categoria pedida, sem diferenciar maiúsculas nem acentos.

    Devolve (categoria, None) quando acha uma só, (None, None) quando não foi
    pedida nenhuma, e (None, erro) quando não acha ou acha mais de uma.
    """
    if not pedido or not str(pedido).strip():
        return None, None
    alvo = _sem_acento(pedido)
    nomes = sorted(tabela["categoria"].unique())
    exatas = [n for n in nomes if _sem_acento(n) == alvo]
    if exatas:
        return exatas[0], None
    parecidas = [n for n in nomes if alvo in _sem_acento(n)]
    if len(parecidas) == 1:
        return parecidas[0], None
    if parecidas:
        return None, {"erro": "Mais de uma categoria corresponde ao pedido.", "opcoes": parecidas[:10]}
    return None, {"erro": f"Nenhuma categoria corresponde a '{pedido}'. Use listar_categorias."}


def _limitar(valor, padrao: int, minimo: int, maximo: int) -> int:
    try:
        return max(minimo, min(maximo, int(valor)))
    except (TypeError, ValueError):
        return padrao


def _motivo_valido(motivo) -> dict | None:
    if motivo not in CATEGORIAS:
        return {"erro": f"Motivo desconhecido: {motivo}. Opções: {', '.join(CATEGORIAS)}."}
    return None


def resumo_dos_motivos(tabela: pd.DataFrame, categoria: str | None = None) -> dict:
    nome_categoria, erro = resolver_categoria(tabela, categoria)
    if erro:
        return erro
    dados = filtrar(tabela, categorias=[nome_categoria] if nome_categoria else None)
    resumo = resumo_geral(dados)
    ranking = ranking_motivos(dados)
    # Os nomes dos campos são lidos pelo modelo, então dizem exatamente o que
    # cada número conta. Na primeira versão, "avaliacoes", "reclamacoes" e
    # "quantidade" lado a lado levaram o modelo a escrever "342 de 1.299
    # avaliações" quando o certo era "342 de 1.299 reclamações".
    return {
        "categoria": nome_categoria or "todas",
        "total_de_avaliacoes": resumo["avaliacoes"],
        "total_de_reclamacoes": resumo["reclamacoes"],
        "pct_das_avaliacoes_que_sao_reclamacoes": resumo["pct_reclamacoes"],
        "nota_media_de_todas_as_avaliacoes": resumo["nota_media"],
        "periodo": (
            f"{resumo['inicio']:%m/%Y} a {resumo['fim']:%m/%Y}" if resumo["avaliacoes"] else None
        ),
        "ranking_dos_motivos_de_reclamacao": [
            {
                "motivo": linha.nome,
                "reclamacoes_com_este_motivo": int(linha.quantidade),
                "pct_do_total_de_reclamacoes": linha.pct_reclamacoes,
                "nota_media_deste_motivo": linha.nota_media,
                "pct_dos_pedidos_entregues_que_atrasaram": (
                    None if pd.isna(linha.pct_atrasados) else linha.pct_atrasados
                ),
            }
            for linha in ranking.itertuples()
        ],
    }


def categorias_mais_afetadas(tabela: pd.DataFrame, motivo: str, quantas: int = 5) -> dict:
    erro = _motivo_valido(motivo)
    if erro:
        return erro
    resultado = categorias_por_motivo(tabela, motivo, quantas=_limitar(quantas, 5, 1, 10))
    return {
        "motivo": NOMES_EXIBICAO[motivo],
        "observacao": "Percentual sobre as avaliações de cada categoria. Só categorias com 20 avaliações ou mais.",
        "categorias": [
            {
                "categoria": linha.categoria,
                "avaliacoes_da_categoria": int(linha.avaliacoes),
                "avaliacoes_da_categoria_com_este_motivo": int(linha.com_motivo),
                "pct_das_avaliacoes_da_categoria": linha.pct,
            }
            for linha in resultado.itertuples()
        ],
    }


def buscar_avaliacoes(
    tabela: pd.DataFrame, motivo: str, trecho: str = "", categoria: str | None = None, quantas: int = 5
) -> dict:
    erro = _motivo_valido(motivo)
    if erro:
        return erro
    nome_categoria, erro = resolver_categoria(tabela, categoria)
    if erro:
        return erro
    dados = filtrar(tabela, categorias=[nome_categoria] if nome_categoria else None)
    todas = exemplos(dados, motivo, quantos=len(dados), busca=trecho or "")
    selecionadas = todas.head(_limitar(quantas, 5, 1, 8))
    return {
        "motivo": NOMES_EXIBICAO[motivo],
        "categoria": nome_categoria or "todas",
        "total_de_avaliacoes_encontradas": len(todas),
        "avaliacoes": [
            {
                "data": f"{linha.data_avaliacao:%d/%m/%Y}",
                "nota": int(linha.nota),
                "categoria": linha.categoria,
                "texto": linha.texto,
            }
            for linha in selecionadas.itertuples()
        ],
    }


def listar_categorias(tabela: pd.DataFrame) -> dict:
    contagem = tabela["categoria"].value_counts()
    return {"categorias": [{"categoria": nome, "total_de_avaliacoes": int(n)} for nome, n in contagem.items()]}


_EXECUTORES = {
    "resumo_dos_motivos": resumo_dos_motivos,
    "categorias_mais_afetadas": categorias_mais_afetadas,
    "buscar_avaliacoes": buscar_avaliacoes,
    "listar_categorias": listar_categorias,
}


def executar(tabela: pd.DataFrame, nome: str, argumentos: dict) -> dict:
    """Roda uma ferramenta pedida pelo modelo. Nunca deixa um erro escapar:
    devolve {"erro": ...} para o modelo poder se corrigir."""
    funcao = _EXECUTORES.get(nome)
    if funcao is None:
        return {"erro": f"Ferramenta desconhecida: {nome}."}
    try:
        return funcao(tabela, **(argumentos or {}))
    except TypeError as problema:
        return {"erro": f"Argumentos inválidos para {nome}: {problema}"}


# --- Conferência dos números ------------------------------------------------------

_NUMERO = re.compile(r"\d+(?:[.,]\d+)*")


def _para_numero(trecho: str) -> float | None:
    """Converte "3.000", "26,3" ou "26.3" em número. Devolve None se não der."""
    if "," in trecho:
        trecho = trecho.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(?:\.\d{3})+", trecho):
        trecho = trecho.replace(".", "")
    try:
        return float(trecho)
    except ValueError:
        return None


def _numeros_em(valor, saida: set) -> None:
    if isinstance(valor, bool):
        return
    if isinstance(valor, (int, float)):
        saida.add(float(valor))
    elif isinstance(valor, str):
        for trecho in _NUMERO.findall(valor):
            numero = _para_numero(trecho)
            if numero is not None:
                saida.add(numero)
    elif isinstance(valor, dict):
        for item in valor.values():
            _numeros_em(item, saida)
    elif isinstance(valor, (list, tuple)):
        for item in valor:
            _numeros_em(item, saida)


def numeros_sem_fonte(texto: str, consultas: list, pergunta: str = "") -> list[str]:
    """Números da resposta que não aparecem em nenhum resultado de consulta.

    É a verificação da regra "todo número vem de uma ferramenta". Inteiros de
    0 a 10 sem casas decimais são ignorados, porque aparecem em frases comuns
    ("as 3 prioridades", "nota 1"). Números que estão na pergunta também valem.
    """
    permitidos: set = set()
    for consulta in consultas:
        _numeros_em(consulta.get("resultado"), permitidos)
    _numeros_em(pergunta, permitidos)

    sem_fonte = []
    for trecho in _NUMERO.findall(texto or ""):
        numero = _para_numero(trecho)
        if numero is None:
            continue
        if numero.is_integer() and 0 <= numero <= 10 and "," not in trecho:
            continue
        if not any(abs(numero - outro) < 1e-6 for outro in permitidos):
            sem_fonte.append(trecho)
    return sem_fonte


# --- Conversa ------------------------------------------------------------------

def responder(pergunta: str, tabela: pd.DataFrame, gemini, nova_conversa=None) -> RespostaDoAgente:
    """Responde uma pergunta do lojista usando as ferramentas.

    `gemini` é um radar.llm.Gemini com o modelo do agente. Cada pergunta é uma
    conversa nova: não há memória entre perguntas. `nova_conversa` existe para
    os testes trocarem a conversa real por uma simulada.
    """
    if nova_conversa is None:
        from radar.llm import Conversa as nova_conversa

    inicio = gemini.requisicoes
    conversa = nova_conversa(gemini, carregar_instrucao(), FERRAMENTAS)
    passo = conversa.perguntar(pergunta)
    consultas = []
    for _ in range(MAXIMO_DE_RODADAS):
        if not passo.chamadas:
            break
        resultados = []
        for chamada in passo.chamadas:
            resultado = executar(tabela, chamada["nome"], chamada["argumentos"])
            consultas.append({**chamada, "resultado": resultado})
            resultados.append({"nome": chamada["nome"], "resultado": resultado})
        passo = conversa.devolver_resultados(resultados)

    texto = passo.texto
    if passo.chamadas or not texto:
        texto = (
            "Não consegui concluir a resposta com as consultas disponíveis. "
            "Tente uma pergunta mais direta, por exemplo: \"Qual é o principal problema?\""
        )
    return RespostaDoAgente(texto=texto, consultas=consultas, requisicoes=gemini.requisicoes - inicio)


def criar_gemini_do_agente():
    """Gemini configurado com o modelo do agente (cota separada da classificação)."""
    from radar.llm import Gemini, criar_cliente

    return Gemini(criar_cliente(), MODELO_AGENTE, intervalo=INTERVALO_AGENTE)
