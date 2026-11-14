"""Automação: a regra da avaliação crítica e o envio das avaliações novas.

O fluxo roda no n8n (ver automacao/README.md). Do nosso lado ficam três coisas:

1. A regra que decide se uma avaliação é crítica. O n8n aplica a mesma regra;
   ela está escrita aqui para ser testada e para conferirmos o que o n8n fez.
2. O envio das avaliações reservadas (data/processado/avaliacoes_novas.csv)
   para o webhook, uma por vez, como um marketplace avisaria um sistema.
3. A conferência do registro que o n8n gravou na planilha.

Este arquivo não fala com o Gemini. O endereço do webhook fica no .env, como a
chave da API: quem tem o endereço consegue disparar o fluxo.
"""

import json
import os
import time
import urllib.error
import urllib.request

import pandas as pd
from dotenv import load_dotenv

from radar.config import NOTA_MAXIMA_CRITICA, RAIZ
from radar.metricas import MOTIVOS_DE_RECLAMACAO

# O que um marketplace mandaria ao avisar de uma avaliação nova. O atraso real
# e a situação do pedido ficam de fora: o fluxo decide só pelo texto e pela nota.
CAMPOS_DO_ENVIO = ["review_id", "data_avaliacao", "nota", "categoria", "texto"]


class WebhookAusente(RuntimeError):
    """O endereço do webhook não foi encontrado no ambiente nem no arquivo .env."""


class EnvioRecusado(RuntimeError):
    """O n8n não aceitou a avaliação."""


# --- Regra da avaliação crítica ---------------------------------------------

def eh_critica(nota: int, motivo: str) -> bool:
    """Crítica = nota 1 ou 2 e um motivo de reclamação identificado.

    Elogio e "outro" nunca são críticos, mesmo com nota baixa: sem um motivo
    concreto, o rascunho de resposta seria genérico.
    """
    return int(nota) <= NOTA_MAXIMA_CRITICA and motivo in MOTIVOS_DE_RECLAMACAO


# --- Escolha e envio ---------------------------------------------------------

def escolher(
    novas: pd.DataFrame,
    quantidade: int,
    semente: int,
    inicio: int = 0,
    nota: int | None = None,
    review_id: str | None = None,
) -> pd.DataFrame:
    """Escolhe as avaliações a enviar, sempre na mesma ordem sorteada.

    Com a mesma semente, `inicio=0, quantidade=20` devolve sempre as mesmas 20,
    e `inicio=20` continua de onde a anterior parou. `review_id` escolhe uma
    avaliação específica; `nota` restringe o sorteio a uma nota.
    """
    if review_id is not None:
        escolhidas = novas[novas["review_id"] == review_id]
        if escolhidas.empty:
            raise ValueError(f"Não existe avaliação nova com o review_id {review_id}.")
        return escolhidas.reset_index(drop=True)
    ordem = novas.sample(frac=1, random_state=semente)
    if nota is not None:
        ordem = ordem[ordem["nota"] == nota]
    return ordem.iloc[inicio:inicio + quantidade].reset_index(drop=True)


def montar_envio(linha) -> dict:
    """Transforma uma linha da tabela no corpo da requisição."""
    return {
        "review_id": str(linha["review_id"]),
        "data_avaliacao": str(linha["data_avaliacao"])[:10],
        "nota": int(linha["nota"]),
        "categoria": str(linha["categoria"]),
        "texto": str(linha["texto"]),
    }


def ler_webhook() -> str:
    """Lê o endereço do webhook do arquivo .env (ou do ambiente)."""
    load_dotenv(RAIZ / ".env")
    endereco = os.getenv("N8N_WEBHOOK_URL", "").strip()
    if not endereco:
        raise WebhookAusente(
            "Endereço do webhook não encontrado. Preencha N8N_WEBHOOK_URL no arquivo .env "
            "com o endereço mostrado no nó Webhook do n8n."
        )
    if not endereco.startswith("https://"):
        raise WebhookAusente("N8N_WEBHOOK_URL precisa começar com https://.")
    return endereco


def eh_endereco_de_teste(endereco: str) -> bool:
    """O endereço de teste do n8n escuta uma única chamada por vez."""
    return "/webhook-test/" in endereco


def enviar(endereco: str, envio: dict, tempo_limite: int = 60) -> int:
    """Envia uma avaliação ao webhook e devolve o código HTTP.

    Levanta EnvioRecusado com uma explicação para os erros mais comuns.
    """
    requisicao = urllib.request.Request(
        endereco,
        data=json.dumps(envio, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(requisicao, timeout=tempo_limite) as resposta:
            return resposta.status
    except urllib.error.HTTPError as erro:
        if erro.code == 404:
            raise EnvioRecusado(
                "O n8n respondeu 404: o webhook não está escutando. No endereço de teste, "
                'clique em "Listen for test event" antes de cada envio. No endereço de '
                "produção, o fluxo precisa estar publicado."
            ) from erro
        raise EnvioRecusado(f"O n8n respondeu com o erro {erro.code}.") from erro
    except urllib.error.URLError as erro:
        raise EnvioRecusado(f"Não foi possível chegar ao n8n: {erro.reason}") from erro


def enviar_todas(
    endereco: str,
    envios: list[dict],
    intervalo: float,
    enviar_uma=enviar,
    esperar=time.sleep,
    ao_enviar=None,
) -> int:
    """Envia as avaliações em sequência, com um intervalo entre elas.

    O intervalo mantém o fluxo abaixo do limite de requisições por minuto do
    Gemini. `ao_enviar(posicao, total, envio)` é chamado depois de cada envio.
    Devolve quantas foram enviadas.
    """
    for posicao, envio in enumerate(envios, start=1):
        if posicao > 1:
            esperar(intervalo)
        enviar_uma(endereco, envio)
        if ao_enviar is not None:
            ao_enviar(posicao, len(envios), envio)
    return len(envios)


# --- Conferência do registro --------------------------------------------------

COLUNAS_DO_REGISTRO = [
    "review_id", "data_avaliacao", "nota", "categoria", "texto", "motivo", "motivo_nome",
    "critica", "situacao", "rascunho", "processada_em",
]
SITUACOES = ("registrada", "aguardando rascunho", "aguardando aprovação", "aprovado", "recusado")


def _eh_verdadeiro(valor) -> bool:
    return str(valor).strip().lower() in ("true", "verdadeiro", "1", "sim")


def conferir_registro(registro: pd.DataFrame, novas: pd.DataFrame) -> list[str]:
    """Confere o registro gravado pelo n8n e devolve a lista de problemas.

    Lista vazia significa: todas as linhas são avaliações que enviamos, nenhuma
    está repetida, a nota não foi alterada, o motivo está dentro da lista e a
    regra da avaliação crítica foi aplicada igual à nossa. Toda avaliação
    crítica tem rascunho, e nenhuma avaliação não crítica tem.
    """
    faltando = [coluna for coluna in COLUNAS_DO_REGISTRO if coluna not in registro.columns]
    if faltando:
        return [f"Colunas faltando no registro: {', '.join(faltando)}."]

    problemas = []
    repetidas = registro["review_id"][registro["review_id"].duplicated()].unique()
    for review_id in repetidas:
        problemas.append(f"{review_id}: registrada mais de uma vez.")

    originais = novas.set_index("review_id")
    todos_os_motivos = set(MOTIVOS_DE_RECLAMACAO) | {"elogio", "outro"}
    for linha in registro.drop_duplicates("review_id").itertuples(index=False):
        if linha.review_id not in originais.index:
            problemas.append(f"{linha.review_id}: não está entre as avaliações novas.")
            continue
        if int(linha.nota) != int(originais.loc[linha.review_id, "nota"]):
            problemas.append(f"{linha.review_id}: a nota do registro difere da original.")
        if linha.motivo not in todos_os_motivos:
            problemas.append(f"{linha.review_id}: motivo fora da lista ({linha.motivo}).")
            continue
        esperada = eh_critica(linha.nota, linha.motivo)
        if _eh_verdadeiro(linha.critica) != esperada:
            problemas.append(
                f"{linha.review_id}: a regra daria crítica={esperada}, o registro diz {linha.critica}."
            )
        tem_rascunho = bool(str(linha.rascunho).strip()) and str(linha.rascunho).strip().lower() != "nan"
        if esperada and not tem_rascunho:
            problemas.append(f"{linha.review_id}: avaliação crítica sem rascunho.")
        if not esperada and tem_rascunho:
            problemas.append(f"{linha.review_id}: avaliação não crítica com rascunho.")
    return problemas


def resumo_do_registro(registro: pd.DataFrame) -> dict:
    """Contagens do registro, calculadas pela nossa regra."""
    unicas = registro.drop_duplicates("review_id")
    criticas = [eh_critica(nota, motivo) for nota, motivo in zip(unicas["nota"], unicas["motivo"])]
    return {
        "registradas": len(unicas),
        "criticas": sum(criticas),
        "por_motivo": unicas["motivo"].value_counts().to_dict(),
    }
