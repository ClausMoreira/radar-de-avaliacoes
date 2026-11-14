"""Único ponto de acesso ao Gemini.

Nenhum outro arquivo do projeto importa a biblioteca do Google. Assim, a
leitura da chave, a escolha do modelo, o cache e o controle de cota ficam em
um só lugar.
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

from radar.config import ESPERAS_APOS_ERRO, INTERVALO_ENTRE_REQUISICOES, PASTA_CACHE, RAIZ

# Outros arquivos tratam erros da API por este nome, sem importar o Google.
ErroDaAPI = errors.APIError

# Modelos que não servem para classificar texto, mesmo com nome parecido.
TRECHOS_IGNORADOS = ("image", "tts", "live", "audio", "embedding")


# Erros que costumam passar sozinhos: limite por minuto (429) e API ocupada.
CODIGOS_PARA_TENTAR_DE_NOVO = (429, 500, 503)
# Quantas respostas fora do formato aceitamos antes de desistir de um pedido.
TENTATIVAS_POR_FORMATO = 2


class ChaveAusente(RuntimeError):
    """A chave do Gemini não foi encontrada no ambiente nem no arquivo .env."""


class RespostaInvalida(ValueError):
    """O modelo respondeu fora do formato combinado."""


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


class Gemini:
    """Requisições com saída estruturada, dentro da cota gratuita.

    Três cuidados ficam aqui e valem para o projeto inteiro:
    - cache em disco: a mesma pergunta ao mesmo modelo não gasta cota de novo,
      e um lote interrompido continua de onde parou;
    - intervalo mínimo entre requisições, por causa do limite por minuto;
    - nova tentativa quando a API está ocupada ou o limite por minuto estoura.

    `dormir` e `relogio` existem para os testes rodarem sem esperar de verdade.
    """

    def __init__(
        self,
        cliente,
        modelo: str,
        pasta_cache: Path = PASTA_CACHE,
        intervalo: float = INTERVALO_ENTRE_REQUISICOES,
        dormir=time.sleep,
        relogio=time.monotonic,
    ):
        self.cliente = cliente
        self.modelo = modelo
        self.pasta_cache = Path(pasta_cache)
        self.intervalo = intervalo
        self.dormir = dormir
        self.relogio = relogio
        self.requisicoes = 0          # enviadas à API nesta execução
        self.respostas_do_cache = 0   # atendidas sem gastar cota
        self._ultima_requisicao = None

    def gerar_json(self, prompt: str, esquema: dict, validar=None) -> dict:
        """Devolve a resposta do modelo já convertida de JSON.

        `validar` é uma função que recebe os dados e levanta RespostaInvalida
        se algo estiver errado. Só respostas aprovadas entram no cache.
        """
        arquivo = self._arquivo_de_cache(prompt, esquema)
        if arquivo.exists():
            guardado = json.loads(arquivo.read_text(encoding="utf-8"))["resposta"]
            try:
                self._conferir(json.dumps(guardado), validar)
            except RespostaInvalida:
                pass  # o cache é de uma regra antiga: perguntamos de novo
            else:
                self.respostas_do_cache += 1
                return guardado

        ultimo_problema = None
        for _ in range(TENTATIVAS_POR_FORMATO):
            texto = self._requisitar(prompt, esquema)
            try:
                dados = self._conferir(texto, validar)
            except RespostaInvalida as problema:
                ultimo_problema = problema
                continue
            self._guardar(arquivo, dados)
            return dados
        raise RespostaInvalida(
            f"O modelo respondeu fora do formato {TENTATIVAS_POR_FORMATO} vezes. "
            f"Último problema: {ultimo_problema}"
        )

    @staticmethod
    def _conferir(texto: str, validar) -> dict:
        try:
            dados = json.loads(texto)
        except json.JSONDecodeError as erro:
            raise RespostaInvalida(f"A resposta não é um JSON válido: {erro}") from erro
        if validar is not None:
            validar(dados)
        return dados

    def _requisitar(self, prompt: str, esquema: dict) -> str:
        configuracao = types.GenerateContentConfig(
            temperature=0,  # mesma pergunta, mesma resposta (na medida do possível)
            response_mime_type="application/json",
            response_json_schema=esquema,
        )
        return self._chamar(prompt, configuracao).text or ""

    def _chamar(self, conteudo, configuracao):
        """Uma requisição, respeitando o intervalo e tentando de novo se a API
        estiver ocupada ou o limite por minuto estourar."""
        for espera in (*ESPERAS_APOS_ERRO, None):
            self._respeitar_intervalo()
            self.requisicoes += 1
            try:
                return self.cliente.models.generate_content(
                    model=self.modelo, contents=conteudo, config=configuracao
                )
            except ErroDaAPI as erro:
                if erro.code in CODIGOS_PARA_TENTAR_DE_NOVO and espera is not None:
                    self.dormir(espera)
                    continue
                raise

    def _respeitar_intervalo(self) -> None:
        agora = self.relogio()
        if self._ultima_requisicao is not None:
            falta = self.intervalo - (agora - self._ultima_requisicao)
            if falta > 0:
                self.dormir(falta)
        self._ultima_requisicao = self.relogio()

    def _arquivo_de_cache(self, prompt: str, esquema: dict) -> Path:
        conteudo = json.dumps([self.modelo, prompt, esquema], sort_keys=True, ensure_ascii=False)
        nome = hashlib.sha256(conteudo.encode("utf-8")).hexdigest()[:32]
        return self.pasta_cache / f"{nome}.json"

    def _guardar(self, arquivo: Path, dados: dict) -> None:
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        registro = {"modelo": self.modelo, "resposta": dados}
        arquivo.write_text(json.dumps(registro, ensure_ascii=False, indent=1), encoding="utf-8")


@dataclass
class Passo:
    """O que o modelo devolveu em uma rodada da conversa.

    Ou ele pede ferramentas (chamadas preenchidas), ou responde (texto).
    Cada chamada é {"nome": str, "argumentos": dict}.
    """

    chamadas: list = field(default_factory=list)
    texto: str = ""


class Conversa:
    """Conversa com ferramentas (chamada de funções do Gemini).

    O modelo só pede ferramentas: quem executa é o nosso código, fora daqui.
    O histórico fica guardado no formato do Google porque o modelo exige de
    volta, a cada rodada, exatamente o que ele mesmo enviou.

    Cada ferramenta é um dicionário {"nome", "descricao", "parametros"}, com os
    parâmetros em JSON Schema.
    """

    def __init__(self, gemini: Gemini, instrucao: str, ferramentas: list[dict]):
        self.gemini = gemini
        self.historico = []
        declaracoes = [
            types.FunctionDeclaration(
                name=f["nome"], description=f["descricao"], parameters_json_schema=f["parametros"]
            )
            for f in ferramentas
        ]
        self.configuracao = types.GenerateContentConfig(
            system_instruction=instrucao,
            temperature=0,
            tools=[types.Tool(function_declarations=declaracoes)],
            # Desligado: queremos executar cada ferramenta nós mesmos e
            # registrar o que foi consultado.
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )

    def perguntar(self, texto: str) -> Passo:
        self.historico.append(types.Content(role="user", parts=[types.Part.from_text(text=texto)]))
        return self._rodada()

    def devolver_resultados(self, resultados: list[dict]) -> Passo:
        """`resultados` é uma lista de {"nome": str, "resultado": dict}, na
        mesma ordem das chamadas pedidas pelo modelo."""
        partes = [
            types.Part.from_function_response(name=r["nome"], response={"resultado": r["resultado"]})
            for r in resultados
        ]
        self.historico.append(types.Content(role="user", parts=partes))
        return self._rodada()

    def _rodada(self) -> Passo:
        resposta = self.gemini._chamar(self.historico, self.configuracao)
        candidatos = resposta.candidates or []
        if candidatos and candidatos[0].content is not None:
            self.historico.append(candidatos[0].content)
        chamadas = [
            {"nome": chamada.name, "argumentos": dict(chamada.args or {})}
            for chamada in (resposta.function_calls or [])
        ]
        if chamadas:
            return Passo(chamadas=chamadas)
        return Passo(texto=(resposta.text or "").strip())
