"""Núcleo do EEGHelper: troca dos ecodes não identificados pelos códigos reais."""

from __future__ import annotations

import logging
from pathlib import Path

from eeghelper.config import ConfiguracaoSubstituicao
from eeghelper.dominio.modelos import (
    ECODE_BOUNDARY,
    Eventlist,
    PreviaParticipante,
    RelatorioSubstituicao,
    SubstituicaoAplicada,
)
from eeghelper.excecoes import ContagemIncompativel, ErroEEGHelper
from eeghelper.io_.escritor_eventlist import escrever_eventlist
from eeghelper.io_.leitor_eventlist import ler_eventlist
from eeghelper.io_.leitor_marcadores import TabelaMarcadores
from eeghelper.servicos.mapeamento import ParEventlistParticipante

logger = logging.getLogger(__name__)


def substituir_ecodes(
    eventlist: Eventlist,
    participante: str,
    codigos: list[int],
    config: ConfiguracaoSubstituicao,
) -> tuple[Eventlist, RelatorioSubstituicao]:
    """Substitui, em ordem, cada `ecode` alvo pelo código correspondente.

    O pareamento é posicional: a n-ésima ocorrência do `ecode` alvo recebe o
    n-ésimo código da coluna do participante. Linhas de boundary (-99) e
    qualquer outro `ecode` são ignoradas e reescritas intactas.

    Raises:
        ContagemIncompativel: quando as quantidades não batem e
            `config.exigir_contagem_exata` está ligado. Seguir adiante nesse caso
            desalinharia todos os marcadores a partir do ponto de divergência.
    """
    alvos = [
        linha
        for linha in eventlist.linhas_de_evento
        if linha.ecode == config.ecode_alvo and linha.ecode != ECODE_BOUNDARY
    ]

    relatorio = RelatorioSubstituicao(
        participante=participante,
        caminho_entrada=eventlist.caminho,
        caminho_saida=None,
    )

    if len(alvos) != len(codigos):
        mensagem = (
            f"{participante}: o eventlist {eventlist.caminho.name} tem {len(alvos)} "
            f"eventos com ecode {config.ecode_alvo}, mas a planilha traz "
            f"{len(codigos)} códigos para esse participante"
        )
        if config.exigir_contagem_exata:
            raise ContagemIncompativel(mensagem)
        relatorio.avisos.append(mensagem + " — substituindo apenas o trecho pareável")

    linhas_alteradas = {linha.numero_linha: linha for linha in alvos}
    novas_linhas = []
    posicao = 0
    for linha in eventlist.linhas:
        if linha.numero_linha in linhas_alteradas and posicao < len(codigos):
            codigo = codigos[posicao]
            posicao += 1
            novas_linhas.append(linha.com_novo_ecode(codigo))
            relatorio.substituicoes.append(
                SubstituicaoAplicada(
                    numero_linha=linha.numero_linha,
                    item=linha.campos[0].strip(),
                    ecode_antigo=config.ecode_alvo,
                    ecode_novo=codigo,
                )
            )
        else:
            novas_linhas.append(linha)

    eventlist_corrigido = Eventlist(caminho=eventlist.caminho, linhas=novas_linhas)
    logger.info(
        "%s: %d ecodes substituídos em %s",
        participante,
        relatorio.total_substituido,
        eventlist.caminho.name,
    )
    return eventlist_corrigido, relatorio


def verificar_par(
    par: ParEventlistParticipante,
    marcadores: TabelaMarcadores,
    config: ConfiguracaoSubstituicao,
) -> PreviaParticipante:
    """Calcula o resultado de um participante sem escrever nada em disco.

    Nenhuma exceção de negócio escapa: uma falha vira `previa.erro`, porque a
    interface gráfica precisa continuar exibindo a fita de um participante que
    não pode ser gravado — é justamente ali que está a informação útil.
    """
    previa = PreviaParticipante(
        participante=par.participante,
        caminho_entrada=par.caminho_eventlist,
        caminho_saida_previsto=config.caminho_saida_para(par.caminho_eventlist),
    )

    try:
        eventlist = ler_eventlist(par.caminho_eventlist)
        eventos = [linha for linha in eventlist.linhas_de_evento if linha.ecode != ECODE_BOUNDARY]
        previa.total_eventos = len(eventos)
        previa.posicoes_alvo = [
            posicao for posicao, linha in enumerate(eventos) if linha.ecode == config.ecode_alvo
        ]

        codigos = marcadores.codigos_de(par.participante)
        previa.total_codigos = len(codigos)

        corrigido, relatorio = substituir_ecodes(eventlist, par.participante, codigos, config)
        previa.eventlist_corrigido = corrigido
        previa.relatorio = relatorio
    except ErroEEGHelper as erro:
        logger.error("falha ao verificar %s: %s", par.caminho_eventlist.name, erro)
        previa.erro = erro

    return previa


def verificar_lote(
    pares: list[ParEventlistParticipante],
    marcadores: TabelaMarcadores,
    config: ConfiguracaoSubstituicao,
) -> list[PreviaParticipante]:
    """Verifica o lote inteiro. Não cria, altera nem remove nenhum arquivo."""
    return [verificar_par(par, marcadores, config) for par in pares]


def gravar_previas(
    previas: list[PreviaParticipante],
) -> tuple[list[RelatorioSubstituicao], dict[Path, ErroEEGHelper]]:
    """Grava os eventlists corrigidos das prévias que a verificação aprovou.

    Prévias com `erro` são devolvidas como falhas sem tentativa de escrita: a
    verificação já decidiu que elas não podem ser gravadas.

    Returns:
        Os relatórios gravados e um dicionário arquivo -> erro para os demais.
    """
    relatorios: list[RelatorioSubstituicao] = []
    falhas: dict[Path, ErroEEGHelper] = {}

    for previa in previas:
        if not previa.gravavel:
            if previa.erro is not None:
                falhas[previa.caminho_entrada] = previa.erro
            continue

        assert previa.eventlist_corrigido is not None and previa.relatorio is not None
        escrever_eventlist(previa.eventlist_corrigido, previa.caminho_saida_previsto)
        previa.relatorio.caminho_saida = previa.caminho_saida_previsto
        relatorios.append(previa.relatorio)

    return relatorios, falhas


def processar_par(
    par: ParEventlistParticipante,
    marcadores: TabelaMarcadores,
    config: ConfiguracaoSubstituicao,
) -> RelatorioSubstituicao:
    """Executa o fluxo completo de um participante: ler, substituir e gravar.

    Raises:
        ErroEEGHelper: qualquer falha de negócio da verificação.
    """
    previa = verificar_par(par, marcadores, config)
    if previa.erro is not None:
        raise previa.erro

    relatorios, _ = gravar_previas([previa])
    return relatorios[0]


def processar_lote(
    pares: list[ParEventlistParticipante],
    marcadores: TabelaMarcadores,
    config: ConfiguracaoSubstituicao,
) -> tuple[list[RelatorioSubstituicao], dict[Path, ErroEEGHelper]]:
    """Processa vários participantes, isolando a falha de um dos demais.

    Um participante com planilha incompatível não deve impedir a correção dos
    outros — daí a coleta de falhas em vez de propagar a primeira exceção.

    Returns:
        Os relatórios bem-sucedidos e um dicionário arquivo -> erro para os que
        falharam.
    """
    return gravar_previas(verificar_lote(pares, marcadores, config))
