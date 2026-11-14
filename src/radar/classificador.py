"""Classificação das avaliações: prompt, saída estruturada e validação.

Entrada: uma lista de textos de avaliações.
Saída: uma lista de motivos, na mesma ordem, todos dentro de CATEGORIAS.

Este arquivo não fala com o Gemini diretamente. Ele recebe um objeto com o
método gerar_json (a classe Gemini de llm.py, ou um substituto nos testes).
"""

import json

from radar.config import AVALIACOES_POR_LOTE, CATEGORIAS, PASTA_PROMPTS
from radar.llm import RespostaInvalida

# Cada arquivo de prompt traz as próprias definições dos motivos. Assim uma
# versão medida nunca muda quando a taxonomia evolui: o v1 continua igual ao
# que foi medido, e o resultado dele continua reproduzível.
MARCA_AVALIACOES = "{{avaliacoes}}"

# Formato que o modelo é obrigado a seguir. O "enum" limita o motivo aos
# nomes da nossa lista, então o modelo não pode inventar uma categoria.
ESQUEMA = {
    "type": "object",
    "properties": {
        "classificacoes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "motivo": {"type": "string", "enum": list(CATEGORIAS)},
                },
                "required": ["id", "motivo"],
            },
        }
    },
    "required": ["classificacoes"],
}


def carregar_prompt(versao: str) -> str:
    """Lê o texto do prompt de prompts/classificacao_<versao>.md."""
    arquivo = PASTA_PROMPTS / f"classificacao_{versao}.md"
    if not arquivo.exists():
        raise FileNotFoundError(f"Não existe o prompt {arquivo.name} em {PASTA_PROMPTS}.")
    texto = arquivo.read_text(encoding="utf-8")
    if MARCA_AVALIACOES not in texto:
        raise ValueError(f"O prompt {arquivo.name} não tem a marca {MARCA_AVALIACOES}.")
    return texto


def montar_prompt(modelo_do_prompt: str, textos: list[str]) -> str:
    """Preenche o prompt com as avaliações do lote.

    As avaliações são numeradas a partir de 1. Um número curto gasta menos
    tokens e é mais difícil de copiar errado do que o review_id original.
    """
    avaliacoes = "\n".join(
        json.dumps({"id": numero, "texto": texto}, ensure_ascii=False)
        for numero, texto in enumerate(textos, start=1)
    )
    return modelo_do_prompt.replace(MARCA_AVALIACOES, avaliacoes)


def extrair_motivos(dados: dict, quantidade: int) -> list[str]:
    """Confere a resposta do modelo e devolve os motivos na ordem do lote.

    Levanta RespostaInvalida se faltar avaliação, se houver número repetido
    ou desconhecido, ou se algum motivo estiver fora da lista. Não corrigimos
    nada em silêncio: resposta errada é rejeitada.
    """
    itens = dados.get("classificacoes") if isinstance(dados, dict) else None
    if not isinstance(itens, list):
        raise RespostaInvalida('A resposta não tem a lista "classificacoes".')

    motivos = {}
    for item in itens:
        if not isinstance(item, dict):
            raise RespostaInvalida(f"Item fora do formato: {item!r}")
        numero, motivo = item.get("id"), item.get("motivo")
        if motivo not in CATEGORIAS:
            raise RespostaInvalida(f"Motivo fora da lista na avaliação {numero}: {motivo!r}")
        if numero in motivos:
            raise RespostaInvalida(f"A avaliação {numero} foi classificada duas vezes.")
        motivos[numero] = motivo

    esperados = set(range(1, quantidade + 1))
    if set(motivos) != esperados:
        faltando = sorted(esperados - set(motivos))
        sobrando = sorted(set(motivos) - esperados, key=str)
        raise RespostaInvalida(f"Números faltando: {faltando}. Números desconhecidos: {sobrando}.")
    return [motivos[numero] for numero in range(1, quantidade + 1)]


def classificar(
    textos: list[str],
    versao: str,
    gemini,
    por_lote: int = AVALIACOES_POR_LOTE,
    ao_concluir_lote=None,
) -> list[str]:
    """Classifica os textos em lotes e devolve um motivo para cada um.

    Cada lote é uma requisição. `ao_concluir_lote(feitas, total)` é chamado
    depois de cada lote, para quem quiser mostrar o andamento.
    """
    modelo_do_prompt = carregar_prompt(versao)
    motivos = []
    for inicio in range(0, len(textos), por_lote):
        lote = textos[inicio:inicio + por_lote]
        motivos.extend(_classificar_lote(modelo_do_prompt, lote, gemini))
        if ao_concluir_lote is not None:
            ao_concluir_lote(len(motivos), len(textos))
    return motivos


def _classificar_lote(modelo_do_prompt: str, lote: list[str], gemini) -> list[str]:
    """Classifica um lote. Se o modelo insistir em responder fora do formato,
    divide o lote ao meio e tenta cada metade, até chegar a uma avaliação.

    Assim, uma avaliação problemática não derruba as outras 24 do lote. Se
    nem sozinha ela for classificada, o erro sobe para quem chamou.
    """
    prompt = montar_prompt(modelo_do_prompt, lote)
    try:
        dados = gemini.gerar_json(
            prompt, ESQUEMA, validar=lambda resposta: extrair_motivos(resposta, len(lote))
        )
    except RespostaInvalida:
        if len(lote) == 1:
            raise
        meio = len(lote) // 2
        return (
            _classificar_lote(modelo_do_prompt, lote[:meio], gemini)
            + _classificar_lote(modelo_do_prompt, lote[meio:], gemini)
        )
    return extrair_motivos(dados, len(lote))
