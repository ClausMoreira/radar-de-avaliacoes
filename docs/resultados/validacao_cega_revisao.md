# Revisão das discordâncias da validação às cegas (14/11/2026)

A validação às cegas (`validacao_cega.md`) mede a concordância entre os nossos rótulos e o modelo. Quando os dois discordam, o erro pode ser do modelo ou do rótulo. Para separar os dois casos, revisamos as 7 discordâncias, uma a uma, aplicando as regras escritas em `docs/taxonomia.md`.

## Regras da revisão

- Revisamos só as discordâncias. Como os 53 casos de concordância não foram revistos, a revisão só pode aumentar o acerto. Por isso o resultado revisado é um **teto**, e o número principal continua sendo o original.
- Os rótulos de `data/validacao/validacao_cega.csv` não foram alterados. Esta revisão é um registro à parte.
- Cada caso recebeu uma de três decisões: o modelo errou, o rótulo estava errado ou o caso é ambíguo.
- Estas 60 avaliações não são usadas para ajustar o prompt. Um futuro prompt v3 de classificação precisará de outra amostra às cegas.

## Decisões

A coluna "Linha" é a linha da planilha `validacao_cega_para_rotular.xlsx` (a linha 1 é o cabeçalho).

| Linha | Texto (início) | Rótulo | Modelo | Decisão | Motivo |
|---|---|---|---|---|---|
| 25 | "Prazo de entrega um pouco longo, mas sem surpresas desagradáveis." | `atraso` | `elogio` | Modelo errou | Regra 2: havendo reclamação, ela vence o elogio |
| 56 | "Houve um pequeno problema na entrega, mas foi resolvido..." | `atraso` | `elogio` | Modelo errou | Regra 2, como na linha 25 |
| 50 | "Recebi o produto apesar de ter feito o cancelamento..." | `atendimento_e_pos_venda` | `nao_recebido` | Modelo errou | O cliente recebeu o produto, então não é `nao_recebido` |
| 53 | "O produto ainda não foi entregue e o prazo já está vencido..." | `nao_recebido` | `atraso` | Modelo errou | Regra 3: se o cliente ainda não tem o produto, é `nao_recebido` |
| 41 | "Comprei dois protetores de um modelo... Recebi modelos diferentes..." | `produto_errado` | `entrega_incompleta` | Modelo errou | Não faltou item: vieram itens diferentes do comprado |
| 32 | "Comprei três tonners pretos. Entregaram dois pretos e um magenta..." | `produto_errado` | `entrega_incompleta` | Ambíguo | Veio um item trocado (`produto_errado`), mas também faltou um dos pretos (`entrega_incompleta`, que tem prioridade pela regra 1) |
| 13 | "Não existe rastreamento da mercadoria... ainda não havia chegado na unidade..." | `atendimento_e_pos_venda` | `atraso` | Rótulo errado | Pela regra 4, problema de rastreio é `atraso`. Se o cliente ainda não recebeu, seria `nao_recebido`. `atendimento_e_pos_venda` não se encaixa em nenhuma das duas leituras |

## Resultado

| Medida | Todas as avaliações | Só as que não são elogio |
|---|---|---|
| Às cegas, sem revisão (número principal) | 53 de 60 (88,3%) | 23 de 30 (76,7%) |
| Teto, contando o rótulo errado e o ambíguo como acerto | 55 de 60 (91,7%) | 25 de 30 (83,3%) |

## O que aprendemos com os erros do modelo

Os 5 erros confirmados têm dois padrões:

1. **Reclamação leve vira elogio** (linhas 25 e 56). Quando o cliente reclama de leve e em seguida diz que ficou tudo bem, o modelo ignora a reclamação. Isso faz o painel subestimar problemas de entrega.
2. **"Não chegou", "atrasou" e "pós-venda" ainda se confundem** (linhas 50, 53 e 41). É o mesmo tipo de erro que motivou o prompt v2. Ele diminuiu, mas não desapareceu.

São os pontos a tratar num futuro prompt v3, que deve ser medido com uma nova amostra às cegas.
