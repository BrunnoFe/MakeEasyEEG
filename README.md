# EEGHelper

Corrige os marcadores (`ecode`) dos **eventlists** do EEGLAB/ERPLAB a partir de
uma planilha de identificação por participante.

## O problema

O eventlist gerado pelo ERPLAB registra *quando* cada estímulo ocorreu, mas não
*qual* estímulo foi: todos os eventos saem com `ecode = 1`. A identificação real
vem de uma análise separada (software de execução do experimento), salva em uma
planilha `.csv`/`.xlsx` com uma coluna por participante.

O EEGHelper cruza os dois: para cada eventlist, substitui em ordem os `ecode`
alvo pelos códigos da coluna do participante correspondente.

## Regras adotadas

- **Só a coluna `ecode` muda.** Cabeçalho, `label`, `onset`, `bin` e formatação
  em colunas ficam byte a byte iguais.
- **Linhas de `boundary` (`ecode = -99`) são ignoradas** — a contagem começa no
  primeiro evento real.
- **Pareamento posicional:** a n-ésima ocorrência do `ecode` alvo recebe o
  n-ésimo código da planilha.
- **`ecode` alvo configurável** (`--ecode-alvo`, padrão `1`).
- **O original nunca é sobrescrito.** Sai um `<nome>_corrigido.txt` mais um
  `relatorio_substituicoes.csv` com uma linha por troca.
- **Contagem incompatível aborta aquele participante** e o erro é reportado ao
  final, sem impedir os demais. Seguir adiante desalinharia todos os marcadores
  seguintes.

## Formato da planilha

Primeira coluna = número do evento; demais colunas = um participante cada
(separador `,` ou `;` é detectado automaticamente):

```
event;B0001;B0002;B0003
1;9;9;9
2;9;12;9
```

## Uso

```bash
# Interface desktop (Flet)
uv run eeghelper-gui

# Tudo por diálogo gráfico (Tkinter)
uv run eeghelper

# Lote, sem diálogos
uv run eeghelper --eventlists eventlists --marcadores marcadores.csv --saida saida

# Outro ecode alvo e mapeamento manual arquivo -> coluna
uv run eeghelper --ecode-alvo 2 --mapeamento manual
```

O mapeamento `auto` extrai o ID do nome do arquivo (`B0002_eventos.txt` →
coluna `B0002`); o que não casar é perguntado ao usuário.

Código de saída: `0` tudo certo, `1` entrada inválida/cancelada, `2` algum
participante falhou.

## Desenvolvimento

```bash
uv sync              # cria .venv e instala tudo
uv run pytest        # testes
uv run ruff check    # lint
uv run ruff format . # formatação
```

## Arquitetura

```
src/eeghelper/
├── config.py          # ConfiguracaoSubstituicao (dataclass)
├── excecoes.py        # hierarquia de erros esperados
├── dominio/modelos.py # LinhaEventlist, Eventlist, RelatorioSubstituicao
├── io_/               # leitura/escrita de eventlist e planilha
├── servicos/          # mapeamento e substituição (regra de negócio pura)
└── interfaces/
    ├── cli.py         # linha de comando (argparse)
    ├── dialogos.py    # diálogos de arquivo (Tkinter)
    └── gui/           # janela desktop (Flet)
```

`servicos` e `dominio` não conhecem Flet, Tkinter nem `argparse`.

### Verificar antes de gravar

O serviço separa o cálculo da escrita:

- `verificar_lote` devolve uma `PreviaParticipante` por participante **sem tocar
  em disco**, inclusive para quem falhou — a prévia guarda as posições dos
  `ecode` alvo e o ponto exato onde as contagens divergem;
- `gravar_previas` grava só as prévias que a verificação aprovou.

`processar_lote` (usado pela CLI) é a composição das duas. A interface desktop
exige a verificação: a gravação só destrava depois dela, e qualquer mudança nas
entradas descarta a prévia e trava tudo de novo.

Ver `docs/tutorial-projeto-python-uv.md` para o passo a passo de criação do
repositório.
