"""Testes das travas que protegem a gravação: colisão, sobrescrita e destinos.

São os testes da promessa central do app aplicada aos nomes de saída: nenhum
arquivo é apagado sem que o usuário tenha visto e autorizado.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from eeghelper.config import ConfiguracaoSubstituicao
from eeghelper.dominio.modelos import PreviaParticipante
from eeghelper.excecoes import ColisaoDeNomeSaida, ContagemIncompativel, SobrescritaRecusada
from eeghelper.io_.escritor_eventlist import escrever_eventlist
from eeghelper.io_.leitor_eventlist import ler_eventlist
from eeghelper.servicos.mapeamento import ParEventlistParticipante
from eeghelper.servicos.substituicao import (
    gravar_previas,
    inspecionar_destinos,
    marcar_colisoes,
    verificar_lote,
)

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


class MarcadoresFalsos:
    """Planilha mínima: toda coluna devolve os mesmos três códigos."""

    participantes = ["B0001", "B0002", "B0003"]

    def codigos_de(self, participante: str) -> list[int]:
        return [9, 12, 7]


@pytest.fixture
def lote(tmp_path: Path) -> list[ParEventlistParticipante]:
    pares = []
    for identificador in MarcadoresFalsos.participantes:
        caminho = tmp_path / f"{identificador}_eventos.txt"
        caminho.write_text(CABECALHO + EVENTOS, encoding="utf-8")
        pares.append(ParEventlistParticipante(caminho, identificador))
    return pares


def _verificar(lote: list[ParEventlistParticipante], **ajustes) -> list[PreviaParticipante]:
    return verificar_lote(lote, MarcadoresFalsos(), ConfiguracaoSubstituicao(**ajustes))


# --- Colisão (T1) --------------------------------------------------------


def test_padrao_colapsado_trava_o_lote_inteiro(lote: list[ParEventlistParticipante]) -> None:
    """`novos` aponta os três participantes para um arquivo só."""
    previas = _verificar(lote, padrao_saida="novos")

    assert all(not previa.gravavel for previa in previas)
    assert all(isinstance(previa.erro, ColisaoDeNomeSaida) for previa in previas)


def test_padrao_de_fabrica_nao_colide(lote: list[ParEventlistParticipante]) -> None:
    previas = _verificar(lote)
    assert all(previa.gravavel for previa in previas)


def test_manter_nome_original_nao_colide(lote: list[ParEventlistParticipante]) -> None:
    """Sem colisão entre si — o perigo aqui é T2, conferido separadamente."""
    previas = _verificar(lote, padrao_saida="{nome}")
    assert all(previa.gravavel for previa in previas)


def test_dois_arquivos_na_mesma_coluna_colidem(tmp_path: Path) -> None:
    """Caso real: o usuário mapeia dois eventlists para a mesma coluna."""
    pares = []
    for nome in ("primeiro", "segundo"):
        caminho = tmp_path / f"{nome}.txt"
        caminho.write_text(CABECALHO + EVENTOS, encoding="utf-8")
        pares.append(ParEventlistParticipante(caminho, "B0001"))

    previas = _verificar(pares, padrao_saida="{participante}")
    assert all(isinstance(previa.erro, ColisaoDeNomeSaida) for previa in previas)


def test_colisao_trava_todos_os_envolvidos_e_poupa_os_demais(tmp_path: Path) -> None:
    """Nunca elege um sobrevivente arbitrário entre os que colidem."""
    pares = []
    for nome, participante in (("a", "B0001"), ("b", "B0001"), ("c", "B0002")):
        caminho = tmp_path / f"{nome}.txt"
        caminho.write_text(CABECALHO + EVENTOS, encoding="utf-8")
        pares.append(ParEventlistParticipante(caminho, participante))

    previas = _verificar(pares, padrao_saida="{participante}")
    assert [previa.gravavel for previa in previas] == [False, False, True]


def test_destino_unico_nao_marca_colisao() -> None:
    previa = PreviaParticipante(
        participante="B0001",
        caminho_entrada=Path("/dados/a.txt"),
        caminho_saida_previsto=Path("/saida/unico.txt"),
    )
    marcar_colisoes([previa])
    assert previa.erro is None


def test_colisao_nao_apaga_erro_mais_especifico() -> None:
    """A contagem incompatível diz mais ao usuário do que "colidiu"."""
    destino = Path("/saida/mesmo.txt")
    ja_falhou = PreviaParticipante("B0001", Path("/dados/a.txt"), destino)
    ja_falhou.erro = ContagemIncompativel("128 alvos para 130 códigos")
    outra = PreviaParticipante("B0002", Path("/dados/b.txt"), destino)

    marcar_colisoes([ja_falhou, outra])

    assert isinstance(ja_falhou.erro, ContagemIncompativel)
    assert isinstance(outra.erro, ColisaoDeNomeSaida)


# --- Sobrescrita do original (T2) ----------------------------------------


def test_escrever_recusa_o_original_por_padrao(tmp_path: Path) -> None:
    caminho = tmp_path / "B0001_eventos.txt"
    caminho.write_text(CABECALHO + EVENTOS, encoding="utf-8")
    eventlist = ler_eventlist(caminho)

    with pytest.raises(FileExistsError):
        escrever_eventlist(eventlist, caminho)


def test_escrever_aceita_o_original_quando_autorizado(tmp_path: Path) -> None:
    caminho = tmp_path / "B0001_eventos.txt"
    caminho.write_text(CABECALHO + EVENTOS, encoding="utf-8")
    eventlist = ler_eventlist(caminho)

    escrever_eventlist(eventlist, caminho, permitir_sobrescrever_original=True)
    assert caminho.exists()


def test_gravar_pula_originais_sem_autorizacao(lote: list[ParEventlistParticipante]) -> None:
    previas = _verificar(lote, padrao_saida="{nome}")
    relatorios, falhas = gravar_previas(previas)

    assert relatorios == []
    assert all(isinstance(erro, SobrescritaRecusada) for erro in falhas.values())
    # Os originais continuam com os ecodes 1 intactos.
    for par in lote:
        assert "      1\t" in par.caminho_eventlist.read_text(encoding="utf-8")


def test_gravar_substitui_originais_quando_autorizado(
    lote: list[ParEventlistParticipante],
) -> None:
    previas = _verificar(lote, padrao_saida="{nome}")
    relatorios, falhas = gravar_previas(previas, permitir_sobrescrever_originais=True)

    assert len(relatorios) == 3
    assert falhas == {}
    for par in lote:
        assert "      9\t" in par.caminho_eventlist.read_text(encoding="utf-8")


def test_recusar_originais_nao_impede_os_demais(tmp_path: Path) -> None:
    """Recusar destruir um original não descarta o resto do lote."""
    pares = []
    for identificador in ("B0001", "B0002"):
        caminho = tmp_path / f"{identificador}_eventos.txt"
        caminho.write_text(CABECALHO + EVENTOS, encoding="utf-8")
        pares.append(ParEventlistParticipante(caminho, identificador))
    # Só o primeiro terá o destino igual à entrada.
    previas = verificar_lote(pares, MarcadoresFalsos(), ConfiguracaoSubstituicao())
    previas[0].caminho_saida_previsto = previas[0].caminho_entrada

    relatorios, falhas = gravar_previas(previas)

    assert len(relatorios) == 1
    assert isinstance(falhas[pares[0].caminho_eventlist], SobrescritaRecusada)


# --- Inspeção de destinos (T2 vs T3) -------------------------------------


def test_destinos_limpos_nao_acusam_nada(lote: list[ParEventlistParticipante]) -> None:
    previas = _verificar(lote)
    originais, anteriores = inspecionar_destinos(previas)

    assert originais == []
    assert anteriores == []


def test_destino_igual_a_entrada_e_classificado_como_original(
    lote: list[ParEventlistParticipante],
) -> None:
    previas = _verificar(lote, padrao_saida="{nome}")
    originais, anteriores = inspecionar_destinos(previas)

    assert len(originais) == 3
    assert anteriores == []


def test_saida_de_rodada_anterior_e_classificada_a_parte(
    lote: list[ParEventlistParticipante], tmp_path: Path
) -> None:
    saida = tmp_path / "saida"
    saida.mkdir()
    (saida / "B0001_eventos_corrigido.txt").write_text("rodada anterior", encoding="utf-8")

    previas = _verificar(lote, pasta_saida=saida)
    originais, anteriores = inspecionar_destinos(previas)

    assert originais == []
    assert [caminho.name for caminho in anteriores] == ["B0001_eventos_corrigido.txt"]
