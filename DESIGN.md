---
name: Thalia
description: A central da assistente local do Péricles, no escuro quente da direção "B · Orbe".
colors:
  fundo: "#0E0D0C"
  superficie: "#141210"
  coluna: "#131110"
  cartao: "#1B1916"
  botao: "#26221D"
  sobre: "#17140F"
  borda: "#221F1B"
  borda-2: "#2A2622"
  borda-3: "#3A342E"
  texto: "#F2EDE4"
  texto-2: "#B3AA9E"
  texto-3: "#8F877C"
  laranja: "#F4A259"
  laranja-claro: "#FFC487"
  orbe-luz: "#FFE6C2"
  orbe-quente: "#D9634E"
  orbe-fundo: "#5A2632"
  fazendo: "#C27A2E"
  feito: "#2FA58A"
  atencao: "#B86AD0"
  atencao-texto: "#D9B3E8"
  papel: "#E9E0CE"
  papel-2: "#DDD2BD"
  tinta: "#2A231B"
  tinta-2: "#665847"
  fio-papel: "#D3C6AE"
  brasa-papel: "#9A4A12"
  papel-azul: "#0F1B2D"
  papel-azul-2: "#1A2A42"
  tinta-azul: "#D6DCE4"
  tinta-azul-2: "#93A3B8"
  fio-azul: "#2A3D59"
typography:
  display:
    fontFamily: "Instrument Serif, Georgia, serif"
    fontSize: "clamp(34px, 4vw, 46px)"
    fontWeight: 400
    lineHeight: 1.05
  headline:
    fontFamily: "Instrument Serif, Georgia, serif"
    fontSize: "30px"
    fontWeight: 400
    lineHeight: 1.1
  numeral:
    fontFamily: "Instrument Serif, Georgia, serif"
    fontSize: "34px"
    fontWeight: 400
    lineHeight: 1.1
  wordmark:
    fontFamily: "Instrument Serif, Georgia, serif"
    fontSize: "26px"
    fontWeight: 400
    lineHeight: 1
  title:
    fontFamily: "Manrope, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 700
    lineHeight: 1.4
  body:
    fontFamily: "Manrope, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 500
    lineHeight: 1.5
  small:
    fontFamily: "Manrope, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 500
    lineHeight: 1.45
  label:
    fontFamily: "Manrope, system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 600
    lineHeight: 1.3
    fontFeature: "tnum"
  answer:
    fontFamily: "Instrument Serif, Georgia, serif"
    fontSize: "clamp(26px, 3.2vw, 36px)"
    fontWeight: 400
    lineHeight: 1.25
  quote:
    fontFamily: "Manrope, system-ui, sans-serif"
    fontSize: "19px"
    fontWeight: 500
    lineHeight: 1.4
  lead:
    fontFamily: "Manrope, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 500
    lineHeight: 1.5
  leitura:
    fontFamily: "Literata, Georgia, serif"
    fontSize: "19px"
    fontWeight: 400
    lineHeight: 1.72
rounded:
  sm: "6px"
  md: "8px"
  lg: "12px"
  xl: "16px"
  pill: "22px"
  campo: "28px"
spacing:
  xs: "6px"
  sm: "8px"
  md: "10px"
  lg: "14px"
  xl: "16px"
  2xl: "20px"
  3xl: "28px"
components:
  botao-avancar:
    backgroundColor: "transparent"
    textColor: "{colors.texto-2}"
    rounded: "{rounded.md}"
    padding: "0 10px"
    height: "32px"
    typography: "{typography.label}"
  botao-avancar-ativo:
    backgroundColor: "{colors.botao}"
    textColor: "{colors.texto}"
    rounded: "{rounded.md}"
  chip-filtro:
    backgroundColor: "transparent"
    textColor: "{colors.texto-2}"
    rounded: "{rounded.pill}"
    padding: "0 14px"
    height: "36px"
  chip-filtro-ligado:
    backgroundColor: "{colors.texto}"
    textColor: "{colors.fundo}"
    rounded: "{rounded.pill}"
  chip-acao:
    backgroundColor: "transparent"
    textColor: "{colors.laranja}"
    rounded: "{rounded.pill}"
    height: "36px"
  campo-busca:
    backgroundColor: "{colors.cartao}"
    textColor: "{colors.texto}"
    rounded: "{rounded.pill}"
    padding: "0 16px"
    height: "44px"
  cartao-tarefa:
    backgroundColor: "{colors.cartao}"
    textColor: "{colors.texto}"
    rounded: "{rounded.lg}"
    padding: "14px 14px 12px"
  bloco-faixa:
    backgroundColor: "{colors.superficie}"
    textColor: "{colors.texto}"
    rounded: "{rounded.xl}"
    padding: "{spacing.2xl}"
  coluna-quadro:
    backgroundColor: "{colors.coluna}"
    rounded: "{rounded.xl}"
    padding: "{spacing.lg}"
  etiqueta-frente:
    backgroundColor: "{colors.botao}"
    textColor: "{colors.texto}"
    rounded: "{rounded.sm}"
    padding: "3px 8px"
    typography: "{typography.label}"
  recado:
    backgroundColor: "{colors.botao}"
    textColor: "{colors.texto}"
    rounded: "14px"
    padding: "8px 8px 8px 16px"
  campo-conversa:
    backgroundColor: "{colors.cartao}"
    textColor: "{colors.texto}"
    rounded: "{rounded.campo}"
    padding: "0 6px 0 24px"
    height: "56px"
---

<!-- Escrito em 22/10/2026 a partir do código da central (src/thalia/web/central.css). Os tokens são os do CSS. Os nomes descritivos e o North Star são uma proposta deduzida do PRODUCT.md e do esboço "B · Orbe": o Péricles ainda não revisou essa linguagem. -->

# Design System: Thalia

## Overview

**Creative North Star: "A Brasa Acesa"**

A Thalia mora num notebook que fica ligado o tempo todo, e a central se comporta como uma brasa numa sala escura: um ponto quente e vivo (o orbe que respira) sobre superfícies quase pretas, também quentes. Nada brilha à toa. O laranja aparece onde há vida ou ação, e o resto da tela se recolhe em degraus de marrom-escuro para o texto aparecer.

É uma tela de uso diário, densa e calma ao mesmo tempo. A voz dela vem da serifa: a saudação, os títulos de seção e a data grande da próxima edição falam em Instrument Serif. O trabalho em si (cartões, filtros, botões, estados) fala em Manrope, firme e legível. A interface explica o que dá para fazer nela em texto corrido, e não em tooltip.

A idade da informação faz parte do visual. Dado velho aparece como velho: em roxo, com o número de dias escrito ao lado.

**Key Characteristics:**
- Escuro quente: o fundo é #0E0D0C, e não preto puro; o texto é marfim, e não branco.
- Um acento só, o laranja do orbe, guardado para identidade e ação.
- Profundidade por degraus de tom; sombra só no que flutua.
- Serifa para a voz da Thalia, sans para o trabalho.
- Cada estado se diz em texto, além da cor.

## Colors

Uma paleta de brasa: degraus de marrom quase preto, um laranja vivo e três cores de estado, cada uma com uma tarefa só.

### Primary
- **Laranja Brasa** (laranja): o acento único. Aparece no orbe e no pontinho da dica, nas barras de uso das skills, no anel de foco, no cursor dos campos, no "+ Nova", no "Desfazer" e na borda da coluna que recebe um cartão arrastado.
- **Laranja Claro** (laranja-claro): o hover do laranja, nas barras e nos botões de texto laranja.

### Tertiary
- **Âmbar de Andamento** (fazendo): o ponto da coluna Fazendo.
- **Verde Concluído** (feito): o ponto da coluna Feito e os itens do notebook que estão certos.
- **Roxo de Atenção** (atencao) e **Lilás de Atenção** (atencao-texto): o que pede atenção. O roxo vai nos pontos e nas bordas; o lilás, no texto ("parado há 49 dias", "sem criptografia", mensagens de erro).

### Neutral
- **Noite** (fundo): o fundo da página e o texto do chip ligado.
- **Fuligem** (superficie): o topo e os blocos da faixa.
- **Carvão** (coluna): o fundo das colunas do quadro.
- **Carvão Claro** (cartao): os cartões, o campo de busca e os campos de formulário.
- **Cinza Quente** (botao): os botões cheios, as etiquetas de frente e o recado.
- **Sombra de Destino** (sobre): o fundo da coluna enquanto um cartão passa sobre ela.
- **Fios** (borda, borda-2, borda-3): três degraus de borda, do separador discreto à borda de hover.
- **Marfim** (texto), **Areia** (texto-2) e **Pedra** (texto-3): os três níveis de texto. A Pedra é o mínimo de contraste e só vai sobre Noite, Fuligem, Carvão e Carvão Claro.
- **Orbe** (orbe-luz, orbe-quente, orbe-fundo): só no gradiente do orbe e do pontinho.

### Named Rules
**The Brasa Única Rule.** O laranja é o único acento e nunca indica estado. Se algo precisa dizer "em andamento", "feito" ou "atenção", usa a cor de estado correspondente.

**The Roxo é Idade Rule.** O roxo significa "precisa de atenção": dado velho, item com problema ou erro. Não decora nada.

## Typography

**Display Font:** Instrument Serif (com Georgia)
**Body Font:** Manrope (com system-ui)

**Character:** Uma serifa de revista, estreita e de alto contraste, faz a voz da Thalia. A Manrope, geométrica e de peso médio, carrega todo o trabalho. As duas fontes são servidas da própria Thalia, sem CDN.

### Hierarchy
- **Display** (400, clamp(34px, 4vw, 46px), 1.05): a hora grande da tela do Orbe (a saudação saiu em 23/10/2026).
- **Headline** (400, 30px, 1.1): os títulos de seção, como "Tarefas".
- **Numeral** (400, 34px, 1.1): o número em destaque de um bloco, como a data da próxima edição do resumo.
- **Wordmark** (itálico 400, 26px, 1): o nome "Thalia" no topo, ao lado do orbe.
- **Title** (700, 15px): os títulos de bloco e de coluna; o título do cartão usa 600.
- **Body** (500, 15px, 1.5): o texto corrido, o subtítulo e a busca.
- **Small** (500, 13px, 1.45): as notas dos cartões, a dica e os rodapés de bloco.
- **Label** (600, 12px, algarismos tabulares): as etiquetas, as idades e os horários.
- **Answer** (400, clamp(26px, 3.2vw, 36px), 1.25): sem uso desde 23/10/2026. A resposta agora mora na gaveta, em Manrope 15px; a serifa grande ficou na hora e na temperatura da tela do Orbe.
- **Quote** (500, 19px, Areia): sem uso desde 23/10/2026 (a pergunta é um balão na gaveta).
- **Lead** (500, 17px, Areia): a data por extenso, abaixo da hora na tela do Orbe.

### Named Rules
**The Serifa Fala Rule.** A Instrument Serif é a voz da Thalia: saudação, títulos de seção, a marca e o número em destaque. Nunca vai em botão, em campo nem em texto abaixo de 26px.

## Layout

Coluna única centralizada com até 1360px de largura e margens laterais fluidas (de 16px a 40px). As seções ficam a 28px uma da outra. A faixa é uma grade automática de blocos com mínimo de 290px, que vira uma pilha no celular. O quadro é uma fileira de três colunas com largura mínima de 300px; abaixo de 700px, cada coluna ocupa 85% da tela e a fileira rola para o lado, com encaixe por coluna. Abaixo de 700px os filtros também viram uma fileira que rola para o lado.

A tela do Orbe (`/`) é outra: uma coluna centrada, sem caixas e sem texto de conversa. Do topo para baixo: a marca "Thalia" com o ouvido do notebook, "Instalar app" e o link "Central"; o orbe; uma linha de estado; a hora grande em serifa; a data; o tempo agora em Natal; a previsão dos 7 dias; e uma dica de uma linha. A conversa mora numa gaveta à direita (ver Gaveta de conversa), fechada por padrão.

O ritmo é apertado dentro dos grupos (6 a 10px) e generoso entre eles (16 a 28px). Os alvos de toque têm 44px em telas de toque.

### Named Rules
**The Coluna na Tela Rule.** Cada coluna cabe na altura da tela e rola por dentro. A página nunca vira a rolagem do quadro, para as três colunas ficarem ao alcance do arrasto.

## Elevation & Depth

O sistema é plano em repouso. A profundidade vem dos degraus de tom (Noite → Fuligem/Carvão → Carvão Claro → Cinza Quente), cada um um pouco mais claro e mais à frente. A sombra aparece só no que se solta da superfície: o cartão sob o mouse (que sobe 1px), o cartão-fantasma durante o arrasto e o recado no rodapé. As sombras são pretas e difusas, e a tabela completa está em `.impeccable/design.json`.

### Named Rules
**The Plano em Repouso Rule.** Nada tem sombra parado. A sombra é uma resposta a um estado: hover, arrasto ou elemento flutuante.

**The Só o Orbe Brilha Rule.** O único brilho colorido da Thalia é a luz do próprio orbe. Foco, botão e campo nunca ganham halo: o foco é um contorno laranja nítido.

**The Borda ou Sombra Rule.** Um elemento flutuante tem sombra ou borda fina, nunca as duas. Por isso o recado não tem borda.

## Shapes

Cantos arredondados e macios, que crescem com o tamanho do elemento: 6px nas etiquetas, 8px nos botões, 12px nos cartões e caixas de aviso, 16px nos blocos e colunas, e pílula na busca e nos chips (22px) e no campo da conversa (28px, metade dos 56px de altura). As bordas têm sempre 1px. O tracejado é reservado para lugares que ainda não têm conteúdo ou que podem receber um: a coluna vazia e a coluna que recebe um cartão. Só o orbe foge do círculo: ele muda de forma devagar, como uma gota.

## Components

### Buttons
- **Shape:** cantos levemente arredondados (8px).
- **Avançar (Começar, Concluir):** o botão fica sempre à vista e discreto, com texto em Areia, fundo transparente e borda de fio, seguido de uma seta desenhada em SVG. Ganha corpo (Cinza Quente, texto em Marfim) quando o mouse passa pelo cartão ou quando recebe o foco; a borda fica laranja no hover.
- **Cheio (Adicionar):** a versão já ganha corpo do mesmo botão, usada em formulário.
- **Botão de texto laranja (Desfazer):** sem borda, laranja em negrito; no hover, fundo Carvão Claro e laranja claro.

### Chips
- **Filtro:** pílula de 36px com borda de fio e texto em Areia. Quando ligado, inverte: fundo Marfim e texto Noite. Usa `aria-pressed`.
- **Ação (+ Nova):** a mesma pílula com texto laranja, para não se confundir com um filtro.

### Cards / Containers
- **Cartão de tarefa:** fundo Carvão Claro, 12px de canto, borda de fio. Mostra o título em Title, a nota cortada em 3 linhas (abre ao clicar ou quando o cartão está em foco) e um rodapé com a etiqueta da frente, a origem, a idade e o botão de avançar. Sob o mouse, sobe 1px e ganha sombra.
- **Bloco da faixa:** fundo Fuligem, 16px de canto, 20px de respiro, cabeçalho com título à esquerda e informação de contexto (Label, Pedra) à direita. O rodapé do bloco fica separado por um fio.
- **Coluna do quadro:** fundo Carvão, 16px de canto, cabeçalho com ponto de estado, nome e contagem. Recebe o cartão arrastado com borda laranja tracejada.

### Inputs / Fields
- **Busca:** pílula de 44px em Carvão Claro com lupa desenhada e um atalho "/" à direita (some no toque e com o foco). O foco troca a borda para laranja; o cursor é laranja.
- **Formulário de tarefa nova:** campo e seletor de frente em Carvão Claro, com 10px de canto e borda de fio mais clara.

### Navigation
- **Topo:** faixa Fuligem com o orbe pequeno e a marca "Thalia" em serifa itálica à esquerda, o link "Conversa" e a busca ocupando o resto. No celular, a busca desce para a linha de baixo.
- **Entre as telas:** um link de texto com sublinhado laranja ("Conversa" na central, "Central" na conversa), com 44px de alvo.

### Orbe
A assinatura da Thalia: um gradiente radial do creme ao vinho, passando pelo laranja, que respira (escala de 0,92 a 1,04 em 5s) e muda de forma (9s). Ele para quando o sistema pede movimento reduzido. O pontinho é a mesma brasa em tamanho de marcador e indica a voz e as dicas. O orbe parado, sem a mudança de forma, também é o ícone do app instalado (`scripts/gerar-icones.py`): sobre fundo transparente, ou sobre a Noite na versão com máscara e na do iPhone.

### Orbe grande
O orbe da tela do Orbe (de 150px a 250px, conforme a tela) é um botão e mostra pelo ritmo em que pé a Thalia está:
- **Dormindo:** respira devagar (6s). É o estado de espera.
- **Ouvindo:** respira mais depressa (2,2s), e dois anéis de fio laranja saem dele e somem, um atrás do outro. Aparece enquanto o microfone grava, ou quando o ouvido do notebook escutou o nome. Na linha de estado: "Ouvindo. Toque de novo para enviar."
- **Pensando:** muda de forma mais depressa. Na linha de estado, em laranja: "Pensando · 4 s" (ou "Entendendo o que você disse" enquanto transcreve a voz), com os segundos contando.
- **Falando:** pulsa no ritmo de uma fala (meio segundo) enquanto a voz toca. Entre o "Deixa eu ver nas notas…" e a resposta, volta a pensar.

**Falar pelo orbe.** O orbe é um botão de verdade (Enter e Espaço funcionam). Tocar nele em repouso começa a gravar, a mesma gravação do microfone da gaveta. Tocar de novo enquanto grava encerra e envia. Tocar enquanto ela pensa ou fala, para: cala a voz e cancela o pedido aberto (o que já chegou fica na gaveta, marcado "interrompida"). Esc cancela a gravação ou cala a voz; sem nada disso, Esc fecha a gaveta. Sem microfone (página não segura), o toque no orbe abre a gaveta. O que ele fala é respondido em voz; o que ele escreve na gaveta é respondido só em texto.

A linha de estado tem altura fixa para a tela não pular. Um erro (cérebro dormindo, sem internet, microfone bloqueado) aparece nela em lilás de atenção e some sozinho em 9 segundos; a gaveta guarda o erro.

Com movimento reduzido, o orbe fica parado, os anéis ficam fixos e apagados, e o estado aparece só no texto.

### Hora, data e tempo em Natal
Abaixo do orbe, a hora em serifa (de 64px a 96px, a única vez que a serifa aparece grande nesta tela) e a data por extenso em Areia. Depois, o tempo agora: ícone, temperatura em serifa (44px), a descrição em negrito ("Poucas nuvens") e, em Areia, "Natal · sensação de 28°". Embaixo, uma fileira de 7 dias (hoje, sáb, dom…) com ícone, máxima em negrito, mínima em Pedra e a chance de chuva com uma gota; a chance de 50% ou mais sobe para Marfim. O dia de hoje ganha o fundo Carvão Claro. Os dados vêm de `/api/clima` e são atualizados a cada 10 minutos; se a atualização falhar, a última leitura fica e uma linha lilás diz de que hora ela é. Sem nenhuma leitura, uma linha discreta explica que falta internet no notebook.

Os ícones do tempo são SVG inline (sprite no `orbe.html`), traço de 1,75 e pontas redondas, em Marfim ou Areia: sem cor, porque o laranja é só da Thalia. O código do tempo (WMO, do Open-Meteo) escolhe o ícone, e de noite o sol vira lua.

### Gaveta de conversa
Um botão redondo de 44px, de fio, no canto inferior direito, com o ícone de balão em Areia. Quando chega resposta com a gaveta fechada, ganha a brasa do orbe como ponto no canto e o nome acessível passa a dizer "há mensagem nova". Tocar nele abre um painel ancorado à direita (`role="dialog"`, 380px no computador, tela cheia no celular), com a cor Fuligem e uma borda de fio, sem sombra. No computador, a tela principal se desloca para o lado em vez de ficar coberta; no celular, ela fica inerte enquanto a gaveta está aberta. Esc ou o X fecham, e o foco volta ao botão.

Dentro, de cima para baixo: o título "Conversa"; a lista de conversas (as últimas 20 que o servidor guarda, inclusive as feitas por voz no notebook e por outras telas, mais a atual); o campo de escrever com o microfone. Cada conversa tem a hora em Pedra, o que ele falou ou escreveu num balão Cinza Quente à direita e a resposta num balão Carvão Claro com fio à esquerda, que vai se escrevendo em stream. A resposta fala em Manrope 15px, porque a serifa não vai abaixo de 26px. Enquanto não há texto, o balão diz "Pensando · 4 s". As fontes vêm como etiquetas embaixo da resposta: nota (nome e data) ou site; as do site são links que abrem em outra aba. O erro é um balão com fio roxo e texto lilás. Vazia, a gaveta explica o que dá para pedir e quantas notas já foram lidas.

### Campo da conversa
Uma pílula de 54px em Carvão Claro, no pé da gaveta, com o botão de enviar redondo e laranja à direita. Antes dele, o microfone: redondo, de 44px, em Cinza Quente com o ícone creme. Gravando, ele se acende em creme com o quadrado de parar escuro, e tocar nele envia, igual ao orbe. Sem página segura (HTTPS ou o próprio notebook), o microfone não aparece. O foco troca a borda para laranja e ganha o contorno de 2px. Microfone negado aparece acima do campo, em lilás, com o caminho para liberar.

### Ouvido do notebook
Uma pílula de fio no topo da tela do Orbe, antes de "Instalar app", que só existe quando o ouvido do notebook dá sinal. A brasa do pontinho e "Ouvindo “Thalia” no notebook", com a ação "Pausar" em laranja. Pausado, a brasa apaga para Pedra e o texto vira "Ouvido pausado", com "Retomar". No celular, o texto some e ficam a brasa e a ação.

### Grupo Para revisar
O lugar dos cartões importados que ninguém mexeu ainda. É um divisor dobrável no fim de A fazer, e não um cartão dentro da coluna. O cabeçalho tem ponto roxo, nome e contagem, e uma frase diz a idade uma vez só, para que cada cartão não repita "parado há N dias". Cada cartão troca o botão de avançar por "Arquivar" e "Ainda vale", nessa ordem, e o foco cai em "Ainda vale". O aviso roxo acima do quadro abre o grupo com "Revisar agora", em laranja, porque é uma ação.

### Recado
Uma pílula Cinza Quente fixa no rodapé, centralizada, que sobe ao aparecer. Diz o resultado do último movimento e oferece "Desfazer" por 8 segundos (ou Ctrl+Z). Não some enquanto o mouse ou o foco estão nela.

### Página de leitura (Escola)
O texto-base das questões é uma página de livro, e não mais uma caixa escura: ele pediu em 29/10/2026 "a mesma ideia do Kindle", porque texto miúdo e corrido embaça a vista dele. É a única superfície clara do sistema, de propósito.
- **Papel:** creme (papel, #E9E0CE), mais apagado que o do Kindle para não ofuscar à noite, com tinta quase preta e quente (tinta, 11,8:1). A tinta-2 (5,2:1) vai na fonte, no título da obra e no número do parágrafo. O fio do papel separa os textos.
- **Letra:** Literata (a do Google Play Livros, servida pela própria Escola), 19px com entrelinha de 1,72 e cerca de 60 caracteres por linha; 18px no celular. Alinhada à esquerda, sem justificar e sem hifenizar.
- **Estrutura:** cada "Texto 1" da prova é uma seção com o nome em Literata 600 e, embaixo, o título da obra e o autor. Os parágrafos têm o número na margem, porque as questões citam "5º §". Os versos vêm em estrofes, sem número, e a fonte vem no pé.
- **Vários textos:** os atalhos "Texto 1 · Texto 2" ficam presos no topo do papel.
- **Foco no papel:** é a brasa-papel (#9A4A12), porque o laranja quase some no creme (1,6:1).
- **Rótulo nos dados:** a linha "Texto 1" (ou "Texto II", como a prova imprime) no `texto` da questão.
- **Barra do papel:** os atalhos ficam à esquerda. À direita vêm dois botões sem borda, com ícone: "Fundo azul" e "Minimizar". A escolha fica guardada no navegador (`escola:leitura` no localStorage) e vale para todos os textos.
  - **Fundo azul**, a pedido dele (29/10): o papel vira azul bem escuro (papel-azul) com tinta cinza-clara (tinta-azul, 12,5:1, e não branca) e um contorno de fio, porque o azul quase some contra a Noite. O foco volta a ser o laranja.
  - **Minimizar:** o texto fica numa janela de 42% da altura da tela (no mínimo 300px), com rolagem própria, para a questão vir logo abaixo. No simulado em tela larga o botão some, porque lá o texto já tem coluna e rolagem próprias.

### Guia do assunto (Escola)
O resumo nosso do que as questões reais de um assunto cobram (29/10/2026). Usa o mesmo papel, a mesma letra e o mesmo Fundo azul da página de leitura, porque também é leitura longa. Não tem Minimizar.
- **Papel (desde 30/10):** o guia completa o vídeo. Ele disse: "não me dou muito bem com textos, lido melhor com vídeo e gosto de resolver questões". Por isso:
  - cada assunto abre com as aulas do Prof. Álvaro Ferreira, o canal de que ele gostou; a leitura de site virou extra;
  - o guia traz só o que os vídeos não ensinam e a banca cobrou, incluindo as questões dos simulados;
  - traz também, numa caixa "Atenção" com o minuto, a correção do que o vídeo diz errado;
  - cada questão fica depois do primeiro item que a ensina, seja o vídeo, seja o guia.

  A primeira linha diz o que o guia completa. O trabalho está em `docs/revisao-ensino-2026-10-29/videos/`.
- **Lugar:** depois do título e dos botões da aula, e não no palco de cima, como o vídeo, porque é longo. As questões vêm logo depois.
- **Índice:** as seções `##` viram uma lista que fica fechada atrás do botão "Índice · N partes" e, aberta, ocupa duas colunas. Ao escolher uma parte, a lista fecha. Até a noite de 29/10 eram botões sempre à mostra, 19 no guia de ortografia, uma tela inteira antes da primeira linha.
- **Tamanho:** cada guia tem até uns 20 minutos de leitura, e o total com as questões fica em até cerca de 35 minutos. O guia maior vira partes ("Parte 2 de 2 do guia de…" na primeira linha), e cada parte traz as questões que ela ensina, o seu "Em 1 minuto" e as fontes. Até a noite de 29/10, os guias iam até 1 hora, e ele achou muito para um bloco só. O script é `scripts/guias-dividir.py`.
- **Topo:** o guia não mostra fonte, nota nem "Também cai em". A primeira linha já diz o que ele completa.
- **Tabela:** de no máximo 4 colunas, com o cabeçalho em Manrope sobre papel-2. No celular (até 760px), cada linha vira um bloco, com o nome da coluna em cima de cada valor.
- **Box:** só um filete de 3px à esquerda, sem fundo. É brasa-papel no "Pegadinha" e no "Atenção" (o vídeo errou), e tinta-2 no "Como cai" e no "Dica". Com fundo papel-2, três pegadinhas seguidas viravam um bloco escuro.
- **Extras (em todo curso, não só no guia):** na lista do curso e na lista lateral da aula, os extras de cada assunto ficam fechados no fim, numa linha discreta ("2 extras, se quiser ir além"). Na lista lateral, o grupo abre sozinho quando a aula aberta é um extra. Na lista do curso, o edital de cada assunto mostra só o trecho daquele curso.
- **Hífen:** a palavra com hífen nunca quebra no fim da linha, porque num guia que ensina hífen "super-" numa linha e "homem" na outra confunde.

## Do's and Don'ts

### Do:
- **Do** use os degraus de tom para separar camadas (Noite → Fuligem → Carvão Claro → Cinza Quente) antes de pensar em sombra.
- **Do** escreva o estado ao lado da cor: "parado há 49 dias" junto do ponto roxo e "Atenção:" para o leitor de tela.
- **Do** desenhe os ícones em SVG inline, com traço 2 e pontas arredondadas, como a lupa, a seta e a dobra.
- **Do** dê 44px aos alvos de toque e mantenha o anel de foco laranja de 2px com 2px de afastamento.
- **Do** pare o orbe e as transições com `prefers-reduced-motion`.

### Don't:
- **Don't** use preto puro nem branco puro; o fundo é #0E0D0C e o texto é #F2EDE4.
- **Don't** traga um segundo acento nem use laranja para estado.
- **Don't** use a Pedra (texto-3) sobre o Cinza Quente: dá 4,46:1, abaixo do AA.
- **Don't** esconda a ação principal de um cartão atrás do hover.
- **Don't** junte borda fina e sombra larga no mesmo elemento.
