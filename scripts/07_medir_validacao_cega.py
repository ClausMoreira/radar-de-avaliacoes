"""Passo 7: compara a validação às cegas com a resposta do modelo.

Uso (depois de rotular e salvar a planilha do passo 6):
    python scripts/07_medir_validacao_cega.py

Não gasta cota: a resposta do modelo para cada avaliação já está em
data/processado/avaliacoes_classificadas.csv (prompt v2).

Saídas:
    data/validacao/validacao_cega.csv      seus rótulos
    docs/resultados/validacao_cega.csv     uma linha por avaliação, com rótulo e resposta do modelo
    docs/resultados/validacao_cega.md      resumo com acerto, intervalo de confiança e erros
"""

from datetime import date

import pandas as pd

from radar.avaliacao import acerto_geral, acerto_por_motivo, confusoes, intervalo_de_confianca
from radar.config import (
    CLASSIFICADAS_CSV, MODELO_CLASSIFICACAO, PASTA_RESULTADOS, PLANILHA_VALIDACAO,
    VALIDACAO_CSV, VERSAO_PROMPT_PRODUCAO,
)
from radar.rotulagem import validar


def porcentagem(valor: float) -> str:
    return f"{valor * 100:.1f}%".replace(".", ",")


def tabela_markdown(tabela: pd.DataFrame) -> str:
    linhas = ["| " + " | ".join(tabela.columns) + " |", "|" + "---|" * len(tabela.columns)]
    for linha in tabela.itertuples(index=False):
        linhas.append("| " + " | ".join(str(valor) for valor in linha) + " |")
    return "\n".join(linhas)


def main():
    if not PLANILHA_VALIDACAO.exists():
        raise SystemExit(f"{PLANILHA_VALIDACAO} não existe. Rode antes scripts/06_gerar_validacao_cega.py.")
    planilha = pd.read_excel(PLANILHA_VALIDACAO, sheet_name="rotular", dtype=str)
    problemas = validar(planilha)
    if problemas:
        print("A validação ainda não está pronta:")
        for problema in problemas:
            print(" -", problema)
        raise SystemExit(1)

    planilha["motivo"] = planilha["motivo"].str.strip()
    planilha["duvida"] = planilha["duvida"].fillna("").str.strip().str.lower().eq("sim")
    planilha.to_csv(VALIDACAO_CSV, index=False, encoding="utf-8")

    modelo = pd.read_csv(CLASSIFICADAS_CSV, usecols=["review_id", "motivo"], dtype=str)
    modelo = modelo.rename(columns={"motivo": "previsto"})
    resultado = planilha.merge(modelo, on="review_id", how="left", validate="one_to_one")
    if resultado["previsto"].isna().any():
        raise SystemExit("Há avaliações da planilha sem resposta do modelo nos dados processados.")
    resultado["acertou"] = resultado["motivo"] == resultado["previsto"]

    geral = acerto_geral(resultado["motivo"], resultado["previsto"])
    minimo, maximo = intervalo_de_confianca(geral["acertos"], geral["total"])
    # O painel ranqueia reclamações. Por isso medimos também o acerto só nas
    # avaliações que o rótulo humano considera reclamação ou texto vago: os
    # elogios são a maioria e são fáceis, e puxam o número geral para cima.
    nao_elogio = resultado[resultado["motivo"] != "elogio"]
    geral_ne = acerto_geral(nao_elogio["motivo"], nao_elogio["previsto"])
    minimo_ne, maximo_ne = intervalo_de_confianca(geral_ne["acertos"], geral_ne["total"])
    sem_duvida = resultado[~resultado["duvida"]]
    geral_sd = acerto_geral(sem_duvida["motivo"], sem_duvida["previsto"])
    por_motivo = acerto_por_motivo(resultado["motivo"], resultado["previsto"])
    por_motivo["acerto"] = por_motivo["acerto"].map(porcentagem)
    trocas = confusoes(resultado["motivo"], resultado["previsto"])
    erros = resultado[~resultado["acertou"]]

    partes = [
        "# Validação às cegas",
        "",
        f"- Data: {date.today():%d/%m/%Y}",
        f"- Classificação avaliada: prompt {VERSAO_PROMPT_PRODUCAO}, modelo {MODELO_CLASSIFICACAO}",
        f"- Amostra: {geral['total']} avaliações sorteadas da amostra do painel, rotuladas à mão sem ver a resposta do modelo nem a nota",
        f"- Acerto: {geral['acertos']} de {geral['total']} ({porcentagem(geral['acerto'])})",
        f"- Intervalo de 95% de confiança (Wilson): de {porcentagem(minimo)} a {porcentagem(maximo)}",
        f"- Sem as linhas marcadas como dúvida: {geral_sd['acertos']} de {geral_sd['total']} ({porcentagem(geral_sd['acerto'])})",
        f"- Só nas avaliações que não são elogio: {geral_ne['acertos']} de {geral_ne['total']} ({porcentagem(geral_ne['acerto'])}), "
        f"intervalo de 95% de {porcentagem(minimo_ne)} a {porcentagem(maximo_ne)}",
        "",
        "O painel ranqueia reclamações, então o acerto sem os elogios é o número que mais importa para ele.",
        "",
        "Diferente do gabarito de 150 avaliações, estas avaliações não foram usadas para escrever nem para ajustar o prompt.",
        "",
        "## Acerto por motivo",
        "",
        tabela_markdown(por_motivo),
        "",
        "Com poucas avaliações por motivo, os percentuais por motivo servem só como indicação.",
        "",
        "## Erros",
        "",
    ]
    if erros.empty:
        partes.append("Nenhum erro.")
    for linha in erros.itertuples():
        partes.append(f"- Rótulo: `{linha.motivo}`. Modelo: `{linha.previsto}`. Texto: \"{linha.texto}\"")
    partes += ["", "## Trocas mais comuns (rótulo, modelo)", "", tabela_markdown(trocas) if len(trocas) else "Nenhuma.", ""]
    resumo = "\n".join(partes)

    PASTA_RESULTADOS.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(PASTA_RESULTADOS / "validacao_cega.csv", index=False, encoding="utf-8")
    (PASTA_RESULTADOS / "validacao_cega.md").write_text(resumo, encoding="utf-8")
    print(resumo)


if __name__ == "__main__":
    main()
