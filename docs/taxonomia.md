# Taxonomia de motivos

Cada avaliação recebe **um** motivo principal. Esta página é o guia de rotulagem do gabarito e também a base das definições usadas nos prompts.

## Categorias

| Motivo | Quando usar | Exemplo típico |
|---|---|---|
| `nao_recebido` | O pedido não chegou até o momento da avaliação. | "Ainda não chegou o meu produto." |
| `entrega_incompleta` | Chegou só parte do pedido. | "Comprei 2 unidades e só recebi 1." |
| `produto_errado` | Chegou um produto diferente do comprado (modelo, cor, versão). | "Pedi azul e veio vermelho." |
| `defeito_ou_qualidade` | Defeito, dano, falsificação, qualidade inferior ou embalagem danificada. | "O relógio veio com defeito." |
| `atraso` | O pedido chegou, mas depois do prazo ou com demora. | "Chegou, mas demorou muito mais que o prometido." |
| `atendimento_e_pos_venda` | Troca, devolução, reembolso, cancelamento, nota fiscal, frete ou falta de resposta. | "Pedi a devolução e ninguém responde." |
| `elogio` | Cliente satisfeito, sem reclamação. | "Chegou antes do prazo, recomendo." |
| `outro` | Texto vago, pergunta ou sem informação suficiente. | "Gostaria de saber o que aconteceu." |

## Regras de decisão

1. **Mais de um problema:** vale o que aparece primeiro na ordem da tabela. A ordem coloca na frente o que impede o cliente de ter o produto certo em mãos.
2. **Elogio com reclamação:** vale a reclamação. `elogio` é só para quem não reclama de nada.
3. **"Não chegou" contra "atrasou":** se o cliente ainda não tem o produto, é `nao_recebido`. Se já recebeu e reclama da demora, é `atraso`.
4. **Rotule só pelo texto.** Não tente adivinhar o que o cliente quis dizer além do que escreveu. Na dúvida real, use `outro`.
5. **Dúvida:** se ficou entre duas categorias, escolha uma, marque `sim` na coluna `duvida` e escreva o porquê em `observacao`. Essas linhas viram material para a análise de erros.

## Observações sobre os dados

- Nomes de lojas foram anonimizados pela Olist com casas de Game of Thrones (por exemplo, "lannister", "targaryen", "baratheon"). Trate como "a loja".
- A planilha de rotulagem não mostra a nota em estrelas. O rótulo deve depender apenas do texto, que é o que o modelo também recebe.

## Histórico de mudanças

Registre aqui qualquer ajuste nas categorias ou regras, com data e motivo. Se a taxonomia mudar depois de iniciada a rotulagem, as linhas já rotuladas precisam ser revistas.

- 13/11/2026: primeira versão.
