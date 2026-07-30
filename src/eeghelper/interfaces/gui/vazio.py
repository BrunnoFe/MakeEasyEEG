"""A tela sem lote: ela ensina o instrumento em vez de dizer que não há nada.

Vista de leitura pura, como `regua.py`. Diz o que falta escolher, mostra um
traço vivo de exemplo e adianta a invariante da gravação — que nada é gerado
antes de uma verificação, e que o original nunca é sobrescrito.
"""

from __future__ import annotations

import flet as ft

from eeghelper.interfaces.gui import controles, espera, tema
from eeghelper.interfaces.gui.estado import EstadoLote


def tela_em_branco(estado: EstadoLote) -> ft.Control:
    """A tela vazia ensina o instrumento, em vez de dizer que não há nada."""
    cor = tema.paleta()
    faltando = []
    if not estado.caminhos_eventlists:
        faltando.append("os eventlists")
    if estado.marcadores is None:
        faltando.append("a planilha de marcadores")

    return ft.Container(
        expand=True,
        padding=ft.Padding.symmetric(horizontal=tema.ESPACO_6, vertical=tema.ESPACO_6),
        content=ft.Column(
            spacing=tema.ESPACO_5,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    f"Escolha {' e '.join(faltando)} ao lado.",
                    size=tema.CORPO_SECAO,
                    color=cor.texto,
                    weight=ft.FontWeight.W_600,
                    font_family=tema.FAMILIA_TEXTO,
                    font_family_fallback=tema.FALLBACK_TEXTO,
                ),
                ft.Row(
                    spacing=tema.ESPACO_4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        # A luz de espera corre DENTRO da fita, de cabeceira a
                        # cabeceira; ver `espera.py`.
                        espera.fita_de_espera(),
                        controles.texto(
                            "cada participante vira um traço deste com os marcadores",
                            cor.texto_fraco,
                            tema.CORPO - 0.5,
                        ),
                    ],
                ),
                ft.Column(
                    spacing=tema.ESPACO_2,
                    controls=[
                        ft.Container(
                            width=640,
                            content=ft.Text(
                                "As marcas acesas são os ecodes que serão trocados; um "
                                "cursor coral aponta onde a contagem deixa de bater.",
                                size=tema.CORPO - 0.5,
                                color=cor.texto_fraco,
                                font_family=tema.FAMILIA_TEXTO,
                                font_family_fallback=tema.FALLBACK_TEXTO,
                            ),
                        ),
                        ft.Container(
                            width=640,
                            content=ft.Text(
                                "Nada é gerado antes de você verificar o lote — o arquivo "
                                "original nunca é sobrescrito.",
                                size=tema.CORPO - 0.5,
                                color=cor.texto_fraco,
                                font_family=tema.FAMILIA_TEXTO,
                                font_family_fallback=tema.FALLBACK_TEXTO,
                            ),
                        ),
                    ],
                ),
            ],
        ),
    )
