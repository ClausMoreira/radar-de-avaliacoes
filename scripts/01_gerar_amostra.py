"""Passo 1: gera a planilha com as avaliações que serão rotuladas à mão.

Uso (na raiz do projeto, com o ambiente virtual ativo):
    python scripts/01_gerar_amostra.py

A planilha não mostra a nota em estrelas de propósito: o rótulo deve vir só
do texto, que é a mesma informação que o modelo vai receber.
"""

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from radar.config import (
    AMOSTRA_POR_NOTA, CATEGORIAS, PASTA_RAW, PLANILHA_ROTULAGEM, SEMENTE,
)
from radar.dados import carregar_avaliacoes, sortear_amostra

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


def main():
    tabela = carregar_avaliacoes(PASTA_RAW)
    amostra = sortear_amostra(tabela, AMOSTRA_POR_NOTA, SEMENTE)

    if PLANILHA_ROTULAGEM.exists():
        raise SystemExit(
            f"{PLANILHA_ROTULAGEM} já existe. Para não apagar rótulos prontos, "
            "renomeie ou remova o arquivo antes de gerar de novo."
        )
    PLANILHA_ROTULAGEM.parent.mkdir(parents=True, exist_ok=True)
    montar_planilha(amostra).save(PLANILHA_ROTULAGEM)

    print(f"Avaliações com texto válido: {len(tabela)}")
    print(f"Amostra sorteada: {len(amostra)} ({AMOSTRA_POR_NOTA} por nota, semente {SEMENTE})")
    print(f"Planilha criada em: {PLANILHA_ROTULAGEM}")


if __name__ == "__main__":
    main()
