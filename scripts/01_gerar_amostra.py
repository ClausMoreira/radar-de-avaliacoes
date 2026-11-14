"""Passo 1: gera a planilha com as avaliações que serão rotuladas à mão.

Uso (na raiz do projeto, com o ambiente virtual ativo):
    python scripts/01_gerar_amostra.py

A planilha não mostra a nota em estrelas de propósito: o rótulo deve vir só
do texto, que é a mesma informação que o modelo vai receber.
"""

from radar.config import AMOSTRA_POR_NOTA, PASTA_RAW, PLANILHA_ROTULAGEM, SEMENTE
from radar.dados import carregar_avaliacoes, sortear_amostra
from radar.rotulagem import montar_planilha


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
