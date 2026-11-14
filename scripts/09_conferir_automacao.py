"""Passo 9: confere o registro que a automação gravou na planilha.

Uso (depois de baixar a aba de registro do Google Planilhas como CSV):
    python scripts/09_conferir_automacao.py caminho/do/registro.csv
    python scripts/09_conferir_automacao.py caminho/do/registro.csv --comparar

Sem --comparar não gasta cota. Confere, pelo nosso código, se cada linha é uma
avaliação que enviamos, se nenhuma se repete, se a regra da avaliação crítica
foi aplicada igual à nossa e se toda crítica tem rascunho.

Com --comparar, classifica as mesmas avaliações com o classificador do projeto
(prompt de produção, em lote; 1 requisição para cada 25) e conta em quantas o
n8n chegou ao mesmo motivo. O n8n classifica uma avaliação por vez, e o acerto
do prompt foi medido em lotes de 25: esta comparação mostra se isso muda algo.

Saídas, em docs/resultados/:
    automacao_registro.csv       cópia do registro conferido
    automacao_conferencia.md     resumo da conferência
"""

import argparse
from datetime import date
from pathlib import Path

import pandas as pd

from radar.automacao import conferir_registro, resumo_do_registro
from radar.config import (
    MODELO_CLASSIFICACAO, NOMES_EXIBICAO, NOVAS_CSV, PASTA_RESULTADOS, VERSAO_PROMPT_PRODUCAO,
)
from radar.metricas import carregar


def comparar_com_o_classificador(registro: pd.DataFrame) -> list[str]:
    """Classifica as mesmas avaliações em lote e devolve as linhas do resumo."""
    from radar.classificador import classificar
    from radar.llm import ChaveAusente, ErroDaAPI, Gemini, RespostaInvalida, criar_cliente

    try:
        gemini = Gemini(criar_cliente(), MODELO_CLASSIFICACAO)
        em_lote = classificar(registro["texto"].tolist(), VERSAO_PROMPT_PRODUCAO, gemini)
    except (ChaveAusente, ErroDaAPI, RespostaInvalida) as erro:
        raise SystemExit(f"Comparação interrompida. {erro}")

    iguais = sum(a == b for a, b in zip(registro["motivo"], em_lote))
    linhas = [
        "## Comparação com o classificador do projeto",
        "",
        f"O n8n classifica uma avaliação por vez. O classificador do projeto usa o mesmo prompt "
        f"({VERSAO_PROMPT_PRODUCAO}) em lotes de 25, que é a configuração medida contra o gabarito.",
        "",
        f"- Mesmo motivo nas duas formas: **{iguais} de {len(registro)}**.",
        f"- Requisições gastas nesta comparação: {gemini.requisicoes}.",
    ]
    diferentes = [
        (linha.review_id[:8], NOMES_EXIBICAO[linha.motivo], NOMES_EXIBICAO[lote])
        for linha, lote in zip(registro.itertuples(index=False), em_lote) if linha.motivo != lote
    ]
    if diferentes:
        linhas += ["", "| Avaliação | Motivo no n8n | Motivo em lote |", "|---|---|---|"]
        linhas += [f"| {a} | {b} | {c} |" for a, b, c in diferentes]
    return linhas


def main():
    leitor = argparse.ArgumentParser(description="Confere o registro gravado pela automação.")
    leitor.add_argument("registro", type=Path, help="CSV baixado da aba de registro da planilha")
    leitor.add_argument("--comparar", action="store_true",
                        help="compara os motivos com o classificador do projeto (gasta cota)")
    argumentos = leitor.parse_args()

    if not argumentos.registro.exists():
        raise SystemExit(f"{argumentos.registro} não existe.")
    registro = pd.read_csv(argumentos.registro, dtype=str, keep_default_na=False)
    registro = registro[registro.get("review_id", pd.Series(dtype=str)).str.strip() != ""]
    if registro.empty:
        raise SystemExit("O registro está vazio ou não tem a coluna review_id.")

    problemas = conferir_registro(registro, carregar(NOVAS_CSV))
    if problemas and problemas[0].startswith("Colunas faltando"):
        raise SystemExit(problemas[0])
    registro["nota"] = registro["nota"].astype(int)
    resumo = resumo_do_registro(registro)

    linhas = [
        "# Conferência da automação",
        "",
        f"Conferido em {date.today().strftime('%d/%m/%Y')} por `scripts/09_conferir_automacao.py`, "
        "a partir do registro gravado pelo n8n na planilha.",
        "",
        f"- Avaliações registradas: **{resumo['registradas']}**.",
        f"- Críticas pela regra (nota 1 ou 2 e motivo de reclamação): **{resumo['criticas']}**.",
        f"- Problemas encontrados: **{len(problemas)}**.",
        "",
        "| Motivo | Avaliações |",
        "|---|---|",
    ]
    linhas += [f"| {NOMES_EXIBICAO.get(m, m)} | {q} |" for m, q in resumo["por_motivo"].items()]
    if problemas:
        linhas += ["", "## Problemas", ""] + [f"- {problema}" for problema in problemas]
    if argumentos.comparar:
        linhas += [""] + comparar_com_o_classificador(registro.drop_duplicates("review_id"))

    PASTA_RESULTADOS.mkdir(parents=True, exist_ok=True)
    registro.to_csv(PASTA_RESULTADOS / "automacao_registro.csv", index=False, encoding="utf-8")
    (PASTA_RESULTADOS / "automacao_conferencia.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")

    print(f"Registradas: {resumo['registradas']}. Críticas: {resumo['criticas']}. Problemas: {len(problemas)}.")
    for problema in problemas:
        print(" -", problema)
    print(f"Resumo salvo em {PASTA_RESULTADOS / 'automacao_conferencia.md'}.")


if __name__ == "__main__":
    main()
