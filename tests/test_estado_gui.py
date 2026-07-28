"""Testes da máquina de estados da interface desktop.

Não abrem janela: `EstadoLote` é puro de propósito, porque a garantia que ele
guarda — nada é gravado sem uma verificação atual — é forte demais para viver
solta em callbacks de tela.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from eeghelper.interfaces.gui.estado import EstadoLote, Fase
from eeghelper.io_.leitor_marcadores import TabelaMarcadores
from eeghelper.servicos.substituicao import verificar_lote

CABECALHO = (
    "#  Non-editable header begin ---\n"
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


@pytest.fixture
def estado(tmp_path: Path, marcadores: TabelaMarcadores) -> EstadoLote:
    estado = EstadoLote()
    caminhos = []
    for nome in ("B0001_eventos.txt", "B0002_eventos.txt"):
        caminho = tmp_path / nome
        caminho.write_text(CABECALHO + EVENTOS, encoding="utf-8")
        caminhos.append(caminho)
    estado.definir_eventlists(caminhos)
    estado.definir_marcadores(tmp_path / "marcadores.csv", marcadores)
    return estado


def test_comeca_vazio() -> None:
    vazio = EstadoLote()
    assert vazio.fase is Fase.VAZIO
    assert not vazio.pode_verificar
    assert not vazio.pode_gravar


def test_entradas_completas_liberam_apenas_a_verificacao(estado: EstadoLote) -> None:
    assert estado.fase is Fase.PRONTO
    assert estado.pode_verificar
    assert not estado.pode_gravar


def test_gravacao_so_libera_depois_de_verificar(
    estado: EstadoLote, marcadores: TabelaMarcadores
) -> None:
    estado.registrar_previas(verificar_lote(estado.pares(), marcadores, estado.configuracao()))

    assert estado.fase is Fase.VERIFICADO
    assert estado.pode_gravar
    assert estado.total_gravavel == 2
    assert estado.total_substituicoes == 6


@pytest.mark.parametrize(
    "mudar",
    [
        lambda estado: estado.definir_ecode_alvo(2),
        lambda estado: estado.definir_pasta_saida(Path("saida")),
        lambda estado: estado.definir_eventlists(estado.caminhos_eventlists[:1]),
    ],
    ids=["ecode", "pasta-saida", "eventlists"],
)
def test_mudar_entrada_descarta_a_verificacao(
    estado: EstadoLote, marcadores: TabelaMarcadores, mudar
) -> None:
    estado.registrar_previas(verificar_lote(estado.pares(), marcadores, estado.configuracao()))
    assert estado.pode_gravar

    mudar(estado)

    # Uma prévia obsoleta descreve um lote que não existe mais.
    assert estado.previas == []
    assert estado.fase is Fase.PRONTO
    assert not estado.pode_gravar


def test_arquivo_sem_coluna_fica_de_fora_ate_ser_preenchido(
    tmp_path: Path, marcadores: TabelaMarcadores
) -> None:
    orfao = tmp_path / "sem_identificador.txt"
    orfao.write_text(CABECALHO + EVENTOS, encoding="utf-8")

    estado = EstadoLote()
    estado.definir_eventlists([orfao])
    estado.definir_marcadores(tmp_path / "marcadores.csv", marcadores)

    assert estado.nao_resolvidos == [orfao]
    assert estado.pares() == []
    assert estado.total_pulados == 1
    assert not estado.pode_verificar

    estado.escolher_coluna(orfao, "B0002")

    assert [par.participante for par in estado.pares()] == ["B0002"]
    assert estado.total_pulados == 0
    assert estado.pode_verificar


def test_planilha_ilegivel_nao_apaga_os_eventlists(estado: EstadoLote) -> None:
    estado.falhar_marcadores(Path("ruim.csv"), "coluna vazia na linha 4")

    assert estado.erro_marcadores == "coluna vazia na linha 4"
    assert len(estado.caminhos_eventlists) == 2
    assert estado.fase is Fase.VAZIO
    assert not estado.pode_verificar
