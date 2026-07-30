"""Os primitivos da bancada: tipografia, pastilha, campo, botão e seletor.

Este módulo é a ÚNICA casa dos controles que não conhecem o lote. Nada aqui lê
`EstadoLote` nem chama serviço: as funções recebem valores e callbacks e
devolvem `ft.Control`. É por isso que `tabela.py`, `aquisicao.py`, `regua.py`,
`acoes.py`, `vazio.py` e `dialogo.py` todos importam daqui, e este arquivo não
importa nenhum deles — a dependência aponta das vistas para os primitivos, sem
exceção.

`texto`, `rotulo` e `cifra` moravam em `tabela.py`, onde nasceram. Não é lugar
de tipografia: o cartão de aquisição e a régua de leitura escrevem rótulos que
não têm relação nenhuma com a grade de participantes, e `dialogo.py` importava o
módulo da tabela inteiro só para escrever uma linha de texto.

As decisões de aparência que valem para a janela toda — por que Gravar é a única
superfície com gradiente, por que a pastilha sobe 1 px ao pairar — estão no
contrato de direção em `app.py`.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

import flet as ft

from eeghelper.interfaces.gui import tema

# Os handlers da bancada são metade `def` e metade `async def` — escolher um
# arquivo abre um diálogo do sistema e precisa aguardar, limpar a pasta de saída
# não. O Flet aceita as duas formas, então os tipos daqui aceitam as duas
# também: um alias que prometesse só `None` recusaria, na checagem de tipo, todo
# handler que precisa esperar o disco.
AoClicar = Callable[[ft.Event[ft.Container]], Awaitable[None] | None]
AoAgir = Callable[[ft.Event[ft.Control]], Awaitable[None] | None]
AoConfirmarTexto = Callable[[ft.Event[ft.TextField]], Awaitable[None] | None]
AoEscolher = Callable[[ft.Event[ft.Dropdown]], Awaitable[None] | None]
AoAlternar = Callable[[ft.Event[ft.Checkbox]], Awaitable[None] | None]

ALTURA_CAMPO_ECODE = 34
ALTURA_BOTAO = 42


def plural(quantidade: int, singular: str, plural_: str) -> str:
    """Concorda o substantivo com a contagem.

    Um lote de um participante é comum aqui, e "1 divergentes" numa tela que
    pede confiança é exatamente o tipo de descuido que a corrói.
    """
    return singular if quantidade == 1 else plural_


def cifra(valor: str, cor: str | None = None, negrito: bool = False) -> ft.Text:
    """Leitura numérica do instrumento: monoespaçada e alinhada à direita."""
    return ft.Text(
        valor,
        font_family=tema.FAMILIA_CIFRA,
        font_family_fallback=tema.FALLBACK_CIFRA,
        size=tema.CORPO,
        color=cor or tema.paleta().texto,
        weight=ft.FontWeight.W_700 if negrito else ft.FontWeight.NORMAL,
        text_align=ft.TextAlign.RIGHT,
        no_wrap=True,
    )


def rotulo(texto_: str, cor: str | None = None) -> ft.Text:
    """Rótulo versalete: caixa alta, corpo miúdo, entreletra aberta."""
    return ft.Text(
        texto_.upper(),
        font_family=tema.FAMILIA_TEXTO,
        font_family_fallback=tema.FALLBACK_TEXTO,
        size=tema.CORPO_MICRO,
        color=cor or tema.paleta().texto_fraco,
        weight=ft.FontWeight.W_600,
        style=ft.TextStyle(letter_spacing=tema.TRACKING_ROTULO),
        no_wrap=True,
        # Como `texto()`: um rótulo que não coube deve terminar em elipse, e não
        # ser cortado no meio do glifo. Não muda nada enquanto ele couber.
        overflow=ft.TextOverflow.ELLIPSIS,
    )


def texto(valor: str, cor: str | None = None, tamanho: float = tema.CORPO) -> ft.Text:
    return ft.Text(
        valor,
        font_family=tema.FAMILIA_TEXTO,
        font_family_fallback=tema.FALLBACK_TEXTO,
        size=tamanho,
        color=cor or tema.paleta().texto,
        no_wrap=True,
        overflow=ft.TextOverflow.ELLIPSIS,
    )


def chip(nome: str, ao_clicar: AoClicar) -> ft.Control:
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
        content=texto(nome, cor.texto_medio, tema.CORPO_MICRO + 1),
    )

    def ao_pairar(evento: ft.Event[ft.Container]) -> None:
        pairando = bool(evento.data)
        pastilha.bgcolor = cor.painel_alto if pairando else ft.Colors.TRANSPARENT
        pastilha.border = ft.Border.all(width=1, color=cor.acento if pairando else cor.contorno)
        pastilha.offset = ft.Offset(0, -0.04 if pairando else 0)
        pastilha.update()

    pastilha.on_hover = ao_pairar
    return pastilha


def campo(nome: str, valor: ft.Control, acoes: list[ft.Control]) -> ft.Control:
    """Um parâmetro de aquisição: placa gravada, valor e ações.

    O ícone saiu. Num cartão de quatro campos, quatro ícones outline de 13 px
    dizem menos do que o próprio nome do campo e cobram uma coluna de 21 px que
    o valor usaria melhor — a marca já carrega a identidade da janela.
    """
    return ft.Column(
        spacing=tema.ESPACO_2,
        controls=[
            rotulo(nome),
            valor,
            ft.Container(
                margin=ft.Margin.only(top=2),
                content=ft.Row(spacing=tema.ESPACO_2, controls=acoes),
            ),
        ],
    )


def botao(
    nome: str,
    icone: str,
    preenchido: bool,
    ao_clicar: AoAgir,
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
    superficie = ft.Container(
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
            superficie.offset = ft.Offset(0, -0.03 if pairando else 0)
            if not preenchido:
                superficie.bgcolor = cor.painel_alto if pairando else ft.Colors.TRANSPARENT
            superficie.update()

        superficie.on_hover = ao_pairar

    return superficie


def moldura_de_campo(conteudo: ft.Control, largura: float | None = None) -> ft.Container:
    """A pastilha arredondada onde os campos editáveis moram.

    O arredondamento vem daqui, e não do `border_radius` do próprio campo:
    com `InputBorder.NONE` o Flutter não tem forma de borda para arredondar,
    e o preenchimento sai quadrado por mais que o raio seja pedido. A
    moldura por fora é o mesmo recurso que `tabela._celula_participante` usa
    para o dropdown das colunas.
    """
    cor = tema.paleta()
    return ft.Container(
        width=largura,
        height=ALTURA_CAMPO_ECODE,
        bgcolor=cor.painel_alto,
        border_radius=tema.RAIO_CHIP,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=conteudo,
    )


def entrada_de_texto(valor: str, ao_confirmar: AoConfirmarTexto) -> ft.TextField:
    """Campo de texto sem fundo próprio — quem pinta é `moldura_de_campo`.

    Confirma em `on_blur` e `on_submit`, e não em `on_change`: revalidar a
    cada tecla marcaria como inválido todo padrão pela metade e faria a
    tabela inteira piscar enquanto o usuário digita.
    """
    cor = tema.paleta()
    return ft.TextField(
        value=valor,
        height=ALTURA_CAMPO_ECODE,
        dense=True,
        border=ft.InputBorder.NONE,
        filled=False,
        content_padding=ft.Padding.symmetric(horizontal=tema.ESPACO_3, vertical=0),
        text_style=ft.TextStyle(
            size=tema.CORPO,
            color=cor.texto,
            font_family=tema.FAMILIA_CIFRA,
            font_family_fallback=tema.FALLBACK_CIFRA,
        ),
        on_blur=ao_confirmar,
        on_submit=ao_confirmar,
    )


def seletor(
    valor: str,
    opcoes: list[ft.DropdownOption],
    ao_escolher: AoEscolher,
    largura: float | None = None,
) -> ft.Control:
    """Dropdown na mesma pastilha arredondada dos campos de texto.

    Três coisas o separam de um dropdown solto do Flet:

    - a seta é declarada à mão. A padrão é um ícone de 24 px, e o
      `InputDecorator` reserva a largura dela ANTES de aplicar o
      `content_padding`: com a pastilha de 34 px a seta encostava na borda
      e empurrava o texto para cima do centro. Em 18 px, com o respiro à
      direita menor que o da esquerda, o rótulo volta à linha do campo de
      texto vizinho;
    - `moldura_de_campo` recorta o retângulo, então o campo não precisa de
      borda nenhuma — só de ter a de foco desligada, ou o Flutter desenha o
      fio azul do Material por baixo do recorte;
    - a moldura acende no foco. O menu do Flet abre e fecha com a animação
      do Flutter, que não é configurável; o que dá para animar é o campo, e
      é o que responde ao clique enquanto a folha viaja.
    """
    cor = tema.paleta()
    moldura = moldura_de_campo(ft.Container(), largura=largura)

    def acender(aceso: bool) -> None:
        moldura.border = ft.Border.all(
            width=1,
            color=cor.varrendo if aceso else ft.Colors.TRANSPARENT,
        )
        moldura.bgcolor = ft.Colors.with_opacity(0.10, cor.varrendo) if aceso else cor.painel_alto
        moldura.update()

    for opcao in opcoes:
        opcao.style = tema.estilo_de_opcao()

    moldura.animate = tema.animacao(tema.MS_RAPIDO)
    moldura.border = ft.Border.all(width=1, color=ft.Colors.TRANSPARENT)
    moldura.content = ft.Dropdown(
        value=valor,
        height=ALTURA_CAMPO_ECODE,
        options=opcoes,
        border=ft.InputBorder.NONE,
        filled=False,
        dense=True,
        text_size=tema.CORPO,
        text_style=ft.TextStyle(size=tema.CORPO, color=cor.texto, font_family=tema.FAMILIA_TEXTO),
        content_padding=ft.Padding.only(left=tema.ESPACO_3, right=tema.ESPACO_1),
        trailing_icon=ft.Icon(ft.Icons.EXPAND_MORE, size=18, color=cor.texto_fraco),
        selected_trailing_icon=ft.Icon(ft.Icons.EXPAND_LESS, size=18, color=cor.varrendo),
        menu_height=tema.ALTURA_MENU,
        menu_style=tema.estilo_de_menu(),
        on_select=ao_escolher,
        on_focus=lambda _: acender(True),
        on_blur=lambda _: acender(False),
    )
    return moldura
