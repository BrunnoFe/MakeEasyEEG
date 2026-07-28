"""Associação entre arquivos de eventlist e colunas da planilha de marcadores.

Duas estratégias, como combinado: automática (o ID no nome do arquivo bate com o
nome da coluna) e manual (o usuário informa o par arquivo -> coluna).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# Captura IDs no estilo "B0002" em nomes como "B0002_eventos.txt".
PADRAO_ID_PADRAO = re.compile(r"(?P<id>[A-Za-z]+\d+)")


@dataclass(frozen=True)
class ParEventlistParticipante:
    """Um eventlist já associado à coluna de participante correspondente."""

    caminho_eventlist: Path
    participante: str


def extrair_id_participante(
    caminho: Path, padrao: re.Pattern[str] = PADRAO_ID_PADRAO
) -> str | None:
    """Extrai o ID do participante do nome do arquivo, ou None se não casar."""
    correspondencia = padrao.search(caminho.stem)
    return correspondencia.group("id") if correspondencia else None


def mapear_automaticamente(
    caminhos: list[Path],
    participantes_disponiveis: list[str],
    padrao: re.Pattern[str] = PADRAO_ID_PADRAO,
) -> tuple[list[ParEventlistParticipante], list[Path]]:
    """Casa cada eventlist com a coluna de mesmo ID.

    A comparação ignora maiúsculas/minúsculas porque a planilha e os nomes de
    arquivo costumam vir de fontes diferentes.

    Returns:
        Os pares resolvidos e a lista de arquivos que ficaram sem coluna — estes
        devem ser mapeados manualmente pelo usuário, não descartados em silêncio.
    """
    por_id = {
        participante.strip().lower(): participante for participante in participantes_disponiveis
    }

    pares: list[ParEventlistParticipante] = []
    nao_resolvidos: list[Path] = []
    for caminho in caminhos:
        identificador = extrair_id_participante(caminho, padrao)
        participante = por_id.get(identificador.lower()) if identificador else None
        if participante is None:
            logger.warning(
                "não encontrei coluna para %s (id extraído: %s)", caminho.name, identificador
            )
            nao_resolvidos.append(caminho)
        else:
            pares.append(ParEventlistParticipante(caminho, participante))

    return pares, nao_resolvidos


def mapear_manualmente(
    associacoes: dict[Path, str],
) -> list[ParEventlistParticipante]:
    """Monta os pares a partir de um mapeamento informado pelo usuário."""
    return [
        ParEventlistParticipante(caminho, participante)
        for caminho, participante in associacoes.items()
    ]
