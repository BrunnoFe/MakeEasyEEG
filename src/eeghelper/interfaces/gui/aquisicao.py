"""O cartão de aquisição: os parâmetros de entrada e de saída do lote.

Arquivos, planilha, pasta de destino, nome dos novos arquivos, relatório e o
marcador procurado — tudo o que se configura antes de varrer. É a vista com mais
callbacks da janela, e eles vêm nomeados um a um em vez de por um objeto de
contexto: a assinatura longa é a lista explícita do que este cartão pode
disparar, e ela avisa quando um campo novo tenta se instalar aqui sem dono.

`montar_cartao_de_aquisicao` devolve `CartaoDeAquisicao`, e não só o controle,
porque o campo do ecode é o único desta vista que a `Bancada` precisa alcançar
depois de desenhado — ver a docstring da dataclass.
"""

from __future__ import annotations

from dataclasses import dataclass

import flet as ft

from eeghelper.config import EXTENSOES_RELATORIO
from eeghelper.dominio.nomes import (
    EXTENSAO_EVENTLIST,
    PADRAO_MANTER_NOME,
    PADRAO_PARTICIPANTE,
    PADRAO_SAIDA_PADRAO,
)
from eeghelper.interfaces.gui import controles, tema
from eeghelper.interfaces.gui.controles import (
    AoAlternar,
    AoClicar,
    AoConfirmarTexto,
    AoEscolher,
)
from eeghelper.interfaces.gui.estado import EstadoLote

# As respostas prontas para o nome de saída, na ordem de quão comuns são. A
# primeira é o padrão de fábrica e a única segura por construção: por carregar o
# nome do arquivo de entrada, nunca faz dois participantes disputarem o mesmo
# destino. As outras duas podem, e é por isso que `marcar_colisoes` confere o
# lote antes de liberar a gravação.
PRESETS_DE_NOME = [
    ("acrescentar _corrigido", PADRAO_SAIDA_PADRAO),
    ("manter o nome original", PADRAO_MANTER_NOME),
    ("usar o nome do participante", PADRAO_PARTICIPANTE),
]
# Sentinela do dropdown. Começa com um caractere que nome de arquivo nenhum
# aceita, para nunca ser confundida com um padrão que o usuário digitou.
CHAVE_PERSONALIZADO = "\x00personalizado"


@dataclass
class CartaoDeAquisicao:
    """O cartão montado e o campo que a `Bancada` precisa reler depois.

    `campo_ecode` sai daqui porque o marcador procurado é o único parâmetro que
    se edita em vez de se escolher: quando a digitação não é um número, o
    handler restaura o valor anterior escrevendo no próprio `ft.TextField`, e
    para isso precisa da referência ao controle que acabou de ser desenhado.
    """

    controle: ft.Control
    campo_ecode: ft.TextField


def _campo_de_padrao(
    estado: EstadoLote,
    *,
    nome_personalizado: bool,
    ao_escolher_preset_de_nome: AoEscolher,
    ao_editar_padrao_de_nome: AoConfirmarTexto,
) -> ft.Control:
    """Preset de nome de saída, com o campo livre escondido atrás dele.

    O usuário comum nunca vê a sintaxe de token: escolhe uma das três
    respostas prontas. O campo só aparece em "personalizado", onde quem
    pediu poder aceita a conta de aprender `{nome}` e `{participante}` — a
    extensão não entra nessa conta porque não é escolha dele.
    """
    cor = tema.paleta()

    selecionado = CHAVE_PERSONALIZADO
    if not nome_personalizado:
        for _, padrao in PRESETS_DE_NOME:
            if padrao == estado.padrao_saida:
                selecionado = padrao
                break

    opcoes = [ft.DropdownOption(key=padrao, text=nome) for nome, padrao in PRESETS_DE_NOME]
    opcoes.append(ft.DropdownOption(key=CHAVE_PERSONALIZADO, text="personalizado…"))

    itens: list[ft.Control] = [
        controles.rotulo("nome dos novos arquivos"),
        controles.seletor(selecionado, opcoes, ao_escolher_preset_de_nome),
    ]

    if nome_personalizado:
        itens.append(
            controles.moldura_de_campo(
                controles.entrada_de_texto(estado.padrao_saida, ao_editar_padrao_de_nome)
            )
        )
        itens.append(
            controles.texto(
                f"{{nome}}  {{participante}}  ·  {EXTENSAO_EVENTLIST} automático",
                cor.texto_fraco,
                tamanho=tema.CORPO_MICRO + 1,
            )
        )

    erro = estado.erro_padrao_saida
    if erro:
        itens.append(
            ft.Text(
                erro,
                size=tema.CORPO_MICRO + 1,
                color=cor.divergente,
                font_family=tema.FAMILIA_TEXTO,
                max_lines=3,
            )
        )

    # STRETCH, e não o START padrão: sem ele cada pastilha se encolhe até o
    # próprio conteúdo, e o dropdown do preset acaba com uma largura
    # diferente da do campo livre logo abaixo — as duas bordas direitas não
    # fecham na mesma linha, que é a borda que o olho segue no cartão.
    return ft.Column(
        spacing=tema.ESPACO_2,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=itens,
    )


def _campo_de_relatorio(
    estado: EstadoLote,
    *,
    ao_alternar_relatorio: AoAlternar,
    ao_editar_nome_do_relatorio: AoConfirmarTexto,
    ao_escolher_formato_do_relatorio: AoEscolher,
) -> ft.Control:
    """Liga o relatório de auditoria, nomeia o arquivo e escolhe o formato.

    O nome vai sem tokens — há um relatório por rodada, não um por
    participante — e sem extensão: a extensão vira um dropdown porque aqui
    ela não é enfeite do nome, e sim a escolha do FORMATO em que o arquivo é
    escrito. Digitá-la à mão deixaria o nome e o conteúdo discordarem.
    """
    cor = tema.paleta()

    interruptor = ft.Checkbox(
        value=estado.gerar_relatorio,
        label="gerar relatório de substituições",
        label_style=ft.TextStyle(size=tema.CORPO, color=cor.texto, font_family=tema.FAMILIA_TEXTO),
        fill_color=cor.varrendo,
        on_change=ao_alternar_relatorio,
    )

    itens: list[ft.Control] = [interruptor]
    if estado.gerar_relatorio:
        itens.append(
            controles.moldura_de_campo(
                controles.entrada_de_texto(estado.nome_relatorio, ao_editar_nome_do_relatorio)
            )
        )
        # Dentro de uma Row porque a coluna estica os filhos: o seletor de
        # formato tem largura fixa de propósito — ".csv" não merece a
        # largura do nome do arquivo — e sob STRETCH ela seria ignorada.
        itens.append(
            ft.Row(
                controls=[
                    controles.seletor(
                        estado.extensao_relatorio,
                        [
                            ft.DropdownOption(key=extensao, text=extensao)
                            for extensao in EXTENSOES_RELATORIO
                        ],
                        ao_escolher_formato_do_relatorio,
                        largura=110,
                    )
                ]
            )
        )

    return ft.Column(
        spacing=tema.ESPACO_2,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=itens,
    )


def _cartao(nome: str, conteudo: ft.Control) -> ft.Control:
    cor = tema.paleta()
    return ft.Container(
        bgcolor=cor.painel,
        border_radius=tema.RAIO_CARTAO,
        border=ft.Border.all(width=1, color=cor.contorno),
        shadow=tema.sombra(),
        padding=ft.Padding.all(tema.ESPACO_4 + 2),
        content=ft.Column(
            spacing=tema.ESPACO_5,
            controls=[controles.rotulo(nome), conteudo],
        ),
    )


def montar_cartao_de_aquisicao(
    estado: EstadoLote,
    *,
    nome_personalizado: bool,
    ao_escolher_eventlists: AoClicar,
    ao_escolher_pasta_eventlists: AoClicar,
    ao_escolher_planilha: AoClicar,
    ao_escolher_saida: AoClicar,
    ao_limpar_saida: AoClicar,
    ao_mudar_ecode: AoConfirmarTexto,
    ao_escolher_preset_de_nome: AoEscolher,
    ao_editar_padrao_de_nome: AoConfirmarTexto,
    ao_alternar_relatorio: AoAlternar,
    ao_editar_nome_do_relatorio: AoConfirmarTexto,
    ao_escolher_formato_do_relatorio: AoEscolher,
) -> CartaoDeAquisicao:
    """Monta o cartão "arquivos e pastas" a partir do estado em vigor."""
    cor = tema.paleta()

    if estado.caminhos_eventlists:
        quantos = len(estado.caminhos_eventlists)
        valor_eventlists = controles.texto(
            f"{quantos} {controles.plural(quantos, 'arquivo', 'arquivos')} · "
            f"{estado.caminhos_eventlists[0].parent.name}"
        )
    else:
        valor_eventlists = controles.texto("nenhum escolhido", cor.texto_fraco)

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
        valor_planilha = controles.texto(
            f"{estado.caminho_marcadores.name} · {colunas} "
            f"{controles.plural(colunas, 'coluna', 'colunas')}"
        )
    else:
        valor_planilha = controles.texto("nenhuma escolhida", cor.texto_fraco)

    if estado.pasta_saida:
        valor_saida: ft.Control = controles.texto(estado.pasta_saida.name)
        acoes_saida = [
            controles.chip("trocar", ao_escolher_saida),
            controles.chip("limpar", ao_limpar_saida),
        ]
    else:
        valor_saida = controles.texto("Na mesma pasta dos eventlists.", cor.texto_fraco)
        acoes_saida = [controles.chip("escolher pasta", ao_escolher_saida)]

    campo_ecode = ft.TextField(
        value=str(estado.ecode_alvo),
        height=controles.ALTURA_CAMPO_ECODE,
        dense=True,
        border=ft.InputBorder.NONE,
        filled=False,
        content_padding=ft.Padding.symmetric(horizontal=tema.ESPACO_3, vertical=0),
        text_align=ft.TextAlign.RIGHT,
        text_style=ft.TextStyle(
            size=tema.CORPO,
            color=cor.texto,
            font_family=tema.FAMILIA_CIFRA,
            font_family_fallback=tema.FALLBACK_CIFRA,
        ),
        input_filter=ft.NumbersOnlyInputFilter(),
        on_blur=ao_mudar_ecode,
        on_submit=ao_mudar_ecode,
    )

    cartao = _cartao(
        "arquivos e pastas",
        ft.Column(
            spacing=tema.ESPACO_5,
            controls=[
                controles.campo(
                    "eventlists",
                    valor_eventlists,
                    [
                        controles.chip("arquivos", ao_escolher_eventlists),
                        controles.chip("pasta", ao_escolher_pasta_eventlists),
                    ],
                ),
                controles.campo(
                    "planilha de marcadores",
                    valor_planilha,
                    [controles.chip("escolher arquivo", ao_escolher_planilha)],
                ),
                controles.campo("onde salvar os novos eventlists", valor_saida, acoes_saida),
                # Nome e pasta são as duas metades da mesma pergunta — para
                # onde vai a saída —, então ficam encostados um no outro.
                _campo_de_padrao(
                    estado,
                    nome_personalizado=nome_personalizado,
                    ao_escolher_preset_de_nome=ao_escolher_preset_de_nome,
                    ao_editar_padrao_de_nome=ao_editar_padrao_de_nome,
                ),
                _campo_de_relatorio(
                    estado,
                    ao_alternar_relatorio=ao_alternar_relatorio,
                    ao_editar_nome_do_relatorio=ao_editar_nome_do_relatorio,
                    ao_escolher_formato_do_relatorio=ao_escolher_formato_do_relatorio,
                ),
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
                                height=controles.ALTURA_CAMPO_ECODE,
                                align=ft.Alignment.CENTER_LEFT,
                                content=controles.rotulo("marcador procurado"),
                            ),
                            controles.moldura_de_campo(campo_ecode, largura=72),
                        ],
                    ),
                ),
            ],
        ),
    )

    return CartaoDeAquisicao(controle=cartao, campo_ecode=campo_ecode)
