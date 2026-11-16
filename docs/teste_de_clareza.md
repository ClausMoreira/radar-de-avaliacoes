# Teste de clareza

Respostas recebidas em 15/11/2026, de 2 pessoas que não conheciam o projeto: uma de fora da área de tecnologia e uma estudante iniciante da área. As duas são conhecidas do autor.

## Como fizemos

Enviamos o link do app por mensagem, sem nenhuma explicação, com quatro perguntas. As respostas vieram por escrito. As duas pessoas viram a mesma versão do app, anterior às mudanças descritas abaixo.

## Perguntas

1. Para a pessoa 1: "Assim que a página abrir, sem clicar em nada, me diz: qual é o problema número 1 que aparece?"
   Para a pessoa 2: "Assim que a página abrir, sem clicar em nada: segundo a página, qual é a reclamação mais frequente dos clientes da loja?"
2. "Com suas palavras: pra que serve isso e pra quem você acha que é?"
3. "Agora pode mexer à vontade. Abre o menu (o ícone no canto de cima, à esquerda), entra em 'Pergunte ao Radar' e clica em uma das perguntas prontas. A resposta te ajudou ou ficou confusa?"
4. "O que ficou mais confuso ou estranho na página toda?"

A pergunta 1 foi reescrita depois da primeira resposta. Na redação original, "problema" podia ser o problema da loja ou um problema da página, e a pessoa 1 entendeu do segundo jeito.

## Respostas

| Pergunta | Pessoa 1 (fora da área) | Pessoa 2 (estudante iniciante da área) |
|---|---|---|
| 1 | "O problema número 1 que aparece é que falta uma página inicial, ou Home, que contenha um título da aplicação e mais informações para identificar seu objetivo." | "A reclamação mais frequente dos clientes de loja é produto não recebido." |
| 2 | "O aplicativo parece ser um estudo de reclamações, feito para apoiar decisões e melhorias na operação de uma empresa ou entidade." | "Isso serve para ter um controle de avaliações, acredito que seja para comerciantes, lojistas e pessoas de varejo." |
| 3 | "Sim, a resposta foi informativa e útil no final ao sugerir uma ação para lidar com o problema apresentado na pergunta que escolhi." | "A resposta me ajudou, apenas uma observação pequena, fiquei esperando cerca de 2 minutos para obter a resposta, talvez isso poderia ser otimizado para diminuir o tempo de espera de quem está usando a ferramenta." |
| 4 | "Me deixou confusa a aba 'Pergunte ao Radar', pois o texto explicativo da seção é técnico e difícil de entender para quem não conhece a aplicação. Pode ser bom abstrair só as informações importantes pro usuário final." | "Acho que o que fica estranho é que a página já abre com 'O que resolver primeiro' sem nada prévio ou explicativo ou uma página home para apresentar a ferramenta e coisas assim." |

A pessoa 1 também sugeriu um modo escuro.

## Retorno livre de uma terceira pessoa

Uma terceira pessoa, também conhecida do autor, recebeu o mesmo link e respondeu no mesmo dia, mais tarde, em nove mensagens livres, sem seguir as quatro perguntas. Por isso o retorno dela não entra na tabela acima. Resumimos os pontos na ordem em que chegaram.

| Ponto | O que ela disse, em resumo |
|---|---|
| 1 | Falta uma página inicial que explique o contexto do sistema antes dos dados |
| 2 | A interface poderia ser mais simples para navegar entre os dados |
| 3 | Os gráficos poderiam ter dicas explicativas ao passar o mouse |
| 4 | O principal, nas palavras dela: "dar um contexto dos dados" que o app mostra |
| 5 | A IA poderia sugerir ações para cada ponto de falha e estimar quanto o indicador melhoraria e em quanto tempo, com dados simulados |
| 6 | Criar um histórico fictício do indicador, semana a semana, para ver a evolução |
| 7 e 8 | Com esse histórico, fazer um algoritmo preditivo da tendência do indicador na semana seguinte |
| 9 | Com o preditivo, criar gatilhos de ação conforme o resultado esperado |

## Retorno de uma quarta pessoa, pelo celular (16/11)

Em 16/11/2026, uma quarta pessoa abriu o link pelo celular e mandou três pontos livres, sem as quatro perguntas. Ela viu a versão com o bloco de contexto e a evolução mês a mês. Não registramos de que área ela é.

| Ponto | O que ela disse, em resumo |
|---|---|
| 1 | A página ainda precisa de um título que se explique sozinho, ou de uma página inicial dedicada |
| 2 | Sugestão: uma entrada animada ao abrir, como a tela de abertura de um aplicativo de celular |
| 3 | Às vezes há texto demais, e os textos poderiam explicar melhor, deixando de lado as informações mais técnicas |

## O que aprendemos

- **As duas entenderam para que serve o app.** A pessoa 2 identificou também o público: comerciantes e lojistas.
- **Com a pergunta clara, a prioridade número um foi identificada.** A pessoa 2 respondeu "produto não recebido", que é a primeira prioridade da tela. A resposta da pessoa 1 não mede isso, porque a pergunta era ambígua.
- **As duas acharam útil a resposta do agente.**
- **As duas sentiram falta de uma apresentação na primeira tela.** O título "O que resolver primeiro" aparecia sem dizer o que é o app.
- **O texto de "Pergunte ao Radar" estava técnico** para quem não conhece o projeto.
- **Uma resposta do agente demorou cerca de 2 minutos.**
- **Com o retorno livre, as três pessoas pediram contexto antes dos números.** A linha de identificação que tínhamos colocado não bastava: faltava dizer de onde vêm os dados e como ler a tela.
- **A terceira pessoa quis ver o indicador no tempo.** A tela mostrava só o retrato do período inteiro.
- **A linha de identificação e o bloco de contexto ainda não bastavam no celular.** A quarta pessoa viu os dois e mesmo assim pediu um título mais claro. Ela também achou a tela com texto demais, justamente depois de acrescentarmos o bloco de contexto que as três primeiras pediram.

## O que mudamos

| Retorno | Mudança | Arquivo |
|---|---|---|
| Falta de apresentação na primeira tela (2 de 2) | Uma linha de identificação acima do título: o que o Radar faz e para quem | `app/paginas/prioridades.py` |
| Texto técnico em "Pergunte ao Radar" (1 de 2) | Texto simples no topo. A explicação técnica foi para um bloco recolhido, "Como a resposta é feita" | `app/paginas/pergunte.py` |
| Contexto dos dados (retorno livre, pontos 1 e 4; com as duas primeiras respostas, 3 de 3) | Bloco de três linhas acima das prioridades: de onde vêm os dados, o que conta como reclamação e como ler os cartões | `app/paginas/prioridades.py` |
| Evolução do indicador no tempo (retorno livre, ponto 6) | Seção "Como cada prioridade evoluiu mês a mês", com as datas reais das avaliações: parte das reclamações do mês e quantidade. Meses com menos de 30 reclamações aparecem em cinza e ficam fora da linha | `src/radar/metricas.py`, `app/comum.py` e `app/paginas/prioridades.py` |
| Título que se explique sozinho (quarta pessoa, ponto 1) | O nome do app virou o título da página, com uma frase simples abaixo: "Descubra, pelo que os clientes escrevem, qual problema da loja priorizar". A seção das prioridades ganhou um título que diz o que está na tela: "As 3 dores mais citadas pelos clientes". O nome da aba do navegador também diz o objetivo | `app/app.py` e `app/paginas/prioridades.py` |
| Entrada animada (quarta pessoa, ponto 2) | Entrada de cerca de 1,4 segundo com o nome do app, uma vez por visita. É só CSS, e os dados carregam por baixo dela | `app/app.py` |
| Menos texto e menos termo técnico (quarta pessoa, ponto 3) | Na primeira tela, o bloco de contexto continua visível, com cerca de metade do texto: dados, quem aponta o motivo e o que o percentual mede. A explicação dos gráficos mês a mês ficou em uma linha, com o restante em um bloco recolhido, "Como ler estes gráficos". O cartão perdeu a linha sobre pedidos entregues depois do prazo, que continua na última seção da página | `app/paginas/prioridades.py` |

## O que não mudamos, e por quê

- **Página inicial separada.** As três prioridades precisam aparecer sem nenhum clique, e uma Home colocaria um clique antes delas. A linha de identificação responde ao pedido sem esse custo. A quarta pessoa repetiu o pedido como alternativa a um título melhor, e atendemos pelo título.
- **Tempo de espera do agente.** Mantivemos como está e registramos como limitação. Não confirmamos a causa neste caso. A hipótese é que a API gratuita estava ocupada: quando isso acontece, o app espera e tenta de novo, e cada pergunta faz 2 ou 3 requisições.
- **Modo escuro.** Fica como sugestão para depois.
- **Textos das outras páginas (quarta pessoa, ponto 3).** Revisamos só a primeira tela. "Como sabemos que funciona" é técnica de propósito, porque mostra as medições.
- **Histórico fictício, semana a semana (ponto 6).** Não usamos dado simulado em telas nem em medições. As avaliações têm data, então mostramos a evolução real. Ela é mensal, e não semanal, porque na amostra de 3.000 avaliações o volume por semana é pequeno demais: mesmo por mês, só de março de 2017 em diante há pelo menos 30 reclamações.
- **Preditivo e gatilhos (pontos 7 a 9).** Com 17 meses de volume suficiente, não conseguimos medir o acerto de uma previsão. O caminho é classificar a base inteira, montar a série semanal e medir o preditivo em semanas reservadas. Fica para depois.
- **Ações com estimativa de melhora (ponto 5).** O agente já sugere ações quando perguntado. Estimar quanto um indicador melhoraria, e em quanto tempo, seria um número sem base nos dados.
- **Dicas ao passar o mouse (ponto 3).** Os gráficos já mostram os valores quando o cursor passa por eles. No celular esse gesto não existe, e não sabemos em qual aparelho ela abriu o app.
- **Interface mais simples (ponto 2).** O pedido não aponta uma mudança concreta. Fica registrado.

## O que este teste não mostra

- São duas pessoas, conhecidas do autor. Não são lojistas, e isto não é uma validação de mercado.
- A redação da pergunta 1 mudou entre as duas pessoas, então as respostas a ela não são comparáveis.
- Não cronometramos nenhuma resposta.
- As mudanças feitas a partir do retorno não foram testadas de novo com outras pessoas.
- O retorno da terceira pessoa foi livre, sem as quatro perguntas, então não mede se ela identificou a prioridade número um. Não registramos qual versão do app ela viu (antes ou depois da linha de identificação) nem em qual aparelho.
- O retorno da quarta pessoa também foi livre. Ela abriu o app pelo celular, e não registramos de que área ela é.
- O bloco de contexto que as três primeiras pessoas pediram ficou mais curto, e a explicação longa dos gráficos ficou recolhida. Não testamos se a versão curta basta para quem queria mais contexto.
- Chegamos a recolher o bloco de contexto inteiro e voltamos atrás antes de publicar: recolhido, quem não toca nele não vê de onde vêm os dados nem que o motivo é apontado por IA.
- A entrada animada aparece depois do carregamento do próprio Streamlit, e não no lugar dele. Ela acrescenta cerca de 1,4 segundo até o conteúdo aparecer.
