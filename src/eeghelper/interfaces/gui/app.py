"""A janela do EEGHelper: uma bancada de instrumento.

Contrato de direção (semente 7ea9d984, rodada 2, índice 3 da lista fundamentada):

TESE: o lote é a tela de um instrumento de bancada, não uma lista de arquivos
com selos de status. Recusa o painel escuro de ferramenta com pílulas coloridas
e cartões de resumo que esta categoria sempre entrega.
MUNDO: tela quase preta com graticule e traços luminosos à esquerda, coluna de
controle à direita; quatro cores de canal — verde pronto, ciano varrendo, âmbar
sem coluna, coral divergente — e nada mais colorido na janela.
HISTÓRIA: o usuário liga as entradas, varre o lote, lê linha a linha onde cada
participante quebrou, e só então gera os novos eventlists.
PRIMEIRA VISTA: tela elevada ocupando a maior parte da janela, um traço por
participante sobre a mesma base de tempo; à direita, aquisição, leitura de
medição em cifras grandes e as duas ações, com Gerar destravado só depois da
varredura.
FORMA: instrumento de bancada, candidato 3 de 6; staging de vigias recusado.
FINISH: unreviewed and undocumented is unfinished; this build ends with the
finish review, the verdict, and DESIGN.md.

O único momento autoral de movimento é a varredura: durante a verificação a
barra de aquisição corre no alto da tela e os traços acendem um a um, na ordem
das linhas. Não é enfeite — é o progresso real do lote, e é a leitura de que
nada foi gerado ainda.

Esta camada não conhece `argparse` nem Tkinter, e não contém regra de negócio:
ela lê `estado.EstadoLote` e chama `servicos.substituicao`.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from pathlib import Path

import flet as ft

from eeghelper.excecoes import ErroEEGHelper
from eeghelper.interfaces.gui import espera, marca, tabela, tema
from eeghelper.interfaces.gui.estado import EstadoLote, Fase
from eeghelper.interfaces.gui.transicao import Revelar
from eeghelper.io_.escritor_eventlist import NOME_RELATORIO_PADRAO, escrever_relatorio
from eeghelper.io_.leitor_marcadores import ler_marcadores
from eeghelper.servicos.substituicao import gravar_previas, verificar_par

logger = logging.getLogger(__name__)

EXTENSOES_PLANILHA = ["csv", "xlsx", "xlsm", "xls"]

ALTURA_CAMPO_ECODE = 34
ALTURA_BOTAO = 42

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


def plural(quantidade: int, singular: str, plural_: str) -> str:
    """Concorda o substantivo com a contagem.

    Um lote de um participante é comum aqui, e "1 divergentes" numa tela que
    pede confiança é exatamente o tipo de descuido que a corrói.
    """
    return singular if quantidade == 1 else plural_


def _chip(nome: str, ao_clicar: Callable[[ft.Event[ft.Container]], None]) -> ft.Control:
    """Pastilha fantasma que acende e sobe 1 px ao pairar.

    O deslocamento vertical é o que faz a pastilha parecer clicável sem precisar
    de preenchimento em repouso — cor sozinha, num cartão que já tem contorno,
    lê como estado e não como convite.
    """
    cor = tema.paleta()
    pastilha = ft.Container(
        bgcolor=ft.Colors.TRANSPARENT,
        border=ft.Border.all(width=1, color=cor.contorno),
        border_radius=tema.RAIO_PILULA,
        padding=ft.Padding.symmetric(horizontal=tema.ESPACO_3, vertical=5),
        offset=ft.Offset(0, 0),
        animate=tema.animacao(tema.MS_RAPIDO),
        animate_offset=tema.animacao(tema.MS_RAPIDO),
        on_click=ao_clicar,
        content=tabela.texto(nome, cor.texto_medio, tema.CORPO_MICRO + 1),
    )

    def ao_pairar(evento: ft.Event[ft.Container]) -> None:
        pairando = bool(evento.data)
        pastilha.bgcolor = cor.painel_alto if pairando else ft.Colors.TRANSPARENT
        pastilha.border = ft.Border.all(width=1, color=cor.acento if pairando else cor.contorno)
        pastilha.offset = ft.Offset(0, -0.04 if pairando else 0)
        pastilha.update()

    pastilha.on_hover = ao_pairar
    return pastilha


def _campo(nome: str, valor: ft.Control, acoes: list[ft.Control]) -> ft.Control:
    """Um parâmetro de aquisição: placa gravada, valor e ações.

    O ícone saiu. Num cartão de quatro campos, quatro ícones outline de 13 px
    dizem menos do que o próprio nome do campo e cobram uma coluna de 21 px que
    o valor usaria melhor — a marca já carrega a identidade da janela.
    """
    return ft.Column(
        spacing=tema.ESPACO_2,
        controls=[
            tabela.rotulo(nome),
            valor,
            ft.Container(
                margin=ft.Margin.only(top=2),
                content=ft.Row(spacing=tema.ESPACO_2, controls=acoes),
            ),
        ],
    )


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
            ft.Container(margin=ft.Margin.only(top=6), content=tabela.rotulo(nome)),
        ],
    )


def _botao(
    nome: str,
    icone: str,
    preenchido: bool,
    ao_clicar: Callable[[ft.Event[ft.Control]], None],
    desabilitado: bool,
) -> ft.Control:
    """Botão do instrumento.

    Gravar é a única superfície com gradiente e a única com sombra colorida em
    toda a janela — é o que o marca como a ação que escreve em disco. Travado,
    perde as duas e vira contorno inerte: o estado desabilitado é escrito à mão
    porque um "Gravar" travado com aparência de ativo mentiria exatamente sobre
    a ação que escreve em disco.
    """
    cor = tema.paleta()
    if desabilitado:
        fundo, frente, contorno = ft.Colors.TRANSPARENT, cor.texto_fraco, cor.contorno
    elif preenchido:
        fundo, frente, contorno = None, cor.sobre_acento, ft.Colors.TRANSPARENT
    else:
        fundo, frente, contorno = ft.Colors.TRANSPARENT, cor.texto, cor.contorno_forte

    conteudo = ft.Row(
        spacing=tema.ESPACO_2,
        alignment=ft.MainAxisAlignment.CENTER,
        tight=True,
        controls=[
            ft.Icon(icone, size=15, color=frente),
            ft.Text(
                nome,
                size=tema.CORPO,
                color=frente,
                weight=ft.FontWeight.W_600 if preenchido and not desabilitado else None,
                font_family=tema.FAMILIA_TEXTO,
                font_family_fallback=tema.FALLBACK_TEXTO,
                no_wrap=True,
            ),
        ],
    )

    # O botão é um Container e não um FilledButton porque o preenchimento é um
    # gradiente, e o Material impõe cor sólida em `bgcolor`. A largura é escrita,
    # não herdada: um Container centrando conteúdo não resolve o próprio tamanho
    # nem por `expand` numa Row nem pelo `STRETCH` da coluna — nos dois casos ele
    # encolhe para uma caixa menor que o rótulo, e o texto vaza para fora dela.
    botao = ft.Container(
        width=tema.LARGURA_CARTAO_CONTROLE,
        height=ALTURA_BOTAO,
        bgcolor=fundo,
        gradient=None
        if fundo is not None
        else ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=[cor.acento, cor.acento_2],
        ),
        border=ft.Border.all(width=1, color=contorno) if contorno else None,
        border_radius=tema.RAIO_CHIP + 2,
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=18,
            color=ft.Colors.with_opacity(0.28, cor.acento),
            offset=ft.Offset(0, 6),
        )
        if preenchido and not desabilitado
        else None,
        align=ft.Alignment.CENTER,
        offset=ft.Offset(0, 0),
        animate=tema.animacao(tema.MS_RAPIDO),
        animate_offset=tema.animacao(tema.MS_RAPIDO),
        on_click=None if desabilitado else ao_clicar,
        content=conteudo,
    )

    if not desabilitado:

        def ao_pairar(evento: ft.Event[ft.Container]) -> None:
            pairando = bool(evento.data)
            botao.offset = ft.Offset(0, -0.03 if pairando else 0)
            if not preenchido:
                botao.bgcolor = cor.painel_alto if pairando else ft.Colors.TRANSPARENT
            botao.update()

        botao.on_hover = ao_pairar

    return botao


class Bancada:
    """Monta a janela e mantém a tela em sincronia com o `EstadoLote`."""

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.estado = EstadoLote()
        self.seletor = ft.FilePicker()
        page.services.append(self.seletor)
        self.total_a_verificar = 0
        # Só "verificacao" ou "gravacao" no exato `atualizar()` que fecha uma
        # verificação ou uma gravação — é o que faz o pulso dos marcadores de
        # canal (ver `tabela.linha`) tocar uma vez, não a cada redesenho.
        self._foco_pulso: str | None = None

    # --- Montagem --------------------------------------------------------

    def montar(self) -> ft.Control:
        """Monta a árvore inteira na paleta em vigor.

        É remontada por completo na troca de tema: as cores estão dentro dos
        controles já construídos, e uma atualização parcial deixaria metade da
        janela no modo antigo.
        """
        cor = tema.paleta()
        self.area_tela = ft.Container(expand=True)
        # As duas áreas nascem preenchidas, e não vazias para receber conteúdo
        # depois do `page.add`: um Row que chega numa árvore já montada não
        # refaz o próprio layout, e era isso que deixava a régua de leitura com
        # o rótulo mas sem as cifras.
        self.area_leitura = ft.Column(
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[self._regua_de_leitura()],
        )
        self.area_acoes = ft.Column(
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[self._acoes()],
        )
        self.varredura = ft.ProgressBar(
            value=0,
            bar_height=3,
            color=cor.varrendo,
            bgcolor=ft.Colors.TRANSPARENT,
            border_radius=0,
            stop_indicator_radius=0,
            track_gap=0,
        )

        return ft.Container(
            expand=True,
            bgcolor=cor.tela,
            padding=ft.Padding.all(tema.ESPACO_5),
            content=ft.Column(
                spacing=tema.ESPACO_4,
                expand=True,
                controls=[
                    self._barra_de_topo(),
                    ft.Row(
                        spacing=tema.ESPACO_4,
                        expand=True,
                        vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                        controls=[self._painel_da_tela(), self._coluna_de_controle()],
                    ),
                ],
            ),
        )

    def _barra_de_topo(self) -> ft.Control:
        """Marca à esquerda, alternador de tema à direita."""
        cor = tema.paleta()
        alternador = ft.Container(
            width=32,
            height=32,
            border_radius=tema.RAIO_CHIP,
            align=ft.Alignment.CENTER,
            animate=tema.animacao(tema.MS_RAPIDO),
            animate_rotation=tema.animacao(tema.MS_TRANSICAO),
            rotate=ft.Rotate(0),
            tooltip="Modo claro" if cor.escura else "Modo escuro",
            on_click=self._alternar_tema,
            content=ft.Icon(
                ft.Icons.LIGHT_MODE_OUTLINED if cor.escura else ft.Icons.DARK_MODE_OUTLINED,
                size=17,
                color=cor.texto_medio,
            ),
        )

        def ao_pairar(evento: ft.Event[ft.Container]) -> None:
            pairando = bool(evento.data)
            alternador.bgcolor = cor.painel_alto if pairando else ft.Colors.TRANSPARENT
            # O giro de -20° é o único movimento gratuito da janela, e ele se paga:
            # é o que diz que o ícone é um interruptor e não um selo de estado.
            alternador.rotate = ft.Rotate(-0.35 if pairando else 0)
            alternador.update()

        alternador.on_hover = ao_pairar

        return ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    expand=True,
                    content=marca.cabecalho_da_marca(
                        "Correção de marcadores de eventlists do ERPLAB"
                    ),
                ),
                alternador,
            ],
        )

    def _painel_da_tela(self) -> ft.Control:
        """A tela do instrumento: a superfície elevada onde o lote é lido."""
        cor = tema.paleta()
        return ft.Container(
            expand=True,
            bgcolor=cor.painel,
            border_radius=tema.RAIO_PAINEL,
            border=ft.Border.all(width=1, color=cor.contorno),
            shadow=tema.sombra(alta=True),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Column(
                spacing=0,
                expand=True,
                controls=[
                    # A pista da barra fica visível sempre, em painel_alto: sem ela
                    # o cabeçalho salta 3 px quando a verificação começa.
                    ft.Container(bgcolor=cor.painel_alto, content=self.varredura),
                    self.area_leitura,
                    tabela.cabecalho(),
                    self.area_tela,
                ],
            ),
        )

    def _coluna_de_controle(self) -> ft.Control:
        """Configurar em cima, agir ao pé — e nada rolando em uso normal.

        Com a leitura movida para a régua do painel, os dois blocos que sobram
        cabem inteiros na janela mínima. A rolagem do primeiro fica só como rede
        de segurança para janelas abaixo do mínimo ou fonte de sistema ampliada;
        se ela precisar disparar, é a configuração que cede, não as ações — os
        botões são o que a janela pede a seguir, e sumir com eles para mostrar
        um campo de arquivo seria trocar o destino pelo caminho.

        A largura mora na própria Column, e não num Container em volta: dentro
        de um Container o `expand` dos filhos não vale, e sem ele nem a altura
        chega à parte rolável — o bloco colapsa e as ações são desenhadas por
        cima dele.

        Os dois blocos recebem a MESMA largura escrita, em vez de esticarem até
        a borda da coluna: só o primeiro rola, e uma barra de rolagem que come
        largura de layout deixaria o cartão de aquisição mais estreito que as
        ações logo abaixo dele. Com a largura escrita, a calha de
        `CALHA_ROLAGEM` à direita absorve a barra — apareça ela por cima do
        conteúdo ou ao lado, as duas bordas direitas coincidem nos dois casos.
        """
        return ft.Column(
            width=tema.LARGURA_COLUNA_CONTROLE,
            spacing=tema.ESPACO_4,
            controls=[
                ft.Column(
                    spacing=tema.ESPACO_4,
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        ft.Container(
                            width=tema.LARGURA_CARTAO_CONTROLE,
                            content=self._cartao_de_aquisicao(),
                        )
                    ],
                ),
                ft.Container(width=tema.LARGURA_CARTAO_CONTROLE, content=self.area_acoes),
            ],
        )

    def _cartao(self, nome: str, conteudo: ft.Control) -> ft.Control:
        cor = tema.paleta()
        return ft.Container(
            bgcolor=cor.painel,
            border_radius=tema.RAIO_CARTAO,
            border=ft.Border.all(width=1, color=cor.contorno),
            shadow=tema.sombra(),
            padding=ft.Padding.all(tema.ESPACO_4 + 2),
            content=ft.Column(
                spacing=tema.ESPACO_5,
                controls=[tabela.rotulo(nome), conteudo],
            ),
        )

    def _cartao_de_aquisicao(self) -> ft.Control:
        estado = self.estado
        cor = tema.paleta()

        if estado.caminhos_eventlists:
            quantos = len(estado.caminhos_eventlists)
            valor_eventlists = tabela.texto(
                f"{quantos} {plural(quantos, 'arquivo', 'arquivos')} · "
                f"{estado.caminhos_eventlists[0].parent.name}"
            )
        else:
            valor_eventlists = tabela.texto("nenhum escolhido", cor.texto_fraco)

        if estado.erro_marcadores:
            valor_planilha: ft.Control = ft.Text(
                estado.erro_marcadores,
                size=tema.CORPO,
                color=cor.divergente,
                font_family=tema.FAMILIA_TEXTO,
                font_family_fallback=tema.FALLBACK_TEXTO,
                max_lines=3,
            )
        elif estado.caminho_marcadores and estado.marcadores:
            colunas = len(estado.marcadores.participantes)
            valor_planilha = tabela.texto(
                f"{estado.caminho_marcadores.name} · {colunas} "
                f"{plural(colunas, 'coluna', 'colunas')}"
            )
        else:
            valor_planilha = tabela.texto("nenhuma escolhida", cor.texto_fraco)

        if estado.pasta_saida:
            valor_saida: ft.Control = tabela.texto(estado.pasta_saida.name)
            acoes_saida = [
                _chip("trocar", self._escolher_saida),
                _chip("limpar", self._limpar_saida),
            ]
        else:
            valor_saida = tabela.texto("Na mesma pasta dos eventlists.", cor.texto_fraco)
            acoes_saida = [_chip("escolher pasta", self._escolher_saida)]

        self.campo_ecode = ft.TextField(
            value=str(estado.ecode_alvo),
            width=72,
            height=ALTURA_CAMPO_ECODE,
            dense=True,
            border=ft.InputBorder.NONE,
            filled=True,
            fill_color=cor.painel_alto,
            border_radius=tema.RAIO_CHIP,
            content_padding=ft.Padding.symmetric(horizontal=tema.ESPACO_3, vertical=0),
            text_align=ft.TextAlign.RIGHT,
            text_style=ft.TextStyle(
                size=tema.CORPO,
                color=cor.texto,
                font_family=tema.FAMILIA_CIFRA,
                font_family_fallback=tema.FALLBACK_CIFRA,
            ),
            input_filter=ft.NumbersOnlyInputFilter(),
            on_blur=self._ao_mudar_ecode,
            on_submit=self._ao_mudar_ecode,
        )

        return self._cartao(
            "arquivos e pastas",
            ft.Column(
                spacing=tema.ESPACO_5,
                controls=[
                    _campo(
                        "eventlists",
                        valor_eventlists,
                        [
                            _chip("arquivos", self._escolher_eventlists),
                            _chip("pasta", self._escolher_pasta_eventlists),
                        ],
                    ),
                    _campo(
                        "planilha de marcadores",
                        valor_planilha,
                        [_chip("escolher arquivo", self._escolher_planilha)],
                    ),
                    _campo("onde salvar os novos eventlists", valor_saida, acoes_saida),
                    # O ecode é o único parâmetro que se edita em vez de se
                    # escolher, e o filete acima o separa dos três campos de
                    # arquivo sem abrir outro cartão para uma linha só.
                    ft.Container(
                        margin=ft.Margin.only(top=18),
                        padding=ft.Padding.only(top=18),
                        border=ft.Border(top=ft.BorderSide(width=1, color=cor.painel_alto)),
                        content=ft.Row(
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                # O rótulo recebe a altura do campo e se alinha
                                # ao centro dela: sem isso ele assume a altura do
                                # próprio texto de 10.5 px e cai abaixo da cifra.
                                ft.Container(
                                    expand=True,
                                    height=ALTURA_CAMPO_ECODE,
                                    align=ft.Alignment.CENTER_LEFT,
                                    content=tabela.rotulo("marcador procurado"),
                                ),
                                self.campo_ecode,
                            ],
                        ),
                    ),
                ],
            ),
        )

    def _regua_de_leitura(self) -> ft.Control:
        """O painel de medição: o que a varredura mediu, em cifras grandes.

        Mora dentro do painel da tela, entre a pista da varredura e o cabeçalho
        de colunas, e não na coluna de controle: as cifras resumem a tabela, e
        na lateral elas disputavam altura com a configuração — os três cartões
        somados passavam da janela, e o de aquisição acabava cortado por uma
        rolagem sem barra visível, que lia como um cartão por cima do outro.

        Não é um cartão. Sem contorno, sem raio e sem sombra, em `painel_alto`:
        é a mesma cor da pista logo acima, então as duas fundem num bloco de
        cabeçalho só, e a borda inferior é a mesma que `tabela.cabecalho` usa.
        """
        estado = self.estado
        cor = tema.paleta()
        verificado = estado.fase in (Fase.VERIFICADO, Fase.GRAVADO)

        if verificado:
            leituras = [
                _leitura(str(estado.total_gravavel), "prontos", cor.pronto),
                _leitura(
                    str(estado.total_divergente),
                    plural(estado.total_divergente, "divergente", "divergentes"),
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
        # (ver `atualizar`), nunca num remonte de tema.
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

    def _tela_em_branco(self) -> ft.Control:
        """A tela vazia ensina o instrumento, em vez de dizer que não há nada."""
        cor = tema.paleta()
        faltando = []
        if not self.estado.caminhos_eventlists:
            faltando.append("os eventlists")
        if self.estado.marcadores is None:
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
                            tabela.texto(
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

    def _tela(self) -> ft.Control:
        estado = self.estado

        if not estado.caminhos_eventlists or estado.marcadores is None:
            return self._tela_em_branco()

        colunas = estado.marcadores.participantes
        por_caminho = {par.caminho_eventlist: par.participante for par in estado.pares()}
        previa_por_caminho = {previa.caminho_entrada: previa for previa in estado.previas}
        verificado = estado.fase in (Fase.VERIFICADO, Fase.GRAVADO)
        lote_limpo = estado.total_divergente == 0

        linhas = [
            tabela.linha(
                caminho=caminho,
                participante=por_caminho.get(caminho),
                previa=previa_por_caminho.get(caminho),
                verificado=verificado,
                colunas=colunas,
                ao_escolher=self._ao_escolher_coluna,
                foco_pulso=self._foco_pulso,
                lote_limpo=lote_limpo,
            )
            for caminho in estado.caminhos_eventlists
        ]

        return ft.ListView(
            controls=linhas,
            expand=True,
            build_controls_on_demand=True,
            item_extent=tema.ALTURA_LINHA,
            padding=ft.Padding.symmetric(vertical=tema.ESPACO_2),
        )

    def _acoes(self) -> ft.Control:
        estado = self.estado
        cor = tema.paleta()
        verificado = estado.fase in (Fase.VERIFICADO, Fase.GRAVADO)
        ocupado = estado.fase in (Fase.VERIFICANDO, Fase.GRAVANDO)

        if estado.fase == Fase.GRAVADO and estado.caminho_relatorio:
            mensagem = f"Gerado. Relatório em {estado.caminho_relatorio.name}"
            cor_ponto = cor.pronto
        elif estado.fase == Fase.GRAVANDO:
            mensagem, cor_ponto = "Gerando os arquivos aprovados…", cor.pronto
        elif estado.fase == Fase.VERIFICANDO:
            mensagem, cor_ponto = "Verificando o lote de arquivos. Nenhum arquivo foi alterado.", cor.varrendo
        elif verificado and estado.total_divergente:
            quantos = estado.total_divergente
            mensagem = (
                f"{quantos} com contagem incompatível — "
                f"{plural(quantos, 'não será gerado', 'não serão gerados')}."
            )
            cor_ponto = cor.divergente
        elif verificado:
            mensagem, cor_ponto = "Verificação sem divergências.", cor.pronto
        else:
            mensagem, cor_ponto = "Verifique os arquivos para liberar a gravação.", cor.texto_fraco

        if estado.pode_gravar:
            quantos = estado.total_gravavel
            nome_gravar = f"Gerar {quantos} {plural(quantos, 'eventlist', 'eventlists')}"
        else:
            nome_gravar = "Gerar eventlist"

        return ft.Column(
            spacing=tema.ESPACO_3,
            controls=[
                ft.Row(
                    spacing=tema.ESPACO_2,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Container(
                            width=6,
                            height=6,
                            bgcolor=cor_ponto,
                            border_radius=tema.RAIO_PILULA,
                            margin=ft.Margin.only(top=5),
                            animate=tema.animacao(tema.MS_RAPIDO),
                        ),
                        ft.Container(
                            expand=True,
                            content=Revelar(
                                ft.Text(
                                    mensagem,
                                    size=tema.CORPO,
                                    color=cor.texto_medio,
                                    font_family=tema.FAMILIA_TEXTO,
                                    font_family_fallback=tema.FALLBACK_TEXTO,
                                )
                            ),
                        ),
                    ],
                ),
                # Empilhados e em largura cheia: o rótulo de Gravar carrega a
                # contagem do lote e cresce com ela, e lado a lado nesta coluna
                # ele seria truncado justamente onde diz quantos arquivos serão
                # escritos.
                ft.Column(
                    spacing=tema.ESPACO_2,
                    controls=[
                        _botao(
                            "Verificar arquivos",
                            ft.Icons.PLAY_ARROW_ROUNDED,
                            preenchido=False,
                            ao_clicar=self._verificar,
                            desabilitado=not estado.pode_verificar or ocupado,
                        ),
                        _botao(
                            nome_gravar,
                            ft.Icons.SAVE_OUTLINED,
                            preenchido=True,
                            ao_clicar=self._gravar,
                            desabilitado=not estado.pode_gravar,
                        ),
                    ],
                ),
            ],
        )

    # --- Sincronização ---------------------------------------------------

    def atualizar(self) -> None:
        self.area_tela.content = self._tela()
        self.area_leitura.controls = [self._regua_de_leitura()]
        self.area_acoes.controls = [self._acoes()]
        self._atualizar_varredura()
        self.page.update()

    def _atualizar_varredura(self) -> None:
        """A barra de aquisição no alto da tela.

        Determinada durante a verificação, porque ali existe progresso real a
        mostrar — participante calculado sobre participantes do lote. Na
        geração vira indeterminada: a escrita acontece num único bloco, e
        fingir uma fração seria inventar um progresso que ninguém mediu.
        """
        cor = tema.paleta()
        fase = self.estado.fase
        if fase == Fase.VERIFICANDO:
            self.varredura.color = cor.varrendo
            self.varredura.value = (
                len(self.estado.previas) / self.total_a_verificar if self.total_a_verificar else 0
            )
        elif fase == Fase.GRAVANDO:
            self.varredura.color = cor.pronto
            self.varredura.value = None
        else:
            self.varredura.color = ft.Colors.TRANSPARENT
            self.varredura.value = 0

    def remontar(self) -> None:
        """Reconstrói a janela inteira — usado na entrada e na troca de tema."""
        self.page.theme_mode = tema.modo_flet()
        self.page.bgcolor = tema.paleta().tela
        self.page.controls.clear()
        self.page.add(self.montar())
        self.atualizar()

    # --- Ações -----------------------------------------------------------

    def _alternar_tema(self, _evento: ft.Event[ft.Control]) -> None:
        tema.alternar_modo()
        self.remontar()

    async def _escolher_eventlists(self, _evento: ft.Event[ft.Container]) -> None:
        arquivos = await self.seletor.pick_files(
            dialog_title="Selecione os eventlists (.txt)",
            allow_multiple=True,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["txt"],
        )
        if arquivos:
            self.estado.definir_eventlists([Path(arquivo.path) for arquivo in arquivos])
            self.remontar()

    async def _escolher_pasta_eventlists(self, _evento: ft.Event[ft.Container]) -> None:
        pasta = await self.seletor.get_directory_path(
            dialog_title="Selecione a pasta com os eventlists"
        )
        if pasta:
            self.estado.definir_eventlists(sorted(Path(pasta).glob("*.txt")))
            self.remontar()

    async def _escolher_planilha(self, _evento: ft.Event[ft.Container]) -> None:
        arquivos = await self.seletor.pick_files(
            dialog_title="Selecione a planilha de marcadores",
            allow_multiple=False,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=EXTENSOES_PLANILHA,
        )
        if not arquivos:
            return

        caminho = Path(arquivos[0].path)
        try:
            self.estado.definir_marcadores(caminho, ler_marcadores(caminho))
        except ErroEEGHelper as erro:
            logger.error("planilha rejeitada em %s: %s", caminho, erro)
            self.estado.falhar_marcadores(caminho, str(erro))
        self.remontar()

    async def _escolher_saida(self, _evento: ft.Event[ft.Container]) -> None:
        pasta = await self.seletor.get_directory_path(dialog_title="Pasta para salvar os novos eventlists")
        if pasta:
            self.estado.definir_pasta_saida(Path(pasta))
            self.remontar()

    def _limpar_saida(self, _evento: ft.Event[ft.Container]) -> None:
        self.estado.definir_pasta_saida(None)
        self.remontar()

    def _ao_mudar_ecode(self, _evento: ft.Event[ft.TextField]) -> None:
        try:
            novo = int(self.campo_ecode.value)
        except (TypeError, ValueError):
            self.campo_ecode.value = str(self.estado.ecode_alvo)
            self.page.update()
            return
        if novo != self.estado.ecode_alvo:
            self.estado.definir_ecode_alvo(novo)
            self.atualizar()

    def _ao_escolher_coluna(self, caminho: Path, participante: str | None) -> None:
        self.estado.escolher_coluna(caminho, participante)
        self.remontar()

    async def _verificar(self, _evento: ft.Event[ft.Control]) -> None:
        """Varre participante a participante, acendendo os traços em ordem.

        O laço não existe por elegância: `ler_eventlist` de duzentos arquivos
        bloqueia por segundos, e devolver o controle ao laço de eventos a cada
        participante é o que mantém a janela viva e faz da barra de aquisição um
        progresso de verdade, não um enfeite.
        """
        estado = self.estado
        pares = estado.pares()
        config = estado.configuracao()
        marcadores = estado.marcadores
        if marcadores is None or not pares:
            return

        estado.fase = Fase.VERIFICANDO
        estado.previas = []
        self.total_a_verificar = len(pares)
        self.atualizar()

        previas = []
        for par in pares:
            previas.append(await asyncio.to_thread(verificar_par, par, marcadores, config))
            estado.previas = list(previas)
            self.area_tela.content = self._tela()
            self._atualizar_varredura()
            self.page.update()

        estado.registrar_previas(previas)
        self._foco_pulso = "verificacao"
        self.atualizar()
        self._foco_pulso = None

    async def _gravar(self, _evento: ft.Event[ft.Control]) -> None:
        estado = self.estado
        if not estado.pode_gravar:
            return

        estado.fase = Fase.GRAVANDO
        self.atualizar()

        relatorios, falhas = await asyncio.to_thread(gravar_previas, estado.previas)

        caminho_relatorio = None
        pasta = estado.pasta_do_relatorio()
        if relatorios and pasta is not None:
            caminho_relatorio = await asyncio.to_thread(
                escrever_relatorio, relatorios, pasta / NOME_RELATORIO_PADRAO
            )

        logger.info("%d gerados, %d falharam", len(relatorios), len(falhas))
        estado.registrar_gravacao(caminho_relatorio)
        self._foco_pulso = "gravacao"
        self.atualizar()
        self._foco_pulso = None


async def _principal(page: ft.Page) -> None:
    page.title = "EEGHelper"
    page.padding = 0
    page.window.min_width = tema.LARGURA_MINIMA_JANELA
    page.window.min_height = tema.ALTURA_MINIMA_JANELA
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
