"""Passo 5: roda as perguntas de exemplo do agente com a API real e confere os números.

Uso (na raiz do projeto, com o ambiente virtual ativo):
    python scripts/05_testar_agente.py

Gasta de 2 a 4 requisições por pergunta, na cota do modelo do agente (separada
da cota da classificação). Para cada pergunta, mostra a resposta, as consultas
feitas e os números da resposta que não aparecem em nenhuma consulta.

Resultado salvo em docs/resultados/teste_agente_<versão da instrução>.md.
"""

import json
from datetime import date

from radar.agente import VERSAO_INSTRUCAO, criar_gemini_do_agente, numeros_sem_fonte, responder
from radar.config import CLASSIFICADAS_CSV, MODELO_AGENTE, PASTA_RESULTADOS
from radar.llm import ChaveAusente, ErroDaAPI
from radar.metricas import carregar

PERGUNTAS = [
    "Qual é o principal problema da loja e o que os clientes dizem sobre ele?",
    "Em quais categorias o defeito ou qualidade pesa mais?",
    "Escreva um rascunho de resposta para um cliente que ainda não recebeu o pedido.",
]


def main():
    tabela = carregar(CLASSIFICADAS_CSV)
    try:
        gemini = criar_gemini_do_agente()
    except ChaveAusente as erro:
        raise SystemExit(str(erro))

    partes = [
        f"# Teste do agente\n\n- Data: {date.today():%d/%m/%Y}\n- Modelo: {MODELO_AGENTE}\n"
        f"- Instrução: prompts/agente_{VERSAO_INSTRUCAO}.md\n"
    ]
    aprovadas = 0
    for numero, pergunta in enumerate(PERGUNTAS, start=1):
        print(f"\n=== Pergunta {numero}: {pergunta}")
        try:
            resposta = responder(pergunta, tabela, gemini)
        except ErroDaAPI as erro:
            raise SystemExit(f"A API recusou a requisição: {erro.code} {erro.message}")

        sem_fonte = numeros_sem_fonte(resposta.texto, resposta.consultas, pergunta)
        consultas = [f"{c['nome']}({json.dumps(c['argumentos'], ensure_ascii=False)})" for c in resposta.consultas]
        situacao = "todos os números vêm das consultas" if not sem_fonte else f"números sem fonte: {', '.join(sem_fonte)}"
        if resposta.consultas and not sem_fonte:
            aprovadas += 1

        print(resposta.texto)
        print(f"\nConsultas: {', '.join(consultas) or 'nenhuma'}")
        print(f"Requisições: {resposta.requisicoes}. Conferência: {situacao}.")

        partes.append(
            f"## {numero}. {pergunta}\n\n{resposta.texto}\n\n"
            f"- Consultas: {', '.join(f'`{c}`' for c in consultas) or 'nenhuma'}\n"
            f"- Requisições: {resposta.requisicoes}\n"
            f"- Conferência automática: {situacao}\n"
        )

    PASTA_RESULTADOS.mkdir(parents=True, exist_ok=True)
    arquivo = PASTA_RESULTADOS / f"teste_agente_{VERSAO_INSTRUCAO}.md"
    partes.append(
        f"\n**Resultado:** {aprovadas} de {len(PERGUNTAS)} respostas usaram consultas e não têm número sem fonte. "
        "A conferência automática verifica a origem dos números; a leitura humana confere se a resposta faz sentido.\n"
    )
    arquivo.write_text("\n".join(partes), encoding="utf-8")
    print(f"\n{aprovadas} de {len(PERGUNTAS)} aprovadas na conferência automática. Salvo em {arquivo}.")


if __name__ == "__main__":
    main()
