"""Configuração central do projeto.

Tudo o que mais de um arquivo precisa saber (caminhos, categorias, parâmetros
da amostra) fica aqui, para existir em um único lugar.
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PASTA_RAW = RAIZ / "data" / "raw"
PASTA_GABARITO = RAIZ / "data" / "gabarito"
PASTA_CACHE = RAIZ / "data" / "cache"
PASTA_PROMPTS = RAIZ / "prompts"
PASTA_RESULTADOS = RAIZ / "docs" / "resultados"

ARQUIVO_AVALIACOES = "olist_order_reviews_dataset.csv"
ARQUIVO_PEDIDOS = "olist_orders_dataset.csv"

PLANILHA_ROTULAGEM = PASTA_GABARITO / "amostra_para_rotular.xlsx"
GABARITO_CSV = PASTA_GABARITO / "gabarito.csv"

# Motivo principal de cada avaliação. A ordem é a ordem de prioridade usada
# quando o cliente cita mais de um problema (ver docs/taxonomia.md).
CATEGORIAS = {
    "nao_recebido": "O pedido não chegou até o momento da avaliação.",
    "entrega_incompleta": "Chegou só parte do pedido (faltou item ou quantidade).",
    "produto_errado": "Chegou um produto diferente do comprado (modelo, cor, versão).",
    "defeito_ou_qualidade": "Produto com defeito, danificado, falsificado ou de qualidade inferior.",
    "atraso": "O pedido chegou, mas depois do prazo ou com demora.",
    "atendimento_e_pos_venda": "Troca, devolução, reembolso, cancelamento, nota fiscal, frete ou falta de resposta.",
    "elogio": "Cliente satisfeito, sem reclamação.",
    "outro": "Texto vago, pergunta ou sem informação suficiente para classificar.",
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
