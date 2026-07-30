"""O pé da coluna de controle: onde o lote é lido em uma frase e agido.

Uma frase de estado com um ponto colorido, e as duas ações. É a última coisa
que a janela pede, e por isso nunca cede espaço à rolagem da configuração —
ver `app.Bancada._coluna_de_controle`.
"""

from __future__ import annotations

import flet as ft

from eeghelper.interfaces.gui import controles, tema
from eeghelper.interfaces.gui.controles import AoAgir
from eeghelper.interfaces.gui.estado import EstadoLote, Fase
from eeghelper.interfaces.gui.transicao import Revelar


def acoes(estado: EstadoLote, *, ao_verificar: AoAgir, ao_gravar: AoAgir) -> ft.Control:
    """A leitura em uma frase e os dois botões, derivados só da `Fase`."""
    cor = tema.paleta()
    verificado = estado.fase in (Fase.VERIFICADO, Fase.GRAVADO)
    ocupado = estado.fase in (Fase.VERIFICANDO, Fase.GRAVANDO)

    if estado.fase == Fase.GRAVADO and estado.caminho_relatorio:
        mensagem = f"Gerado. Relatório em {estado.caminho_relatorio.name}"
        cor_ponto = cor.pronto
    elif estado.fase == Fase.GRAVANDO:
        mensagem, cor_ponto = "Gerando os arquivos aprovados…", cor.pronto
    elif estado.fase == Fase.VERIFICANDO:
        mensagem = "Verificando o lote de arquivos. Nenhum arquivo foi alterado."
        cor_ponto = cor.varrendo
    elif verificado and estado.total_divergente:
        quantos = estado.total_divergente
        mensagem = (
            f"{quantos} com contagem incompatível — "
            f"{controles.plural(quantos, 'não será gerado', 'não serão gerados')}."
        )
        cor_ponto = cor.divergente
    elif verificado:
        mensagem, cor_ponto = "Verificação sem divergências.", cor.pronto
    else:
        mensagem, cor_ponto = "Verifique os arquivos para liberar a gravação.", cor.texto_fraco

    if estado.pode_gravar:
        quantos = estado.total_gravavel
        nome_gravar = f"Gerar {quantos} {controles.plural(quantos, 'eventlist', 'eventlists')}"
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
                    controles.botao(
                        "Verificar arquivos",
                        ft.Icons.PLAY_ARROW_ROUNDED,
                        preenchido=False,
                        ao_clicar=ao_verificar,
                        desabilitado=not estado.pode_verificar or ocupado,
                    ),
                    controles.botao(
                        nome_gravar,
                        ft.Icons.SAVE_OUTLINED,
                        preenchido=True,
                        ao_clicar=ao_gravar,
                        desabilitado=not estado.pode_gravar,
                    ),
                ],
            ),
        ],
    )
