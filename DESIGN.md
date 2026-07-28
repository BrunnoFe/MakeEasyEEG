---
name: EEGHelper
description: A bancada de um instrumento de medição para corrigir marcadores de eventlists do ERPLAB — dois modos, uma grade de colunas, um traço por participante.
colors:
  escura:
    tela: "#0A0E11"
    painel: "#111B21"
    painel-alto: "#18232A"
    graticule: "#22323C"
    traco: "#3D525E"
    contorno: "#21303A"
    contorno-forte: "#2C3E49"
    texto: "#E6EEF2"
    texto-medio: "#9AAFB9"
    texto-fraco: "#6F8189"
    pronto: "#38E2B0"
    varrendo: "#38BDF8"
    pulado: "#FBBF24"
    divergente: "#FB7185"
    acento: "#38E2B0"
    acento-2: "#1FA8C9"
    sobre-acento: "#04231A"
    sombra: "#59000000"
    sombra-alta: "#73000000"
  clara:
    tela: "#EEF2F4"
    painel: "#FFFFFF"
    painel-alto: "#F2F6F8"
    graticule: "#DBE4E8"
    traco: "#B3C4CC"
    contorno: "#DCE5E9"
    contorno-forte: "#CBD8DE"
    texto: "#0B1417"
    texto-medio: "#41535B"
    texto-fraco: "#66787F"
    pronto: "#0B7A5A"
    varrendo: "#0B7C99"
    pulado: "#8A5A00"
    divergente: "#C62A1C"
    acento: "#0FA47F"
    acento-2: "#0D7F9C"
    sobre-acento: "#FFFFFF"
    sombra: "#12000000"
    sombra-alta: "#1F000000"
typography:
  wordmark:
    fontFamily: "JetBrains Mono, Consolas, SF Mono, DejaVu Sans Mono, Courier New, monospace"
    fontSize: "17px"
    fontWeight: 600
  titulo:
    fontFamily: "Segoe UI, Inter, Helvetica Neue, Arial, sans-serif"
    fontSize: "19px"
    fontWeight: 600
  secao:
    fontFamily: "Segoe UI, Inter, Helvetica Neue, Arial, sans-serif"
    fontSize: "15px"
    fontWeight: 600
  corpo:
    fontFamily: "Segoe UI, Inter, Helvetica Neue, Arial, sans-serif"
    fontSize: "13px"
    fontWeight: 400
  cifra:
    fontFamily: "JetBrains Mono, Consolas, SF Mono, DejaVu Sans Mono, Courier New, monospace"
    fontSize: "13px"
    fontWeight: 400
  cifra-forte:
    fontFamily: "JetBrains Mono, Consolas, SF Mono, DejaVu Sans Mono, Courier New, monospace"
    fontSize: "13px"
    fontWeight: 700
  leitura:
    fontFamily: "JetBrains Mono, Consolas, SF Mono, DejaVu Sans Mono, Courier New, monospace"
    fontSize: "28px"
    fontWeight: 700
  rotulo:
    fontFamily: "Segoe UI, Inter, Helvetica Neue, Arial, sans-serif"
    fontSize: "10.5px"
    fontWeight: 600
    letterSpacing: "1.3px"
rounded:
  linha: "8px"
  chip: "9px"
  botao: "11px"
  cartao: "14px"
  painel: "14px"
  pilula: "999px"
spacing:
  "1": "4px"
  "2": "8px"
  "3": "12px"
  "4": "16px"
  "5": "22px"
  "6": "32px"
shadows:
  cartao: "0 4px 14px {colors.sombra}"
  painel: "0 10px 28px {colors.sombra-alta}"
  gravar: "0 6px 18px rgba({colors.acento}, 0.28)"
  brilho: "0 0 8px rgba({colors.pronto}, 0.45) — só no modo escuro"
motion:
  rapido: "140ms ease-out-cubic"
  transicao: "220ms ease-out-cubic"
  varredura: "1900ms ease-in-out-sine"
components:
  botao-gravar:
    background: "linear-gradient(135deg, {colors.acento}, {colors.acento-2})"
    textColor: "{colors.sobre-acento}"
    typography: "{typography.corpo}"
    fontWeight: 600
    rounded: "{rounded.botao}"
    height: "42px"
    shadow: "{shadows.gravar}"
  botao-verificar:
    background: "transparent"
    textColor: "{colors.texto}"
    border: "1px solid {colors.contorno-forte}"
    rounded: "{rounded.botao}"
    height: "42px"
  botao-desabilitado:
    background: "transparent"
    textColor: "{colors.texto-fraco}"
    border: "1px solid {colors.contorno}"
    rounded: "{rounded.botao}"
    height: "42px"
  chip:
    background: "transparent"
    textColor: "{colors.texto-medio}"
    border: "1px solid {colors.contorno}"
    rounded: "{rounded.pilula}"
    padding: "5px 12px"
  campo-ecode:
    background: "{colors.painel-alto}"
    textColor: "{colors.texto}"
    typography: "{typography.cifra}"
    rounded: "{rounded.chip}"
    width: "72px"
    height: "34px"
    textAlign: "right"
  cartao:
    background: "{colors.painel}"
    border: "1px solid {colors.contorno}"
    rounded: "{rounded.cartao}"
    padding: "18px"
    shadow: "{shadows.cartao}"
  painel-da-tela:
    background: "{colors.painel}"
    border: "1px solid {colors.contorno}"
    rounded: "{rounded.painel}"
    shadow: "{shadows.painel}"
  cabecalho-tabela:
    textColor: "{colors.texto-fraco}"
    typography: "{typography.rotulo}"
    height: "32px"
    padding: "0 20px"
    margin: "0 8px"
  linha-tabela:
    textColor: "{colors.texto}"
    typography: "{typography.corpo}"
    rounded: "{rounded.linha}"
    height: "34px"
    padding: "0 20px"
    margin: "0 8px"
  fita:
    background: "transparent"
    width: "380px"
    height: "20px"
---

# Design System: EEGHelper

## Overview

**Creative North Star: "A Bancada"**

A janela é a tela de um instrumento de bancada, não uma lista de arquivos com selos de status. À esquerda, um painel elevado onde o lote inteiro é lido como um feixe de canais: um participante por linha, um traço por linha, todos sobre a mesma base de tempo. À direita, uma coluna de controle estreita e fixa — aquisição, leitura de medição em cifras grandes, e as duas ações ao pé. O usuário liga as entradas, varre o lote, lê linha a linha onde cada participante quebrou, e só então grava.

O instrumento tem dois modos, e nenhum dos dois é uma inversão automática do outro: o escuro é a bancada no laboratório apagado, com halo de fósforo nas marcas acesas; o claro é o mesmo instrumento sob luz de trabalho, com os mesmos matizes reancorados em luminosidade para ≥4.5:1 — e sem halo, porque sob luz um halo não lê como luz, lê como borrão.

A cor é rigorosamente racionada em quatro canais e mais nada. Menta é pronto, ciano é varrendo, âmbar é sem coluna, coral é divergente. Fora desses quatro, a janela é neutra: os únicos outros usos de cor são o wordmark e o preenchimento do botão que grava, e ambos usam a família de acento, não as cores de canal.

**Key Characteristics:**
- Neutros escuros tingidos de teal (nunca azul-cinza, nunca cinza puro), com claro reancorado no mesmo matiz
- Quatro cores de canal e mais nada colorido no conteúdo
- Uma única definição de grade de colunas, partilhada por cabeçalho e linha
- Numerais tabulares em JetBrains Mono em toda cifra, sem exceção
- Cartões flutuando sobre o gabinete por sombra alta e suave, não por borda escura
- Medidas fixas onde a comparação depende delas (fita 380×20, linha 34)
- Movimento em três lugares: a varredura da verificação, os realces de hover, e a luz de espera da tela vazia

## Colors

Duas paletas de vinte cores cada, uma por modo, com os mesmos nomes de token — nenhuma superfície escolhe cor por conta própria: tudo vem de `tema.paleta()`, lido no momento em que o controle é construído.

### Canais
- **Pronto** (`pronto`, menta): participante que a verificação aprovou. Marcador de canal aceso, marcas do traço, cifra de "prontos", ponto de estado da gravação concluída.
- **Varrendo** (`varrendo`, ciano): a barra de aquisição enquanto a verificação corre. Existe só durante a fase `VERIFICANDO`.
- **Sem coluna** (`pulado`, âmbar): arquivo que não casou com nenhuma coluna da planilha. Tinge o fundo de repouso da linha a 6% e o campo de escolha inline a 14% — é a única linha da tabela que pede uma ação, e a margem sozinha não chama o olho num lote de duzentos arquivos.
- **Divergente** (`divergente`, coral): contagem que não fecha. Cursor de medição no traço, cifra em peso 700, contadores da leitura, mensagem de erro da planilha.

### Acento
- **Acento / Acento 2** (`acento`, `acento-2`): reservados ao wordmark, ao contorno do chip sob o cursor, à luz de espera e ao gradiente do botão que grava. **Nenhuma superfície de conteúdo os usa.** No modo escuro `acento` coincide com `pronto`; isso é intencional e não os torna intercambiáveis — trocar um pelo outro quebraria o modo claro, onde eles divergem.

### Neutros
- **Tela** (`tela`): o gabinete, o fundo da janela inteira.
- **Painel** (`painel`): a superfície de todo cartão e do painel da tela.
- **Painel alto** (`painel-alto`): o degrau acima do painel — realce de hover de linha e de chip, preenchimento do campo `ecode`, pista da barra de aquisição, filete que separa o `ecode` dos campos de arquivo.
- **Graticule** (`graticule`): a grade dentro da fita — base de tempo e divisões verticais.
- **Traço** (`traco`): os tiques de evento não-alvo e as cabeceiras da fita.
- **Contorno / Contorno forte** (`contorno`, `contorno-forte`): 1 px em cartões, painel, cabeçalho de tabela e chips; o forte é reservado ao botão contornado, que precisa se ler como ação e não como caixa.
- **Texto / Texto médio / Texto fraco**: primário, secundário, apoio. O fraco é tingido, nunca cinza puro, e mantém ≥4.5:1 sobre o painel nos dois modos.

### Named Rules

**A Regra dos Quatro Canais.** Cor no conteúdo só existe em quatro valores, e cada um significa um estado do participante. Não há quinta cor de status, não há cor decorativa, e o acento de marca nunca é usado para descrever um estado.

**A Regra da Cor Depois da Medição.** Antes da verificação nada foi decidido: os marcadores de canal ficam vazados, as marcas do traço ficam em texto médio, e nenhuma linha recebe verde. Uma marca acesa num lote que ninguém calculou seria uma promessa falsa.

**A Regra do Halo Só no Escuro.** `brilho()` devolve blur 8 no modo escuro e blur 0 no claro. O halo de fósforo é o que faz a marca acesa parecer luz; sob luz de laboratório ele viraria borrão, e ali a cor cheia do marcador já basta.

## Typography

**Texto:** Segoe UI (com Inter, Helvetica Neue, Arial, sans-serif)
**Cifra:** JetBrains Mono (com Consolas, SF Mono, DejaVu Sans Mono, Courier New, monospace)

A JetBrains Mono é registrada em `page.fonts` na entrada da aplicação, porque quase nenhuma máquina de laboratório a tem instalada; os fallbacks cobrem quem abrir o app sem rede. Ela carrega toda cifra e também o wordmark — de propósito, para que a marca não introduza uma terceira voz tipográfica.

### Hierarchy
- **Wordmark** (600, 17px, mono): `eeg·helper`, uma vez por janela.
- **Título** (600, 19px): degrau disponível no sistema; nesta versão o cabeçalho é o wordmark.
- **Seção** (600, 15px): a instrução principal da tela vazia. Único uso.
- **Corpo** (400, 13px): texto de linha, valores de campo, mensagens de estado, rótulos de botão. Sempre `no_wrap` com elipse — uma linha da tabela nunca reflui. Os textos de apoio da tela vazia usam 12.5px.
- **Cifra** (400, 13px, mono, alinhada à direita): contagem alvos/códigos por linha, `ecode` alvo.
- **Cifra forte** (700, 13px, mono): contagem divergente. O peso carrega a divergência junto com a cor.
- **Leitura** (700, 28px, mono): as três cifras grandes do painel de medição.
- **Rótulo** (600, 10.5px, tracking 1.3, CAIXA ALTA): cabeçalhos de coluna, nomes de campo, nomes de contador, nomes de cartão.

### Named Rules

**A Regra do Numeral Tabular.** Todo número exibido usa a família mono com alinhamento à direita, inclusive o `ecode` num campo de 72 px. Números em sans quebram a coluna, e a coluna é a leitura.

**A Regra do Versalete.** Toda etiqueta que nomeia um campo, uma coluna ou um contador é caixa alta em 10.5px com tracking 1.3. Nomes de coisas nunca competem em corpo com os valores das coisas.

## Layout

Uma barra de topo e, abaixo dela, duas colunas com 16 px entre elas: o **painel da tela** (elástico) e a **coluna de controle** (308 px fixos). A janela tem calha de 22 px em toda a volta, piso de 1180×700 e abre em 1320×820. Não há breakpoints: é um desktop de janela única.

O painel da tela empilha, sem espaçamento: a pista da barra de aquisição (sempre visível, em painel alto, para que o cabeçalho não salte 3 px quando a verificação começa), o cabeçalho de colunas, e a lista virtualizada de linhas.

A coluna de controle rola nos dois cartões de cima — aquisição e leitura — e ancora as ações ao pé. Numa janela baixa a soma dos cartões passa da altura disponível, e uma coluna única empurraria o botão que grava para fora da tela: a ação mais consequente da janela seria a primeira a sumir.

O ritmo de espaçamento é 4 / 8 / 12 / 16 / 22 / 32.

### A grade de colunas

**Existe uma única definição das cinco colunas da tabela**, e cabeçalho e linha passam os dois por ela: marcador (14), participante (116), nome do arquivo (elástico), fita (380), contagem (104, alinhada à direita), com 12 px entre colunas. Os dois usam também a mesma calha interna (`CALHA_TABELA`, 20 px) e a mesma margem lateral (`MARGEM_LINHA`, 8 px) — a linha precisa de margem porque seu realce de hover é uma pastilha arredondada, e o cabeçalho precisa da mesma margem ou cada rótulo cai deslocado da coluna que nomeia.

**A Regra da Grade Única.** Cabeçalho e linha nunca declaram larguras de coluna em dois lugares. A coluna elástica do nome do arquivo é a que empurra as duas seguintes se as calhas divergirem, e foi exatamente esse desalinhamento que motivou este refino. Uma função, um alinhamento.

**A Regra da Medida Fixa.** A fita tem medida, não largura elástica. Duas fitas em linhas diferentes só são comparáveis porque começam e terminam no mesmo x.

## Elevation & Depth

Três alturas, todas com deslocamento e desfoque — nunca borda escura fazendo as vezes de sombra.

- **Cartão:** blur 14, offset (0, 4). Aquisição, leitura, ações.
- **Painel:** blur 28, offset (0, 10). Só o painel da tela, que é a superfície dominante e precisa parecer flutuar sobre o gabinete.
- **Gravar:** blur 18, offset (0, 6), na cor de acento a 28%. **A única sombra colorida da janela.**

Além delas existe o halo de `brilho()`, que não é elevação e sim luz: blur 8 sem deslocamento, atrás do marcador de canal aceso, e somente no modo escuro.

**A Regra da Sombra Colorida Única.** Só a ação que escreve em disco tem sombra colorida. Se outra superfície ganhar uma, o botão perde o que o distingue.

## Shapes

Raios: linha 8, chip 9, botão 11, cartão 14, painel 14, pílula 999. A escala sobe com o tamanho da superfície — a pastilha de hover de uma linha de 34 px não pode ter o mesmo raio de um cartão.

A pílula existe em três lugares: os chips de ação, o marcador de canal (8×8) e o ponto de estado do rodapé (6×6). Contornos são sempre 1 px, exceto o marcador vazado (1.5 px, porque precisa vencer o fundo da linha) e o cursor de divergência (2 px, porque precisa vencer os tiques ao redor).

Tracejado existe em três lugares, todos dentro da fita: as divisões da graticule `[1,3]`, as marcas sem correspondência `[2,2]` e a base pós-quebra `[3,3]` — os dois últimos significando "sem correspondência".

## Components

### Marca (`eeg·helper`)
Um **sinete** de anel de eletrodo — gradiente cônico de volta completa (acento → acento 2 → acento, para não deixar costura visível no topo do círculo), miolo na cor do painel e um contato horizontal no centro — ao lado do **wordmark** em mono caixa baixa, com o ponto médio na cor de acento. O ponto médio é o mesmo separador que a interface já usa em "20 arquivos · eventlists". Abaixo, o subtítulo em texto fraco.

### Buttons
- **Forma:** 42 px de altura, raio 11, ícone de 15 px à esquerda do rótulo.
- **Gravar (preenchido):** gradiente diagonal acento → acento 2, texto em `sobre-acento` peso 600, sem contorno, com a sombra colorida. É um `Container` e não um `FilledButton` porque o Material impõe cor sólida em `bgcolor` e o preenchimento aqui é um gradiente. O rótulo conta o lote ("Gravar 12 arquivos") e concorda em número.
- **Verificar lote (contornado):** fundo transparente, texto primário, contorno forte; sob o cursor o fundo vira painel alto.
- **Desabilitado:** perde gradiente, sombra e handler de clique — fundo transparente, texto fraco, contorno comum. Escrito à mão, não herdado do Material: um "Gravar" travado com aparência de ativo mentiria exatamente sobre a ação que escreve em disco.
- **Hover:** o botão ativo sobe 3% da própria altura em 140 ms. Travado, não se move.

### Chips
Pastilha fantasma em pílula: sem preenchimento em repouso, contorno comum, texto em 11.5px. Sob o cursor ganha fundo em painel alto, contorno de acento e sobe 4% — o deslocamento é o que a faz parecer clicável, porque cor sozinha, num cartão que já tem contorno, lê como estado e não como convite.

### Inputs / Fields
- **Campo de aquisição:** rótulo versalete, valor, e os chips de ação embaixo. Sem ícone: num cartão de quatro campos, quatro ícones outline dizem menos que o próprio nome do campo e cobram uma coluna que o valor usa melhor.
- **Campo `ecode alvo`:** 72×34, preenchido em painel alto, raio de chip, cifra alinhada à direita, filtro numérico. Fica na mesma linha de base do seu rótulo, separado dos três campos de arquivo por um filete de 1 px em painel alto com 18 px de respiro acima e abaixo — é o único parâmetro que se edita em vez de se escolher, e o filete o separa sem abrir outro cartão para uma linha só.
- **Escolha inline de coluna:** um arquivo sem coluna casada vira um dropdown tingido de âmbar, na própria linha da tabela, com o hint "preencher". Escolher a coluna é conferir a linha, não sair dela.
- **Erro de leitura:** a planilha ilegível mostra a mensagem no lugar do valor, em coral, com no máximo três linhas.

### Tabela de participantes
- **Cabeçalho:** 32 px, rótulos versaletes, filete de contorno embaixo, mesma calha e mesma margem das linhas.
- **Linha:** 34 px fixos, sem divisória — a separação é o próprio ritmo. Sob o cursor, a linha inteira vira uma pastilha de raio 8 em painel alto (âmbar mais forte, se pulada), em 140 ms.
- **Marcador de canal:** disco de 8 px à esquerda de cada traço — preenchido com halo quando o participante foi decidido, vazado em 1.5 px quando não.
- **Estado vazio:** a tela em branco ensina o instrumento em vez de dizer que não há nada — a instrução em corpo de seção, a fita de espera ao lado da frase "cada participante vira um traço destes", e duas linhas de apoio de 640 px explicando o que as marcas significam e que nada é gravado antes da verificação.

### O traço (componente-assinatura)
Um eventlist inteiro desenhado como uma varredura de 380×20, em quatro camadas de baixo para cima: a **graticule** (base de tempo, três divisões tracejadas e duas cabeceiras verticais que impedem a fita de ser lida como barra de progresso); os **tiques** de evento não-alvo, agrupados por coluna de pixel; as **marcas** de `ecode` alvo, com halo de fósforo quando acesas; e o **cursor de medição**, régua coral de 2 px com duas cabeças, na posição exata da divergência, seguida das marcas sem correspondência tracejadas.

**A Regra da Quebra no Lugar Certo.** A divergência é desenhada onde ela acontece, nunca na borda da fita nem como selo no fim da linha. Quando sobram códigos em vez de faltarem, o cursor fica 3 px depois da última marca — a borda diria que o descompasso está no fim da gravação, quando ele está no fim das marcas.

**A Regra das Marcas Neutras no Divergente.** Num participante divergente nenhuma troca acontece, então as marcas pareáveis ficam em texto médio, não em coral: pintá-las inundaria o traço e afogaria justamente o cursor, que é a única coisa ali dizendo onde o problema está.

### A fita de espera
Na tela vazia, a graticule aparece sem participante nenhum e uma luz de 46 px a percorre em 1900 ms, ida e volta, com gradiente que apaga nas duas pontas — o que se lê é a varredura de um feixe, não um retângulo andando.

**A Regra da Luz Dentro da Fita.** A luz vai de `MARGEM` até `LARGURA_TRACO - MARGEM - LARGURA_LUZ` e volta, e o `Stack` ainda recorta em `HARD_EDGE`: os dois juntos, porque o recorte garante o limite mesmo se a animação for interrompida no meio por um redesenho de tema. Uma luz que começasse antes da cabeceira sugeriria que a gravação começa fora do quadro — o contrário do que a fita afirma.

### Painel de medição
Três colunas de largura igual, cada uma com a cifra grande sobre o rótulo versalete. Largura igual porque as cifras precisam cair nas mesmas posições antes e depois da varredura: assim a troca de fase não reflui o cartão. Antes da verificação conta participantes e "sem coluna"; depois conta prontos, divergentes e trocas. O plural concorda com a contagem.

### Movimento
- **Varredura (1900 ms, ease-in-out-sine):** a luz de espera da tela vazia.
- **Transição (220 ms, ease-out-cubic):** o giro de -20° do alternador de tema sob o cursor — o único movimento gratuito da janela, e ele se paga: é o que diz que o ícone é um interruptor e não um selo de estado.
- **Rápido (140 ms, ease-out-cubic):** todo hover — linha, chip, botão, alternador — e o acender do marcador de canal.
- **A varredura da verificação** não tem curva porque não é animação: a barra de aquisição é determinada durante a verificação (participante calculado sobre participantes do lote) e indeterminada durante a gravação, que acontece num único bloco. Fingir uma fração ali seria inventar um progresso que ninguém mediu.

## Do's and Don'ts

### Do:
- **Do** ler a cor de `tema.paleta()` no momento de construir o controle; a árvore inteira é remontada na troca de tema.
- **Do** passar cabeçalho e linha pela mesma função de grade, com a mesma calha e a mesma margem.
- **Do** escrever toda cifra na família mono com alinhamento à direita, inclusive contagens de um dígito.
- **Do** manter a pista da barra de aquisição visível sempre, para o cabeçalho não saltar quando a verificação começa.
- **Do** exprimir divergência em três materiais ao mesmo tempo: cursor no traço, cifra em peso 700 e cor coral.
- **Do** concordar o plural com a contagem em todo rótulo que carrega número.
- **Do** reservar o gradiente e a sombra colorida para a única ação que escreve em disco.

### Don't:
- **Don't** usar `acento` ou `acento-2` para descrever estado de participante; eles são marca, não canal.
- **Don't** introduzir uma quinta cor de status nem uma terceira família tipográfica.
- **Don't** declarar larguras de coluna fora da função de grade.
- **Don't** dar largura elástica à fita: duas fitas só são comparáveis se começarem e terminarem no mesmo x.
- **Don't** deixar o halo de fósforo aceso no modo claro.
- **Don't** resolver escolha de coluna em modal; ela é inline, na própria linha.
- **Don't** marcar a divergência como selo no fim da linha; ela pertence à posição em que acontece.
- **Don't** usar cinza puro para texto de apoio; os neutros são tingidos de teal.
