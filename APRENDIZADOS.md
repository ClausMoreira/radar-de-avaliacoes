# Aprendizados

Este é o diário de bordo do Radar: o que deu certo, o que deu errado e o que eu faria diferente. Os números otimistas ficam aqui junto com as medições que os colocaram no lugar.

## 13/11

### Escolha do projeto

- **Aprendi:** começar pelo problema, e não pela tecnologia. Com uma dor bem delimitada (o lojista que não sabe por onde começar), um único produto conseguiu reunir painel, agente e automação sem virar uma colcha de retalhos.
- **Errei:** só questionei se o Radar era o melhor projeto depois de já estar montando a base. A reavaliação chegou à mesma escolha, mas o tempo foi embora.
- **Faria diferente:** fechar a escolha antes da primeira linha de código, já com os pontos fracos escritos.

### Ambiente, arquitetura e dados

- **Aprendi:** quem desenha a arquitetura, no fim das contas, são os limites da camada gratuita do Gemini. Eles valem por projeto (e não por chave), e só os modelos Flash-Lite aguentam o volume. Daí a classificação em lotes de 25 e um único arquivo conversando com o Gemini.
- **Errei:** os arquivos iniciais não estavam onde eu achava que estariam (em Downloads), e precisei remontar o esqueleto. Para completar, a primeira pasta ficava dentro de outro repositório Git (ProjetosVSC).
- **Faria diferente:** definir o lugar da pasta e fazer o primeiro commit logo de cara, para nada depender de arquivo baixado.

## 14/11

### Gabarito (150 avaliações rotuladas à mão)

- **Aprendi:** um validador automático da planilha enxerga o que o olho deixa passar. Foi ele que achou a linha 93 com a observação da linha 92 colada no lugar do motivo.
- **Errei:** rotulei algumas linhas contrariando a minha própria taxonomia (cor diferente deveria ser "produto errado"), e problemas dos Correios caíram em "outro" porque não havia regra para eles.
- **Faria diferente:** rotular umas 20, revisar a taxonomia e só então encarar as 150.

### Prompts v1 e v2

- **Aprendi:** olhar os erros um por um ensina mais do que olhar a porcentagem. Os 26 erros do v1 mostraram que faltavam regras de desempate, como "se ainda não recebeu, não é atraso".
- **Errei:** ajustei o v2 olhando os erros nas mesmas 150 avaliações, então os 91,3% são otimistas. E revisei o gabarito também olhando os erros, o que puxa a balança para o lado do modelo.
- **Faria diferente:** separar desde o primeiro dia uma amostra intocada para medir a versão final, que foi exatamente o papel da validação às cegas depois.

### App publicado

- **Aprendi:** com os dados já processados, o app fica leve e barato de publicar. E a primeira tela precisa responder à pergunta do produto sem pedir nenhum clique.
- **Errei:** não sabia que o Streamlit só recarrega a pasta `app/`. Mexeu em `src/radar/`? Tem que reiniciar o app.
- **Faria diferente:** deixar no README, desde o começo, um passo a passo de publicação que inclua o reinício.

### Agente

- **Aprendi:** nenhum número deve sair da cabeça do modelo. As ferramentas consultam os dados, a IA só redige, e uma conferência automática denuncia qualquer número sem origem.
- **Errei:** as respostas saíam como "342 de 1.299 avaliações" porque os campos da ferramenta tinham nomes ambíguos. Passei um tempo brigando com o texto do prompt quando o problema estava nos nomes dos campos.
- **Faria diferente:** nomear os campos de forma explícita desde o início e parar de polir a redação mais cedo. Frase que muda de uma rodada para outra é limitação, não erro.

### Validação às cegas (60 avaliações)

- **Aprendi:** o número geral esconde onde o modelo erra. Deu 88,3% no geral, mas 76,7% só nas reclamações. Elogio é fácil de acertar e infla o resultado, e é das reclamações que o painel depende.
- **Errei:** dos 7 desacordos, um era rótulo meu errado e outro era ambíguo. A régua humana também falha.
- **Faria diferente:** mostrar sempre o acerto separado por tipo, nunca só o geral.

### Automação no n8n

- **Aprendi:** regra de negócio (o que conta como crítico) é código, não decisão da IA. O registro vem antes do alerta, para nada se perder. E o webhook tem dois endereços: o de teste, que vale para uma chamada, e o de produção, que só funciona com o fluxo publicado.
- **Errei:** já no primeiro teste, o rascunho admitia culpa da loja ("por essa falha no atendimento"). Em vez de ir direto na regra do prompt que causava isso, esperei aparecerem mais casos.
- **Faria diferente:** escrever o prompt do rascunho com uma regra explícita proibindo afirmar falha antes da verificação, e testá-lo em algumas avaliações antes de ligar o fluxo.

### Teste cronometrado (noite de 14/11)

- **Aprendi:** uma conferência por escrito depois do teste pega o que a revisão rápida deixa passar. Em 2 min 47 s aprovei 5 rascunhos, e 4 deles afirmavam falha da loja.
- **Errei:** revisei os rascunhos conforme chegavam, sem anotar nada. Só conferi o formato da planilha de triagem na hora do teste, e na triagem à mão prometi um reembolso que o próprio prompt da automação proíbe.
- **Faria diferente:** usar uma checklist curta para cada rascunho (afirma falha? promete algo? responde ao que o cliente disse?) e conferir os arquivos antes de disparar o cronômetro.

## O que se repete

1. **Medir antes de acreditar.** Todo número otimista acabou ganhando uma medição mais dura depois: o v2 ganhou a validação às cegas, e o tempo da automação ganhou a conferência dos rascunhos.
2. **A régua humana também erra.** Aconteceu no gabarito, na validação às cegas e na revisão rápida.
3. **Regra fixa em código, IA onde ela foi medida.** Vale para os números do agente, para a regra de avaliação crítica e para a conferência do registro.
