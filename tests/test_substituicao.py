"""Testes do núcleo de substituição de ecodes."""

from __future__ import annotations

from pathlib import Path

import pytest

from eeghelper.config import ConfiguracaoSubstituicao
from eeghelper.excecoes import ContagemIncompativel, ErroLeituraEventlist
from eeghelper.io_.leitor_eventlist import ler_eventlist
from eeghelper.servicos.mapeamento import extrair_id_participante, mapear_automaticamente
from eeghelper.servicos.substituicao import substituir_ecodes

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
def eventlist_exemplo(tmp_path: Path) -> Path:
    caminho = tmp_path / "B0002_eventos.txt"
    caminho.write_text(CABECALHO + EVENTOS, encoding="utf-8")
    return caminho


def test_boundary_e_cabecalho_ficam_intactos(eventlist_exemplo: Path) -> None:
    eventlist = ler_eventlist(eventlist_exemplo)
    corrigido, _ = substituir_ecodes(eventlist, "B0002", [9, 12, 7], ConfiguracaoSubstituicao())

    linhas = corrigido.para_texto().splitlines()
    assert linhas[:6] == CABECALHO.splitlines()
    assert linhas[6].split("\t")[2].strip() == "-99"
    assert [linha.split("\t")[2].strip() for linha in linhas[7:]] == ["9", "12", "7"]


def test_largura_da_coluna_ecode_e_preservada(eventlist_exemplo: Path) -> None:
    eventlist = ler_eventlist(eventlist_exemplo)
    corrigido, _ = substituir_ecodes(eventlist, "B0002", [9, 12, 7], ConfiguracaoSubstituicao())

    campos = corrigido.para_texto().splitlines()[7].split("\t")
    assert campos[2] == "      9"
    assert campos[3] == "              S1"


def test_relatorio_registra_cada_troca(eventlist_exemplo: Path) -> None:
    eventlist = ler_eventlist(eventlist_exemplo)
    _, relatorio = substituir_ecodes(eventlist, "B0002", [9, 12, 7], ConfiguracaoSubstituicao())

    assert relatorio.total_substituido == 3
    assert relatorio.substituicoes[0].item == "2"
    assert relatorio.substituicoes[0].ecode_novo == 9


def test_contagem_incompativel_aborta(eventlist_exemplo: Path) -> None:
    eventlist = ler_eventlist(eventlist_exemplo)
    with pytest.raises(ContagemIncompativel):
        substituir_ecodes(eventlist, "B0002", [9, 12], ConfiguracaoSubstituicao())


def test_contagem_incompativel_com_aviso_quando_permitido(eventlist_exemplo: Path) -> None:
    eventlist = ler_eventlist(eventlist_exemplo)
    config = ConfiguracaoSubstituicao(exigir_contagem_exata=False)
    _, relatorio = substituir_ecodes(eventlist, "B0002", [9, 12], config)

    assert relatorio.total_substituido == 2
    assert relatorio.avisos


def test_arquivo_sem_eventos_e_rejeitado(tmp_path: Path) -> None:
    caminho = tmp_path / "vazio.txt"
    caminho.write_text(CABECALHO, encoding="utf-8")
    with pytest.raises(ErroLeituraEventlist):
        ler_eventlist(caminho)


def test_mapeamento_automatico_por_id_no_nome(tmp_path: Path) -> None:
    caminhos = [tmp_path / "B0002_eventos.txt", tmp_path / "sem_id.txt"]
    pares, nao_resolvidos = mapear_automaticamente(caminhos, ["B0001", "B0002"])

    assert extrair_id_participante(caminhos[0]) == "B0002"
    assert [par.participante for par in pares] == ["B0002"]
    assert nao_resolvidos == [caminhos[1]]
