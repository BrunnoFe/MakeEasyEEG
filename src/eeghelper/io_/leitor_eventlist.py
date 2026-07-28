"""Leitura dos arquivos .txt de eventlist gerados pelo ERPLAB."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from eeghelper.dominio.modelos import INDICE_CAMPO_ECODE, Eventlist, LinhaEventlist
from eeghelper.excecoes import ErroLeituraEventlist

logger = logging.getLogger(__name__)

# Linhas de evento começam com o número do item na coluna 0; cabeçalho e
# comentários começam com "#" ou são linhas em branco.
PADRAO_LINHA_EVENTO = re.compile(r"^\s*\d+\s*\t")

CODIFICACAO_PADRAO = "utf-8"


def ler_eventlist(caminho: Path, codificacao: str = CODIFICACAO_PADRAO) -> Eventlist:
    """Lê um eventlist preservando integralmente o cabeçalho e o texto original.

    Só as linhas de evento são divididas em campos; todo o resto é mantido como
    está para que o arquivo corrigido continue idêntico fora da coluna `ecode`.

    Raises:
        ErroLeituraEventlist: se o arquivo não existir, não puder ser decodificado
            ou não contiver nenhuma linha de evento.
    """
    if not caminho.is_file():
        raise ErroLeituraEventlist(f"eventlist não encontrado: {caminho}")

    try:
        texto = caminho.read_text(encoding=codificacao)
    except UnicodeDecodeError as erro:
        raise ErroLeituraEventlist(
            f"falha ao decodificar {caminho} com codificação {codificacao}: {erro}"
        ) from erro

    linhas: list[LinhaEventlist] = []
    for numero, texto_linha in enumerate(texto.splitlines(), start=1):
        eh_evento = bool(PADRAO_LINHA_EVENTO.match(texto_linha))
        campos = tuple(texto_linha.split("\t")) if eh_evento else ()
        if eh_evento and len(campos) <= INDICE_CAMPO_ECODE:
            raise ErroLeituraEventlist(
                f"linha {numero} de {caminho.name} parece um evento mas tem só "
                f"{len(campos)} campos separados por TAB: {texto_linha!r}"
            )
        linhas.append(
            LinhaEventlist(
                numero_linha=numero,
                texto_original=texto_linha,
                eh_evento=eh_evento,
                campos=campos,
            )
        )

    eventlist = Eventlist(caminho=caminho, linhas=linhas)
    if not eventlist.linhas_de_evento:
        raise ErroLeituraEventlist(
            f"nenhuma linha de evento encontrada em {caminho} — o arquivo é mesmo "
            "um eventlist do ERPLAB?"
        )

    logger.debug(
        "eventlist %s lido: %d linhas, %d eventos",
        caminho.name,
        len(linhas),
        len(eventlist.linhas_de_evento),
    )
    return eventlist
