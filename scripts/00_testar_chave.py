"""Passo 0: confere se a chave do Gemini funciona e quais modelos ela enxerga.

Uso (na raiz do projeto, com o ambiente virtual ativo):
    python scripts/00_testar_chave.py

Listar os modelos não gasta cota. O teste final gasta 1 requisição do dia.
A chave nunca é impressa.
"""

from radar.config import MODELOS_CANDIDATOS
from radar.llm import (
    ChaveAusente, ErroDaAPI, criar_cliente, escolher_modelo, gerar_texto, listar_modelos,
)


def main():
    try:
        cliente = criar_cliente()
    except ChaveAusente as erro:
        raise SystemExit(str(erro))

    try:
        nomes = listar_modelos(cliente)
    except ErroDaAPI as erro:
        raise SystemExit(f"A API recusou a chave ao listar os modelos: {erro.code} {erro.message}")

    print("Modelos Flash-Lite e Gemma disponíveis para esta chave:")
    for nome in nomes:
        if "flash-lite" in nome or "gemma" in nome:
            print(" -", nome)

    modelo = escolher_modelo(nomes, MODELOS_CANDIDATOS)
    if modelo is None:
        raise SystemExit(
            f"Nenhum modelo corresponde a {MODELOS_CANDIDATOS}. "
            "Envie a lista acima para ajustarmos a configuração."
        )

    print(f"\nModelo escolhido para o teste: {modelo}")
    try:
        texto = gerar_texto(cliente, modelo, "Responda apenas com a palavra: funcionando")
    except ErroDaAPI as erro:
        raise SystemExit(f"A requisição de teste falhou: {erro.code} {erro.message}")

    print("Resposta do modelo:", texto)
    print("\nChave funcionando. Este teste gastou 1 requisição da cota diária.")


if __name__ == "__main__":
    main()
