"""Configuração da substituição de marcadores."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from eeghelper.dominio.nomes import PADRAO_SAIDA_PADRAO, expandir_padrao

# Só o nome: a extensão é escolhida à parte, porque ela decide o FORMATO em que
# o relatório é escrito, e não apenas como o arquivo se chama.
NOME_RELATORIO_PADRAO = "relatorio_substituicoes"

EXTENSAO_CSV = ".csv"
EXTENSAO_XLSX = ".xlsx"
EXTENSOES_RELATORIO = (EXTENSAO_CSV, EXTENSAO_XLSX)


@dataclass
class ConfiguracaoSubstituicao:
    """Parâmetros de uma execução de substituição de ecodes.

    Attributes:
        ecode_alvo: valor de `ecode` que representa marcadores não
            identificados e deve ser trocado. Em geral 1, mas configurável
            porque outras montagens de experimento usam outro código.
        pasta_saida: onde gravar os .txt corrigidos. Se None, grava ao lado do
            arquivo de entrada.
        padrao_saida: template do nome do arquivo corrigido, com os tokens
            `{nome}`, `{participante}` e `{ext}`. O padrão de fábrica acrescenta
            um sufixo ao nome original, o que garante que cada participante
            tenha um destino próprio; padrões escritos pelo usuário podem não
            garantir, e por isso `marcar_colisoes` confere o lote depois.
        gerar_relatorio: se False, a gravação não escreve o relatório de
            auditoria.
        nome_relatorio: nome do relatório, sem extensão, dentro da pasta de
            saída. Sem tokens: há um relatório por rodada, não um por arquivo de
            entrada.
        extensao_relatorio: `.csv` ou `.xlsx`. Decide o formato de escrita, não
            só o nome do arquivo.
        exigir_contagem_exata: se True, aborta o participante quando a
            quantidade de ecodes alvo no .txt difere da quantidade de códigos
            na coluna da planilha. Desligar isso é arriscado: o pareamento é
            posicional e um descompasso desalinha todos os marcadores seguintes.
    """

    ecode_alvo: int = 1
    pasta_saida: Path | None = None
    padrao_saida: str = PADRAO_SAIDA_PADRAO
    gerar_relatorio: bool = True
    nome_relatorio: str = NOME_RELATORIO_PADRAO
    extensao_relatorio: str = EXTENSAO_CSV
    exigir_contagem_exata: bool = True

    def caminho_saida_para(self, caminho_entrada: Path, participante: str) -> Path:
        pasta = self.pasta_saida or caminho_entrada.parent
        return pasta / expandir_padrao(self.padrao_saida, caminho_entrada, participante)

    def caminho_do_relatorio(self, pasta: Path) -> Path:
        return pasta / f"{self.nome_relatorio}{self.extensao_relatorio}"
