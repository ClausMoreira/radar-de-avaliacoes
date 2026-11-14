"""Passo 6: gera a planilha da validação às cegas.

Uso (na raiz do projeto, com o ambiente virtual ativo):
    python scripts/06_gerar_validacao_cega.py

Sorteia avaliações da amostra do painel, que o modelo já classificou, e monta
uma planilha só com o texto. A resposta do modelo e a nota em estrelas ficam
de fora: quem rotula não pode ser influenciado por elas.

Não gasta cota: as respostas do modelo já estão em data/processado/.
Depois de rotular, rode scripts/07_medir_validacao_cega.py.
"""

import pandas as pd

from radar.config import (
    CLASSIFICADAS_CSV, GABARITO_CSV, PLANILHA_VALIDACAO, SEMENTE_VALIDACAO, TAMANHO_VALIDACAO,
)
from radar.rotulagem import montar_planilha


def main():
    if PLANILHA_VALIDACAO.exists():
        raise SystemExit(
            f"{PLANILHA_VALIDACAO} já existe. Para não apagar rótulos prontos, "
            "renomeie ou remova o arquivo antes de gerar de novo."
        )
    painel = pd.read_csv(CLASSIFICADAS_CSV, dtype=str, keep_default_na=False)
    do_gabarito = set(pd.read_csv(GABARITO_CSV, usecols=["review_id"])["review_id"])
    if painel["review_id"].isin(do_gabarito).any():
        raise SystemExit("A amostra do painel contém avaliações do gabarito. Confira os dados processados.")

    # Sorteio simples, sem estratificar por nota: a validação mede o acerto
    # na mesma proporção de avaliações que o painel mostra.
    amostra = painel.sample(n=TAMANHO_VALIDACAO, random_state=SEMENTE_VALIDACAO)[["review_id", "texto"]]
    amostra = amostra.reset_index(drop=True)

    PLANILHA_VALIDACAO.parent.mkdir(parents=True, exist_ok=True)
    montar_planilha(amostra).save(PLANILHA_VALIDACAO)
    print(f"Planilha com {len(amostra)} avaliações (semente {SEMENTE_VALIDACAO}) criada em:")
    print(f"  {PLANILHA_VALIDACAO}")
    print("Rotule só pelo texto, com a taxonomia ao lado, sem consultar o app.")


if __name__ == "__main__":
    main()
