# Contexto do EEGHelper

Glossário do domínio. Use estes termos ao nomear código, testes, issues e
mensagens de erro; não troque por sinônimos.

## Dados de entrada

**Eventlist** — o `.txt` exportado pelo ERPLAB com uma linha por evento. As
colunas que importam são `item`, `bepoch`, `ecode`, `label` e `onset`.

**Ecode** — o código numérico do evento. O **ecode alvo** (em geral `1`) é o
marcador que o experimento não conseguiu identificar e que este programa troca.

**Boundary** — evento de fronteira, ecode `-99`. Nunca conta como evento real
nem é pareado com nada.

**Planilha de marcadores** — a tabela com uma coluna por participante, cada uma
trazendo os códigos reais na ordem de apresentação.

**Participante** — o nome da coluna da planilha. É o identificador canônico:
nem o nome do eventlist nem o cabeçalho seguem estrutura garantida, e por isso
o **mapeamento** arquivo→participante pode falhar e cair na escolha manual.

## Verificação e gravação

**Prévia** (`PreviaParticipante`) — o que aconteceria com um participante,
calculado sem tocar em disco. Uma prévia com `erro` preenchido não é gravável,
mas continua na tela: é ali que está a informação útil.

**Contagem incompatível** — a quantidade de ecodes alvo no `.txt` difere da
quantidade de códigos na coluna. O pareamento é posicional, então um descompasso
desalinha todos os marcadores seguintes.

**Invariante da gravação** — nada é gravado antes de uma verificação que o
usuário viu, e **qualquer** mudança nas entradas descarta a verificação e trava
a gravação de novo. Uma prévia obsoleta é pior que nenhuma.

## Nomes de saída

**Padrão de saída** — o template do nome do arquivo corrigido, com os tokens
`{nome}` (nome do eventlist de entrada, sem extensão) e `{participante}` (a
coluna casada). O padrão de fábrica é `{nome}_corrigido`. A extensão **não**
faz parte do padrão: eventlist do ERPLAB é `.txt`, e `EXTENSAO_EVENTLIST` é
acrescentada sempre. Escrever um ponto no padrão é recusado, porque só poderia
produzir `B0001.txt.txt`.

**Relatório** — a trilha de auditoria da rodada, opcional. Nome e **formato**
são escolhidos em separado: a extensão (`.csv` ou `.xlsx`) decide como o
arquivo é escrito, não apenas como se chama, e por isso é um dropdown e não
texto digitado.

Três formas distintas de apagar um arquivo, deliberadamente **nunca somadas**
numa contagem só — elas têm severidades incomparáveis:

**Colisão** — dois eventlists do lote resolvem para o mesmo caminho de saída.
Trava todos os envolvidos, nunca todos menos um: eleger um sobrevivente seria
arbitrário. Ver `servicos.substituicao.marcar_colisoes`.

**Sobrescrita de original** — o destino é o próprio eventlist de entrada.
Destrói o dado bruto do experimento e é irreversível. Exige autorização
explícita do usuário, por sessão, no diálogo de confirmação.

**Sobrescrita de saída anterior** — o destino está ocupado por um arquivo que
não é entrada do lote, tipicamente a saída de uma rodada passada. É o caso
rotineiro do reprocessamento e recebe uma confirmação leve.

## Interface

**Bancada** — a janela inteira, em `interfaces/gui/app.py`. **Tela** é o painel
esquerdo com a tabela; **régua de leitura** é a faixa de cifras acima dela;
**traço** é a fita de eventos de um participante, com uma marca por ecode alvo.

A `Bancada` monta o layout e mantém as áreas vivas, mas não desenha as regiões:
cada uma é uma **vista**, uma função livre que recebe `EstadoLote` e callbacks e
devolve um controle. **`controles.py`** é a única casa dos primitivos e da
tipografia (`texto`, `rotulo`, `cifra`); **`aquisicao.py`** é o cartão de
arquivos e pastas; **`regua.py`** a régua de leitura; **`acoes.py`** a frase de
estado e os dois botões; **`vazio.py`** a tela sem lote; **`tabela.py`** a grade;
**`janela.py`** o ponto de entrada. A orquestração assíncrona do lote não é
interface e mora em **`servicos/lote.py`** (`varrer_lote`, `gravar_lote`), sem
importar `flet`. Ver ADR-0002.

**Modo estreito** — quando o painel fica menor que `tabela.LARGURA_MINIMA_TABELA`
a grade troca colunas elásticas por larguras fixas e passa a rolar na
horizontal. Cabeçalho e linhas rolam juntos, num scroller único.

**Áreas vivas** — `area_tela`, `area_leitura`, `area_acoes`, `area_config` e
`area_corpo_tabela`: contêineres cujo conteúdo `atualizar()` troca sem recriar a
árvore. Toda ação do usuário deve chamar `atualizar()`; `remontar()` fica
reservado à entrada e à troca de tema, porque recriar a árvore zera a posição de
rolagem da coluna de controle.
