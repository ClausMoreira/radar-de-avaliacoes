# Diário de aprendizado

Três linhas por bloco de trabalho: o que aprendi, o que errei, o que mudaria.

## 13/11/2026

**Bloco: dados e gabarito**

- O que aprendi:
- O que errei:
- O que mudaria:

## Limites do Gemini (camada gratuita)

Lidos em 13/11/2026 no AI Studio (aistudio.google.com/rate-limit), para o projeto "Rating radar". Os limites valem para o projeto inteiro, não para cada chave, e a cota diária zera às 5h de Brasília.

| Modelo | Requisições por minuto | Tokens por minuto | Requisições por dia |
|---|---|---|---|
| Gemini 3.5 Flash Lite | 15 | 250 mil | 500 |
| Gemini 3.1 Flash Lite | 15 | 250 mil | 500 |
| Gemini 2.5 Flash Lite | 10 | 250 mil | 20 |
| Gemini 2.5 Flash, 3 Flash, 3.6 Flash, 3.8 Flash e 4 Hydrogen | 5 | 250 mil | 20 |
| Gemma 4 (26B e 31B) | 30 | 16 mil | 14,4 mil |
| Modelos Pro | 0 | 0 | 0 |

O que isso muda no projeto:

- Usamos só os modelos Flash-Lite 3.5 e 3.1. Os Flash comuns, com 20 requisições por dia, não sustentam nem a medição.
- Classificamos em lotes de 25 avaliações por requisição. Uma amostra de 3.000 avaliações custa cerca de 120 requisições.
- Cada chamada precisa ser contada. Por isso o acesso ao Gemini fica em um único arquivo (`src/radar/llm.py`).
