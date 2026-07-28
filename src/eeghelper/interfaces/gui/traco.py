"""O traço: um eventlist inteiro desenhado como uma varredura de instrumento.

Cada linha da tabela carrega o traço do seu participante, e todos os traços
partilham a mesma base de tempo e a mesma medida — é isso que torna duas linhas
comparáveis de relance.

O traço é o único lugar da tela onde a divergência de contagem aparece *onde
ela acontece*. Um selo no fim da linha diria "deu errado"; o cursor de medição
diz "deu errado a partir da terceira marca", que é exatamente a informação que
o assistente de pesquisa não tem como obter de outro jeito.

Camadas, de baixo para cima:

1. a graticule — as divisões verticais e a base de tempo do instrumento;
2. os tiques de evento — um por evento que não é o `ecode` alvo;
3. as marcas — os `ecode` alvo, apagados antes da verificação e acesos na cor do
   estado depois dela;
4. o cursor de medição — régua vertical na posição da divergência, com o trecho
   sem correspondência redesenhado tracejado.
"""

from __future__ import annotations

import flet.canvas as cv

import flet as ft
from eeghelper.dominio.modelos import PreviaParticipante
from eeghelper.interfaces.gui import tema

MARGEM = 1.0
_DIVISOES = 4  # divisões verticais da graticule, como num instrumento real


def posicao_em_pixels(indice: int, total: int, largura: float) -> float:
    """Converte o índice de um evento na coordenada x do traço."""
    if total <= 1:
        return MARGEM
    util = largura - 2 * MARGEM
    return MARGEM + (indice / (total - 1)) * util


def _colunas(indices: list[int], total: int, largura: float) -> list[float]:
    """Agrupa índices por coluna de pixel.

    Um eventlist de milhares de eventos não cabe em 420 px como traços
    distintos, e desenhar um shape por evento custaria caro em 200 linhas.
    Agrupar por pixel mantém a leitura — densidade e posição — e limita o
    desenho à largura do traço.
    """
    vistos: dict[int, float] = {}
    for indice in indices:
        x = posicao_em_pixels(indice, total, largura)
        vistos.setdefault(round(x), x)
    return list(vistos.values())


def graticule(largura: float, altura: float) -> list[cv.Shape]:
    """A grade do instrumento: base de tempo e divisões verticais."""
    cor = tema.paleta()
    meio = altura / 2
    formas: list[cv.Shape] = [
        cv.Line(
            x1=MARGEM,
            y1=meio,
            x2=largura - MARGEM,
            y2=meio,
            paint=ft.Paint(color=cor.graticule, stroke_width=1),
        )
    ]
    for divisao in range(1, _DIVISOES):
        x = MARGEM + (largura - 2 * MARGEM) * divisao / _DIVISOES
        formas.append(
            cv.Line(
                x1=x,
                y1=2,
                x2=x,
                y2=altura - 2,
                paint=ft.Paint(color=cor.graticule, stroke_width=1, stroke_dash_pattern=[1, 3]),
            )
        )
    # As cabeceiras impedem que o traço seja lido como barra de progresso: sem
    # elas, marcas concentradas à esquerda pareceriam "40% feito" em vez de
    # "os alvos estão nesta região da gravação".
    for x in (MARGEM, largura - MARGEM):
        formas.append(
            cv.Line(
                x1=x,
                y1=meio - 6,
                x2=x,
                y2=meio + 6,
                paint=ft.Paint(color=cor.traco, stroke_width=1),
            )
        )
    return formas


def cor_do_estado(previa: PreviaParticipante | None, verificado: bool, pulado: bool) -> str:
    """A cor de canal que descreve este participante.

    Regra única de cor da interface: antes da verificação nada foi decidido, e
    marca acesa em verde num lote que ninguém calculou seria uma promessa
    falsa. Depois dela, verde é gravável, coral é contagem que não fecha e
    âmbar é arquivo sem coluna, que nunca chegou a entrar no lote.
    """
    cor = tema.paleta()
    if pulado:
        return cor.pulado
    if not verificado or previa is None:
        return cor.texto_medio
    return cor.pronto if previa.gravavel else cor.divergente


def _cor_das_marcas(previa: PreviaParticipante, verificado: bool) -> str:
    """A cor das marcas de `ecode` alvo dentro do traço.

    Deliberadamente diferente da cor do estado da linha. Num participante
    divergente *nenhuma* troca acontece, então pintar as marcas pareáveis de
    coral inundaria o traço inteiro e afogaria justamente o cursor, que é a
    única coisa ali que diz onde o problema está. Elas ficam neutras: coral no
    traço é reservado ao cursor e ao trecho sem correspondência.
    """
    cor = tema.paleta()
    if verificado and previa.gravavel:
        return cor.pronto
    return cor.texto_medio


def desenhar(
    previa: PreviaParticipante,
    verificado: bool,
    largura: float = tema.LARGURA_TRACO,
    altura: float = tema.ALTURA_TRACO,
) -> list[cv.Shape]:
    """Monta os shapes do traço de um participante."""
    cor = tema.paleta()
    meio = altura / 2
    formas = graticule(largura, altura)

    total = previa.total_eventos
    if total == 0:
        return formas

    alvos = set(previa.posicoes_alvo)
    nao_alvos = [indice for indice in range(total) if indice not in alvos]
    for x in _colunas(nao_alvos, total, largura):
        formas.append(
            cv.Line(
                x1=x,
                y1=meio - 3.5,
                x2=x,
                y2=meio + 3.5,
                paint=ft.Paint(color=cor.traco, stroke_width=1),
            )
        )

    cor_marca = _cor_das_marcas(previa, verificado)
    quebra = previa.indice_divergencia if verificado else None

    for ordem, indice in enumerate(previa.posicoes_alvo):
        x = posicao_em_pixels(indice, total, largura)
        # Depois do ponto de quebra não existe correspondência nenhuma: aquelas
        # marcas continuam desenhadas, porque os eventos existem no arquivo, mas
        # tracejadas e apagadas, porque nada será escrito nelas.
        pareada = quebra is None or ordem < quebra
        if pareada and verificado and previa.gravavel:
            # Halo de fósforo: um traço largo e translúcido sob a marca nítida.
            # É o que faz a marca acesa parecer luz e não adesivo.
            formas.append(
                cv.Line(
                    x1=x,
                    y1=2,
                    x2=x,
                    y2=altura - 2,
                    paint=ft.Paint(color=ft.Colors.with_opacity(0.18, cor_marca), stroke_width=4),
                )
            )
        formas.append(
            cv.Line(
                x1=x,
                y1=2,
                x2=x,
                y2=altura - 2,
                paint=ft.Paint(
                    color=cor_marca if pareada else cor.texto_fraco,
                    stroke_width=2 if pareada else 1,
                    stroke_dash_pattern=None if pareada else [2, 2],
                ),
            )
        )

    if quebra is not None:
        formas.extend(_cursor(previa, quebra, total, largura, altura))

    return formas


def _cursor(
    previa: PreviaParticipante,
    quebra: int,
    total: int,
    largura: float,
    altura: float,
) -> list[cv.Shape]:
    """O cursor de medição sobre a posição exata da divergência.

    Quando sobram códigos na planilha em vez de faltarem, não existe marca
    nenhuma na divergência: ela acontece logo *depois* da última. O cursor fica
    ali, três pixels adiante, e não na borda — a borda diria que o descompasso
    está no fim da gravação, quando ele está no fim das marcas.
    """
    cor = tema.paleta()
    if quebra < len(previa.posicoes_alvo):
        x = posicao_em_pixels(previa.posicoes_alvo[quebra], total, largura)
    elif previa.posicoes_alvo:
        x = min(posicao_em_pixels(previa.posicoes_alvo[-1], total, largura) + 3, largura - MARGEM)
    else:
        x = MARGEM

    pincel = ft.Paint(color=cor.divergente, stroke_width=2)
    return [
        cv.Line(x1=x, y1=0, x2=x, y2=altura, paint=pincel),
        # As duas cabeças do cursor, como no instrumento: elas dizem que aquela
        # régua é uma medição posicionada, não uma borda de seção.
        cv.Line(x1=x - 3, y1=1, x2=x + 3, y2=1, paint=pincel),
        cv.Line(x1=x - 3, y1=altura - 1, x2=x + 3, y2=altura - 1, paint=pincel),
        cv.Line(
            x1=x,
            y1=altura / 2,
            x2=largura - MARGEM,
            y2=altura / 2,
            paint=ft.Paint(
                color=ft.Colors.with_opacity(0.5, cor.divergente),
                stroke_width=1,
                stroke_dash_pattern=[3, 3],
            ),
        ),
    ]


def construir(previa: PreviaParticipante, verificado: bool) -> cv.Canvas:
    return cv.Canvas(
        width=tema.LARGURA_TRACO,
        height=tema.ALTURA_TRACO,
        shapes=desenhar(previa, verificado),
    )


def vazio() -> cv.Canvas:
    """A graticule sozinha, para quem ainda não foi lido do disco."""
    return cv.Canvas(
        width=tema.LARGURA_TRACO,
        height=tema.ALTURA_TRACO,
        shapes=graticule(tema.LARGURA_TRACO, tema.ALTURA_TRACO),
    )
