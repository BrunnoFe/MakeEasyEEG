# ADR-0001 — Nomes de saída abertos, protegidos por bloqueio e confirmação

**Data:** 2026-07-29
**Status:** aceito

## Contexto

O nome do eventlist corrigido era imposto pelo programa (`{stem}_corrigido.txt`).
Pesquisadores precisam de outras convenções, quase sempre porque um script
MATLAB/ERPLAB a jusante espera um nome específico — inclusive o nome original do
arquivo de entrada, preservado numa pasta diferente.

O nome imposto era seguro **por construção**: por carregar sempre o nome do
arquivo de entrada, e como dois arquivos na mesma pasta nunca têm o mesmo nome,
cada participante tinha um destino próprio garantido. Abrir o padrão destrói
essa garantia e cria três formas de perder dado:

1. **Colisão** — um padrão sem token variável (`novos`) aponta o lote inteiro
   para um arquivo só, e as gravações se apagam em cascata.
2. **Sobrescrita do original** — `{nome}` sem trocar a pasta de saída apaga o
   eventlist bruto. Irreversível.
3. **Sobrescrita de saída anterior** — já acontecia em silêncio antes desta
   mudança, ao reprocessar um lote.

A tentação óbvia é restringir o vocabulário para que o erro seja impossível de
expressar. Ela não sobrevive ao contato com os dados reais: o usuário nomeia os
eventlists como quiser (`BFM01_12090.txt`) e os cabeçalhos da planilha como
quiser (`1`, `2`, `3`). Não há estrutura confiável para inferir nada, e qualquer
regra esperta erraria em algum laboratório.

## Decisão

**Abrir o vocabulário e tornar o erro impossível de não ver e impossível de
gravar.** Três camadas, em vez de uma sintaxe restrita:

1. **Unicidade por construção no default.** `{nome}` é o único token
   garantidamente único por arquivo, e o preset de fábrica o usa. Quem não mexe
   em nada permanece seguro.
2. **Checagem de injetividade sobre o lote.** Calculados os N destinos,
   `marcar_colisoes` confere que são N distintos e trava **todos** os
   participantes de cada grupo em conflito. Não depende de adivinhar nada, então
   pega inclusive os casos que não previmos — como dois eventlists mapeados
   manualmente para a mesma coluna.
3. **Preview ao vivo.** A coluna "novos arquivos" mostra o nome real de cada
   saída antes de qualquer gravação, e antes mesmo da verificação.

Para a sobrescrita, um diálogo modal — o único do aplicativo — no clique de
gravar, com **decisões separadas** para original e saída anterior. Recusar
destruir os originais pula apenas aquelas linhas; o resto do lote grava.

## Consequências

- A trava absoluta de `escrever_eventlist` deixa de ser "nunca" e passa a "não,
  a menos que autorizado". O default segue recusando.
- Colisão e sobrescrita recusada são modeladas como `ErroEEGHelper` preenchendo
  `previa.erro`, e não como campo novo. Assim reaproveitam `gravavel`, a linha
  coral, o contador de problemas e o pulo em `gravar_previas` — sem introduzir
  um segundo conceito de bloqueio.
- Nada é persistido entre sessões, deliberadamente: um padrão "manter o nome
  original" que sobrevivesse ao fechamento voltaria armado numa rodada futura,
  quando a pasta de saída já seria outra.
- A tabela ganhou uma sétima coluna e, com ela, um modo de rolagem horizontal.
  A janela padrão subiu de 1280 para 1480 px para que o modo elástico continue
  sendo o normal. A coluna de saída fica por último, depois do traço e da
  contagem: essas duas são a leitura do instrumento sobre o arquivo de entrada e
  pertencem a ele, enquanto a saída é a consequência — e é a primeira a sair de
  vista quando a grade rola.
- A extensão dos eventlists corrigidos saiu do vocabulário do padrão e passou a
  ser fixa em `.txt`. Já a do relatório virou uma escolha explícita entre `.csv`
  e `.xlsx`, e ela seleciona de fato o formato de escrita — `escrever_relatorio`
  deriva o formato da extensão do caminho, para que nome e conteúdo nunca
  discordem.

## Alternativas descartadas

- **Restringir tokens a um vocabulário à prova de erro** — impossível sem
  estrutura confiável nos dados, conforme o contexto.
- **Desambiguar colisões automaticamente** com sufixos `(2)`, `(3)` — um arquivo
  `B0001_novos (2).txt` é indistinguível de um erro do usuário três meses
  depois, e o programa inteiro se apoia na ideia de que nome de arquivo é a
  identidade do dado.
- **Um interruptor persistente "permitir substituir os originais"** — o pior
  dos mundos: fica ligado de uma sessão e mata a próxima.
- **Somar original e saída anterior numa contagem só** no diálogo — esconderia
  que alguns dos arquivos são insubstituíveis e outros são descartáveis.
