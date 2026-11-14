"""Único ponto de acesso ao Gemini.

Nenhum outro arquivo do projeto importa a biblioteca do Google. Assim, a
leitura da chave, a escolha do modelo e (nas próximas etapas) os lotes, o
cache e o controle de cota ficam em um só lugar.
"""

import os

from dotenv import load_dotenv
from google import genai
from google.genai import errors

from radar.config import RAIZ

# Outros arquivos tratam erros da API por este nome, sem importar o Google.
ErroDaAPI = errors.APIError

# Modelos que não servem para classificar texto, mesmo com nome parecido.
TRECHOS_IGNORADOS = ("image", "tts", "live", "audio", "embedding")


class ChaveAusente(RuntimeError):
    """A chave do Gemini não foi encontrada no ambiente nem no arquivo .env."""


def ler_chave() -> str:
    """Lê a chave do arquivo .env (ou do ambiente). Nunca a imprime."""
    load_dotenv(RAIZ / ".env")
    chave = os.getenv("GEMINI_API_KEY", "").strip()
    if not chave:
        raise ChaveAusente(
            "Chave do Gemini não encontrada. Copie .env.example para .env e "
            "preencha GEMINI_API_KEY com a chave criada no Google AI Studio."
        )
    return chave


def criar_cliente() -> genai.Client:
    return genai.Client(api_key=ler_chave())


def listar_modelos(cliente: genai.Client) -> list[str]:
    """Nomes dos modelos que geram texto, sem o prefixo "models/"."""
    todos, de_texto = [], []
    for modelo in cliente.models.list():
        nome = (modelo.name or "").removeprefix("models/")
        todos.append(nome)
        if "generateContent" in (modelo.supported_actions or []):
            de_texto.append(nome)
    return sorted(de_texto or todos)


def escolher_modelo(nomes: list[str], candidatos: tuple[str, ...]) -> str | None:
    """Devolve o primeiro modelo disponível, na ordem de preferência.

    Cada candidato é um trecho do nome (por exemplo, "3.5-flash-lite"). Entre
    os nomes que contêm o trecho, fica o mais curto, que é a versão estável
    sem sufixos como "-preview".
    """
    for trecho in candidatos:
        achados = [
            nome for nome in nomes
            if trecho in nome and not any(t in nome for t in TRECHOS_IGNORADOS)
        ]
        if achados:
            return min(achados, key=len)
    return None


def gerar_texto(cliente: genai.Client, modelo: str, prompt: str) -> str:
    """Faz uma requisição simples e devolve o texto da resposta."""
    resposta = cliente.models.generate_content(model=modelo, contents=prompt)
    return (resposta.text or "").strip()
