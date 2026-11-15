# Diário de aprendizado

O que aprendi, o que errei e o que mudaria.

## 13/11/2026

**Bloco: escolha do projeto e da trilha**

- O que aprendi: comparar o meu perfil com as duas trilhas antes de escolher. A AI Builder pede evidências de negócio (automação, painel, agente, produto em dias), e um único produto pode cobrir as cinco.
- O que errei: questionei se o Radar era o melhor projeto só depois de começar a montar a base. A reavaliação chegou à mesma escolha, mas custou tempo.
- O que mudaria: fechar a escolha do projeto, com os pontos fracos declarados, antes de escrever a primeira linha de código.

**Bloco: ambiente, arquitetura e dados**

- O que aprendi: os limites da camada gratuita do Gemini definem a arquitetura. Eles valem por projeto, e não por chave, e só os modelos Flash-Lite aguentam o volume. Por isso classificamos em lotes de 25 e deixamos um único arquivo falando com o Gemini.
- O que errei: os arquivos do início do projeto não estavam onde eu esperava, e o esqueleto teve que ser remontado. A primeira pasta ficava dentro de outro repositório Git.
- O que mudaria: definir o local da pasta e fazer o primeiro commit logo no início, para nada depender de arquivo baixado.

## 14/11/2026

**Bloco: gabarito (150 avaliações rotuladas à mão)**

- O que aprendi: um validador automático da planilha pega erros que o olho não vê. Ele encontrou uma linha com a observação da linha anterior colada no lugar do motivo.
- O que errei: rotulei algumas linhas contra a própria taxonomia escrita (cor diferente deveria ser produto errado), e problemas dos Correios foram para "outro" por falta de regra.
- O que mudaria: rotular umas 20 avaliações, revisar a taxonomia e só então seguir com as 150.

**Bloco: prompts v1 e v2**

- O que aprendi: analisar os erros um por um mostra o que falta. Os 26 erros do v1 apontaram a ausência de regras de desempate, como "se ainda não recebeu, não é atraso".
- O que errei: ajustei o v2 olhando os erros nas mesmas 150 avaliações, o que torna os 91,3% otimistas. A revisão do gabarito também foi feita olhando os erros, o que favorece o modelo.
- O que mudaria: separar desde o início uma amostra intocada para medir a versão final, como a validação às cegas fez depois.

**Bloco: app publicado**

- O que aprendi: um app com dados já processados é leve e barato de publicar, e a primeira tela precisa responder à pergunta do produto sem nenhum clique.
- O que errei: não sabia que o Streamlit só recarrega a pasta `app/`. Depois de mudar `src/radar/`, é preciso reiniciar o app.
- O que mudaria: colocar no README, desde o começo, um passo a passo de publicação com o reinício.

**Bloco: agente**

- O que aprendi: número nenhum deve vir do modelo. As ferramentas consultam os dados, a IA só redige, e uma conferência automática aponta qualquer número sem origem.
- O que errei: a resposta saía como "342 de 1.299 avaliações", quando 1.299 é o total de reclamações, porque os campos da ferramenta tinham nomes ambíguos. Tentei resolver pelo texto do prompt quando o problema estava nos nomes dos campos.
- O que mudaria: nomear os campos das ferramentas de forma explícita desde o início e parar de ajustar a redação mais cedo. A variação de frase entre rodadas é limitação, e não erro.

**Bloco: validação às cegas (60 avaliações)**

- O que aprendi: o número geral esconde onde o modelo erra. Foram 88,3% no geral, mas 76,7% só nas reclamações, porque os elogios são fáceis e inflam o resultado, e o painel depende das reclamações.
- O que errei: uma das 7 discordâncias era rótulo meu errado, e outra era ambígua. A régua humana também falha.
- O que mudaria: apresentar sempre o acerto separado por tipo, e não só o geral.

**Bloco: automação no n8n**

- O que aprendi: a regra de negócio (o que é crítico) deve ser código, e não decisão da IA. O registro vem antes do alerta, para nada se perder. O webhook tem dois endereços: o de teste, para uma chamada, e o de produção, que só funciona com o fluxo publicado.
- O que errei: o rascunho do primeiro teste já admitia culpa da loja ("por essa falha no atendimento"). Esperei mais casos em vez de olhar a regra do prompt que causava isso.
- O que mudaria: escrever o prompt de rascunho com uma regra explícita contra afirmar falha antes da verificação e testá-lo em algumas avaliações antes de ligar o fluxo.

**Bloco: teste cronometrado**

- O que aprendi: uma conferência escrita depois do teste pega o que a revisão rápida deixa passar. Nos 2 min 47 s, aprovei 5 rascunhos, e 4 deles afirmavam falha da loja.
- O que errei: revisei os rascunhos durante a chegada sem anotar nada. Verifiquei o formato da planilha de triagem só na hora do teste, e na triagem à mão prometi um reembolso que o prompt da automação proíbe.
- O que mudaria: usar uma lista curta de conferência para cada rascunho (afirma falha? promete algo? responde ao que o cliente disse?) e conferir os arquivos do teste antes de ligar o cronômetro.

## O que se repetiu

1. **Medir antes de acreditar.** Cada número otimista ganhou uma medição mais dura depois: o v2 ganhou a validação às cegas, e o tempo da automação ganhou a conferência dos rascunhos.
2. **A régua humana também erra.** Aconteceu no gabarito, na validação às cegas e na revisão rápida dos rascunhos.
3. **Regras fixas em código, IA onde ela foi medida.** Vale para os números do agente, para a regra da avaliação crítica e para a conferência do registro.

## Limites do Gemini (camada gratuita)

Lidos em 13/11/2026 no AI Studio (aistudio.google.com/rate-limit), para o projeto "Rating radar". Os limites valem para o projeto inteiro, não para cada chave, e a cota diária zera às 5h de Brasília.

| Modelo | Requisições por minuto | Tokens por minuto | Requisições por dia |
|---|---|---|---|
| Gemini 3.5 Flash Lite | 15 | 250 mil | 500 |
| Gemini 3.1 Flash Lite | 15 | 250 mil | 500 |
| Gemini 2.5 Flash Lite | 10 | 250 mil | 20 |
| Gemini 2.5 Flash, 3 Flash, 3.6 Flash, 3.8 Flash e 4 Hydrogen | 5 | 250 mil | 20 |
| Gemma 4 (26B e 31B) | 30 | 16 mil | 14,4 mil |
| Modelos Pro | 0 | 0 | 0 |

O que isso muda no projeto:

- Usamos só os modelos Flash-Lite 3.5 e 3.1. Os Flash comuns, com 20 requisições por dia, não sustentam nem a medição.
- Classificamos em lotes de 25 avaliações por requisição. Uma amostra de 3.000 avaliações custa cerca de 120 requisições.
- Cada chamada precisa ser contada. Por isso o acesso ao Gemini fica em um único arquivo (`src/radar/llm.py`).
