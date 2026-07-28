# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

Registrado como `web` por convenção do Impeccable. A cena real de uso é **desktop**:
a interface planejada em Flet roda como aplicativo nativo na máquina do laboratório,
lendo e escrevendo arquivos locais. Não há navegador, upload nem servidor.

## Users

Usuário principal: **assistente de pesquisa / bolsista** de um laboratório de EEG.
Executa a etapa mecânica de corrigir marcadores no meio do pré-processamento
EEGLAB/ERPLAB, sem dominar o ERPLAB a fundo. Trabalha em lote, com uma pasta de
eventlists e uma planilha de identificação por participante.

Consequência: a ferramenta deve proteger contra erro silencioso, não oferecer
flexibilidade. O usuário não tem como perceber sozinho que um marcador ficou
desalinhado.

O autor (pesquisador com domínio de ERPLAB) é usuário secundário, tipicamente via CLI.

## Product Purpose

O eventlist do ERPLAB registra *quando* cada estímulo ocorreu, mas não *qual* — todos
os eventos saem com `ecode = 1`. A identificação real vem de uma planilha externa
gerada pelo software de execução do experimento, com uma coluna por participante.

O EEGHelper cruza os dois: para cada eventlist, substitui em ordem os `ecode` alvo
pelos códigos da coluna do participante correspondente.

Sucesso = o lote inteiro sai corrigido, com um relatório auditável de cada troca, e
qualquer participante cuja contagem não bate falha visivelmente em vez de sair errado.

## Positioning

Automatiza um cruzamento que hoje é feito à mão ou em scripts MATLAB descartáveis,
com duas garantias que um script ad hoc não dá: **preservação byte a byte** de tudo
que não é a coluna `ecode` (cabeçalho, `label`, `onset`, `bin`, alinhamento em colunas)
e **relatório de substituições** linha a linha.

## Operating Context

- Pipeline EEGLAB/ERPLAB; o EEGHelper entra entre a geração do eventlist e o binlister.
- Entradas: pasta de eventlists `.txt` do ERPLAB + planilha `.csv`/`.xlsx` (primeira
  coluna = número do evento, demais colunas = um participante cada; separador `,` ou `;`
  detectado automaticamente).
- Saídas: `<nome>_corrigido.txt` por eventlist + um `relatorio_substituicoes.csv`.
- Mapeamento arquivo → coluna: modo `auto` extrai o ID do nome do arquivo
  (`B0002_eventos.txt` → coluna `B0002`); o que não casar é perguntado ao usuário.
  Modo `manual` pergunta tudo.
- Interfaces: CLI (`argparse`), diálogos Tkinter e a janela desktop em Flet
  (`interfaces/gui/`, comando `eeghelper-gui`).
- A janela desktop exige **verificação antes de gravar**: o lote é calculado inteiro
  sem tocar em disco, o resultado é exibido participante a participante, e só então
  a gravação destrava. Mudar qualquer entrada descarta a verificação.

## Capabilities and Constraints

Confirmado:

- Só a coluna `ecode` muda; todo o resto do arquivo é preservado byte a byte.
- Linhas de `boundary` (`ecode = -99`) são ignoradas na contagem.
- Pareamento posicional: a n-ésima ocorrência do `ecode` alvo recebe o n-ésimo código
  da planilha.
- `ecode` alvo configurável (`--ecode-alvo`, padrão `1`).
- Códigos de saída: `0` tudo certo, `1` entrada inválida/cancelada, `2` algum
  participante falhou.
- Python ≥ 3.13, `uv` como gerenciador; `pandas` e `openpyxl` como dependências.
- `servicos` e `dominio` são puros: não conhecem Tkinter nem `argparse`.

Terminologia (usada verbatim no código e na UI, em português): eventlist, ecode,
marcador, participante, mapeamento, substituição, relatório, boundary, bin, onset.

## Brand Commitments

- **Toda a interface e o código em português (pt-BR):** nomes de identificadores,
  mensagens de erro, rótulos e documentação.
- Nome do projeto: EEGHelper.

## Evidence on Hand

- `README.md` — problema, regras adotadas, formato da planilha, uso.
- `docs/tutorial-projeto-python-uv.md` — histórico de criação do repositório.
- `tests/test_substituicao.py` — regra de negócio coberta por testes.
- Não há capturas de tela, logo, dados de exemplo publicáveis, usuários citáveis nem
  qualquer métrica de adoção. Trabalho futuro não deve inventar nenhum deles.

## Product Principles

1. **Errar alto, nunca errar quieto.** Contagem incompatível aborta aquele participante
   e é reportada ao final; seguir adiante desalinharia todos os marcadores seguintes.
2. **Falha isolada por participante.** Um erro não impede o processamento dos demais.
3. **O original é intocável.** A saída é sempre um arquivo novo mais o relatório de
   substituições — em qualquer interface, inclusive na futura GUI.
4. **Offline por princípio.** Dados de EEG nunca saem da máquina: sem nuvem, sem
   serviço externo, sem telemetria.
5. **Regra de negócio no núcleo, não na interface.** Cada nova interface é uma casca
   sobre `servicos.substituicao.processar_lote`.

## Accessibility & Inclusion

Nenhum requisito específico de acessibilidade foi estabelecido. Em aberto.
