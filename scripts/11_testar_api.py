"""Passo 11: mede a API do Radar (fluxo automacao/fluxo_api.json no n8n).

Uso (na raiz do projeto, com o ambiente virtual ativo e RADAR_API_URL no .env):
    python scripts/11_testar_api.py               # medição completa: 60 avaliações + conferências
    python scripts/11_testar_api.py --uma         # uma chamada só, para ver se a API responde

O que mede:
1. Acerto pela API: as 60 avaliações da validação às cegas, enviadas uma por
   vez, sem rascunho. O rótulo é o que demos à mão, antes de qualquer
   comparação com o modelo. Estas avaliações nunca foram usadas para ajustar
   um prompt, e este script também não ajusta nada: só mede.
2. Regra da avaliação crítica: cada resposta é conferida contra
   radar.automacao.eh_critica, com a nota real da avaliação.
3. Tempo de resposta de cada chamada.
4. Pedidos inválidos (sem texto, nota fora de 1 a 5) precisam voltar com erro
   400, sem gastar cota.
5. Uma chamada com rascunho, para conferir que ele volta com o aviso de revisão.
6. Se a API aceita chamadas do navegador (cabeçalho de CORS).

Gasta cerca de 62 requisições do modelo de classificação e 1 do modelo de
rascunho, em cotas separadas. Resultado em docs/resultados/api_medicao.md.
O endereço da API não é impresso nem salvo no resultado.
"""

import argparse
import json
import os
import statistics
import time
import urllib.error
import urllib.request
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv

from radar.automacao import eh_critica
from radar.avaliacao import acerto_geral, confusoes, intervalo_de_confianca
from radar.config import CLASSIFICADAS_CSV, NOMES_EXIBICAO, PASTA_RESULTADOS, RAIZ, VALIDACAO_CSV

ARQUIVO = PASTA_RESULTADOS / "api_medicao.md"
INTERVALO = 5.0  # segundos entre as chamadas: 12 por minuto, abaixo do limite de 15
ORIGEM_DE_TESTE = "https://exemplo-de-tela.vercel.app"


def ler_endereco() -> str:
    load_dotenv(RAIZ / ".env")
    endereco = os.getenv("RADAR_API_URL", "").strip()
    if not endereco.startswith("https://"):
        raise SystemExit(
            "Preencha RADAR_API_URL no arquivo .env com a Production URL do nó \"Pedido (API)\" "
            "(o fluxo precisa estar publicado no n8n)."
        )
    return endereco


def chamar(endereco: str, corpo: dict, tempo_limite: int = 90) -> tuple[int, dict, float]:
    """Faz um POST e devolve (código HTTP, resposta em JSON, segundos)."""
    requisicao = urllib.request.Request(
        endereco,
        data=json.dumps(corpo, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    inicio = time.monotonic()
    try:
        with urllib.request.urlopen(requisicao, timeout=tempo_limite) as resposta:
            codigo, bruto = resposta.status, resposta.read()
    except urllib.error.HTTPError as erro:
        codigo, bruto = erro.code, erro.read()
    except urllib.error.URLError as erro:
        raise SystemExit(f"Não foi possível chegar à API: {erro.reason}")
    segundos = time.monotonic() - inicio
    try:
        dados = json.loads(bruto.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        dados = {"resposta_nao_json": bruto.decode("utf-8", "replace")[:200]}
    return codigo, dados, segundos


def conferir_cors(endereco: str) -> str:
    """Simula o pedido de permissão que o navegador faz antes de chamar a API."""
    requisicao = urllib.request.Request(
        endereco, method="OPTIONS",
        headers={"Origin": ORIGEM_DE_TESTE, "Access-Control-Request-Method": "POST",
                 "Access-Control-Request-Headers": "content-type"},
    )
    try:
        with urllib.request.urlopen(requisicao, timeout=30) as resposta:
            permitido = resposta.headers.get("Access-Control-Allow-Origin")
    except urllib.error.HTTPError as erro:
        permitido = erro.headers.get("Access-Control-Allow-Origin")
    except urllib.error.URLError as erro:
        return f"não foi possível conferir ({erro.reason})"
    if permitido in ("*", ORIGEM_DE_TESTE):
        return f"sim (Access-Control-Allow-Origin: {permitido})"
    return f"não (Access-Control-Allow-Origin: {permitido or 'ausente'})"


def amostra() -> pd.DataFrame:
    """As 60 avaliações da validação às cegas, com a nota real de cada uma."""
    rotulos = pd.read_csv(VALIDACAO_CSV, dtype=str, keep_default_na=False)
    notas = pd.read_csv(CLASSIFICADAS_CSV, usecols=["review_id", "nota"])
    tabela = rotulos.merge(notas, on="review_id", how="left", validate="one_to_one")
    if tabela["nota"].isna().any():
        raise SystemExit("Alguma avaliação da validação às cegas não tem nota na amostra do painel.")
    tabela["nota"] = tabela["nota"].astype(int)
    return tabela


def pct(valor: float) -> str:
    return f"{100 * valor:.1f}%".replace(".", ",")


def seg(valor: float) -> str:
    return f"{valor:.1f} s".replace(".", ",")


def main():
    leitor = argparse.ArgumentParser(description="Mede a API do Radar no n8n.")
    leitor.add_argument("--uma", action="store_true", help="faz uma chamada só e mostra a resposta")
    argumentos = leitor.parse_args()
    endereco = ler_endereco()

    if argumentos.uma:
        codigo, dados, segundos = chamar(endereco, {"texto": "Comprei há um mês e até agora não chegou.", "nota": 1})
        print(f"HTTP {codigo} em {seg(segundos)}")
        print(json.dumps(dados, ensure_ascii=False, indent=2))
        return

    quando = datetime.now()
    tabela = amostra()
    print(f"Medindo a API com {len(tabela)} avaliações, {INTERVALO:g} s entre as chamadas...")

    previstos, tempos, regra_errada, falhas = [], [], [], []
    for posicao, linha in enumerate(tabela.itertuples(), start=1):
        if posicao > 1:
            time.sleep(INTERVALO)
        codigo, dados, segundos = chamar(endereco, {"texto": linha.texto, "nota": linha.nota, "incluir_rascunho": False})
        if codigo != 200 or "motivo" not in dados:
            falhas.append(f"{linha.review_id[:8]}: HTTP {codigo} {json.dumps(dados, ensure_ascii=False)[:120]}")
            previstos.append(None)
            print(f"  {posicao:2d}/{len(tabela)}  FALHOU (HTTP {codigo})")
            continue
        tempos.append(segundos)
        previstos.append(dados["motivo"])
        if bool(dados.get("critica")) != eh_critica(linha.nota, dados["motivo"]):
            regra_errada.append(linha.review_id[:8])
        marca = "ok" if dados["motivo"] == linha.motivo else "  "
        print(f"  {posicao:2d}/{len(tabela)}  {marca}  {seg(segundos):>7}  {dados['motivo']}")

    tabela["previsto"] = previstos
    respondidas = tabela[tabela["previsto"].notna()]
    geral = acerto_geral(respondidas["motivo"], respondidas["previsto"])
    minimo, maximo = intervalo_de_confianca(geral["acertos"], geral["total"])
    reclamacoes = respondidas[respondidas["motivo"] != "elogio"]
    geral_rec = acerto_geral(reclamacoes["motivo"], reclamacoes["previsto"])

    print("\nPedidos inválidos (não devem chegar à IA):")
    invalidos = []
    for descricao, corpo in [
        ("sem texto", {"nota": 1}),
        ("texto vazio", {"texto": "   ", "nota": 1}),
        ("nota 0", {"texto": "Não chegou.", "nota": 0}),
        ("nota 3,5", {"texto": "Não chegou.", "nota": 3.5}),
    ]:
        codigo, dados, _ = chamar(endereco, corpo)
        invalidos.append((descricao, codigo, dados.get("erro", "")))
        print(f"  {descricao}: HTTP {codigo}")

    time.sleep(INTERVALO)
    criticas = tabela[(tabela["nota"] <= 2) & ~tabela["motivo"].isin(["elogio", "outro"])]
    critica = criticas.sort_values("motivo", key=lambda m: m != "nao_recebido").iloc[0]
    codigo_rascunho, com_rascunho, segundos_rascunho = chamar(endereco, {"texto": critica.texto, "nota": int(critica.nota)})
    print(f"\nChamada com rascunho: HTTP {codigo_rascunho} em {seg(segundos_rascunho)}")
    cors = conferir_cors(endereco)
    print(f"Aceita chamadas do navegador: {cors}")

    # --- Registro -------------------------------------------------------------
    partes = [
        "# Medição da API do Radar\n",
        f"- Data: {quando:%d/%m/%Y, %H:%M}",
        "- Fluxo: `automacao/fluxo_api.json`, publicado no n8n Cloud",
        "- Script: `scripts/11_testar_api.py`",
        "- Classificação: prompt `classificacao_v2`, modelo gemini-3.5-flash-lite, uma avaliação por chamada",
        "",
        "## Acerto pela API\n",
        f"As {len(tabela)} avaliações da validação às cegas, enviadas uma por vez, sem rascunho. "
        "O rótulo é o que demos à mão antes de qualquer comparação com o modelo.\n",
        "| Medida | Resultado |",
        "|---|---|",
        f"| Chamadas respondidas | {len(respondidas)} de {len(tabela)} |",
        f"| Acerto geral | **{geral['acertos']} de {geral['total']} ({pct(geral['acerto'])})**, intervalo de 95% de {pct(minimo)} a {pct(maximo)} |",
        f"| Acerto sem os elogios | {geral_rec['acertos']} de {geral_rec['total']} ({pct(geral_rec['acerto'])}) |",
        f"| Referência: mesma amostra, classificada em lotes de 25 pelo script 07 | 53 de 60 (88,3%); sem os elogios, 23 de 30 (76,7%) |",
        f"| Regra da avaliação crítica igual à do código | {len(respondidas) - len(regra_errada)} de {len(respondidas)} |",
        "",
        "## Tempo de resposta\n",
        "| Medida | Resultado |",
        "|---|---|",
    ]
    if tempos:
        partes += [
            f"| Mediana | {seg(statistics.median(tempos))} |",
            f"| Mais rápida | {seg(min(tempos))} |",
            f"| Mais lenta | {seg(max(tempos))} |",
            f"| Com rascunho (uma chamada) | {seg(segundos_rascunho)} |",
        ]
    partes += [
        "",
        "O tempo inclui a ida e a volta pela internet a partir do computador do autor, em São Paulo.\n",
        "## Conferências\n",
        "| Conferência | Resultado |",
        "|---|---|",
    ]
    for descricao, codigo, erro in invalidos:
        partes.append(f"| Pedido inválido ({descricao}) | HTTP {codigo}{': ' + erro if erro else ''} |")
    rascunho_ok = codigo_rascunho == 200 and bool(com_rascunho.get("rascunho")) and "revisão" in com_rascunho.get("aviso", "")
    partes += [
        f"| Avaliação crítica com rascunho | HTTP {codigo_rascunho}; rascunho {'presente, com aviso de revisão' if rascunho_ok else 'ausente ou sem aviso'} |",
        f"| Aceita chamadas do navegador (CORS) | {cors} |",
        "",
    ]
    if falhas:
        partes += ["## Chamadas que falharam\n"] + [f"- {f}" for f in falhas] + [""]
    if regra_errada:
        partes += ["## Regra diferente da do código\n"] + [f"- {r}" for r in regra_errada] + [""]
    erros = confusoes(respondidas["motivo"], respondidas["previsto"])
    if not erros.empty:
        partes += ["## Discordâncias com o rótulo\n", "| Rótulo | Resposta da API | Quantidade |", "|---|---|---|"]
        for linha in erros.itertuples(index=False):
            partes.append(f"| {NOMES_EXIBICAO.get(linha[0], linha[0])} | {NOMES_EXIBICAO.get(linha[1], linha[1])} | {linha[2]} |")
        partes.append("")
    if rascunho_ok:
        partes += ["## Exemplo de resposta com rascunho\n", "```json",
                   json.dumps(com_rascunho, ensure_ascii=False, indent=2), "```", ""]
    partes += [
        "## O que esta medição não mostra\n",
        "- É uma rodada só. A mesma avaliação pode receber outro motivo em outra rodada.",
        "- A diferença para os 88,3% em lote pode vir da classificação uma a uma ou da variação entre rodadas. Com 60 avaliações, não dá para separar as duas.",
        "- O tempo depende da carga da API gratuita do Gemini e do n8n Cloud no momento da medição.",
        "- O fluxo roda no teste gratuito do n8n Cloud, que dura 14 dias. Depois disso, a API sai do ar, e esta medição fica como registro.",
        "",
    ]
    PASTA_RESULTADOS.mkdir(parents=True, exist_ok=True)
    ARQUIVO.write_text("\n".join(partes), encoding="utf-8")
    print(f"\nAcerto: {geral['acertos']} de {geral['total']} ({pct(geral['acerto'])}). Salvo em {ARQUIVO}.")


if __name__ == "__main__":
    main()
