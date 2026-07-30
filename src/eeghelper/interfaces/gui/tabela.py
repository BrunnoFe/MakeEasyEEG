"""A tabela de participantes: uma linha, um canal do instrumento.

O refino aqui é de grade, não de estilo: `_grade()` é a ÚNICA definição das
colunas da tabela, e tanto `cabecalho()` quanto `linha()` a usam. Antes o
cabeçalho e a linha declaravam a mesma sequência de larguras em dois lugares, e
a linha ainda carregava uma margem lateral que o cabeçalho não tinha — o
resultado era cada rótulo deslocado da coluna que nomeia. Uma função, um
alinhamento.

A grade tem dois modos, e eles são exclusivos por imposição do Flutter: dentro
de uma `Row` com rolagem horizontal os filhos recebem largura infinita, e um
`expand` nesse contexto quebra o layout. Então ou as colunas de arquivo esticam
(`estreita=False`) ou a grade inteira tem largura fixa e rola
(`estreita=True`). Quem decide é `Bancada`, medindo o painel — e o mesmo valor
tem de chegar ao cabeçalho e às linhas, senão o rótulo desalinha da coluna que
nomeia, que é exatamente o defeito que este módulo existe para não ter.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import flet as ft

from eeghelper.dominio.modelos import PreviaParticipante
from eeghelper.excecoes import ColisaoDeNomeSaida, SobrescritaRecusada
from eeghelper.interfaces.gui import tema, traco
from eeghelper.interfaces.gui.controles import cifra, rotulo, texto
from eeghelper.interfaces.gui.transicao import Revelar

LARGURA_MARCADOR = 14
# As duas colunas fixas são medidas pelo conteúdo mais largo que cabe nelas, e
# não arredondadas para cima: o nome do eventlist é a ÚNICA coluna elástica da
# grade, então cada pixel folgado aqui sai do identificador da linha — e é ele
# que o usuário lê para saber de qual arquivo a linha fala. Participante cabe o
# dropdown "preencher" (~90); contagem cabe "128 / 130" em Consolas 13 (~64).
LARGURA_PARTICIPANTE = 104
LARGURA_CONTAGEM = 88

# Larguras que só valem no modo estreito, quando nada estica. São o PISO de
# legibilidade, não o confortável: abaixo disto o nome vira elipse e a coluna
# deixa de informar, então é aqui que a grade prefere rolar a espremer. A
# entrada leva 10 px a mais porque é o nome que o usuário não escolheu e por
# isso não consegue prever.
LARGURA_ARQUIVO_FIXA = 180
LARGURA_SAIDA_FIXA = 170
LARGURA_SETA = 14

# Abaixo disto a grade passa a rolar em vez de espremer. Somada aqui a partir
# das partes, e não escrita como número redondo: uma constante decorada ficaria
# errada em silêncio no dia em que uma coluna mudasse de largura.
LARGURA_MINIMA_TABELA = (
    LARGURA_MARCADOR
    + LARGURA_PARTICIPANTE
    + LARGURA_ARQUIVO_FIXA
    + LARGURA_SETA
    + LARGURA_SAIDA_FIXA
    + tema.LARGURA_TRACO
    + LARGURA_CONTAGEM
    + tema.ESPACO_3 * 6
    + tema.CALHA_TABELA * 2
    + tema.MARGEM_LINHA * 2
)


def _grade(
    marcador: ft.Control,
    participante: ft.Control,
    arquivo: ft.Control,
    seta: ft.Control,
    saida: ft.Control,
    fita: ft.Control,
    contagem: ft.Control,
    estreita: bool,
) -> ft.Control:
    """As sete colunas da tabela, definidas uma única vez.

    Cabeçalho e linha passam por aqui, então as bordas de coluna são as mesmas
    nos dois — inclusive as duas colunas elásticas de nome de arquivo, que são
    as que empurram as seguintes se as calhas divergirem.

    A saída fica por ÚLTIMO, depois do traço e da contagem, e não colada no
    eventlist: o traço e a contagem são a leitura do instrumento sobre aquele
    arquivo e pertencem a ele: separá-los do nome quebraria a linha em dois
    assuntos. A saída é a consequência, e consequência se lê no fim. É também a
    coluna que sai de vista primeiro quando a grade rola, e a única cuja
    informação o usuário já pode prever.

    A entrada recebe mais folga que a saída pelo mesmo motivo: ela é o dado
    bruto, a saída é derivada — e o caminho completo dela está no tooltip.
    """
    if estreita:
        celula_arquivo = ft.Container(width=LARGURA_ARQUIVO_FIXA, content=arquivo)
        celula_saida = ft.Container(width=LARGURA_SAIDA_FIXA, content=saida)
    else:
        celula_arquivo = ft.Container(expand=3, content=arquivo)
        celula_saida = ft.Container(expand=2, content=saida)

    return ft.Row(
        spacing=tema.ESPACO_3,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(width=LARGURA_MARCADOR, content=marcador),
            ft.Container(width=LARGURA_PARTICIPANTE, content=participante),
            celula_arquivo,
            ft.Container(width=tema.LARGURA_TRACO, content=fita),
            ft.Container(
                width=LARGURA_CONTAGEM,
                content=ft.Row(alignment=ft.MainAxisAlignment.END, controls=[contagem]),
            ),
            ft.Container(width=LARGURA_SETA, content=seta),
            celula_saida,
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


def cabecalho(estreita: bool = False) -> ft.Control:
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
            seta=ft.Container(),
            saida=rotulo("novos arquivos"),
            fita=rotulo("traço de eventos"),
            contagem=rotulo("alvos / cód."),
            estreita=estreita,
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
            options=[
                ft.DropdownOption(key=coluna, text=coluna, style=tema.estilo_de_opcao())
                for coluna in colunas
            ],
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
            # A seta segue a cor do aviso, e não a do texto: a célula inteira é
            # um pedido de preenchimento, e a seta é o que se clica para
            # atendê-lo.
            trailing_icon=ft.Icon(ft.Icons.EXPAND_MORE, size=16, color=cor.pulado),
            selected_trailing_icon=ft.Icon(ft.Icons.EXPAND_LESS, size=16, color=cor.pulado),
            menu_height=tema.ALTURA_MENU,
            menu_style=tema.estilo_de_menu(),
            on_select=lambda evento: ao_escolher(caminho, evento.control.value),
        ),
    )


def _celula_saida(caminho_saida: Path | None, pulado: bool, colidiu: bool) -> ft.Control:
    """O nome que este participante vai gerar, com o caminho completo no tooltip.

    Mostra só o nome porque a pasta é a mesma em todas as linhas — repeti-la
    duzentas vezes gastaria a coluna com o trecho que não varia, e a elipse do
    fim comeria justamente o sufixo que o usuário está conferindo.
    """
    cor = tema.paleta()
    if pulado or caminho_saida is None:
        return texto("—", cor.texto_fraco)

    return ft.Container(
        tooltip=str(caminho_saida),
        content=texto(caminho_saida.name, cor.divergente if colidiu else cor.texto_medio),
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
    caminho_saida: Path | None = None,
    foco_pulso: str | None = None,
    lote_limpo: bool = True,
    estreita: bool = False,
) -> ft.Control:
    """Uma linha de participante, com realce em pastilha ao pairar o cursor.

    `foco_pulso` só chega diferente de `None` no exato render em que uma
    verificação ou gravação acabou de terminar (ver `Bancada._tela`); em
    qualquer outro redesenho o marcador nasce já no estado final, sem
    assentar — do contrário o pulso replicaria a cada rolagem da lista.
    """
    cor = tema.paleta()
    pulado = participante is None
    # Problemas de NOME, e não de contagem: pintam a coluna de saída, que é onde
    # o usuário pode corrigi-los mudando o padrão ou a pasta.
    colidiu = isinstance(previa.erro, ColisaoDeNomeSaida | SobrescritaRecusada) if previa else False
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
            seta=texto("→", cor.texto_fraco),
            saida=_celula_saida(caminho_saida, pulado, colidiu),
            fita=conteudo_traco,
            contagem=contagem,
            estreita=estreita,
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
