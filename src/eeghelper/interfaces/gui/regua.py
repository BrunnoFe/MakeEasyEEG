"""A régua de leitura: o que a varredura mediu, em cifras grandes.

Vista de leitura pura — não recebe callback nenhum, porque não há nada para
clicar aqui. Só lê `EstadoLote` e devolve controles.

Mora dentro do painel da tela, entre a pista da varredura e o cabeçalho de
colunas, e não na coluna de controle: as cifras resumem a tabela, e na lateral
elas disputavam altura com a configuração — os três cartões somados passavam da
janela, e o de aquisição acabava cortado por uma rolagem sem barra visível, que
lia como um cartão por cima do outro.
"""

from __future__ import annotations

import flet as ft

from eeghelper.interfaces.gui import controles, tema
from eeghelper.interfaces.gui.estado import EstadoLote, Fase
from eeghelper.interfaces.gui.transicao import Revelar

# Três compartimentos de largura escrita: a régua passa de duas leituras para
# três ao verificar, e sem posição fixa a cifra de divergentes apareceria
# deslocada de onde o olho acabou de ler "sem coluna". A medida vem do rótulo
# mais largo (PARTICIPANTES ≈ 95 px em 10.5/1.3) mais a cifra deitada ao lado.
LARGURA_LEITURA = 190
CALHA_LEITURA = tema.ESPACO_6
# O recuo mínimo da régua, herdado da margem das linhas da tabela: as leituras
# ficam centradas na largura do painel, e este recuo só existe para que elas
# nunca encostem na borda numa janela estreita.
RECUO_REGUA = tema.CALHA_TABELA + tema.MARGEM_LINHA

# A cifra sem medida: o mesmo travessão que a tabela usa para contagem
# desconhecida, em vez de um zero que tem cara de dado.
SEM_MEDIDA = "—"


def _leitura(valor: str, nome: str, cor_valor: str) -> ft.Control:
    """Um mostrador da régua: a cifra grande e a placa gravada ao lado dela.

    Deitado, e não empilhado: a régua é uma faixa dentro do painel, e cada
    linha que ela ganha sai da tabela. O rótulo desce 6 px porque a caixa de
    uma cifra de 28 px é bem mais alta que a de um versalete de 10.5, e
    centralizar as duas deixaria o rótulo pairando acima da base da cifra.

    O par fica centrado no compartimento, e não encostado à esquerda dele: a
    régua inteira é centrada no painel, e um compartimento com a folga toda de
    um lado só puxaria o centro óptico do conjunto para o lado contrário.
    """
    return ft.Row(
        width=LARGURA_LEITURA,
        tight=True,
        spacing=tema.ESPACO_2,
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text(
                valor,
                size=tema.CORPO_LEITURA,
                color=cor_valor,
                weight=ft.FontWeight.W_700,
                font_family=tema.FAMILIA_CIFRA,
                font_family_fallback=tema.FALLBACK_CIFRA,
                no_wrap=True,
            ),
            ft.Container(margin=ft.Margin.only(top=6), content=controles.rotulo(nome)),
        ],
    )


def regua_de_leitura(estado: EstadoLote) -> ft.Control:
    """O painel de medição da bancada.

    Não é um cartão. Sem contorno, sem raio e sem sombra, em `painel_alto`:
    é a mesma cor da pista logo acima, então as duas fundem num bloco de
    cabeçalho só, e a borda inferior é a mesma que `tabela.cabecalho` usa.
    """
    cor = tema.paleta()
    verificado = estado.fase in (Fase.VERIFICADO, Fase.GRAVADO)

    if verificado:
        leituras = [
            _leitura(str(estado.total_gravavel), "prontos", cor.pronto),
            _leitura(
                str(estado.total_divergente),
                controles.plural(estado.total_divergente, "divergente", "divergentes"),
                cor.divergente if estado.total_divergente else cor.texto_fraco,
            ),
            _leitura(str(estado.total_substituicoes), "trocas", cor.texto),
        ]
    else:
        total_pares = len(estado.pares())
        # Antes de haver lote não há o que medir, e um zero grande numa
        # tela que está pedindo os arquivos é ruído com cara de dado. O
        # travessão é o que a tabela já escreve para contagem desconhecida.
        if total_pares:
            leituras = [
                _leitura(str(total_pares), "participantes", cor.texto),
                _leitura(
                    str(estado.total_pulados),
                    "sem coluna",
                    cor.pulado if estado.total_pulados else cor.texto_fraco,
                ),
            ]
        else:
            leituras = [
                _leitura(SEM_MEDIDA, "participantes", cor.texto_fraco),
                _leitura(SEM_MEDIDA, "sem coluna", cor.texto_fraco),
            ]

    # Compartimentos de largura escrita, centrados no painel: a cifra não
    # muda de posição quando o número ganha um dígito, e a folga sobra
    # simétrica dos dois lados em vez de toda à direita. `Revelar` assenta
    # a leitura nova porque a régua só se refaz numa medição de verdade
    # (ver `app.Bancada.atualizar`), nunca num remonte de tema.
    return ft.Container(
        bgcolor=cor.painel_alto,
        padding=ft.Padding.symmetric(horizontal=RECUO_REGUA, vertical=tema.ESPACO_3 + 2),
        border=ft.Border(bottom=ft.BorderSide(width=1, color=cor.contorno)),
        content=Revelar(
            ft.Row(
                spacing=CALHA_LEITURA,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=leituras,
            )
        ),
    )
