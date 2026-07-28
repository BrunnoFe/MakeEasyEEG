"""Interface de linha de comando do EEGHelper.

Esta camada só coleta entradas (por argumento ou diálogo) e imprime resultados.
Toda a regra de negócio vive em `eeghelper.servicos`, para que a interface em
Flet possa reaproveitá-la sem duplicação.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from eeghelper.config import SUFIXO_SAIDA_PADRAO, ConfiguracaoSubstituicao
from eeghelper.excecoes import ErroEEGHelper
from eeghelper.interfaces import dialogos
from eeghelper.io_.escritor_eventlist import NOME_RELATORIO_PADRAO, escrever_relatorio
from eeghelper.io_.leitor_marcadores import TabelaMarcadores, ler_marcadores
from eeghelper.servicos.mapeamento import (
    ParEventlistParticipante,
    mapear_automaticamente,
)
from eeghelper.servicos.substituicao import processar_lote

logger = logging.getLogger(__name__)


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eeghelper",
        description=(
            "Substitui os ecodes não identificados de eventlists do ERPLAB pelos "
            "códigos de marcador da planilha de cada participante."
        ),
    )
    parser.add_argument(
        "--eventlists",
        type=Path,
        nargs="*",
        help="arquivos .txt ou uma pasta contendo eles. Se omitido, abre o diálogo de seleção.",
    )
    parser.add_argument(
        "--marcadores",
        type=Path,
        help="planilha .csv/.xlsx com os códigos. Se omitida, abre o diálogo de seleção.",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        help="pasta de destino dos arquivos corrigidos (padrão: ao lado do original).",
    )
    parser.add_argument(
        "--ecode-alvo",
        type=int,
        default=1,
        help="valor de ecode a ser substituído (padrão: 1).",
    )
    parser.add_argument(
        "--sufixo",
        default=SUFIXO_SAIDA_PADRAO,
        help=f"sufixo do arquivo corrigido (padrão: {SUFIXO_SAIDA_PADRAO}).",
    )
    parser.add_argument(
        "--mapeamento",
        choices=("auto", "manual"),
        default="auto",
        help=(
            "auto: casa o ID do nome do arquivo com o nome da coluna; "
            "manual: pergunta a coluna de cada arquivo."
        ),
    )
    parser.add_argument(
        "--permitir-contagem-diferente",
        action="store_true",
        help=(
            "não aborta quando a quantidade de ecodes alvo difere da planilha. "
            "Use com cautela: o pareamento é posicional."
        ),
    )
    parser.add_argument("--verboso", action="store_true", help="mostra logs de depuração.")
    return parser


def expandir_eventlists(caminhos: list[Path]) -> list[Path]:
    """Aceita arquivos e pastas, devolvendo a lista ordenada de .txt encontrados."""
    arquivos: list[Path] = []
    for caminho in caminhos:
        if caminho.is_dir():
            arquivos.extend(sorted(caminho.glob("*.txt")))
        else:
            arquivos.append(caminho)
    return arquivos


def perguntar_mapeamento_manual(
    caminhos: list[Path], marcadores: TabelaMarcadores
) -> list[ParEventlistParticipante]:
    """Pergunta, arquivo a arquivo, qual coluna da planilha usar.

    Enter em branco pula o arquivo — útil quando a planilha ainda não tem a
    identificação daquele participante.
    """
    print("\nColunas disponíveis na planilha:")
    print("  " + ", ".join(marcadores.participantes))

    pares: list[ParEventlistParticipante] = []
    for caminho in caminhos:
        resposta = input(f"Coluna para {caminho.name} (Enter para pular): ").strip()
        if not resposta:
            logger.warning("%s pulado pelo usuário", caminho.name)
            continue
        pares.append(ParEventlistParticipante(caminho, resposta))
    return pares


def executar(argumentos: list[str] | None = None) -> int:
    """Ponto de entrada da CLI. Devolve o código de saída do processo."""
    opcoes = construir_parser().parse_args(argumentos)
    logging.basicConfig(
        level=logging.DEBUG if opcoes.verboso else logging.INFO,
        format="%(levelname)s | %(name)s | %(message)s",
    )

    caminhos_eventlists = (
        expandir_eventlists(opcoes.eventlists)
        if opcoes.eventlists
        else dialogos.selecionar_eventlists()
    )
    if not caminhos_eventlists:
        print("Nenhum eventlist selecionado. Encerrando.")
        return 1

    caminho_marcadores = opcoes.marcadores or dialogos.selecionar_planilha_marcadores()
    if not caminho_marcadores:
        print("Nenhuma planilha de marcadores selecionada. Encerrando.")
        return 1

    try:
        marcadores = ler_marcadores(caminho_marcadores)
    except ErroEEGHelper as erro:
        print(f"Erro ao ler a planilha: {erro}")
        return 1

    if opcoes.mapeamento == "auto":
        pares, nao_resolvidos = mapear_automaticamente(
            caminhos_eventlists, marcadores.participantes
        )
        if nao_resolvidos:
            print("\nSem coluna correspondente (informe manualmente):")
            pares.extend(perguntar_mapeamento_manual(nao_resolvidos, marcadores))
    else:
        pares = perguntar_mapeamento_manual(caminhos_eventlists, marcadores)

    if not pares:
        print("Nenhum arquivo pôde ser associado a um participante. Encerrando.")
        return 1

    config = ConfiguracaoSubstituicao(
        ecode_alvo=opcoes.ecode_alvo,
        pasta_saida=opcoes.saida,
        sufixo_saida=opcoes.sufixo,
        exigir_contagem_exata=not opcoes.permitir_contagem_diferente,
    )

    relatorios, falhas = processar_lote(pares, marcadores, config)

    print("\n=== Resultado ===")
    for relatorio in relatorios:
        print("  " + relatorio.resumo())
        for aviso in relatorio.avisos:
            print(f"    aviso: {aviso}")
    for caminho, erro in falhas.items():
        print(f"  FALHA em {caminho.name}: {erro}")

    if relatorios:
        pasta_relatorio = opcoes.saida or relatorios[0].caminho_entrada.parent
        caminho_relatorio = escrever_relatorio(relatorios, pasta_relatorio / NOME_RELATORIO_PADRAO)
        print(f"\nRelatório: {caminho_relatorio}")

    return 0 if not falhas else 2


def main() -> None:
    sys.exit(executar())


if __name__ == "__main__":
    main()
