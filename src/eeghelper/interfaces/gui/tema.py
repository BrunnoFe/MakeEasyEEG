"""Tokens visuais da interface: A BANCADA, refino 1a.

O que mudou em relação à versão anterior, e por quê:

- **Paleta reancorada.** Os neutros escuros ganharam um resto de teal em vez de
  azul-cinza (`#0A0E11` / `#111B21` / `#21303A`), e as quatro cores de canal
  foram trocadas por uma família de matiz coerente: menta `#38E2B0` para
  pronto, ciano `#38BDF8` para varrendo, âmbar `#FBBF24` para sem coluna e
  coral `#FB7185` para divergente. O modo claro é o mesmo instrumento sob luz
  de laboratório: mesmos matizes, luminosidade reancorada para ≥4.5:1.
- **Acento de marca.** `acento` e `acento_2` existem só para o wordmark e o
  preenchimento do botão que grava — nenhuma superfície de conteúdo os usa.
- **Raios e sombras revistos.** Cartão 14, painel 14, chip 9; a sombra do
  painel ficou mais alta e mais suave, para o cartão parecer flutuar sobre o
  gabinete em vez de ter uma borda escura.
- **Grade de colunas em token.** `CALHA_TABELA` e `MARGEM_LINHA` passaram a ser
  tokens porque cabeçalho e linha *precisam* usar os dois valores iguais — foi
  o desalinhamento entre rótulo e coluna que motivou este refino.
"""

from __future__ import annotations

from dataclasses import dataclass

import flet as ft


@dataclass(frozen=True)
class Paleta:
    """As cores de um dos dois modos do instrumento."""

    escura: bool

    tela: str
    painel: str
    painel_alto: str
    graticule: str
    traco: str
    contorno: str
    contorno_forte: str

    texto: str
    texto_medio: str
    texto_fraco: str

    pronto: str
    varrendo: str
    pulado: str
    divergente: str

    acento: str
    acento_2: str
    sobre_acento: str
    sombra: str
    sombra_alta: str


ESCURA = Paleta(
    escura=True,
    tela="#0A0E11",
    painel="#111B21",
    painel_alto="#18232A",
    graticule="#22323C",
    traco="#3D525E",
    contorno="#21303A",
    contorno_forte="#2C3E49",
    texto="#E6EEF2",
    texto_medio="#9AAFB9",
    texto_fraco="#6F8189",
    pronto="#38E2B0",
    varrendo="#38BDF8",
    pulado="#FBBF24",
    divergente="#FB7185",
    acento="#38E2B0",
    acento_2="#1FA8C9",
    sobre_acento="#04231A",
    sombra="#59000000",
    sombra_alta="#73000000",
)

CLARA = Paleta(
    escura=False,
    tela="#EEF2F4",
    painel="#FFFFFF",
    painel_alto="#F2F6F8",
    graticule="#DBE4E8",
    traco="#B3C4CC",
    contorno="#DCE5E9",
    contorno_forte="#CBD8DE",
    texto="#0B1417",
    texto_medio="#41535B",
    texto_fraco="#66787F",
    pronto="#0B7A5A",
    varrendo="#0B7C99",
    pulado="#8A5A00",
    divergente="#C62A1C",
    acento="#0FA47F",
    acento_2="#0D7F9C",
    sobre_acento="#FFFFFF",
    sombra="#12000000",
    sombra_alta="#1F000000",
)

_atual: Paleta = ESCURA


def paleta() -> Paleta:
    """A paleta do modo em vigor. Nunca guarde uma cor em variável longa."""
    return _atual


def alternar_modo() -> Paleta:
    global _atual
    _atual = CLARA if _atual.escura else ESCURA
    return _atual


def modo_flet() -> ft.ThemeMode:
    return ft.ThemeMode.DARK if _atual.escura else ft.ThemeMode.LIGHT


# --- Tipografia ----------------------------------------------------------
FAMILIA_TEXTO = "Segoe UI"
FALLBACK_TEXTO = ["Inter", "Helvetica Neue", "Arial", "sans-serif"]

# A cifra é a monoespaçada que a máquina já tem: numerais tabulares alinhados em
# coluna, sem baixar fonte nenhuma. O app roda em bancada de laboratório, muitas
# vezes sem rede, e uma janela que espera um download para desenhar a primeira
# contagem seria pior do que uma que usa a Consolas.
FAMILIA_CIFRA = "Consolas"
FALLBACK_CIFRA = ["SF Mono", "DejaVu Sans Mono", "Courier New", "monospace"]

CORPO_MICRO = 10.5
CORPO = 13.0
CORPO_SECAO = 15.0
CORPO_TITULO = 19.0
CORPO_LEITURA = 28.0

TRACKING_ROTULO = 1.3

# --- Ritmo ---------------------------------------------------------------
ESPACO_1 = 4
ESPACO_2 = 8
ESPACO_3 = 12
ESPACO_4 = 16
ESPACO_5 = 22
ESPACO_6 = 32

# --- Forma ---------------------------------------------------------------
RAIO_CHIP = 9
RAIO_CARTAO = 14
RAIO_PAINEL = 14
RAIO_LINHA = 8
RAIO_PILULA = 999

# --- Medidas fixas -------------------------------------------------------
ALTURA_LINHA = 34
ALTURA_CABECALHO = 32
LARGURA_TRACO = 380
ALTURA_TRACO = 20
LARGURA_COLUNA_CONTROLE = 308

# A coluna de controle tem um bloco que rola (a aquisição) e dois que não (a
# leitura e as ações). Os três são desenhados nesta largura menor, e a calha que
# sobra à direita é onde a barra de rolagem cabe — sem ela, o único bloco rolável
# ficaria mais estreito que os outros dois e as bordas direitas não fechariam.
CALHA_ROLAGEM = 10
LARGURA_CARTAO_CONTROLE = LARGURA_COLUNA_CONTROLE - CALHA_ROLAGEM

# A grade da tabela. Cabeçalho e linha usam OS DOIS valores, iguais: a linha
# tem margem lateral porque o realce de hover é uma pastilha arredondada, e o
# cabeçalho precisa da mesma margem ou cada rótulo cai deslocado da sua coluna.
CALHA_TABELA = 20
MARGEM_LINHA = 8

LARGURA_MINIMA_JANELA = 1180
ALTURA_MINIMA_JANELA = 700

# --- Movimento -----------------------------------------------------------
MS_RAPIDO = 140
MS_TRANSICAO = 220
MS_VARREDURA = 1900  # ida da luz de espera na fita vazia
CURVA = ft.AnimationCurve.EASE_OUT_CUBIC
CURVA_VARREDURA = ft.AnimationCurve.EASE_IN_OUT_SINE

# Deslocamento vertical (fração da altura do controle) do assentamento de
# `Revelar`. O padrão serve a cifras e mensagens; os dois extremos servem ao
# pulso dos marcadores de canal no instante em que uma verificação ou
# gravação termina — cheio quando o lote saiu limpo, contido quando não saiu,
# porque o instrumento nunca comemora um lote com divergência.
DESLOCAMENTO_REVELAR = 0.06
DESLOCAMENTO_PULSO_CHEIO = 0.14
DESLOCAMENTO_PULSO_CONTIDO = 0.03


def animacao(ms: int = MS_TRANSICAO) -> ft.Animation:
    return ft.Animation(ms, CURVA)


def sombra(alta: bool = False) -> ft.BoxShadow:
    """Sombra do instrumento: sempre com deslocamento e desfoque."""
    cor = paleta()
    if alta:
        return ft.BoxShadow(
            spread_radius=0, blur_radius=28, color=cor.sombra_alta, offset=ft.Offset(0, 10)
        )
    return ft.BoxShadow(spread_radius=0, blur_radius=14, color=cor.sombra, offset=ft.Offset(0, 4))


def brilho(cor_estado: str, forca: float = 0.45) -> ft.BoxShadow:
    """Halo de fósforo do marcador de canal: só no modo escuro.

    Sob luz de laboratório um halo não lê como luz, lê como borrão — no claro a
    cor cheia do marcador já basta.
    """
    return ft.BoxShadow(
        spread_radius=0,
        blur_radius=8 if paleta().escura else 0,
        color=ft.Colors.with_opacity(forca if paleta().escura else 0.0, cor_estado),
        offset=ft.Offset(0, 0),
    )
