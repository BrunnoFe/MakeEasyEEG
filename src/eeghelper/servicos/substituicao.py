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
from eeghelper.excecoes import (
    ColisaoDeNomeSaida,
    ContagemIncompativel,
    ErroEEGHelper,
    SobrescritaRecusada,
)
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
        caminho_saida_previsto=config.caminho_saida_para(par.caminho_eventlist, par.participante),
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


def marcar_colisoes(previas: list[PreviaParticipante]) -> None:
    """Trava as prévias que disputam o mesmo arquivo de saída.

    Colisão é propriedade do lote, não de um participante, então não cabe em
    `verificar_par`: só depois de calcular todos os destinos dá para saber se
    eles são distintos. Com o padrão de fábrica nunca são iguais — ele carrega o
    nome do arquivo de entrada —, mas um padrão do usuário sem token variável
    (`novos{ext}`) apontaria o lote inteiro para um arquivo só, e as gravações
    se apagariam em cascata sem nenhum aviso.

    Todos os envolvidos numa colisão são travados, e não todos menos um: gravar
    "o primeiro" elegeria um sobrevivente arbitrário e o usuário perderia os
    demais achando que o lote passou.
    """
    por_destino: dict[Path, list[PreviaParticipante]] = {}
    for previa in previas:
        por_destino.setdefault(previa.caminho_saida_previsto.resolve(), []).append(previa)

    for destino, disputantes in por_destino.items():
        if len(disputantes) < 2:
            continue
        nomes = ", ".join(previa.caminho_entrada.name for previa in disputantes)
        logger.error("colisão de nome de saída em %s entre %s", destino.name, nomes)
        for previa in disputantes:
            # Não sobrescreve um erro anterior: a contagem incompatível que a
            # verificação achou é mais específica e mais útil ao usuário do que
            # "colidiu", e as duas travam a linha do mesmo jeito.
            if previa.erro is None:
                previa.erro = ColisaoDeNomeSaida(
                    f"{len(disputantes)} eventlists gerariam {destino.name}: {nomes}"
                )


def verificar_lote(
    pares: list[ParEventlistParticipante],
    marcadores: TabelaMarcadores,
    config: ConfiguracaoSubstituicao,
) -> list[PreviaParticipante]:
    """Verifica o lote inteiro. Não cria, altera nem remove nenhum arquivo."""
    previas = [verificar_par(par, marcadores, config) for par in pares]
    marcar_colisoes(previas)
    return previas


def inspecionar_destinos(
    previas: list[PreviaParticipante],
) -> tuple[list[PreviaParticipante], list[Path]]:
    """Separa o que a gravação apagaria, em duas categorias bem diferentes.

    A checagem toca o disco e por isso deve rodar no instante da gravação, não
    no da verificação: entre uma e outra o usuário pode ter mexido nas pastas
    pelo explorador de arquivos, e um aviso calculado antes mentiria.

    Returns:
        Os participantes cujo destino é o próprio eventlist de entrada — perda
        irreversível de dado bruto — e os demais caminhos já ocupados em disco,
        que costumam ser a saída de uma rodada anterior sendo reprocessada.
    """
    originais: list[PreviaParticipante] = []
    anteriores: list[Path] = []

    for previa in previas:
        if not previa.gravavel:
            continue
        destino = previa.caminho_saida_previsto
        if destino.resolve() == previa.caminho_entrada.resolve():
            originais.append(previa)
        elif destino.exists():
            anteriores.append(destino)

    return originais, anteriores


def gravar_previas(
    previas: list[PreviaParticipante],
    permitir_sobrescrever_originais: bool = False,
) -> tuple[list[RelatorioSubstituicao], dict[Path, ErroEEGHelper]]:
    """Grava os eventlists corrigidos das prévias que a verificação aprovou.

    Prévias com `erro` são devolvidas como falhas sem tentativa de escrita: a
    verificação já decidiu que elas não podem ser gravadas.

    Args:
        permitir_sobrescrever_originais: autorização vinda da confirmação do
            usuário. Sem ela, um participante cujo destino é o próprio arquivo
            de entrada é marcado com `SobrescritaRecusada` e pulado — o restante
            do lote grava normalmente, porque recusar destruir três originais
            não é motivo para descartar os outros cento e noventa e sete.

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

        e_o_original = previa.caminho_saida_previsto.resolve() == previa.caminho_entrada.resolve()
        if e_o_original and not permitir_sobrescrever_originais:
            previa.erro = SobrescritaRecusada(
                f"substituir {previa.caminho_entrada.name} não foi autorizado"
            )
            falhas[previa.caminho_entrada] = previa.erro
            continue

        escrever_eventlist(
            previa.eventlist_corrigido,
            previa.caminho_saida_previsto,
            permitir_sobrescrever_original=e_o_original,
        )
        previa.relatorio.caminho_saida = previa.caminho_saida_previsto
        relatorios.append(previa.relatorio)

    return relatorios, falhas
