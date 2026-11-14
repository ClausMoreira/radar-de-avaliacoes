"""Passo 2: confere a planilha rotulada e salva o gabarito em CSV.

Uso (depois de rotular e salvar a planilha):
    python scripts/02_validar_gabarito.py

O script não corrige nada sozinho. Ele aponta o que falta e só grava o
gabarito quando todas as linhas têm um motivo válido.
"""

import pandas as pd

from radar.config import CATEGORIAS, GABARITO_CSV, PLANILHA_ROTULAGEM


def validar(planilha: pd.DataFrame) -> list[str]:
    """Devolve a lista de problemas encontrados (vazia se estiver tudo certo)."""
    problemas = []
    motivo = planilha["motivo"].fillna("").astype(str).str.strip()

    vazias = planilha.index[motivo == ""]
    if len(vazias):
        linhas = ", ".join(str(i + 2) for i in vazias[:15])
        problemas.append(f"{len(vazias)} linha(s) sem motivo. Linhas da planilha: {linhas}")

    invalidas = planilha.index[(motivo != "") & ~motivo.isin(CATEGORIAS)]
    if len(invalidas):
        linhas = ", ".join(str(i + 2) for i in invalidas[:15])
        problemas.append(f"{len(invalidas)} linha(s) com motivo fora da lista. Linhas: {linhas}")

    if planilha["review_id"].duplicated().any():
        problemas.append("Há review_id repetido na planilha.")
    return problemas


def main():
    planilha = pd.read_excel(PLANILHA_ROTULAGEM, sheet_name="rotular", dtype=str)
    problemas = validar(planilha)
    if problemas:
        print("O gabarito ainda não está pronto:")
        for problema in problemas:
            print(" -", problema)
        raise SystemExit(1)

    planilha["motivo"] = planilha["motivo"].str.strip()
    planilha["duvida"] = planilha["duvida"].fillna("").str.strip().str.lower().eq("sim")
    planilha.to_csv(GABARITO_CSV, index=False, encoding="utf-8")

    print(f"Gabarito salvo em {GABARITO_CSV} com {len(planilha)} avaliações.")
    print("\nDistribuição dos motivos:")
    print(planilha["motivo"].value_counts().to_string())
    print(f"\nLinhas marcadas como dúvida: {int(planilha['duvida'].sum())}")


if __name__ == "__main__":
    main()
