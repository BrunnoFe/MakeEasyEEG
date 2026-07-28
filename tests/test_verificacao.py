"""Testes da verificação: o que a interface gráfica mostra antes de gravar.

A garantia central destes testes é negativa — `verificar_lote` não pode encostar
no disco. É ela que sustenta a promessa da tela de que dá para desistir depois
de ver o resultado.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from eeghelper.config import ConfiguracaoSubstituicao
from eeghelper.excecoes import ContagemIncompativel
from eeghelper.io_.leitor_marcadores import TabelaMarcadores
from eeghelper.servicos.mapeamento import ParEventlistParticipante
from eeghelper.servicos.substituicao import gravar_previas, verificar_lote, verificar_par

CABECALHO = (
    "#  Non-editable header begin ---\n"
    "#  nevents...................: 4\n"
    "#  Non-editable header end ---\n"
    "\n"
    "# item\t bepoch\t  ecode\t            label\t      onset\n"
    "\n"
)
EVENTOS = (
    "1     \t0     \t    -99\t        boundary\t      0.0000\n"
    "2     \t0     \t      1\t              S1\t     14.3840\n"
    "3     \t0     \t      1\t              S1\t     18.1720\n"
    "4     \t0     \t      1\t              S1\t     21.0120\n"
)


@pytest.fixture
def marcadores() -> TabelaMarcadores:
    dados = pd.DataFrame({"event": [1, 2, 3], "B0001": [9, 12, 7], "B0002": [9, 9, 9]})
    return TabelaMarcadores(dados=dados, coluna_evento="event")


def _eventlist(pasta: Path, nome: str) -> Path:
    caminho = pasta / nome
    caminho.write_text(CABECALHO + EVENTOS, encoding="utf-8")
    return caminho


def test_verificar_nao_toca_no_disco(tmp_path: Path, marcadores: TabelaMarcadores) -> None:
    entrada = _eventlist(tmp_path, "B0001_eventos.txt")
    antes = sorted(caminho.name for caminho in tmp_path.iterdir())

    previas = verificar_lote(
        [ParEventlistParticipante(entrada, "B0001")], marcadores, ConfiguracaoSubstituicao()
    )

    assert previas[0].gravavel
    assert sorted(caminho.name for caminho in tmp_path.iterdir()) == antes


def test_previa_descreve_a_fita(tmp_path: Path, marcadores: TabelaMarcadores) -> None:
    entrada = _eventlist(tmp_path, "B0001_eventos.txt")

    previa = verificar_par(
        ParEventlistParticipante(entrada, "B0001"), marcadores, ConfiguracaoSubstituicao()
    )

    # O boundary não entra na fita: a contagem começa no primeiro evento real.
    assert previa.total_eventos == 3
    assert previa.posicoes_alvo == [0, 1, 2]
    assert previa.total_codigos == 3
    assert previa.indice_divergencia is None
    assert previa.codigos_aplicados == [9, 12, 7]


def test_divergencia_aponta_a_posicao_da_quebra(tmp_path: Path) -> None:
    entrada = _eventlist(tmp_path, "B0001_eventos.txt")
    dados = pd.DataFrame({"event": [1, 2], "B0001": [9, 12]})
    marcadores_curtos = TabelaMarcadores(dados=dados, coluna_evento="event")

    previa = verificar_par(
        ParEventlistParticipante(entrada, "B0001"),
        marcadores_curtos,
        ConfiguracaoSubstituicao(),
    )

    assert isinstance(previa.erro, ContagemIncompativel)
    assert not previa.gravavel
    # A fita continua desenhável, e quebra na terceira marca.
    assert previa.total_alvos == 3
    assert previa.total_codigos == 2
    assert previa.indice_divergencia == 2


def test_gravar_pula_previa_com_erro(tmp_path: Path, marcadores: TabelaMarcadores) -> None:
    boa = _eventlist(tmp_path, "B0001_eventos.txt")
    # Dois eventos alvo contra três códigos na planilha: contagem incompatível.
    ruim = tmp_path / "B0002_eventos.txt"
    ruim.write_text(CABECALHO + "".join(EVENTOS.splitlines(True)[:3]), encoding="utf-8")

    previas = verificar_lote(
        [
            ParEventlistParticipante(boa, "B0001"),
            ParEventlistParticipante(ruim, "B0002"),
        ],
        marcadores,
        ConfiguracaoSubstituicao(),
    )
    relatorios, falhas = gravar_previas(previas)

    assert [relatorio.participante for relatorio in relatorios] == ["B0001"]
    assert list(falhas) == [ruim]
    assert (tmp_path / "B0001_eventos_corrigido.txt").is_file()
    assert not (tmp_path / "B0002_eventos_corrigido.txt").exists()


def test_original_nunca_e_sobrescrito(tmp_path: Path, marcadores: TabelaMarcadores) -> None:
    entrada = _eventlist(tmp_path, "B0001_eventos.txt")
    original = entrada.read_text(encoding="utf-8")

    previas = verificar_lote(
        [ParEventlistParticipante(entrada, "B0001")], marcadores, ConfiguracaoSubstituicao()
    )
    gravar_previas(previas)

    assert entrada.read_text(encoding="utf-8") == original
