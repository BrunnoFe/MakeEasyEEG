"""Revelar: o assentamento de uma leitura nova.

O instrumento reconstrói a janela inteira a cada troca de tema ou escolha de
arquivo (`Bancada.remontar`), de propósito — as cores já nascem embutidas nos
controles construídos, então uma atualização parcial deixaria metade da janela
no modo antigo. Isso significa que a maior parte da árvore não tem como animar
uma troca de conteúdo: não existe um controle anterior para interpolar contra.

`atualizar()` é diferente: ela troca só o conteúdo do cartão de leitura, do
rodapé de ações e dos marcadores de canal da tabela, sem derrubar o resto da
página. Esses são os únicos pontos onde uma troca de conteúdo corresponde a
uma medição nova de verdade — o lote passou de VERIFICANDO para VERIFICADO,
ou de GRAVANDO para GRAVADO — e onde `Revelar` assenta o conteúdo novo com o
mesmo deslocamento vertical que o resto da janela já usa como "isto
respondeu" (ver `_chip` e `_botao` em `app.py`), em vez de inventar um
material novo.

O `deslocamento` é o único grau de liberdade: maior nos marcadores de um lote
que fechou limpo, menor nos que não fecharam — o instrumento nunca comemora
uma divergência, só a assinala (ver `tabela.linha`).
"""

from __future__ import annotations

import flet as ft
from eeghelper.interfaces.gui import tema


class Revelar(ft.Container):
    """Assenta o conteúdo com um deslocamento vertical curto ao montar.

    Um único disparo por montagem, não um laço: ao contrário da luz de espera
    da fita vazia, aqui não há nada para cancelar em `will_unmount`.
    """

    def __init__(
        self, content: ft.Control, deslocamento: float = tema.DESLOCAMENTO_REVELAR
    ) -> None:
        super().__init__(
            content=content,
            opacity=0,
            offset=ft.Offset(0, deslocamento),
            animate_opacity=tema.animacao(tema.MS_TRANSICAO),
            animate_offset=tema.animacao(tema.MS_TRANSICAO),
        )

    def did_mount(self) -> None:
        self.opacity = 1
        self.offset = ft.Offset(0, 0)
        self.update()
