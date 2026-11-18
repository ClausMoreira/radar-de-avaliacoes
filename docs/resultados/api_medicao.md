# Medição da API do Radar

- Data: 16/11/2026, 15:01
- Fluxo: `automacao/fluxo_api.json`, publicado no n8n Cloud
- Script: `scripts/11_testar_api.py`
- Classificação: prompt `classificacao_v2`, modelo gemini-3.5-flash-lite, uma avaliação por chamada

## Acerto pela API

As 60 avaliações da validação às cegas, enviadas uma por vez, sem rascunho. O rótulo é o que demos à mão antes de qualquer comparação com o modelo.

| Medida | Resultado |
|---|---|
| Chamadas respondidas | 60 de 60 |
| Acerto geral | **58 de 60 (96,7%)**, intervalo de 95% de 88,6% a 99,1% |
| Acerto sem os elogios | 28 de 30 (93,3%) |
| Referência: mesma amostra, classificada em lotes de 25 pelo script 07 | 53 de 60 (88,3%); sem os elogios, 23 de 30 (76,7%) |
| Regra da avaliação crítica igual à do código | 60 de 60 |

## Tempo de resposta

| Medida | Resultado |
|---|---|
| Mediana | 1,4 s |
| Mais rápida | 0,9 s |
| Mais lenta | 6,0 s |
| Com rascunho (uma chamada) | 7,0 s |

O tempo inclui a ida e a volta pela internet a partir do computador do autor, em São Paulo.

## Conferências

| Conferência | Resultado |
|---|---|
| Pedido inválido (sem texto) | HTTP 400: Envie o campo "texto" com a avaliação. |
| Pedido inválido (texto vazio) | HTTP 400: Envie o campo "texto" com a avaliação. |
| Pedido inválido (nota 0) | HTTP 400: Envie o campo "nota" com um número inteiro de 1 a 5. |
| Pedido inválido (nota 3,5) | HTTP 400: Envie o campo "nota" com um número inteiro de 1 a 5. |
| Avaliação crítica com rascunho | HTTP 200; rascunho presente, com aviso de revisão |
| Aceita chamadas do navegador (CORS) | sim (Access-Control-Allow-Origin: https://radar-de-avaliacoes.vercel.app/) |

## Discordâncias com o rótulo

| Rótulo | Resposta da API | Quantidade |
|---|---|---|
| Atendimento e pós-venda | Atraso ou problema na entrega | 1 |
| Produto errado | Entrega incompleta | 1 |

## Exemplo de resposta com rascunho

```json
{
  "motivo": "nao_recebido",
  "motivo_nome": "Não recebido",
  "nota": 2,
  "critica": true,
  "precisa_de_rascunho": true,
  "rascunho": "Lamentamos muito pelo atraso na entrega do seu pedido e pedimos desculpas pelo transtorno causado. Já estamos verificando o status da sua encomenda junto à transportadora para entender o que ocorreu. Caso queira acrescentar alguma informação, sinta-se à vontade para nos contatar diretamente pelo nosso canal de atendimento. Agradecemos o seu contato e seguiremos acompanhando o seu caso.",
  "aviso": "Classificação e rascunho feitos por IA. O rascunho precisa de revisão e aprovação de uma pessoa antes de qualquer envio ao cliente.",
  "versao": {
    "prompt": "classificacao_v2",
    "modelo": "gemini-3.5-flash-lite"
  }
}
```

## O que esta medição não mostra

- É uma rodada só. A mesma avaliação pode receber outro motivo em outra rodada.
- A diferença para os 88,3% em lote pode vir da classificação uma a uma ou da variação entre rodadas. Com 60 avaliações, não dá para separar as duas.
- O tempo depende da carga da API gratuita do Gemini e do n8n Cloud no momento da medição.
- O fluxo roda no teste gratuito do n8n Cloud, que dura 14 dias. Depois disso, a API sai do ar, e esta medição fica como registro.
