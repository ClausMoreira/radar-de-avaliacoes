# Teste cronometrado da automação

Feito em 14/11/2026, à noite, uma única vez, por uma pessoa (o autor do projeto).

## Como fizemos

Comparamos o tempo para tratar 20 avaliações novas à mão com o tempo para tratar outras 20 com a automação e revisão humana. Usamos dois conjuntos diferentes, sorteados da mesma forma, para a pessoa não rever avaliações que já tinha lido.

| | À mão (conjunto A) | Automação com revisão (conjunto B) |
|---|---|---|
| Avaliações | Posições 20 a 39 da ordem sorteada das avaliações reservadas (agosto de 2018) | Posições 0 a 19 da mesma ordem |
| Comando | `python scripts/08_enviar_avaliacoes_novas.py --quantidade 20 --inicio 20 --salvar triagem_manual.csv` | `python scripts/08_enviar_avaliacoes_novas.py --quantidade 20` |
| Tarefa | Ler, escolher o motivo, marcar se é crítica pela regra e escrever a resposta das críticas | Conferir o motivo dado pela IA, ler cada rascunho e mudar a situação para `aprovado` ou `recusado` |
| Início do cronômetro | Ao abrir a planilha | Ao rodar o comando de envio |
| Fim do cronômetro | Ao terminar a última linha | Ao revisar a última linha |
| Arquivo | `data/automacao/triagem_manual.xlsx` | `data/automacao/registro_teste_cronometrado.csv` |

Na triagem à mão, usamos uma planilha no mesmo padrão das rotulagens anteriores, com a lista dos oito motivos e a taxonomia aberta ao lado. Diferente do gabarito e da validação às cegas, a nota em estrelas aparecia, porque a regra da avaliação crítica depende dela e a automação também a recebe.

As duas medições foram feitas na mesma noite. A triagem à mão terminou por volta das 23h37 e o envio começou às 23h55. Entre as duas, conferimos os rótulos do conjunto A. Os conjuntos não têm avaliações em comum, então essa conferência não adiantou a leitura do conjunto B.

## Resultado

| | À mão | Automação com revisão humana |
|---|---|---|
| Tempo | **11 min 36 s** | **2 min 47 s** |
| Avaliações tratadas | 20 | 20 |
| Elogios | 13 | 10 |
| Críticas pela regra | 6 | 5 |
| Respostas às críticas | 5 de 6 escritas (uma ficou sem resposta, por dúvida sobre o que responder) | 5 de 5 rascunhos gerados e aprovados |
| Motivos discordados na revisão | Não se aplica | 0 |
| Rascunhos recusados na revisão | Não se aplica | 0 |

Como descrevemos: "Em teste cronometrado, feito uma vez por uma pessoa, com 20 avaliações em cada forma, a triagem levou 11 min 36 s à mão e 2 min 47 s com a automação e revisão humana."

## O que o número não mostra

1. **Boa parte do tempo da automação é espera.** O script envia uma avaliação a cada 8 segundos, por causa do limite por minuto da cota gratuita do Gemini. As 20 linhas chegaram à planilha entre 23h55min26s e 23h58min05s, e a revisão terminou 8 segundos depois da última. A pessoa revisou conforme as linhas chegavam. Não separamos o tempo de espera do tempo de trabalho.
2. **A revisão rápida deixou passar um problema nos rascunhos.** Os 5 rascunhos foram aprovados durante o teste. Na conferência posterior, 4 deles afirmam que houve falha da loja antes de qualquer verificação (avaliações 3bd61c84, 8186d9eb, a16297a5 e 863d79e1). No caso a16297a5, o próprio texto do cliente sugere que o aparelho pode ter sido ligado do jeito errado. Só o rascunho de ae413882 pede desculpas pelo transtorno sem afirmar a falha. É o mesmo padrão observado no primeiro teste com as contas reais. Parte da diferença de tempo, portanto, vem de uma revisão menos cuidadosa do que a escrita à mão.
3. **As respostas não seguiram as mesmas regras.** O prompt de rascunho proíbe prometer reembolso, troca ou prazo. Na triagem à mão, a resposta à avaliação 26a88078 promete o reembolso.
4. **Os conjuntos têm composições diferentes.** O conjunto A tem uma crítica a mais e três elogios a mais.
5. **É uma medição única.** Uma pessoa, uma vez, 20 avaliações em cada forma. Não convertemos o resultado em horas por mês, porque isso exigiria uma suposição de volume que não temos.

## Qualidade da classificação

**Conferência do registro pelo nosso código** (`scripts/09_conferir_automacao.py`, resumo em `automacao_conferencia.md`): 20 avaliações registradas, nenhuma repetida, todas entre as enviadas, regra da avaliação crítica aplicada igual à nossa em todas e rascunho presente nas 5 críticas. Nenhum problema encontrado.

**Uma avaliação por vez contra lote de 25:** o n8n chegou ao mesmo motivo que o classificador do projeto em 19 de 20 avaliações. A diferença foi na avaliação 7b98de6a, uma roupa que ficou pequena e já teve a troca pedida: o n8n deu atendimento e pós-venda, e o lote deu defeito ou qualidade. Pela regra 5 da taxonomia é um caso de fronteira, porque depende de o tamanho ser ou não um problema do produto. Com nota 5, a avaliação não é crítica em nenhuma das duas formas.

**Leitura nossa pela taxonomia, feita depois do teste.** Não é uma medição às cegas, e a mesma pessoa que fez a triagem participou da leitura.

- À mão: 18 de 20 rótulos sem ressalva e 2 de fronteira. Na dfc29ecc, um item de material diferente do esperado foi marcado como produto errado, mas o cliente compara com uma compra anterior, e não com o anúncio. Na 8f05d371, a mercadoria aguardava retirada nos Correios e foi marcada como não recebido, que é a leitura da regra 3, embora a regra 4 também se aplique.
- Automação: 19 de 20 sem ressalva e 1 de fronteira. Na 9857b937, um anúncio que sugeria dois itens quando era um foi marcado como produto errado. Pela regra 6, seria defeito ou qualidade.
- Nenhum dos casos de fronteira muda a marcação de crítica.

## Limitação registrada

O prompt de rascunho (`prompts/rascunho_v1.md`) manda pedir desculpas "quando houver falha da loja ou da entrega", e o modelo trata o relato do cliente como falha confirmada. Decidimos registrar como limitação e não alterar o prompt antes do envio da candidatura. O próximo passo é um `rascunho_v2` que reconheça o relato sem afirmar a falha, avaliado em avaliações críticas diferentes destas 5, para não ajustar o prompt aos casos em que o problema foi visto.
