"""A marca do EEGHelper: wordmark 2 — eletrodo + cifra monoespaçada.

O sinete é um anel de eletrodo (gradiente cônico do acento para o acento 2) com
um miolo na cor do painel e um contato horizontal no centro; ao lado, o wordmark
`eeg·helper` em monoespaçada caixa baixa, com o ponto médio na cor de acento.

Duas razões para o wordmark ser mono: é a mesma família de toda cifra da janela,
então a marca não introduz uma terceira voz tipográfica; e o ponto médio é o
separador que a tabela já usa em "20 arquivos · eventlists".
"""

from __future__ import annotations

import math

import flet as ft
from eeghelper.interfaces.gui import tema


def sinete(tamanho: int = 30) -> ft.Control:
    """O anel de eletrodo, sozinho — serve de ícone de janela e de favicon."""
    cor = tema.paleta()
    miolo = round(tamanho * 0.66)
    return ft.Container(
        width=tamanho,
        height=tamanho,
        border_radius=tema.RAIO_PILULA,
        # Gradiente cônico: o anel parece um eletrodo visto de cima, e a volta
        # completa (acento -> acento_2 -> acento) evita a costura visível que um
        # gradiente linear deixaria no topo do círculo.
        gradient=ft.SweepGradient(
            center=ft.Alignment.CENTER,
            start_angle=0.0,
            end_angle=math.tau,
            colors=[cor.acento, cor.acento_2, cor.acento],
            stops=[0.0, 0.5, 1.0],
        ),
        align=ft.Alignment.CENTER,
        content=ft.Container(
            width=miolo,
            height=miolo,
            bgcolor=cor.painel,
            border_radius=tema.RAIO_PILULA,
            align=ft.Alignment.CENTER,
            content=ft.Container(
                width=round(tamanho * 0.27),
                height=2,
                bgcolor=cor.acento,
                border_radius=1,
            ),
        ),
    )


def wordmark(tamanho_sinete: int = 30, corpo: float = 17.0) -> ft.Control:
    """Sinete e assinatura, lado a lado — o bloco de marca do cabeçalho."""
    cor = tema.paleta()
    fonte = {
        "font_family": tema.FAMILIA_CIFRA,
        "font_family_fallback": tema.FALLBACK_CIFRA,
        "size": corpo,
        "weight": ft.FontWeight.W_600,
        "no_wrap": True,
    }
    return ft.Row(
        spacing=tema.ESPACO_3 - 1,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        tight=True,
        controls=[
            sinete(tamanho_sinete),
            ft.Row(
                spacing=0,
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("eeg", color=cor.texto, **fonte),
                    ft.Text("·", color=cor.acento, **fonte),
                    ft.Text("helper", color=cor.texto, **fonte),
                ],
            ),
        ],
    )


def cabecalho_da_marca(subtitulo: str) -> ft.Control:
    """O bloco de marca com o subtítulo embaixo, para a barra de topo."""
    cor = tema.paleta()
    return ft.Column(
        spacing=tema.ESPACO_1,
        controls=[
            wordmark(),
            ft.Text(
                subtitulo,
                size=tema.CORPO - 0.5,
                color=cor.texto_fraco,
                font_family=tema.FAMILIA_TEXTO,
                font_family_fallback=tema.FALLBACK_TEXTO,
                no_wrap=True,
            ),
        ],
    )
