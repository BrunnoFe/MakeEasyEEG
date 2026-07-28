"""Revelar: o assentamento de uma leitura nova.

O instrumento reconstrói a janela inteira a cada troca de tema ou escolha de
arquivo (`Bancada.remontar`), de propósito — as cores já nascem embutidas nos
controles construídos, então uma atualização parcial deixaria metade da janela
no modo antigo. Isso significa que a maior parte da árvore não tem como animar
uma troca de conteúdo: não existe um controle anterior para interpolar contra.

`atualizar()` é diferente: ela troca só o conteúdo do cartão de leitura e do
rodapé de ações, sem derrubar o resto da página. Esses dois pontos são os
únicos onde uma troca de conteúdo corresponde a uma medição nova de verdade —
o lote passou de VERIFICANDO para VERIFICADO, ou de GRAVANDO para GRAVADO — e
onde `Revelar` assenta o conteúdo novo com o mesmo deslocamento vertical que
o resto da janela já usa como "isto respondeu" (ver `_chip` e `_botao` em
`app.py`), em vez de inventar um material novo.
"""

from __future__ import annotations

import flet as ft
from eeghelper.interfaces.gui import tema

_DESLOCAMENTO_INICIAL = 0.06


class Revelar(ft.Container):
    """Assenta o conteúdo com um deslocamento vertical curto ao montar.

    Um único disparo por montagem, não um laço: ao contrário da luz de espera
    da fita vazia, aqui não há nada para cancelar em `will_unmount`.
    """

    def __init__(self, content: ft.Control) -> None:
        super().__init__(
            content=content,
            opacity=0,
            offset=ft.Offset(0, _DESLOCAMENTO_INICIAL),
            animate_opacity=tema.animacao(tema.MS_TRANSICAO),
            animate_offset=tema.animacao(tema.MS_TRANSICAO),
        )

    def did_mount(self) -> None:
        self.opacity = 1
        self.offset = ft.Offset(0, 0)
        self.update()
