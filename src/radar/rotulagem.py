"""Planilhas de rotulagem à mão: montagem e validação.

Usado pelo gabarito (scripts 01 e 02) e pela validação às cegas (scripts 06
e 07), para que as duas rotulagens sigam exatamente as mesmas regras.
A planilha não mostra a nota em estrelas nem a resposta do modelo: o rótulo
deve vir só do texto.
"""

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from radar.config import CATEGORIAS

CABECALHO = ["review_id", "texto", "motivo", "duvida", "observacao"]
LARGURAS = {"A": 14, "B": 90, "C": 26, "D": 10, "E": 40}


def montar_planilha(amostra):
    wb = Workbook()

    # Aba 1: rotulagem
    aba = wb.active
    aba.title = "rotular"
    aba.append(CABECALHO)
    for linha in amostra.itertuples():
        aba.append([linha.review_id, linha.texto, None, None, None])

    negrito = Font(bold=True)
    fundo = PatternFill("solid", fgColor="E5E7EB")
    for celula in aba[1]:
        celula.font = negrito
        celula.fill = fundo
    for coluna, largura in LARGURAS.items():
        aba.column_dimensions[coluna].width = largura
    for linha in aba.iter_rows(min_row=2):
        for celula in linha:
            celula.alignment = Alignment(wrap_text=True, vertical="top")
    aba.freeze_panes = "A2"

    ultima = len(amostra) + 1
    lista_motivos = DataValidation(
        type="list", formula1=f"=categorias!$A$2:$A${len(CATEGORIAS) + 1}", allow_blank=True
    )
    lista_motivos.error = "Escolha um motivo da lista."
    lista_motivos.showErrorMessage = True
    lista_duvida = DataValidation(type="list", formula1='"sim"', allow_blank=True)
    aba.add_data_validation(lista_motivos)
    aba.add_data_validation(lista_duvida)
    lista_motivos.add(f"C2:C{ultima}")
    lista_duvida.add(f"D2:D{ultima}")

    # Aba 2: categorias e definições (alimenta a lista suspensa)
    aba_cat = wb.create_sheet("categorias")
    aba_cat.append(["motivo", "definicao"])
    for nome, definicao in CATEGORIAS.items():
        aba_cat.append([nome, definicao])
    for celula in aba_cat[1]:
        celula.font = negrito
        celula.fill = fundo
    aba_cat.column_dimensions["A"].width = 28
    aba_cat.column_dimensions["B"].width = 95

    return wb


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
