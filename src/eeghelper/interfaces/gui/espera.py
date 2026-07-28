"""A fita de espera do estado vazio.

A tela vazia mostra uma fita sem participante nenhum e uma luz que a percorre —
é o que ensina, antes de qualquer arquivo ser escolhido, que aquela tira de 380
px é uma gravação inteira e não uma barra de progresso.

**A luz nunca sai da fita.** Ela vai de `MARGEM` até
`LARGURA_TRACO - MARGEM - LARGURA_LUZ` e volta, e o `Stack` recorta em
`HARD_EDGE` — os dois juntos, porque o recorte garante o limite mesmo se a
animação for interrompida no meio por um redesenho de tema. Uma luz que começa
antes da cabeceira sugeriria que a gravação começa fora do quadro, que é
exatamente o contrário do que a fita afirma.
"""

from __future__ import annotations

import asyncio

import flet.canvas as cv

import flet as ft
from eeghelper.interfaces.gui import tema
from eeghelper.interfaces.gui.traco import MARGEM, graticule

LARGURA_LUZ = 46


class FitaDeEspera(ft.Stack):
    """A graticule vazia com a luz de espera correndo dentro dela."""

    def __init__(self) -> None:
        cor = tema.paleta()
        self._inicio = MARGEM
        self._fim = tema.LARGURA_TRACO - MARGEM - LARGURA_LUZ

        self.luz = ft.Container(
            width=LARGURA_LUZ,
            top=2,
            bottom=2,
            left=self._inicio,
            border_radius=2,
            # Gradiente que apaga nas duas pontas: assim a luz não tem borda, e
            # o que se lê é a varredura de um feixe, não um retângulo andando.
            gradient=ft.LinearGradient(
                begin=ft.Alignment.CENTER_LEFT,
                end=ft.Alignment.CENTER_RIGHT,
                colors=[
                    ft.Colors.TRANSPARENT,
                    ft.Colors.with_opacity(0.35 if cor.escura else 0.22, cor.acento),
                    ft.Colors.TRANSPARENT,
                ],
            ),
            animate_position=ft.Animation(tema.MS_VARREDURA, tema.CURVA_VARREDURA),
        )

        super().__init__(
            width=tema.LARGURA_TRACO,
            height=tema.ALTURA_TRACO,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            controls=[
                cv.Canvas(
                    width=tema.LARGURA_TRACO,
                    height=tema.ALTURA_TRACO,
                    shapes=graticule(tema.LARGURA_TRACO, tema.ALTURA_TRACO),
                ),
                self.luz,
            ],
        )
        self._tarefa: asyncio.Task | None = None

    def did_mount(self) -> None:
        self._tarefa = self.page.run_task(self._laco)

    def will_unmount(self) -> None:
        if self._tarefa is not None:
            self._tarefa.cancel()

    async def _laco(self) -> None:
        """Vai e volta entre os dois extremos internos da fita, para sempre."""
        indo = True
        try:
            while True:
                await asyncio.sleep(tema.MS_VARREDURA / 1000)
                self.luz.left = self._fim if indo else self._inicio
                indo = not indo
                self.luz.update()
        except asyncio.CancelledError:
            return


def fita_de_espera() -> ft.Control:
    return FitaDeEspera()
