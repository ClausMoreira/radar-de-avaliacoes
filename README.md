# Radar de Avaliações

> Projeto em construção. Esta página será atualizada com resultados medidos, demonstração e limitações.

Triagem de avaliações de clientes de marketplace com LLM: cada avaliação em texto livre recebe um motivo principal (por exemplo, pedido não recebido, produto errado, defeito), e o resultado é medido contra um gabarito rotulado à mão.

## Problema

O vendedor recebe muitas avaliações em texto livre. A nota em estrelas diz que o cliente está insatisfeito, mas não diz por quê. Ler uma a uma não escala.

## Estado atual

- [x] Leitura e limpeza dos dados, com atraso real de entrega calculado
- [x] Amostra estratificada para rotulagem manual
- [x] Gabarito de 150 avaliações rotuladas à mão ([taxonomia](docs/taxonomia.md) e [revisão](docs/revisao_gabarito.md))
- [x] Classificação com LLM e comparação de prompts
- [x] Painel com prioridades, exemplos reais e página de medição (`app/`)
- [ ] Automação no n8n: fluxo, script de envio e conferência prontos ([instruções](automacao/README.md)); falta rodar com as contas reais
- [x] Agente "Pergunte ao Radar": o modelo escolhe as consultas, os números vêm de `metricas.py` e cada resposta passa por uma conferência automática dos números

## Resultado atual

| Prompt | Acerto em 150 avaliações rotuladas à mão |
|---|---|
| v1 (só definições dos motivos) | 127 de 150 (84,7%) |
| v2 (definições e regras de decisão) | 137 de 150 (91,3%) |

O v2 foi escrito depois da análise de erros do v1 nas mesmas avaliações, então o número tende a ser otimista. Detalhes, revisão do gabarito e pontos em aberto em [docs/revisao_gabarito.md](docs/revisao_gabarito.md).

Para medir sem esse viés, fizemos uma **validação às cegas**: 60 avaliações sorteadas do painel, rotuladas à mão sem ver a resposta do modelo nem a nota.

| Validação às cegas (prompt v2) | Todas as avaliações | Só as que não são elogio |
|---|---|---|
| Acerto (número principal) | 53 de 60 (88,3%), intervalo de 95% de 77,8% a 94,2% | 23 de 30 (76,7%), intervalo de 95% de 59,1% a 88,2% |
| Teto após revisar as 7 discordâncias | 55 de 60 (91,7%) | 25 de 30 (83,3%) |

Os elogios são fáceis e puxam o acerto geral para cima. Como o painel ranqueia reclamações, o acerto sem os elogios é o que mais importa para ele. Resultado completo em [docs/resultados/validacao_cega.md](docs/resultados/validacao_cega.md) e revisão das discordâncias em [docs/resultados/validacao_cega_revisao.md](docs/resultados/validacao_cega_revisao.md).

## Como rodar

Requisitos: Python 3.10 ou superior.

```bash
python -m venv .venv
source .venv/Scripts/activate      # Windows (Git Bash). No Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Para as etapas que usam o Gemini, copie `.env.example` para `.env`, preencha `GEMINI_API_KEY` com uma chave do Google AI Studio e confira com `python scripts/00_testar_chave.py`.

Baixe o conjunto de dados da Olist (link abaixo) e copie para `data/raw/` os arquivos `olist_order_reviews_dataset.csv` e `olist_orders_dataset.csv`. Depois:

```bash
python scripts/01_gerar_amostra.py       # cria data/gabarito/amostra_para_rotular.xlsx
python scripts/02_validar_gabarito.py    # confere a rotulagem e salva data/gabarito/gabarito.csv
python scripts/03_medir_prompt.py v1     # mede o prompt v1 contra o gabarito (6 requisições)
```

Para classificar a amostra do painel e abrir o app no computador:

```bash
python scripts/04_classificar_amostra.py   # 3.000 avaliações, cerca de 120 requisições
python scripts/05_testar_agente.py         # perguntas de exemplo do agente, com conferência dos números
python scripts/06_gerar_validacao_cega.py  # planilha da validação às cegas (60 avaliações do painel)
python scripts/07_medir_validacao_cega.py  # compara os rótulos às cegas com o modelo (0 requisições)
python -m streamlit run app/app.py
```

Para a automação (instruções completas em [automacao/README.md](automacao/README.md)):

```bash
python scripts/08_enviar_avaliacoes_novas.py --nota 1   # envia 1 avaliação nova ao webhook do n8n
python scripts/09_conferir_automacao.py registro.csv   # confere o registro gravado pelo n8n (0 requisições)
```

As regras de rotulagem estão em [docs/taxonomia.md](docs/taxonomia.md). A organização do projeto e as decisões de desenho estão em [docs/arquitetura.md](docs/arquitetura.md).

## Dados

[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), com pedidos reais e anonimizados feitos entre 2016 e 2018. Os dados brutos não são versionados neste repositório.

## Estrutura

```
src/radar/     código reutilizável (configuração, dados, acesso ao Gemini, classificador, avaliação e métricas)
app/           app em Streamlit (só lê dados processados; todos os números vêm de src/radar/metricas.py)
prompts/       versões do prompt de classificação
scripts/       passos do projeto, numerados na ordem de execução
tests/         testes automatizados
automacao/     fluxo do n8n e instruções da automação
docs/          taxonomia, decisões e resultados das medições
data/          dados brutos (fora do Git), gabarito e dados processados para o app
```
