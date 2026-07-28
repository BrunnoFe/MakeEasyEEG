"""Gravação dos eventlists corrigidos e do relatório de substituições."""

from __future__ import annotations

import csv
import logging
from pathlib import Path

from eeghelper.dominio.modelos import Eventlist, RelatorioSubstituicao

logger = logging.getLogger(__name__)

NOME_RELATORIO_PADRAO = "relatorio_substituicoes.csv"


def escrever_eventlist(eventlist: Eventlist, caminho_saida: Path) -> Path:
    """Grava o eventlist corrigido, criando a pasta de destino se necessário.

    Raises:
        FileExistsError: se o destino for o próprio arquivo de entrada — o
            original nunca deve ser sobrescrito.
    """
    if caminho_saida.resolve() == eventlist.caminho.resolve():
        raise FileExistsError(f"recusando sobrescrever o eventlist original: {eventlist.caminho}")

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    caminho_saida.write_text(eventlist.para_texto() + "\n", encoding="utf-8")
    logger.info("eventlist corrigido gravado em %s", caminho_saida)
    return caminho_saida


def escrever_relatorio(relatorios: list[RelatorioSubstituicao], caminho_saida: Path) -> Path:
    """Grava um CSV com uma linha por substituição aplicada.

    O relatório é a trilha de auditoria da correção: permite conferir depois
    qual código entrou em qual linha sem reabrir os arquivos no MATLAB.
    """
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    with caminho_saida.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")
        escritor.writerow(
            ["participante", "arquivo", "linha", "item", "ecode_antigo", "ecode_novo"]
        )
        for relatorio in relatorios:
            for substituicao in relatorio.substituicoes:
                escritor.writerow(
                    [
                        relatorio.participante,
                        relatorio.caminho_entrada.name,
                        substituicao.numero_linha,
                        substituicao.item,
                        substituicao.ecode_antigo,
                        substituicao.ecode_novo,
                    ]
                )

    logger.info("relatório gravado em %s", caminho_saida)
    return caminho_saida
