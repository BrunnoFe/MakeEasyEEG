"""O ponto de entrada: abre a janela e entrega a bancada.

Só o que é dimensão e ajuste de `ft.Page` mora aqui. A janela em si — o que ela
mostra e por quê — é `app.Bancada`.
"""

from __future__ import annotations

import logging

import flet as ft

from eeghelper.interfaces.gui import tema
from eeghelper.interfaces.gui.app import Bancada


async def _principal(page: ft.Page) -> None:
    page.title = "EEGHelper"
    page.padding = 0
    page.window.min_width = tema.LARGURA_MINIMA_JANELA
    page.window.min_height = tema.ALTURA_MINIMA_JANELA
    # Larga o bastante para a grade caber inteira no modo elástico: com a coluna
    # de saída, o traço de 380 px e a coluna de controle, abaixo disto a tabela
    # abriria já rolando na horizontal — e rolar deve ser a exceção da janela
    # apertada, não o estado normal do aplicativo.
    page.window.width = 1280
    page.window.height = 768
    # Nenhuma fonte é registrada: a cifra é a monoespaçada do sistema
    # (`tema.FAMILIA_CIFRA` e seus fallbacks), e a janela não faz requisição de
    # rede para desenhar.
    page.theme = ft.Theme(font_family=tema.FAMILIA_TEXTO, use_material3=True)

    Bancada(page).remontar()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
    ft.run(_principal)


if __name__ == "__main__":
    main()
