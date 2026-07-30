"""Testes do padrão de nome de saída na camada de interface.

Não abrem janela. Cobrem duas coisas que só se quebram em tempo de execução: a
grade da tabela montar nos dois modos com a coluna nova, e o estado calcular o
nome de saída ao vivo — antes de qualquer verificação, que é o ponto da coluna.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from eeghelper.config import EXTENSAO_CSV, EXTENSAO_XLSX, EXTENSOES_RELATORIO
from eeghelper.dominio.modelos import RelatorioSubstituicao, SubstituicaoAplicada
from eeghelper.interfaces.gui import tabela
from eeghelper.interfaces.gui.estado import EstadoLote
from eeghelper.io_.escritor_eventlist import escrever_relatorio

ENTRADA = Path("/dados/B0001_eventos.txt")


@pytest.mark.parametrize("estreita", [False, True])
def test_grade_monta_nos_dois_modos(estreita: bool) -> None:
    """Elástico e rolante são exclusivos; nenhum dos dois pode explodir."""
    tabela.cabecalho(estreita)
    tabela.linha(
        caminho=ENTRADA,
        participante="B0001",
        previa=None,
        verificado=False,
        colunas=["B0001"],
        ao_escolher=lambda *_: None,
        caminho_saida=Path("/saida/B0001_eventos_corrigido.txt"),
        estreita=estreita,
    )


@pytest.mark.parametrize("estreita", [False, True])
def test_linha_pulada_aceita_saida_ausente(estreita: bool) -> None:
    """Sem coluna casada não há nome de saída — a célula mostra o travessão."""
    tabela.linha(
        caminho=Path("/dados/sem_id.txt"),
        participante=None,
        previa=None,
        verificado=False,
        colunas=["B0001"],
        ao_escolher=lambda *_: None,
        caminho_saida=None,
        estreita=estreita,
    )


def test_largura_minima_e_somada_das_partes() -> None:
    assert tabela.LARGURA_MINIMA_TABELA > tabela.LARGURA_ARQUIVO_FIXA + tabela.LARGURA_SAIDA_FIXA


def test_saida_ao_vivo_segue_o_padrao_default() -> None:
    estado = EstadoLote()
    caminho = estado.caminho_saida_de(ENTRADA, "B0001")
    assert caminho is not None
    assert caminho.name == "B0001_eventos_corrigido.txt"


def test_saida_ao_vivo_responde_a_troca_de_padrao() -> None:
    """O caso que motivou a feature: B0001_eventos.txt -> B0001_novos.txt."""
    estado = EstadoLote()
    estado.definir_padrao_saida("{participante}_novos")

    caminho = estado.caminho_saida_de(ENTRADA, "B0001")
    assert caminho is not None
    assert caminho.name == "B0001_novos.txt"


def test_padrao_invalido_trava_a_verificacao_e_some_com_a_previsao() -> None:
    estado = EstadoLote()
    estado.definir_padrao_saida("{data}")

    assert estado.erro_padrao_saida is not None
    assert estado.caminho_saida_de(ENTRADA, "B0001") is None
    assert not estado.pode_verificar


def test_trocar_padrao_invalida_a_verificacao(tmp_path: Path) -> None:
    """A invariante do módulo aplicada ao nome: prévia velha descreve outro lote."""
    estado = EstadoLote()
    estado.previas = ["prévia obsoleta"]  # type: ignore[list-item]

    estado.definir_padrao_saida("{nome}")

    assert estado.previas == []


def test_relatorio_junta_nome_e_extensao_escolhida(tmp_path: Path) -> None:
    """O nome vai sem extensão; o formato vem do dropdown."""
    estado = EstadoLote()
    estado.definir_relatorio(True, "auditoria", EXTENSAO_XLSX)

    assert estado.configuracao().caminho_do_relatorio(tmp_path).name == "auditoria.xlsx"


def test_relatorio_nasce_em_csv() -> None:
    assert EstadoLote().extensao_relatorio == EXTENSAO_CSV


@pytest.mark.parametrize("extensao", EXTENSOES_RELATORIO)
def test_relatorio_e_escrito_no_formato_do_nome(tmp_path: Path, extensao: str) -> None:
    """A extensão do caminho decide o formato, e os dois nunca discordam."""
    relatorio = RelatorioSubstituicao(
        participante="B0001",
        caminho_entrada=Path("/a/B0001.txt"),
        caminho_saida=Path("/b/B0001_corrigido.txt"),
    )
    relatorio.substituicoes.append(
        SubstituicaoAplicada(numero_linha=2, item="2", ecode_antigo=1, ecode_novo=9)
    )

    caminho = escrever_relatorio([relatorio], tmp_path / f"r{extensao}")

    assert caminho.exists()
    assert caminho.stat().st_size > 0
    if extensao == EXTENSAO_CSV:
        assert "participante" in caminho.read_text(encoding="utf-8")
    else:
        # Assinatura de arquivo ZIP — todo .xlsx é um contêiner OOXML.
        assert caminho.read_bytes()[:2] == b"PK"


def test_formato_de_relatorio_desconhecido_e_recusado(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="não suportado"):
        escrever_relatorio([], tmp_path / "relatorio.json")


def test_mudar_o_relatorio_nao_invalida_a_verificacao() -> None:
    """Assimetria deliberada: o relatório não entra em nenhuma prévia."""
    estado = EstadoLote()
    estado.previas = ["prévia válida"]  # type: ignore[list-item]

    estado.definir_relatorio(False)
    estado.definir_relatorio(True, "outro_nome.csv")

    assert estado.previas == ["prévia válida"]
    assert estado.nome_relatorio == "outro_nome.csv"
