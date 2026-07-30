"""Testes da expansão e da validação do padrão de nome de saída."""

from __future__ import annotations

from pathlib import Path

import pytest

from eeghelper.dominio.nomes import (
    EXTENSAO_EVENTLIST,
    PADRAO_MANTER_NOME,
    PADRAO_PARTICIPANTE,
    PADRAO_SAIDA_PADRAO,
    expandir_padrao,
    validar_padrao,
)

ENTRADA = Path("/dados/B0001_eventos.txt")


def test_padrao_de_fabrica_acrescenta_sufixo() -> None:
    assert expandir_padrao(PADRAO_SAIDA_PADRAO, ENTRADA, "B0001") == "B0001_eventos_corrigido.txt"


def test_manter_nome_original_repete_a_entrada() -> None:
    assert expandir_padrao(PADRAO_MANTER_NOME, ENTRADA, "B0001") == "B0001_eventos.txt"


def test_participante_substitui_o_nome_inteiro() -> None:
    """O caso que motivou a feature: B0001_eventos.txt -> B0001_novos.txt."""
    assert expandir_padrao("{participante}_novos", ENTRADA, "B0001") == "B0001_novos.txt"


def test_extensao_e_sempre_txt_independente_da_entrada() -> None:
    """O usuário não escolhe a extensão: eventlist do ERPLAB é sempre .txt."""
    assert expandir_padrao(PADRAO_PARTICIPANTE, Path("a.dat"), "P1") == f"P1{EXTENSAO_EVENTLIST}"


def test_participante_com_caractere_proibido_e_higienizado() -> None:
    """Cabeçalho de planilha é texto livre: `P01/P02` não pode virar uma pasta."""
    assert expandir_padrao(PADRAO_PARTICIPANTE, ENTRADA, "P01/P02") == "P01_P02.txt"


def test_acento_e_espaco_sobrevivem() -> None:
    assert expandir_padrao(PADRAO_PARTICIPANTE, ENTRADA, "Sessão 2") == "Sessão 2.txt"


def test_token_desconhecido_levanta_na_expansao() -> None:
    with pytest.raises(ValueError, match="token desconhecido"):
        expandir_padrao("{data}", ENTRADA, "B0001")


@pytest.mark.parametrize("padrao", [PADRAO_SAIDA_PADRAO, PADRAO_MANTER_NOME, PADRAO_PARTICIPANTE])
def test_presets_sao_validos(padrao: str) -> None:
    assert validar_padrao(padrao) is None


@pytest.mark.parametrize("padrao", ["", "   "])
def test_padrao_vazio_e_recusado(padrao: str) -> None:
    assert validar_padrao(padrao) is not None


def test_token_desconhecido_e_recusado() -> None:
    mensagem = validar_padrao("{data}")
    assert mensagem is not None
    assert "{data}" in mensagem


def test_ext_deixou_de_ser_token() -> None:
    """A extensão saiu do vocabulário quando virou fixa."""
    assert validar_padrao("{nome}{ext}") is not None


@pytest.mark.parametrize("proibido", list('\\/:*?"<>|'))
def test_caractere_proibido_no_literal_e_recusado(proibido: str) -> None:
    assert validar_padrao(f"{{nome}}{proibido}x") is not None


def test_padrao_sem_extensao_e_o_esperado() -> None:
    assert validar_padrao("{nome}_corrigido") is None


def test_extensao_escrita_a_mao_e_recusada() -> None:
    """Aceitá-la produziria `B0001.txt.txt` — o ponto é sempre engano aqui."""
    mensagem = validar_padrao("{nome}.txt")
    assert mensagem is not None
    assert EXTENSAO_EVENTLIST in mensagem
