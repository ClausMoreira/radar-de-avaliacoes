"""Configuração central do projeto.

Tudo o que mais de um arquivo precisa saber (caminhos, categorias, parâmetros
da amostra) fica aqui, para existir em um único lugar.
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PASTA_RAW = RAIZ / "data" / "raw"
PASTA_GABARITO = RAIZ / "data" / "gabarito"
PASTA_CACHE = RAIZ / "data" / "cache"
PASTA_PROCESSADO = RAIZ / "data" / "processado"
PASTA_PROMPTS = RAIZ / "prompts"
PASTA_RESULTADOS = RAIZ / "docs" / "resultados"

ARQUIVO_AVALIACOES = "olist_order_reviews_dataset.csv"
ARQUIVO_PEDIDOS = "olist_orders_dataset.csv"
ARQUIVO_ITENS = "olist_order_items_dataset.csv"
ARQUIVO_PRODUTOS = "olist_products_dataset.csv"

PLANILHA_ROTULAGEM = PASTA_GABARITO / "amostra_para_rotular.xlsx"
GABARITO_CSV = PASTA_GABARITO / "gabarito.csv"
CLASSIFICADAS_CSV = PASTA_PROCESSADO / "avaliacoes_classificadas.csv"
NOVAS_CSV = PASTA_PROCESSADO / "avaliacoes_novas.csv"

# Motivo principal de cada avaliação. A ordem é a ordem de prioridade usada
# quando o cliente cita mais de um problema (ver docs/taxonomia.md).
# Os prompts não leem estas definições: cada versão de prompt traz as suas,
# para que uma versão já medida não mude quando a taxonomia evoluir.
CATEGORIAS = {
    "nao_recebido": "O cliente ainda não recebeu o pedido (inclui extravio, roubo ou cancelamento antes da entrega).",
    "entrega_incompleta": "Chegou só parte do pedido (faltou item, quantidade, peça ou acessório).",
    "produto_errado": "Chegou um item diferente do comprado ou do anunciado (modelo, cor, tamanho, versão).",
    "defeito_ou_qualidade": "Produto com defeito, danificado, falsificado ou de qualidade inferior.",
    "atraso": "Atraso ou problema na entrega: chegou com demora ou houve falha no processo de entrega.",
    "atendimento_e_pos_venda": "Troca, devolução, reembolso, cancelamento, nota fiscal, frete ou falta de resposta.",
    "elogio": "Cliente satisfeito, sem reclamação.",
    "outro": "Texto vago, pergunta ou sem informação suficiente para classificar.",
}

# Nome curto de cada motivo para telas e relatórios.
NOMES_EXIBICAO = {
    "nao_recebido": "Não recebido",
    "entrega_incompleta": "Entrega incompleta",
    "produto_errado": "Produto errado",
    "defeito_ou_qualidade": "Defeito ou qualidade",
    "atraso": "Atraso ou problema na entrega",
    "atendimento_e_pos_venda": "Atendimento e pós-venda",
    "elogio": "Elogio",
    "outro": "Outro",
}

# Amostra para o gabarito: mesma quantidade por nota (1 a 5), para que as
# reclamações não fiquem escondidas atrás da maioria de avaliações 5 estrelas.
AMOSTRA_POR_NOTA = 30
TAMANHO_MINIMO_TEXTO = 20
SEMENTE = 42

# Gemini, camada gratuita. Limites lidos no AI Studio em 13/11/2026 para o
# nosso projeto: os modelos Flash-Lite 3.1 e 3.5 têm 15 requisições por
# minuto, 250 mil tokens por minuto e 500 requisições por dia, cada um.
# Os modelos Flash comuns têm só 20 requisições por dia, por isso ficam fora.
# A cota diária zera às 5h de Brasília (meia-noite no horário do Pacífico).
MODELOS_CANDIDATOS = ("3.5-flash-lite", "3.1-flash-lite")  # trechos do nome, em ordem de preferência

# Nomes confirmados pela chave do projeto em 13/11/2026 (scripts/00_testar_chave.py).
# Cada modelo tem a própria cota diária, então separamos os usos: as visitas ao
# app público não consomem a cota da classificação.
MODELO_CLASSIFICACAO = "gemini-3.5-flash-lite"
MODELO_AGENTE = "gemini-3.1-flash-lite"
LIMITE_REQUISICOES_POR_MINUTO = 15
LIMITE_REQUISICOES_POR_DIA = 500
AVALIACOES_POR_LOTE = 25

# Intervalo entre requisições para ficar abaixo do limite por minuto, com folga.
INTERVALO_ENTRE_REQUISICOES = 60 / LIMITE_REQUISICOES_POR_MINUTO + 0.5  # segundos
# Quando a API está ocupada ou o limite por minuto estoura, esperamos e
# tentamos de novo. Os tempos são as esperas antes de cada nova tentativa.
ESPERAS_APOS_ERRO = (20, 40)  # segundos

# Amostra do painel e avaliações reservadas para a automação.
# O painel usa avaliações até julho de 2018. As de agosto de 2018 (o último mês
# da base) ficam guardadas sem classificação e fazem o papel das avaliações
# novas que chegam na automação.
VERSAO_PROMPT_PRODUCAO = "v2"
AMOSTRA_PAINEL = 3000
DATA_CORTE_NOVAS = "2018-08-01"
QUANTIDADE_NOVAS = 200

# Agente no app: intervalo menor entre requisições, para a resposta não
# demorar. Se o limite por minuto estourar, a classe Gemini espera e tenta de
# novo. Cada visitante pode fazer algumas perguntas livres por sessão.
INTERVALO_AGENTE = 1.0  # segundos
PERGUNTAS_POR_SESSAO = 5

# Validação às cegas: avaliações sorteadas da amostra do painel e rotuladas à
# mão sem ver a resposta do modelo. Mede o acerto em dados que não foram usados
# para ajustar o prompt, na proporção real de avaliações que o painel mostra.
PASTA_VALIDACAO = RAIZ / "data" / "validacao"
PLANILHA_VALIDACAO = PASTA_VALIDACAO / "validacao_cega_para_rotular.xlsx"
VALIDACAO_CSV = PASTA_VALIDACAO / "validacao_cega.csv"
TAMANHO_VALIDACAO = 60
SEMENTE_VALIDACAO = 2026

# Automação (n8n). Regra da avaliação crítica: nota baixa e um motivo de
# reclamação identificado. É uma regra fixa, decidida por nós, e não pela IA.
# Medida na amostra do painel em 14/11/2026: 862 de 3.000 avaliações (28,7%).
# Reclamações com nota 3 ou mais (437) não geram alerta: ficam só no registro.
NOTA_MAXIMA_CRITICA = 2
# As avaliações novas são enviadas em uma ordem sorteada e fixa, para o teste
# cronometrado poder ser repetido com as mesmas avaliações.
SEMENTE_AUTOMACAO = 2026
QUANTIDADE_TESTE_AUTOMACAO = 20
# Cada avaliação nova gasta 1 requisição de classificação no n8n. Com 8
# segundos entre os envios, ficamos em 7 a 8 por minuto, metade do limite.
INTERVALO_ENTRE_ENVIOS = 8  # segundos
