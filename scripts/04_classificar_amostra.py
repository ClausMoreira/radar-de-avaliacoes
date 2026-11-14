"""Passo 4: classifica a amostra do painel e separa as avaliações novas.

Uso (na raiz do projeto, com o ambiente virtual ativo):
    python scripts/04_classificar_amostra.py

Gasta 1 requisição para cada 25 avaliações (cerca de 120 para 3.000) e leva
uns 10 minutos, por causa do limite de 15 requisições por minuto. Se parar no
meio (queda de internet, cota do dia), rode de novo: os lotes já feitos vêm do
cache e não gastam cota.

Saídas, em data/processado/:
    avaliacoes_classificadas.csv   amostra do painel, com o motivo de cada avaliação
    avaliacoes_novas.csv           avaliações de agosto de 2018, sem motivo, para a automação
"""

import time

import pandas as pd

from radar.classificador import classificar
from radar.config import (
    AMOSTRA_PAINEL, CLASSIFICADAS_CSV, DATA_CORTE_NOVAS, GABARITO_CSV, MODELO_CLASSIFICACAO,
    NOVAS_CSV, PASTA_RAW, QUANTIDADE_NOVAS, SEMENTE, VERSAO_PROMPT_PRODUCAO,
)
from radar.dados import adicionar_categoria, carregar_avaliacoes, separar_painel_e_novas
from radar.llm import ChaveAusente, ErroDaAPI, Gemini, RespostaInvalida, criar_cliente


def main():
    tabela = adicionar_categoria(carregar_avaliacoes(PASTA_RAW), PASTA_RAW)
    ids_do_gabarito = set(pd.read_csv(GABARITO_CSV, usecols=["review_id"])["review_id"])
    painel, novas = separar_painel_e_novas(
        tabela, ids_do_gabarito, DATA_CORTE_NOVAS, AMOSTRA_PAINEL, QUANTIDADE_NOVAS, SEMENTE
    )

    print(f"Avaliações com texto válido: {len(tabela)}")
    print(f"Amostra do painel: {len(painel)} (avaliações anteriores a {DATA_CORTE_NOVAS}, sem as do gabarito)")
    print(f"Avaliações novas reservadas para a automação: {len(novas)}")

    try:
        gemini = Gemini(criar_cliente(), MODELO_CLASSIFICACAO)
    except ChaveAusente as erro:
        raise SystemExit(str(erro))

    inicio = time.monotonic()

    def andamento(feitas, total):
        minutos = (time.monotonic() - inicio) / 60
        print(f"  {feitas} de {total}  ({minutos:.1f} min, {gemini.requisicoes} requisições novas)")

    print(f"\nClassificando com o prompt {VERSAO_PROMPT_PRODUCAO} ({MODELO_CLASSIFICACAO})...")
    try:
        painel["motivo"] = classificar(
            painel["texto"].tolist(), VERSAO_PROMPT_PRODUCAO, gemini, ao_concluir_lote=andamento
        )
    except ErroDaAPI as erro:
        raise SystemExit(
            f"A API recusou a requisição: {erro.code} {erro.message}\n"
            "Os lotes já concluídos estão no cache. Rodar de novo continua de onde parou."
        )
    except RespostaInvalida as erro:
        raise SystemExit(f"Classificação interrompida. {erro}")

    CLASSIFICADAS_CSV.parent.mkdir(parents=True, exist_ok=True)
    painel.to_csv(CLASSIFICADAS_CSV, index=False, encoding="utf-8")
    novas.to_csv(NOVAS_CSV, index=False, encoding="utf-8")

    print(f"\nRequisições enviadas agora: {gemini.requisicoes}. Lotes vindos do cache: {gemini.respostas_do_cache}.")
    print(f"Salvo em {CLASSIFICADAS_CSV} e {NOVAS_CSV}.")
    print("\nMotivos na amostra do painel:")
    print(painel["motivo"].value_counts().to_string())


if __name__ == "__main__":
    main()
