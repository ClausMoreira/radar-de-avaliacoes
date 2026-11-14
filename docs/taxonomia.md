# Taxonomia de motivos

Cada avaliação recebe **um** motivo principal. Esta página é o guia de rotulagem do gabarito. Cada versão do prompt traz as suas próprias definições em `prompts/`, para que uma versão já medida não mude quando esta página for atualizada.

## Categorias

A ordem da tabela é a ordem de prioridade.

| Motivo | Quando usar | Exemplo típico |
|---|---|---|
| `nao_recebido` | O cliente ainda não recebeu o pedido. Inclui extravio, roubo ou cancelamento antes da entrega. | "Ainda não chegou o meu produto." |
| `entrega_incompleta` | Chegou só parte do pedido: faltou item, quantidade, peça ou acessório que deveria acompanhar o produto. | "Comprei 2 unidades e só recebi 1." |
| `produto_errado` | Chegou um item diferente do comprado ou do anunciado (modelo, cor, tamanho, versão). | "Pedi azul e veio vermelho." |
| `defeito_ou_qualidade` | É o item certo, mas com defeito, dano, falsificação, qualidade inferior ou embalagem danificada. | "O relógio veio com defeito." |
| `atraso` | Atraso ou problema na entrega: chegou com demora ou houve falha no processo de entrega, da loja, da transportadora ou dos Correios. | "Chegou, mas demorou muito mais que o prometido." |
| `atendimento_e_pos_venda` | Troca, devolução, reembolso, cancelamento, nota fiscal, frete ou falta de resposta. | "Pedi a devolução e ninguém responde." |
| `elogio` | Cliente satisfeito, sem reclamação. | "Chegou antes do prazo, recomendo." |
| `outro` | Texto vago, pergunta, ou problema que não se encaixa nos motivos acima. | "Gostaria de saber o que aconteceu." |

## Regras de decisão

1. **Mais de um problema:** vale o que aparece primeiro na ordem da tabela. A ordem coloca na frente o que impede o cliente de ter o produto certo em mãos.
2. **Elogio com reclamação:** vale a reclamação. `elogio` é só para quem não reclama de nada.
3. **"Não chegou" contra "atrasou":** se o cliente ainda não tem o produto, é `nao_recebido`. Se já recebeu e reclama da demora, ou se o problema foi no processo de entrega, é `atraso`.
4. **Pelo que o cliente viveu, não por quem causou:** um problema causado pela transportadora ou pelos Correios é classificado como qualquer outro. Quem escolhe a forma de entrega é o lojista, então essa informação é útil para ele.
5. **Troca ou reembolso por causa de um problema:** se o cliente pede troca, devolução ou reembolso por causa de um problema do produto ou da entrega, vale o problema, e não `atendimento_e_pos_venda`.
6. **Diferente do anúncio:** se for outro item, é `produto_errado`. Se for o mesmo item abaixo do prometido, é `defeito_ou_qualidade`.
7. **Rotule só pelo texto.** Não tente adivinhar o que o cliente quis dizer além do que escreveu. Na dúvida real, use `outro`.
8. **Dúvida:** se ficou entre duas categorias, escolha uma, marque `sim` na coluna `duvida` e escreva o porquê em `observacao`. Essas linhas viram material para a análise de erros.

## Observações sobre os dados

- Nomes de lojas foram anonimizados pela Olist com casas de Game of Thrones (por exemplo, "lannister", "targaryen", "baratheon"). Trate como "a loja".
- A planilha de rotulagem não mostra a nota em estrelas. O rótulo deve depender apenas do texto, que é o que o modelo também recebe.

## Histórico de mudanças

Registre aqui qualquer ajuste nas categorias ou regras, com data e motivo. Se a taxonomia mudar depois de iniciada a rotulagem, as linhas já rotuladas precisam ser revistas.

- 13/11/2026: primeira versão.
- 14/11/2026, antes da rotulagem: dois casos combinados por escrito para a rotulagem, agora registrados aqui. Peça ou acessório faltando conta como `entrega_incompleta`. Produto diferente do anúncio segue a regra 6.
- 14/11/2026, depois da medição do prompt v1: `atraso` passa a incluir problema no processo de entrega (regra 4). Motivo: nas linhas de dúvida, problemas de entrega causados pelos Correios estavam indo para `outro`, o que esconderia do lojista um problema que ele pode resolver trocando a forma de entrega. A regra 5 deixa explícito um caso da regra 1. As linhas atingidas foram revistas (ver `docs/revisao_gabarito.md`).
