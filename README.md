# Radar de Avaliações

> Projeto em construção. Esta página será atualizada com resultados medidos, demonstração e limitações.

Triagem de avaliações de clientes de marketplace com LLM: cada avaliação em texto livre recebe um motivo principal (por exemplo, pedido não recebido, produto errado, defeito), e o resultado é medido contra um gabarito rotulado à mão.

## Problema

O vendedor recebe muitas avaliações em texto livre. A nota em estrelas diz que o cliente está insatisfeito, mas não diz por quê. Ler uma a uma não escala.

## Estado atual

- [x] Leitura e limpeza dos dados, com atraso real de entrega calculado
- [x] Amostra estratificada para rotulagem manual
- [ ] Gabarito de 150 avaliações
- [ ] Classificação com LLM e comparação de prompts
- [ ] Painel

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

As regras de rotulagem estão em [docs/taxonomia.md](docs/taxonomia.md). A organização do projeto e as decisões de desenho estão em [docs/arquitetura.md](docs/arquitetura.md).

## Dados

[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), com pedidos reais e anonimizados feitos entre 2016 e 2018. Os dados brutos não são versionados neste repositório.

## Estrutura

```
src/radar/     código reutilizável (configuração, dados, acesso ao Gemini, classificador e avaliação)
prompts/       versões do prompt de classificação
scripts/       passos do projeto, numerados na ordem de execução
tests/         testes automatizados
docs/          taxonomia, decisões e resultados das medições
data/          dados brutos (fora do Git) e gabarito
```
