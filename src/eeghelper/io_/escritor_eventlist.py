"""Gravação dos eventlists corrigidos e do relatório de substituições."""

from __future__ import annotations

import csv
import logging
from pathlib import Path

from eeghelper.config import EXTENSAO_CSV, EXTENSAO_XLSX
from eeghelper.dominio.modelos import Eventlist, RelatorioSubstituicao

logger = logging.getLogger(__name__)


def escrever_eventlist(
    eventlist: Eventlist,
    caminho_saida: Path,
    permitir_sobrescrever_original: bool = False,
) -> Path:
    """Grava o eventlist corrigido, criando a pasta de destino se necessário.

    Args:
        permitir_sobrescrever_original: libera gravar por cima do arquivo de
            entrada. O default recusa, e essa recusa é a proteção do dado bruto
            do experimento: uma vez apagado, o eventlist original não volta. A
            autorização só chega pela confirmação explícita do usuário na
            interface, nunca por configuração persistida — um interruptor que
            sobrevivesse à sessão voltaria armado numa rodada futura.

    Raises:
        FileExistsError: se o destino for o próprio arquivo de entrada e a
            sobrescrita não tiver sido autorizada.
    """
    e_o_original = caminho_saida.resolve() == eventlist.caminho.resolve()
    if e_o_original and not permitir_sobrescrever_original:
        raise FileExistsError(f"recusando sobrescrever o eventlist original: {eventlist.caminho}")

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    caminho_saida.write_text(eventlist.para_texto() + "\n", encoding="utf-8")
    logger.info("eventlist corrigido gravado em %s", caminho_saida)
    return caminho_saida


COLUNAS_RELATORIO = ["participante", "arquivo", "linha", "item", "ecode_antigo", "ecode_novo"]


def _linhas_do_relatorio(relatorios: list[RelatorioSubstituicao]) -> list[list[object]]:
    """Uma linha por substituição aplicada, na ordem dos participantes."""
    return [
        [
            relatorio.participante,
            relatorio.caminho_entrada.name,
            substituicao.numero_linha,
            substituicao.item,
            substituicao.ecode_antigo,
            substituicao.ecode_novo,
        ]
        for relatorio in relatorios
        for substituicao in relatorio.substituicoes
    ]


def escrever_relatorio(relatorios: list[RelatorioSubstituicao], caminho_saida: Path) -> Path:
    """Grava a trilha de auditoria da correção, em CSV ou XLSX.

    O formato vem da EXTENSÃO do caminho pedido, e não de um parâmetro à parte:
    assim o nome do arquivo e o que está dentro dele nunca discordam.

    O relatório permite conferir depois qual código entrou em qual linha sem
    reabrir os arquivos no MATLAB.

    Raises:
        ValueError: extensão fora de `.csv` e `.xlsx`.
    """
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    linhas = _linhas_do_relatorio(relatorios)
    extensao = caminho_saida.suffix.lower()

    if extensao == EXTENSAO_XLSX:
        # Import adiado: pandas custa alguns segundos para carregar, e o CSV é o
        # caminho comum. Quem nunca escolhe xlsx não paga por ele.
        import pandas as pd

        pd.DataFrame(linhas, columns=COLUNAS_RELATORIO).to_excel(caminho_saida, index=False)
    elif extensao == EXTENSAO_CSV:
        with caminho_saida.open("w", encoding="utf-8", newline="") as arquivo:
            escritor = csv.writer(arquivo, delimiter=";")
            escritor.writerow(COLUNAS_RELATORIO)
            escritor.writerows(linhas)
    else:
        raise ValueError(f"formato de relatório não suportado: {caminho_saida.suffix}")

    logger.info("relatório gravado em %s", caminho_saida)
    return caminho_saida
