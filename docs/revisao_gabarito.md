# Revisão do gabarito (14/11/2026)

O gabarito original, com 150 avaliações rotuladas à mão, está no commit `c372126`. O prompt v1 foi medido contra ele e acertou 124 de 150 (82,7%), resultado registrado no commit `6afb207`.

Depois dessa medição, revisamos 10 rótulos e a marcação de dúvida de algumas linhas. Este documento registra cada mudança e o motivo.

## Por que revisamos

Na análise dos 26 erros do v1, encontramos três situações:

1. **Linhas de dúvida.** A rotulagem marcou 8 linhas como dúvida para revisão posterior. Essa revisão já estava prevista antes da medição.
2. **Lacuna na taxonomia.** Problemas de entrega causados pelos Correios estavam sendo rotulados como `outro`. Decidimos classificar pelo que o cliente viveu, não por quem causou o problema, e ampliamos `atraso` para incluir falhas no processo de entrega (ver o histórico em `taxonomia.md`).
3. **Rótulos que contradiziam a taxonomia escrita.** Em alguns erros, o modelo seguiu a taxonomia e o rótulo não.

## Cuidado com o viés

As mudanças dos grupos 2 e 3 foram encontradas olhando os erros do modelo, e isso tende a favorecer o modelo. Por isso:

- mantemos o resultado original do v1 (82,7%) no histórico e o citamos ao lado dos novos;
- medimos o v1 de novo contra o gabarito revisado, para comparar v1 e v2 com a mesma régua;
- além dos erros, procuramos em todas as 150 linhas os casos atingidos pela regra nova. A linha 142 veio dessa busca. Nela, o v1 tinha acertado pelo rótulo antigo e passou a errar.

## Mudanças

A coluna "Linha" é a linha da planilha `amostra_para_rotular.xlsx` (a linha 1 é o cabeçalho).

| Linha | Texto (início) | Antes | Depois | Origem | Motivo |
|---|---|---|---|---|---|
| 2 | "Demorou muito pra ter uma resposta ou nota do produto..." | `atraso` | `atendimento_e_pos_venda` | Análise de erros | O produto chegou antes do prazo. A reclamação é sobre resposta e nota fiscal |
| 10 | "Não é que o produto seja ruim, é que achei que era menor..." | `defeito_ou_qualidade` | `outro` | Linha de dúvida | Não há defeito. É expectativa do cliente sobre o tamanho |
| 30 | "Recomendo a loja, porém, a entrega pelo Correios..." | `outro` | `atraso` | Linha de dúvida e regra nova | Falha no processo de entrega |
| 33 | "Recebi notificação dos Correios que o objeto foi roubado..." | `outro` | `nao_recebido` | Linha de dúvida | O cliente não recebeu o pedido, e esse motivo vem antes de atendimento |
| 52 | "a cor do fivela das sacolas deveriam ser azuis..." | `defeito_ou_qualidade` | `produto_errado` | Análise de erros | A taxonomia define cor diferente como `produto_errado` |
| 59 | "O jogo só é bonitinho, pois é extremamente fino e frágil..." | `elogio` | `defeito_ou_qualidade` | Análise de erros | Regra 2: elogio com reclamação vale a reclamação |
| 65 | "Tivemos que retirar nos correios, maior burocracia..." | `outro` | `atraso` | Linha de dúvida e regra nova | Falha no processo de entrega |
| 92 | "Não manda mais pelo correio..." | `outro` | `atraso` | Linha de dúvida e regra nova | Falha no processo de entrega |
| 126 | "Foi anunciada capa para moto z..." | `defeito_ou_qualidade` | `produto_errado` | Análise de erros | Regra 6: um item diferente do anunciado é `produto_errado` |
| 142 | "...na segunda houve problemas com erro de informação no rastreio." | `atendimento_e_pos_venda` | `atraso` | Busca pela regra nova | Falha no processo de entrega |

## Marcações de dúvida

| Linha | Mudança | Motivo |
|---|---|---|
| 10, 30, 33, 65, 92 | Dúvida retirada | A revisão ou a regra nova resolveu o caso |
| 123 | Dúvida marcada | "Não chega no prazo" não deixa claro se o produto chegou depois |
| 67, 104, 115 | Mantidas como `outro`, com dúvida | Textos vagos. Na linha 115, "tirar o frente" pode ser "frete", mas a regra 7 manda não adivinhar |

Resultado: o gabarito revisado tem 4 linhas de dúvida, contra 8 no original.

## Resultados com o gabarito revisado

Todas as medições abaixo usam o gabarito revisado (impressão digital `06427d2476`), exceto a primeira.

| Medição | Acerto geral | Sem as linhas de dúvida |
|---|---|---|
| v1, gabarito original | 124 de 150 (82,7%) | 122 de 142 (85,9%) |
| v1, gabarito revisado | 127 de 150 (84,7%) | 125 de 146 (85,6%) |
| v2, gabarito revisado | 137 de 150 (91,3%) | 135 de 146 (92,5%) |

Comparando v1 e v2 linha a linha, com o mesmo gabarito: o v2 acertou 13 avaliações que o v1 errava e errou 3 que o v1 acertava. As outras 10 continuam erradas nas duas versões.

O v2 foi escrito depois de olharmos os erros do v1 nessas mesmas 150 avaliações. Por isso, o 91,3% tende a ser otimista. A forma correta de confirmar o número é medir o v2 em avaliações novas, rotuladas sem olhar a resposta do modelo.

## Pontos em aberto (gabarito congelado)

Depois da medição do v2, o gabarito não muda mais. Duas das três linhas que o v2 passou a errar mostram ambiguidades da taxonomia. Registramos essas ambiguidades aqui, mas não corrigimos os rótulos, porque isso ajustaria o gabarito à resposta do v2:

- **Linha 45** ("Cancelou o meu pedido sem eu mesma saber..."): o rótulo é `atendimento_e_pos_venda` e o v2 respondeu `nao_recebido`. A definição nova de `nao_recebido` inclui "cancelamento antes da entrega", e a de `atendimento_e_pos_venda` também cita cancelamento. As duas definições se sobrepõem.
- **Linha 97** ("Tive problema no produto, mas... a loja já está efetuando a troca"): o rótulo é `atendimento_e_pos_venda` e o v2 respondeu `defeito_ou_qualidade`, seguindo a regra 5.

A terceira linha (108, "só queria que aumentasse meu limite") é erro do modelo: o texto é um elogio.
