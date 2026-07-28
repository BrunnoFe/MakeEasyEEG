"""Modelos de domínio do EEGHelper.

Estruturas puras, sem dependência de I/O, pandas ou GUI. Isso mantém a lógica
testável e reaproveitável tanto pela CLI quanto pela futura interface em Flet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from eeghelper.excecoes import ErroEEGHelper

# Índice da coluna `ecode` nos campos separados por TAB de uma linha de evento
# do eventlist gerado pelo ERPLAB (item, bepoch, ecode, label, ...).
INDICE_CAMPO_ECODE = 2

# Código que o ERPLAB usa para marcar descontinuidades da fita contínua.
# Essas linhas nunca são substituídas.
ECODE_BOUNDARY = -99


@dataclass(frozen=True)
class LinhaEventlist:
    """Uma linha do arquivo .txt de eventlist, preservando o texto original.

    `campos` guarda a linha já dividida por TAB para não reprocessar a string a
    cada consulta; `texto_original` é mantido para que linhas não modificadas
    sejam reescritas byte a byte como estavam.
    """

    numero_linha: int
    texto_original: str
    eh_evento: bool
    campos: tuple[str, ...] = ()

    @property
    def ecode(self) -> int | None:
        """Valor numérico da coluna `ecode`, ou None se a linha não é evento."""
        if not self.eh_evento:
            return None
        try:
            return int(self.campos[INDICE_CAMPO_ECODE].strip())
        except (IndexError, ValueError):
            return None

    def com_novo_ecode(self, novo_ecode: int) -> LinhaEventlist:
        """Devolve uma cópia da linha com o `ecode` trocado.

        A largura do campo é preservada (alinhado à direita, como o ERPLAB
        escreve) para que o arquivo continue legível e alinhado em colunas.
        """
        if not self.eh_evento:
            raise ValueError(
                f"linha {self.numero_linha} não é uma linha de evento e não pode ter ecode alterado"
            )

        campo_atual = self.campos[INDICE_CAMPO_ECODE]
        campo_novo = str(novo_ecode).rjust(len(campo_atual))
        campos_novos = list(self.campos)
        campos_novos[INDICE_CAMPO_ECODE] = campo_novo
        return LinhaEventlist(
            numero_linha=self.numero_linha,
            texto_original="\t".join(campos_novos),
            eh_evento=True,
            campos=tuple(campos_novos),
        )


@dataclass
class Eventlist:
    """Conteúdo completo de um arquivo de eventlist do ERPLAB."""

    caminho: Path
    linhas: list[LinhaEventlist]

    @property
    def linhas_de_evento(self) -> list[LinhaEventlist]:
        return [linha for linha in self.linhas if linha.eh_evento]

    def para_texto(self) -> str:
        return "\n".join(linha.texto_original for linha in self.linhas)


@dataclass(frozen=True)
class SubstituicaoAplicada:
    """Registro de uma única troca de `ecode`, usado no relatório."""

    numero_linha: int
    item: str
    ecode_antigo: int
    ecode_novo: int


@dataclass
class RelatorioSubstituicao:
    """Resultado da substituição de um participante.

    `avisos` guarda problemas não fatais (ex.: eventos sobrando na planilha) —
    problemas fatais são levantados como exceção, não acumulados aqui.
    """

    participante: str
    caminho_entrada: Path
    caminho_saida: Path | None
    substituicoes: list[SubstituicaoAplicada] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    @property
    def total_substituido(self) -> int:
        return len(self.substituicoes)

    def resumo(self) -> str:
        destino = self.caminho_saida.name if self.caminho_saida else "(não gravado)"
        return (
            f"{self.participante}: {self.total_substituido} ecodes substituídos "
            f"em {self.caminho_entrada.name} -> {destino}"
        )


@dataclass
class PreviaParticipante:
    """O que aconteceria com um participante, calculado sem tocar em disco.

    A interface gráfica exige verificar o lote inteiro antes de gravar: o
    assistente de pesquisa não tem como perceber sozinho que um marcador ficou
    desalinhado, então ele precisa ver o resultado — inclusive a posição exata
    de uma divergência de contagem — enquanto ainda dá para desistir.

    Diferente de `processar_lote`, um participante que falha não vira exceção
    nem some do resultado: ele fica aqui com `erro` preenchido, porque a fita
    dele ainda precisa ser desenhada na tela.

    Attributes:
        total_eventos: eventos reais do eventlist (boundaries já excluídos).
            É o comprimento da fita.
        posicoes_alvo: índice, dentro dos eventos reais, de cada ocorrência do
            `ecode` alvo. São as marcas na fita.
        total_codigos: quantos códigos a coluna da planilha traz.
    """

    participante: str
    caminho_entrada: Path
    caminho_saida_previsto: Path
    total_eventos: int = 0
    posicoes_alvo: list[int] = field(default_factory=list)
    total_codigos: int = 0
    eventlist_corrigido: Eventlist | None = None
    relatorio: RelatorioSubstituicao | None = None
    erro: ErroEEGHelper | None = None

    @property
    def total_alvos(self) -> int:
        return len(self.posicoes_alvo)

    @property
    def gravavel(self) -> bool:
        """True quando a verificação produziu um eventlist pronto para gravar."""
        return self.erro is None and self.eventlist_corrigido is not None

    @property
    def indice_divergencia(self) -> int | None:
        """Posição pareável a partir da qual as duas contagens deixam de bater.

        None quando batem. É onde a fita quebra: até esse ponto o pareamento é
        confiável, depois dele não existe correspondência nenhuma.
        """
        if self.total_alvos == self.total_codigos:
            return None
        return min(self.total_alvos, self.total_codigos)

    @property
    def codigos_aplicados(self) -> list[int]:
        """Códigos que entrariam, na ordem. Vazio quando a verificação falhou."""
        if self.relatorio is None:
            return []
        return [substituicao.ecode_novo for substituicao in self.relatorio.substituicoes]
