"""Configuração da substituição de marcadores."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SUFIXO_SAIDA_PADRAO = "_corrigido"


@dataclass
class ConfiguracaoSubstituicao:
    """Parâmetros de uma execução de substituição de ecodes.

    Attributes:
        ecode_alvo: valor de `ecode` que representa marcadores não
            identificados e deve ser trocado. Em geral 1, mas configurável
            porque outras montagens de experimento usam outro código.
        pasta_saida: onde gravar os .txt corrigidos. Se None, grava ao lado do
            arquivo de entrada.
        sufixo_saida: sufixo acrescentado ao nome do arquivo corrigido. O
            original nunca é sobrescrito.
        exigir_contagem_exata: se True, aborta o participante quando a
            quantidade de ecodes alvo no .txt difere da quantidade de códigos
            na coluna da planilha. Desligar isso é arriscado: o pareamento é
            posicional e um descompasso desalinha todos os marcadores seguintes.
    """

    ecode_alvo: int = 1
    pasta_saida: Path | None = None
    sufixo_saida: str = SUFIXO_SAIDA_PADRAO
    exigir_contagem_exata: bool = True

    def caminho_saida_para(self, caminho_entrada: Path) -> Path:
        pasta = self.pasta_saida or caminho_entrada.parent
        return pasta / f"{caminho_entrada.stem}{self.sufixo_saida}{caminho_entrada.suffix}"
