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

## O que aprendemos

- **As duas entenderam para que serve o app.** A pessoa 2 identificou também o público: comerciantes e lojistas.
- **Com a pergunta clara, a prioridade número um foi identificada.** A pessoa 2 respondeu "produto não recebido", que é a primeira prioridade da tela. A resposta da pessoa 1 não mede isso, porque a pergunta era ambígua.
- **As duas acharam útil a resposta do agente.**
- **As duas sentiram falta de uma apresentação na primeira tela.** O título "O que resolver primeiro" aparecia sem dizer o que é o app.
- **O texto de "Pergunte ao Radar" estava técnico** para quem não conhece o projeto.
- **Uma resposta do agente demorou cerca de 2 minutos.**

## O que mudamos

| Retorno | Mudança | Arquivo |
|---|---|---|
| Falta de apresentação na primeira tela (2 de 2) | Uma linha de identificação acima do título: o que o Radar faz e para quem | `app/paginas/prioridades.py` |
| Texto técnico em "Pergunte ao Radar" (1 de 2) | Texto simples no topo. A explicação técnica foi para um bloco recolhido, "Como a resposta é feita" | `app/paginas/pergunte.py` |

## O que não mudamos, e por quê

- **Página inicial separada.** As três prioridades precisam aparecer sem nenhum clique, e uma Home colocaria um clique antes delas. A linha de identificação responde ao pedido sem esse custo.
- **Tempo de espera do agente.** Mantivemos como está e registramos como limitação. Não confirmamos a causa neste caso. A hipótese é que a API gratuita estava ocupada: quando isso acontece, o app espera e tenta de novo, e cada pergunta faz 2 ou 3 requisições.
- **Modo escuro.** Fica como sugestão para depois.

## O que este teste não mostra

- São duas pessoas, conhecidas do autor. Não são lojistas, e isto não é uma validação de mercado.
- A redação da pergunta 1 mudou entre as duas pessoas, então as respostas a ela não são comparáveis.
- Não cronometramos nenhuma resposta.
- As mudanças feitas a partir do retorno não foram testadas de novo com outras pessoas.
