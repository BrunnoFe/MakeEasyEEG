"""A tabela de participantes: uma linha, um canal do instrumento.

O refino aqui é de grade, não de estilo: `_grade()` é a ÚNICA definição das
colunas da tabela, e tanto `cabecalho()` quanto `linha()` a usam. Antes o
cabeçalho e a linha declaravam a mesma sequência de larguras em dois lugares, e
a linha ainda carregava uma margem lateral que o cabeçalho não tinha — o
resultado era cada rótulo deslocado da coluna que nomeia. Uma função, um
alinhamento.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import flet as ft
from eeghelper.dominio.modelos import PreviaParticipante
from eeghelper.interfaces.gui import tema, traco
from eeghelper.interfaces.gui.transicao import Revelar

LARGURA_MARCADOR = 14
# As duas colunas fixas são medidas pelo conteúdo mais largo que cabe nelas, e
# não arredondadas para cima: o nome do eventlist é a ÚNICA coluna elástica da
# grade, então cada pixel folgado aqui sai do identificador da linha — e é ele
# que o usuário lê para saber de qual arquivo a linha fala. Participante cabe o
# dropdown "preencher" (~90); contagem cabe "128 / 130" em Consolas 13 (~64).
LARGURA_PARTICIPANTE = 104
LARGURA_CONTAGEM = 88


def cifra(valor: str, cor: str | None = None, negrito: bool = False) -> ft.Text:
    """Leitura numérica do instrumento: monoespaçada e alinhada à direita."""
    return ft.Text(
        valor,
        font_family=tema.FAMILIA_CIFRA,
        font_family_fallback=tema.FALLBACK_CIFRA,
        size=tema.CORPO,
        color=cor or tema.paleta().texto,
        weight=ft.FontWeight.W_700 if negrito else ft.FontWeight.NORMAL,
        text_align=ft.TextAlign.RIGHT,
        no_wrap=True,
    )


def rotulo(texto_: str, cor: str | None = None) -> ft.Text:
    """Rótulo versalete: caixa alta, corpo miúdo, entreletra aberta."""
    return ft.Text(
        texto_.upper(),
        font_family=tema.FAMILIA_TEXTO,
        font_family_fallback=tema.FALLBACK_TEXTO,
        size=tema.CORPO_MICRO,
        color=cor or tema.paleta().texto_fraco,
        weight=ft.FontWeight.W_600,
        style=ft.TextStyle(letter_spacing=tema.TRACKING_ROTULO),
        no_wrap=True,
        # Como `texto()`: um rótulo que não coube deve terminar em elipse, e não
        # ser cortado no meio do glifo. Não muda nada enquanto ele couber.
        overflow=ft.TextOverflow.ELLIPSIS,
    )


def texto(valor: str, cor: str | None = None, tamanho: float = tema.CORPO) -> ft.Text:
    return ft.Text(
        valor,
        font_family=tema.FAMILIA_TEXTO,
        font_family_fallback=tema.FALLBACK_TEXTO,
        size=tamanho,
        color=cor or tema.paleta().texto,
        no_wrap=True,
        overflow=ft.TextOverflow.ELLIPSIS,
    )


def _grade(
    marcador: ft.Control,
    participante: ft.Control,
    arquivo: ft.Control,
    fita: ft.Control,
    contagem: ft.Control,
) -> ft.Control:
    """As cinco colunas da tabela, definidas uma única vez.

    Cabeçalho e linha passam por aqui, então as bordas de coluna são as mesmas
    nos dois — inclusive a coluna elástica do nome do arquivo, que é a que
    empurra as duas colunas seguintes se as calhas divergirem.
    """
    return ft.Row(
        spacing=tema.ESPACO_3,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(width=LARGURA_MARCADOR, content=marcador),
            ft.Container(width=LARGURA_PARTICIPANTE, content=participante),
            ft.Container(expand=True, content=arquivo),
            ft.Container(width=tema.LARGURA_TRACO, content=fita),
            ft.Container(
                width=LARGURA_CONTAGEM,
                content=ft.Row(alignment=ft.MainAxisAlignment.END, controls=[contagem]),
            ),
        ],
    )


def _marcador_de_canal(cor_estado: str, aceso: bool) -> ft.Control:
    """O marcador que os instrumentos põem à esquerda de cada traço."""
    return ft.Container(
        width=8,
        height=8,
        bgcolor=cor_estado if aceso else ft.Colors.TRANSPARENT,
        border=None if aceso else ft.Border.all(width=1.5, color=cor_estado),
        border_radius=tema.RAIO_PILULA,
        shadow=tema.brilho(cor_estado) if aceso else None,
        animate=tema.animacao(tema.MS_RAPIDO),
    )


def cabecalho() -> ft.Control:
    """Cabeçalho de colunas, na mesma calha e na mesma margem das linhas."""
    cor = tema.paleta()
    return ft.Container(
        height=tema.ALTURA_CABECALHO,
        padding=ft.Padding.symmetric(horizontal=tema.CALHA_TABELA),
        margin=ft.Margin.symmetric(horizontal=tema.MARGEM_LINHA),
        border=ft.Border(bottom=ft.BorderSide(width=1, color=cor.contorno)),
        content=_grade(
            marcador=ft.Container(),
            participante=rotulo("participante"),
            arquivo=rotulo("eventlist"),
            fita=rotulo("traço de eventos"),
            contagem=rotulo("alvos / cód."),
        ),
    )


def _celula_participante(
    caminho: Path,
    participante: str | None,
    colunas: list[str],
    ao_escolher: Callable[[Path, str | None], None],
) -> ft.Control:
    """Nome da coluna casada, ou o campo em branco a ser preenchido."""
    cor = tema.paleta()
    if participante is not None:
        return texto(participante)

    return ft.Container(
        height=tema.ALTURA_LINHA - tema.ESPACO_1 - 2,
        bgcolor=ft.Colors.with_opacity(0.14, cor.pulado),
        border=ft.Border.all(width=1, color=ft.Colors.with_opacity(0.35, cor.pulado)),
        border_radius=tema.RAIO_LINHA,
        padding=ft.Padding.only(left=tema.ESPACO_2 + 2, right=tema.ESPACO_1),
        align=ft.Alignment.CENTER_LEFT,
        animate=tema.animacao(tema.MS_RAPIDO),
        content=ft.Dropdown(
            height=tema.ALTURA_LINHA - tema.ESPACO_1 - 2,
            value=None,
            hint_text="preencher",
            hint_style=ft.TextStyle(
                size=tema.CORPO_MICRO + 1,
                color=cor.pulado,
                weight=ft.FontWeight.W_500,
                font_family=tema.FAMILIA_TEXTO,
            ),
            options=[ft.DropdownOption(key=coluna, text=coluna) for coluna in colunas],
            border=ft.InputBorder.NONE,
            dense=True,
            filled=False,
            text_size=tema.CORPO_MICRO + 1,
            text_style=ft.TextStyle(
                size=tema.CORPO_MICRO + 1,
                color=cor.texto,
                font_family=tema.FAMILIA_TEXTO,
            ),
            content_padding=ft.Padding.all(0),
            menu_height=320,
            on_select=lambda evento: ao_escolher(caminho, evento.control.value),
        ),
    )


def _amplitude_do_pulso(
    foco_pulso: str | None, previa: PreviaParticipante | None, lote_limpo: bool
) -> float | None:
    """O deslocamento do assentamento do marcador ao fim de uma verificação ou
    gravação: cheio quando o lote não tem nada a esconder, contido quando tem
    — e a divergência sempre recebe o cheio, mesmo num lote sujo, porque é
    exatamente o que "errar alto, nunca quieto" pede para destacar.
    """
    if foco_pulso is None or previa is None:
        return None
    if foco_pulso == "verificacao":
        divergente = not previa.gravavel
        if lote_limpo or divergente:
            return tema.DESLOCAMENTO_PULSO_CHEIO
        return tema.DESLOCAMENTO_PULSO_CONTIDO
    if foco_pulso == "gravacao" and previa.gravavel:
        return tema.DESLOCAMENTO_PULSO_CHEIO if lote_limpo else tema.DESLOCAMENTO_PULSO_CONTIDO
    return None


def linha(
    caminho: Path,
    participante: str | None,
    previa: PreviaParticipante | None,
    verificado: bool,
    colunas: list[str],
    ao_escolher: Callable[[Path, str | None], None],
    foco_pulso: str | None = None,
    lote_limpo: bool = True,
) -> ft.Control:
    """Uma linha de participante, com realce em pastilha ao pairar o cursor.

    `foco_pulso` só chega diferente de `None` no exato render em que uma
    verificação ou gravação acabou de terminar (ver `Bancada._tela`); em
    qualquer outro redesenho o marcador nasce já no estado final, sem
    assentar — do contrário o pulso replicaria a cada rolagem da lista.
    """
    cor = tema.paleta()
    pulado = participante is None
    cor_estado = traco.cor_do_estado(previa, verificado, pulado)
    decidido = pulado or (verificado and previa is not None)
    amplitude_pulso = None if pulado else _amplitude_do_pulso(foco_pulso, previa, lote_limpo)

    if previa is not None:
        divergente = verificado and not previa.gravavel
        contagem: ft.Control = cifra(
            f"{previa.total_alvos} / {previa.total_codigos}",
            cor=cor.divergente if divergente else cor.texto,
            negrito=divergente,
        )
        conteudo_traco: ft.Control = traco.construir(previa, verificado)
    else:
        contagem = cifra("— / —", cor=cor.texto_fraco)
        conteudo_traco = traco.vazio()

    # O fundo de repouso da linha sem coluna é tingido de âmbar: é a única
    # linha da tabela que pede uma ação do usuário, e a margem sozinha não
    # chama o olho num lote de duzentos arquivos.
    repouso = ft.Colors.with_opacity(0.06, cor.pulado) if pulado else ft.Colors.TRANSPARENT

    marcador: ft.Control = _marcador_de_canal(cor_estado, aceso=decidido)
    if amplitude_pulso is not None:
        marcador = Revelar(marcador, deslocamento=amplitude_pulso)

    fundo = ft.Container(
        height=tema.ALTURA_LINHA,
        bgcolor=repouso,
        border_radius=tema.RAIO_LINHA,
        padding=ft.Padding.symmetric(horizontal=tema.CALHA_TABELA),
        margin=ft.Margin.symmetric(horizontal=tema.MARGEM_LINHA),
        animate=tema.animacao(tema.MS_RAPIDO),
        content=_grade(
            marcador=marcador,
            participante=_celula_participante(caminho, participante, colunas, ao_escolher),
            arquivo=texto(caminho.name, cor.texto_fraco if pulado else cor.texto_medio),
            fita=conteudo_traco,
            contagem=contagem,
        ),
    )

    def ao_pairar(evento: ft.Event[ft.Container]) -> None:
        if evento.data:
            fundo.bgcolor = ft.Colors.with_opacity(0.12, cor.pulado) if pulado else cor.painel_alto
        else:
            fundo.bgcolor = repouso
        fundo.update()

    fundo.on_hover = ao_pairar
    return fundo
