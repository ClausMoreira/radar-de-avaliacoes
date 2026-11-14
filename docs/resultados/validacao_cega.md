# Validação às cegas

- Data: 14/11/2026
- Classificação avaliada: prompt v2, modelo gemini-3.5-flash-lite
- Amostra: 60 avaliações sorteadas da amostra do painel, rotuladas à mão sem ver a resposta do modelo nem a nota
- Acerto: 53 de 60 (88,3%)
- Intervalo de 95% de confiança (Wilson): de 77,8% a 94,2%
- Sem as linhas marcadas como dúvida: 53 de 60 (88,3%)

Diferente do gabarito de 150 avaliações, estas avaliações não foram usadas para escrever nem para ajustar o prompt.

## Acerto por motivo

| motivo | total | acertos | acerto |
|---|---|---|---|
| nao_recebido | 9 | 8 | 88,9% |
| entrega_incompleta | 1 | 1 | 100,0% |
| produto_errado | 5 | 3 | 60,0% |
| defeito_ou_qualidade | 8 | 8 | 100,0% |
| atraso | 4 | 2 | 50,0% |
| atendimento_e_pos_venda | 3 | 1 | 33,3% |
| elogio | 30 | 30 | 100,0% |

Com poucas avaliações por motivo, os percentuais por motivo servem só como indicação.

## Erros

- Rótulo: `atendimento_e_pos_venda`. Modelo: `atraso`. Texto: "Não existe rastreamento da mercadoria, pois não há atualização da mesma. Quando houve foi 15 dias depois da última atualização, dizendo que, a mercadoria ainda não havia chegado na unidade SSA."
- Rótulo: `atraso`. Modelo: `elogio`. Texto: "Prazo de entrega um pouco longo, mas sem surpresas desagradáveis."
- Rótulo: `produto_errado`. Modelo: `entrega_incompleta`. Texto: "Comprei três tonners pretos. Entregaram dois pretos e um magenta. Para devolver eu preciso da nota fiscal que eles não enviaram e a chave de acesso para a nfe estava incorreta."
- Rótulo: `produto_errado`. Modelo: `entrega_incompleta`. Texto: "Comprei dois protetores de um modelo em uma mesma compra. Recebi modelos diferentes e em dias diferente e,diferente do modelo mostrado no site e ainda com nota fiscal de outro produto. Além do atraso"
- Rótulo: `atendimento_e_pos_venda`. Modelo: `nao_recebido`. Texto: "Recebí o produto apesar de ter feito o cancelamento tanto por e-mail quanto pelo site das lannister.com. Fiz o cancelamento antes da nota fiscal ser emitida mas não tive sucesso nem retorno."
- Rótulo: `nao_recebido`. Modelo: `atraso`. Texto: "O produto ainda não foi entregue e o prazo já está vencido desde o dia 06/03! Gostaria de uma atualização de vocês sobre está situação! Obrigado!"
- Rótulo: `atraso`. Modelo: `elogio`. Texto: "Houve um pequeno problema na entrega, mas foi resolvido e logo em seguida chegou."

## Trocas mais comuns (rótulo, modelo)

| gabarito | previsto | quantidade |
|---|---|---|
| atraso | elogio | 2 |
| produto_errado | entrega_incompleta | 2 |
| atendimento_e_pos_venda | atraso | 1 |
| atendimento_e_pos_venda | nao_recebido | 1 |
| nao_recebido | atraso | 1 |
