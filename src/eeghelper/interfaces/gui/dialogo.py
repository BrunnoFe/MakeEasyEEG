"""A confirmação de sobrescrita — o único diálogo modal do aplicativo.

Todo o resto do EEGHelper avisa de forma inline: o erro da planilha aparece no
cartão, a divergência de contagem pinta a linha. Modal é interrupção, e
interromper por rotina treina o usuário a clicar no botão afirmativo sem ler.

Aqui se justifica porque é a única ação irreversível do programa. E ela vem em
duas severidades que este módulo se recusa a somar num número só:

- **originais** (T2): o destino é o próprio eventlist de entrada. O dado bruto
  do experimento desaparece e não volta.
- **anteriores** (T3): o destino é a saída de uma rodada passada. Reprocessar é
  o caso comum, e chamar isso de perigo esvaziaria o alarme do primeiro.

Por isso as duas categorias têm decisões separadas: quem só queria reprocessar
não deve ser obrigado a autorizar a destruição dos originais junto — nem a
cancelar o lote inteiro por causa dela.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import flet as ft

from eeghelper.dominio.modelos import PreviaParticipante
from eeghelper.interfaces.gui import tema
from eeghelper.interfaces.gui.controles import texto

# Quantos nomes o diálogo lista antes de resumir o resto numa contagem. Uma
# lista de duzentos itens não é informação, é parede.
MAXIMO_NOMES_LISTADOS = 8


def _lista_de_nomes(nomes: list[str]) -> ft.Control:
    cor = tema.paleta()
    mostrados = nomes[:MAXIMO_NOMES_LISTADOS]
    restantes = len(nomes) - len(mostrados)
    linhas: list[ft.Control] = [
        texto(nome, cor.texto_medio, tamanho=tema.CORPO_MICRO + 1) for nome in mostrados
    ]
    if restantes:
        linhas.append(texto(f"e mais {restantes}…", cor.texto_fraco, tamanho=tema.CORPO_MICRO + 1))
    return ft.Column(spacing=tema.ESPACO_1, controls=linhas)


async def confirmar_sobrescrita(
    page: ft.Page,
    originais: list[PreviaParticipante],
    anteriores: list[Path],
    pasta_saida: Path | None,
) -> tuple[bool, bool] | None:
    """Pede autorização antes de apagar qualquer coisa.

    Returns:
        None se o usuário cancelou — nada deve ser gravado. Caso contrário, um
        par `(gravar, substituir_originais)`, onde o segundo item só é True se o
        usuário ligou explicitamente o interruptor dos originais. Recusar os
        originais NÃO cancela o lote: as demais linhas gravam.
    """
    if not originais and not anteriores:
        return True, False

    cor = tema.paleta()
    resposta: asyncio.Future[tuple[bool, bool] | None] = asyncio.get_running_loop().create_future()
    interruptor_originais = ft.Switch(value=False, active_color=cor.divergente)

    def responder(valor: tuple[bool, bool] | None) -> None:
        # `on_dismiss` também chama isto quando o diálogo fecha por fora, então
        # a guarda do future não é zelo: sem ela o segundo caminho estoura.
        if resposta.done():
            return
        page.pop_dialog()
        page.update()
        resposta.set_result(valor)

    blocos: list[ft.Control] = []

    if originais:
        quantos = len(originais)
        blocos.append(
            ft.Container(
                bgcolor=ft.Colors.with_opacity(0.10, cor.divergente),
                border=ft.Border.all(width=1, color=ft.Colors.with_opacity(0.4, cor.divergente)),
                border_radius=tema.RAIO_LINHA,
                padding=ft.Padding.all(tema.ESPACO_3),
                content=ft.Column(
                    spacing=tema.ESPACO_2,
                    controls=[
                        ft.Text(
                            f"{quantos} eventlist{'s' if quantos > 1 else ''} "
                            f"ORIGINA{'IS' if quantos > 1 else 'L'} "
                            "seria substituído e não poderia ser recuperado.",
                            size=tema.CORPO,
                            color=cor.divergente,
                            weight=ft.FontWeight.W_600,
                            font_family=tema.FAMILIA_TEXTO,
                        ),
                        _lista_de_nomes([previa.caminho_entrada.name for previa in originais]),
                        ft.Row(
                            spacing=tema.ESPACO_2,
                            controls=[
                                interruptor_originais,
                                texto("substituir os originais mesmo assim"),
                            ],
                        ),
                        texto(
                            "Deixe desligado para preservá-los — o resto grava normalmente.",
                            cor.texto_fraco,
                            tamanho=tema.CORPO_MICRO + 1,
                        ),
                    ],
                ),
            )
        )

    if anteriores:
        quantos = len(anteriores)
        onde = f" em {pasta_saida.name}" if pasta_saida else ""
        blocos.append(
            ft.Column(
                spacing=tema.ESPACO_2,
                controls=[
                    texto(
                        f"{quantos} arquivo{'s' if quantos > 1 else ''} "
                        f"de uma rodada anterior{onde} "
                        f"{'serão substituídos' if quantos > 1 else 'será substituído'}."
                    ),
                    _lista_de_nomes([caminho.name for caminho in anteriores]),
                ],
            )
        )

    dialogo = ft.AlertDialog(
        modal=True,
        bgcolor=cor.painel,
        title=ft.Text(
            "Confirmar substituição" if originais else "Substituir arquivos existentes?",
            size=tema.CORPO_SECAO,
            color=cor.texto,
            weight=ft.FontWeight.W_700,
            font_family=tema.FAMILIA_TEXTO,
        ),
        scrollable=True,
        content=ft.Column(width=460, tight=True, spacing=tema.ESPACO_4, controls=blocos),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda _: responder(None)),
            ft.FilledButton(
                "Gravar",
                autofocus=not originais,
                on_click=lambda _: responder((True, interruptor_originais.value or False)),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=lambda _: responder(None),
    )

    page.show_dialog(dialogo)
    page.update()
    return await resposta
