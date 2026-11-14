"""Passo 3: mede uma versão do prompt contra o gabarito rotulado à mão.

Uso (na raiz do projeto, com o ambiente virtual ativo):
    python scripts/03_medir_prompt.py v1

Gasta 1 requisição para cada 25 avaliações do gabarito (6 para 150). Rodar de
novo a mesma versão não gasta cota, porque as respostas ficam em data/cache.

Saídas, em docs/resultados/:
    medicao_<versao>.csv   uma linha por avaliação, com gabarito e previsto
    medicao_<versao>.md    resumo: acerto geral, por motivo e trocas mais comuns
"""

import sys
from datetime import date

import pandas as pd

from radar.avaliacao import acerto_geral, acerto_por_motivo, confusoes
from radar.classificador import classificar
from radar.config import GABARITO_CSV, MODELO_CLASSIFICACAO, PASTA_RESULTADOS
from radar.llm import ChaveAusente, ErroDaAPI, Gemini, RespostaInvalida, criar_cliente


def porcentagem(valor: float) -> str:
    return f"{valor * 100:.1f}%".replace(".", ",")


def tabela_markdown(tabela: pd.DataFrame) -> str:
    linhas = ["| " + " | ".join(tabela.columns) + " |", "|" + "---|" * len(tabela.columns)]
    for linha in tabela.itertuples(index=False):
        linhas.append("| " + " | ".join(str(valor) for valor in linha) + " |")
    return "\n".join(linhas)


def montar_resumo(versao: str, resultado: pd.DataFrame) -> str:
    geral = acerto_geral(resultado["motivo"], resultado["previsto"])
    sem_duvida = resultado[~resultado["duvida"]]
    geral_sem_duvida = acerto_geral(sem_duvida["motivo"], sem_duvida["previsto"])

    por_motivo = acerto_por_motivo(resultado["motivo"], resultado["previsto"])
    por_motivo["acerto"] = por_motivo["acerto"].map(porcentagem)
    trocas = confusoes(resultado["motivo"], resultado["previsto"])

    partes = [
        f"# Medição do prompt {versao}",
        "",
        f"- Data: {date.today():%d/%m/%Y}",
        f"- Modelo: {MODELO_CLASSIFICACAO}",
        f"- Gabarito: {geral['total']} avaliações rotuladas à mão",
        f"- Acerto geral: {geral['acertos']} de {geral['total']} ({porcentagem(geral['acerto'])})",
        f"- Acerto sem as linhas marcadas como dúvida: {geral_sem_duvida['acertos']} de "
        f"{geral_sem_duvida['total']} ({porcentagem(geral_sem_duvida['acerto'])})",
        "",
        "## Acerto por motivo do gabarito",
        "",
        tabela_markdown(por_motivo),
        "",
        "## Trocas mais comuns (gabarito, previsto)",
        "",
        tabela_markdown(trocas) if len(trocas) else "Nenhum erro.",
        "",
    ]
    return "\n".join(partes)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Informe a versão do prompt. Exemplo: python scripts/03_medir_prompt.py v1")
    versao = sys.argv[1]

    if not GABARITO_CSV.exists():
        raise SystemExit(f"{GABARITO_CSV} não existe. Rode antes scripts/02_validar_gabarito.py.")
    gabarito = pd.read_csv(GABARITO_CSV, dtype=str, keep_default_na=False)
    gabarito["duvida"] = gabarito["duvida"].str.lower().eq("true")

    try:
        gemini = Gemini(criar_cliente(), MODELO_CLASSIFICACAO)
    except ChaveAusente as erro:
        raise SystemExit(str(erro))

    print(f"Classificando {len(gabarito)} avaliações com o prompt {versao}...")
    try:
        previsto = classificar(
            gabarito["texto"].tolist(),
            versao,
            gemini,
            ao_concluir_lote=lambda feitas, total: print(f"  {feitas} de {total}"),
        )
    except FileNotFoundError as erro:
        raise SystemExit(str(erro))
    except ErroDaAPI as erro:
        raise SystemExit(
            f"A API recusou a requisição: {erro.code} {erro.message}\n"
            "Os lotes já concluídos estão no cache. Rodar de novo continua de onde parou."
        )
    except RespostaInvalida as erro:
        raise SystemExit(f"Medição interrompida. {erro}")

    resultado = gabarito.copy()
    resultado["previsto"] = previsto
    resultado["acertou"] = resultado["motivo"] == resultado["previsto"]

    PASTA_RESULTADOS.mkdir(parents=True, exist_ok=True)
    arquivo_csv = PASTA_RESULTADOS / f"medicao_{versao}.csv"
    arquivo_md = PASTA_RESULTADOS / f"medicao_{versao}.md"
    resultado.to_csv(arquivo_csv, index=False, encoding="utf-8")
    resumo = montar_resumo(versao, resultado)
    arquivo_md.write_text(resumo, encoding="utf-8")

    print()
    print(resumo)
    print(f"Requisições enviadas agora: {gemini.requisicoes}. Lotes vindos do cache: {gemini.respostas_do_cache}.")
    print(f"Detalhe por avaliação em: {arquivo_csv}")


if __name__ == "__main__":
    main()
