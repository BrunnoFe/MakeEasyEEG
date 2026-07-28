"""Leitura da planilha de marcadores identificados (.csv ou .xlsx).

Formato esperado: primeira coluna com o número do evento e uma coluna por
participante, cada célula contendo o código numérico do marcador daquele evento.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from eeghelper.excecoes import ErroLeituraMarcadores, ParticipanteNaoEncontrado

logger = logging.getLogger(__name__)

EXTENSOES_EXCEL = {".xlsx", ".xlsm", ".xls"}


class TabelaMarcadores:
    """Acesso às colunas de códigos de cada participante."""

    def __init__(self, dados: pd.DataFrame, coluna_evento: str) -> None:
        self._dados = dados
        self.coluna_evento = coluna_evento

    @property
    def participantes(self) -> list[str]:
        """Nomes das colunas de participantes, na ordem da planilha."""
        return [str(coluna) for coluna in self._dados.columns if coluna != self.coluna_evento]

    def codigos_de(self, participante: str) -> list[int]:
        """Códigos do participante, na ordem dos eventos da planilha.

        Raises:
            ParticipanteNaoEncontrado: se não houver coluna com esse nome.
            ErroLeituraMarcadores: se a coluna tiver células vazias ou não numéricas.
        """
        if participante not in self._dados.columns:
            raise ParticipanteNaoEncontrado(
                f"participante {participante!r} não existe na planilha. "
                f"Colunas disponíveis: {', '.join(self.participantes)}"
            )

        coluna = self._dados[participante]
        if coluna.isna().any():
            linhas_vazias = [int(indice) + 2 for indice in coluna[coluna.isna()].index]
            raise ErroLeituraMarcadores(
                f"coluna {participante!r} tem células vazias ou não numéricas nas "
                f"linhas {linhas_vazias} da planilha"
            )
        return [int(valor) for valor in coluna]


def ler_marcadores(caminho: Path, aba: str | int = 0) -> TabelaMarcadores:
    """Lê a planilha de marcadores, aceitando .csv (com , ou ;) e Excel.

    Raises:
        ErroLeituraMarcadores: se o arquivo não existir, estiver vazio ou não
            puder ser interpretado.
    """
    if not caminho.is_file():
        raise ErroLeituraMarcadores(f"planilha de marcadores não encontrada: {caminho}")

    try:
        if caminho.suffix.lower() in EXTENSOES_EXCEL:
            dados = pd.read_excel(caminho, sheet_name=aba)
        else:
            # sep=None + engine="python" deixa o pandas inferir o separador,
            # porque exportações em pt-BR costumam usar ";".
            dados = pd.read_csv(caminho, sep=None, engine="python")
    except (ValueError, pd.errors.ParserError) as erro:
        raise ErroLeituraMarcadores(f"falha ao ler {caminho}: {erro}") from erro

    if dados.empty or len(dados.columns) < 2:
        raise ErroLeituraMarcadores(
            f"{caminho} precisa ter uma coluna de evento e ao menos uma de "
            f"participante; encontrei colunas: {list(dados.columns)}"
        )

    dados = dados.apply(pd.to_numeric, errors="coerce")
    coluna_evento = str(dados.columns[0])
    logger.debug(
        "planilha %s lida: %d eventos, %d participantes",
        caminho.name,
        len(dados),
        len(dados.columns) - 1,
    )
    return TabelaMarcadores(dados=dados, coluna_evento=coluna_evento)
