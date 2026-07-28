"""Exceções específicas do EEGHelper.

Ter uma hierarquia própria permite que a CLI e a futura GUI em Flet tratem
falhas de negócio (planilha incompatível, participante ausente) de forma
diferente de erros de programação.
"""

from __future__ import annotations


class ErroEEGHelper(Exception):
    """Base de todos os erros esperados do EEGHelper."""


class ErroLeituraEventlist(ErroEEGHelper):
    """Arquivo .txt de eventlist ausente, vazio ou fora do formato do ERPLAB."""


class ErroLeituraMarcadores(ErroEEGHelper):
    """Planilha de marcadores ausente, vazia ou com colunas inesperadas."""


class ParticipanteNaoEncontrado(ErroEEGHelper):
    """Não há coluna na planilha correspondente ao participante do eventlist."""


class ContagemIncompativel(ErroEEGHelper):
    """Quantidade de ecodes alvo no .txt difere da quantidade de códigos na planilha."""
