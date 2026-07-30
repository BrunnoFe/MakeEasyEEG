"""Orquestração do lote de ponta a ponta, sem bloquear quem chama.

São os irmãos assíncronos do que `substituicao.py` já faz de forma síncrona:
`substituicao.verificar_lote` varre o lote num só bloco, o que serve a um teste
mas congela uma janela por segundos num lote de duzentos arquivos. `varrer_lote`
aqui devolve o controle ao laço de eventos a cada participante e informa o
progresso, o que é o que mantém a interface viva.

Este módulo não importa `flet` e não conhece tela: o progresso sai por callback,
e quem chama decide se isso vira uma barra, uma linha de log ou nada. Foi
extraído de `interfaces/gui/app.py`, onde o laço da varredura e a chamada de
`marcar_colisoes` desmentiam a promessa de que a GUI é casca sem regra de
negócio.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from eeghelper.config import ConfiguracaoSubstituicao
from eeghelper.dominio.modelos import PreviaParticipante, RelatorioSubstituicao
from eeghelper.excecoes import ErroEEGHelper
from eeghelper.io_.escritor_eventlist import escrever_relatorio
from eeghelper.io_.leitor_marcadores import TabelaMarcadores
from eeghelper.servicos.mapeamento import ParEventlistParticipante
from eeghelper.servicos.substituicao import gravar_previas, marcar_colisoes, verificar_par

logger = logging.getLogger(__name__)


@dataclass
class ResultadoDaGravacao:
    """O que a gravação escreveu, o que falhou e onde ficou o relatório.

    As falhas vêm em separado dos relatórios, e não somadas numa contagem só:
    um participante que não gravou é informação que a tela precisa mostrar linha
    a linha, não um número no rodapé.
    """

    relatorios: list[RelatorioSubstituicao] = field(default_factory=list)
    falhas: dict[Path, ErroEEGHelper] = field(default_factory=dict)
    caminho_relatorio: Path | None = None


async def varrer_lote(
    pares: list[ParEventlistParticipante],
    marcadores: TabelaMarcadores,
    config: ConfiguracaoSubstituicao,
    *,
    ao_progredir: Callable[[list[PreviaParticipante]], None] | None = None,
) -> list[PreviaParticipante]:
    """Verifica o lote participante a participante, sem tocar em disco.

    O laço não existe por elegância: `ler_eventlist` de duzentos arquivos
    bloqueia por segundos, e devolver o controle ao laço de eventos a cada
    participante é o que mantém a janela viva e faz da barra de aquisição um
    progresso de verdade, não um enfeite.

    Args:
        ao_progredir: chamado depois de cada participante, com as prévias
            acumuladas até ali. As colisões ainda NÃO foram marcadas nessa
            lista parcial — ver abaixo.

    Returns:
        Uma prévia por par, na ordem recebida, já com as colisões marcadas.
    """
    previas: list[PreviaParticipante] = []
    for par in pares:
        previas.append(await asyncio.to_thread(verificar_par, par, marcadores, config))
        if ao_progredir is not None:
            ao_progredir(list(previas))

    # Só aqui, com o lote inteiro calculado, dá para saber se dois arquivos
    # disputam o mesmo destino — colisão é propriedade do lote, não da linha.
    marcar_colisoes(previas)
    return previas


async def gravar_lote(
    previas: list[PreviaParticipante],
    config: ConfiguracaoSubstituicao,
    *,
    substituir_originais: bool,
    pasta_relatorio: Path | None,
) -> ResultadoDaGravacao:
    """Grava as prévias aprovadas e, se pedido, a trilha de auditoria.

    Args:
        pasta_relatorio: onde escrever o relatório da rodada, ou None para não
            escrever nenhum. O nome e o formato vêm de `config`.

    Returns:
        Os relatórios das substituições aplicadas, as falhas por caminho de
        entrada e o caminho do relatório, quando houve um.
    """
    relatorios, falhas = await asyncio.to_thread(gravar_previas, previas, substituir_originais)

    caminho_relatorio = None
    if pasta_relatorio is not None and relatorios:
        caminho_relatorio = await asyncio.to_thread(
            escrever_relatorio,
            relatorios,
            config.caminho_do_relatorio(pasta_relatorio),
        )

    logger.info("%d gerados, %d falharam", len(relatorios), len(falhas))
    return ResultadoDaGravacao(
        relatorios=relatorios,
        falhas=falhas,
        caminho_relatorio=caminho_relatorio,
    )
