# ADR-0002 — Vistas da bancada como funções livres

**Data:** 2026-07-29
**Status:** aceito

## Contexto

`interfaces/gui/app.py` chegou a 1391 linhas, quase 4× o segundo maior módulo da
GUI. Num arquivo só conviviam cinco assuntos sem relação entre si: os primitivos
de widget que não conhecem o lote, as vistas de cada região da janela, o
esqueleto de layout com as áreas vivas, os handlers de evento e os dois fluxos
assíncronos de varredura e gravação.

O sintoma não era o tamanho: era que uma mudança de pixel na régua de leitura
obrigava a rolar por cima do cartão de aquisição inteiro, e que nenhuma vista
podia ser exercitada sem instanciar uma `ft.Page`.

Duas inversões estavam escondidas nesse arquivo:

- `app.py` importava `tabela.texto` e `tabela.rotulo` 14 vezes para escrever
  rótulos que não têm relação com a grade de participantes, e `dialogo.py`
  importava o módulo da tabela **exclusivamente** para isso. Dois módulos
  dependiam da tabela por causa de dois helpers tipográficos que apenas nasceram
  lá.
- o laço que ordena a varredura do lote e chama `marcar_colisoes` é regra de
  negócio, e `interfaces/gui/__init__.py` promete que a GUI é casca sem regra de
  negócio.

## Decisão

**Uma vista é uma função livre.** Recebe `EstadoLote` e os callbacks como
parâmetros nomeados, devolve `ft.Control`, e não guarda estado. É o padrão que
`tabela.linha(..., ao_escolher=...)` já usava; agora vale para todas as regiões
da janela. Nem mixin da `Bancada`, nem sub-objeto com referência a ela: as duas
formas mantêm o acoplamento por `self` e apenas o espalham por mais arquivos.

Quatro consequências de arranjo:

1. **`controles.py` é a única casa dos primitivos**, tipografia inclusa
   (`texto`, `rotulo`, `cifra`). Ele não importa vista nenhuma; toda vista
   importa dele. A dependência aponta numa direção só.
2. **`app.py` é o único dono das áreas vivas.** O esqueleto de layout
   (`montar`, `_painel_da_tela`, `_coluna_de_controle`) **não** foi extraído,
   deliberadamente: ele existe para criar `area_tela`, `area_leitura`,
   `area_config`, `area_acoes` e `area_corpo_tabela`, e uma função livre teria
   que devolver cinco contêineres para a `Bancada` guardar — mais confuso que o
   problema que resolveria.
3. **Orquestração de lote vive em `servicos/`, não na GUI.** `servicos/lote.py`
   traz `varrer_lote` e `gravar_lote`, corrotinas que não importam `flet`: o
   progresso sai por callback e quem chama decide se aquilo vira barra, log ou
   nada. São os irmãos assíncronos de `substituicao.verificar_lote`, que segue
   existindo como a versão síncrona de um bloco só.
4. **O contrato de direção fica em `app.py`.** Ele governa a janela e `app.py`
   continua sendo a janela. Cada módulo novo abre com docstring sobre o seu
   próprio assunto e aponta para o contrato quando a decisão vem dele.

## Consequências

- **Não se adiciona um método `_cartao_*`, `_painel_*` ou `_campo_*` novo à
  `Bancada`.** Vista nova é módulo novo, ou função nova num módulo de vista
  existente. É por acréscimo que um refactor de GUI é desfeito, não por reversão.
- A `Bancada` caiu de 1391 para 591 linhas e tem uma responsabilidade só:
  layout, áreas vivas, `atualizar()`/`remontar()`, handlers e as transições de
  `Fase`.
- `dialogo.py` não depende mais de `tabela.py`.
- `montar_cartao_de_aquisicao` devolve `CartaoDeAquisicao`, e não só o controle:
  o campo do ecode é o único que a `Bancada` precisa alcançar depois de
  desenhado, porque `_ao_mudar_ecode` restaura o valor anterior escrevendo nele
  quando a digitação não é um número.
- Os aliases de callback (`AoClicar`, `AoAgir`, `AoConfirmarTexto`, `AoEscolher`,
  `AoAlternar`) moram em `controles.py` e aceitam `Awaitable[None] | None`: os
  handlers da janela são metade `def` e metade `async def`, e o Flet aceita as
  duas formas.
- `_nome_personalizado`, `_tabela_estreita` e `_foco_pulso` seguem na `Bancada`,
  não no `EstadoLote` — são preferência de tela, e o lote não muda de sentido
  conforme o usuário digitou o padrão ou escolheu um pronto. Agora viajam como
  argumento nomeado até a vista que os consome.
- As vistas passaram a ser exercitáveis sem abrir janela. Nenhum teste foi
  escrito nesta rodada: a validação foi manual, pelo roteiro completo da janela.
  A porta ficou aberta, e é a razão principal pela qual `servicos/lote.py` valeu
  a extração mesmo sem cobertura hoje.

## Alternativas descartadas

- **Mixins da classe `Bancada`** (`_AquisicaoMixin`, `_FluxosMixin`) — o diff
  seria mínimo porque o corpo dos métodos não mudaria, mas os arquivos
  continuariam mutuamente dependentes via `self`, nada ficaria exercitável
  isoladamente, e o leitor precisaria da MRO para saber onde um método mora.
- **Sub-objetos com referência à `Bancada`** (`PainelDeAquisicao(bancada)`) —
  introduz uma camada de indireção e uma dependência circular de tipo entre
  `app.py` e cada painel, sem remover o acoplamento.
- **Granularidade máxima**, um arquivo por primitivo e por vista — entender uma
  tela passaria a exigir abrir seis arquivos, e os primitivos só fazem sentido
  juntos: compartilham `ALTURA_CAMPO_ECODE` e a mesma moldura.
- **Extrair o contrato de direção para `DESIGN.md`** — ele deixaria de estar sob
  os olhos de quem edita a janela, que é exatamente onde funciona.
- **Repetir o contrato em cada módulo** — oito cópias que divergem na primeira
  edição, o mesmo defeito de duplicação que o cabeçalho de `tabela.py` se orgulha
  de ter eliminado nas larguras de coluna.
