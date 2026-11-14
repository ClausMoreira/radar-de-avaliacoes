"""Passo 8: envia avaliações novas para a automação no n8n.

Faz o papel do marketplace: cada avaliação reservada em
data/processado/avaliacoes_novas.csv é enviada ao webhook do fluxo, uma por vez.

Uso (na raiz do projeto, com o ambiente virtual ativo e N8N_WEBHOOK_URL no .env):
    python scripts/08_enviar_avaliacoes_novas.py                  # 1 avaliação
    python scripts/08_enviar_avaliacoes_novas.py --nota 1         # 1 avaliação de nota 1, para ver o alerta
    python scripts/08_enviar_avaliacoes_novas.py --quantidade 20  # as 20 do teste cronometrado
    python scripts/08_enviar_avaliacoes_novas.py --quantidade 20 --inicio 20   # as 20 seguintes
    python scripts/08_enviar_avaliacoes_novas.py --id <review_id> # uma avaliação específica
    python scripts/08_enviar_avaliacoes_novas.py --quantidade 20 --inicio 20 --salvar manual.csv
                                                                  # não envia: salva as avaliações em um CSV

A ordem das avaliações é sorteada com semente fixa: os mesmos argumentos
enviam sempre as mesmas avaliações. Este script não gasta cota do Gemini;
quem gasta é o fluxo no n8n (1 requisição por avaliação, mais 1 por rascunho).
"""

import argparse
import time

from radar.automacao import (
    CAMPOS_DO_ENVIO, EnvioRecusado, WebhookAusente, eh_endereco_de_teste, enviar_todas, escolher, ler_webhook,
    montar_envio,
)
from radar.config import INTERVALO_ENTRE_ENVIOS, NOVAS_CSV, SEMENTE_AUTOMACAO
from radar.metricas import carregar


def main():
    leitor = argparse.ArgumentParser(description="Envia avaliações novas ao webhook do n8n.")
    leitor.add_argument("--quantidade", type=int, default=1, help="quantas avaliações enviar (padrão: 1)")
    leitor.add_argument("--inicio", type=int, default=0, help="posição inicial na ordem sorteada (padrão: 0)")
    leitor.add_argument("--nota", type=int, choices=range(1, 6), help="enviar só avaliações com esta nota")
    leitor.add_argument("--id", dest="review_id", help="enviar a avaliação com este review_id")
    leitor.add_argument("--intervalo", type=float, default=INTERVALO_ENTRE_ENVIOS,
                        help=f"segundos entre os envios (padrão: {INTERVALO_ENTRE_ENVIOS})")
    leitor.add_argument("--salvar", metavar="ARQUIVO.csv",
                        help="não envia: salva as avaliações escolhidas em um CSV (para a triagem à mão)")
    argumentos = leitor.parse_args()

    try:
        escolhidas = escolher(
            carregar(NOVAS_CSV), argumentos.quantidade, SEMENTE_AUTOMACAO,
            inicio=argumentos.inicio, nota=argumentos.nota, review_id=argumentos.review_id,
        )
    except ValueError as erro:
        raise SystemExit(str(erro))
    if escolhidas.empty:
        raise SystemExit("Nenhuma avaliação com esses argumentos.")

    if argumentos.salvar:
        escolhidas[CAMPOS_DO_ENVIO].to_csv(argumentos.salvar, index=False, encoding="utf-8-sig")
        print(f"{len(escolhidas)} avaliação(ões) salva(s) em {argumentos.salvar}. Nada foi enviado.")
        return

    try:
        endereco = ler_webhook()
    except WebhookAusente as erro:
        raise SystemExit(str(erro))

    # O endereço não é impresso: quem o tem consegue disparar o fluxo.
    if eh_endereco_de_teste(endereco):
        print('Endereço de TESTE. Ele escuta uma chamada por vez: clique em "Listen for test event" no n8n antes de enviar.')
        if len(escolhidas) > 1:
            raise SystemExit("Com o endereço de teste, envie uma avaliação por vez. Para várias, publique o fluxo e use o endereço de produção.")
    else:
        print("Endereço de PRODUÇÃO: o fluxo precisa estar publicado no n8n.")

    envios = [montar_envio(linha) for _, linha in escolhidas.iterrows()]
    inicio = time.monotonic()

    def andamento(posicao, total, envio):
        trecho = envio["texto"][:60].replace("\n", " ")
        print(f"  {posicao} de {total}  nota {envio['nota']}  {envio['review_id'][:8]}  {trecho}")

    print(f"Enviando {len(envios)} avaliação(ões), com {argumentos.intervalo:g} s entre elas...")
    try:
        enviadas = enviar_todas(endereco, envios, argumentos.intervalo, ao_enviar=andamento)
    except EnvioRecusado as erro:
        raise SystemExit(f"Envio interrompido. {erro}")

    segundos = time.monotonic() - inicio
    print(f"\n{enviadas} enviada(s) em {segundos:.0f} s. Confira a planilha de registro e a caixa de e-mail.")


if __name__ == "__main__":
    main()
