"""Máquina de estados do lote, sem nenhuma dependência de Flet.

Toda a regra sobre *quando* a gravação pode acontecer mora aqui, e não nos
callbacks da tela. O motivo é a promessa central da interface: nada é gravado
antes de uma verificação que o usuário viu. Se essa condição ficasse espalhada
pelos handlers, uma tela nova ou um atalho a contornaria sem ninguém perceber.

Por isso a invariante mais importante deste módulo é destrutiva: **qualquer
mudança nas entradas descarta a verificação e trava a gravação de novo**. Uma
prévia obsoleta é pior que nenhuma — ela descreve um lote que não existe mais.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

from eeghelper.config import EXTENSAO_CSV, NOME_RELATORIO_PADRAO, ConfiguracaoSubstituicao
from eeghelper.dominio.modelos import PreviaParticipante
from eeghelper.dominio.nomes import PADRAO_SAIDA_PADRAO, validar_padrao
from eeghelper.io_.leitor_marcadores import TabelaMarcadores
from eeghelper.servicos.mapeamento import ParEventlistParticipante, mapear_automaticamente


class Fase(Enum):
    """Onde o lote está. A tela inteira é derivada deste valor."""

    VAZIO = auto()  # falta escolher eventlists e/ou planilha
    PRONTO = auto()  # entradas completas, nada verificado ainda
    VERIFICANDO = auto()
    VERIFICADO = auto()  # há prévias válidas; a gravação está liberada
    GRAVANDO = auto()
    GRAVADO = auto()


@dataclass
class EstadoLote:
    """Entradas escolhidas, mapeamento resolvido e prévias da verificação."""

    caminhos_eventlists: list[Path] = field(default_factory=list)
    caminho_marcadores: Path | None = None
    pasta_saida: Path | None = None
    ecode_alvo: int = 1
    # Nenhum destes é persistido entre sessões, e isso é deliberado: um padrão
    # "manter o nome original" que sobrevivesse ao fechamento voltaria armado na
    # próxima abertura, quando a pasta de saída já seria outra.
    padrao_saida: str = PADRAO_SAIDA_PADRAO
    gerar_relatorio: bool = True
    nome_relatorio: str = NOME_RELATORIO_PADRAO
    extensao_relatorio: str = EXTENSAO_CSV

    marcadores: TabelaMarcadores | None = None
    erro_marcadores: str | None = None

    # Arquivos que o mapeamento automático não resolveu, e a coluna que o
    # usuário escolheu para cada um. Uma escolha vazia significa "pular".
    nao_resolvidos: list[Path] = field(default_factory=list)
    escolhas_manuais: dict[Path, str] = field(default_factory=dict)

    previas: list[PreviaParticipante] = field(default_factory=list)
    fase: Fase = Fase.VAZIO
    caminho_relatorio: Path | None = None

    # Resultado do mapeamento automático, recalculado só quando as entradas mudam.
    _automaticos: dict[Path, str] = field(default_factory=dict, repr=False)

    # --- Entradas --------------------------------------------------------

    def definir_eventlists(self, caminhos: list[Path]) -> None:
        self.caminhos_eventlists = sorted(caminhos)
        self._remapear()

    def definir_marcadores(self, caminho: Path, tabela: TabelaMarcadores) -> None:
        self.caminho_marcadores = caminho
        self.marcadores = tabela
        self.erro_marcadores = None
        self._remapear()

    def falhar_marcadores(self, caminho: Path, mensagem: str) -> None:
        """Registra uma planilha ilegível sem apagar o que já estava escolhido."""
        self.caminho_marcadores = caminho
        self.marcadores = None
        self.erro_marcadores = mensagem
        self._remapear()

    def definir_pasta_saida(self, pasta: Path | None) -> None:
        self.pasta_saida = pasta
        self.invalidar_verificacao()

    def definir_ecode_alvo(self, ecode: int) -> None:
        self.ecode_alvo = ecode
        self.invalidar_verificacao()

    def definir_padrao_saida(self, padrao: str) -> None:
        """Troca o padrão de nome. Invalida a verificação como toda entrada.

        Obrigatório invalidar: `caminho_saida_previsto` é congelado em cada
        prévia no momento da verificação, então prévias antigas descreveriam
        arquivos que o padrão novo não geraria mais.
        """
        self.padrao_saida = padrao
        self.invalidar_verificacao()

    def definir_relatorio(
        self, gerar: bool, nome: str | None = None, extensao: str | None = None
    ) -> None:
        """Liga/desliga o relatório de auditoria, nomeia e escolhe o formato.

        Único ajuste que NÃO invalida a verificação: o relatório é escrito no
        fim da gravação e não entra em nenhuma prévia, então mudá-lo não torna
        obsoleto nada que o usuário já viu.
        """
        self.gerar_relatorio = gerar
        if nome is not None:
            self.nome_relatorio = nome
        if extensao is not None:
            self.extensao_relatorio = extensao

    def escolher_coluna(self, caminho: Path, participante: str | None) -> None:
        if participante:
            self.escolhas_manuais[caminho] = participante
        else:
            self.escolhas_manuais.pop(caminho, None)
        self.invalidar_verificacao()

    # --- Mapeamento ------------------------------------------------------

    def _remapear(self) -> None:
        """Recalcula o mapeamento automático — a única vez que ele roda.

        O resultado fica guardado porque a tela consulta `pares()` a cada
        redesenho: refazer o casamento de duzentos arquivos por quadro custaria
        caro e ainda encheria o log de avisos repetidos.
        """
        self.escolhas_manuais.clear()
        if self.marcadores is None or not self.caminhos_eventlists:
            self._automaticos = {}
            self.nao_resolvidos = list(self.caminhos_eventlists)
        else:
            resolvidos, nao_resolvidos = mapear_automaticamente(
                self.caminhos_eventlists, self.marcadores.participantes
            )
            self._automaticos = {par.caminho_eventlist: par.participante for par in resolvidos}
            self.nao_resolvidos = nao_resolvidos
        self.invalidar_verificacao()

    def pares(self) -> list[ParEventlistParticipante]:
        """Pares arquivo -> coluna prontos para verificar, na ordem da tela.

        Arquivos sem coluna automática nem escolha manual ficam de fora: são
        pulados, não adivinhados.
        """
        if self.marcadores is None:
            return []

        por_caminho = dict(self._automaticos)
        por_caminho.update(self.escolhas_manuais)

        return [
            ParEventlistParticipante(caminho, por_caminho[caminho])
            for caminho in self.caminhos_eventlists
            if caminho in por_caminho
        ]

    # --- Verificação e gravação -------------------------------------------

    def invalidar_verificacao(self) -> None:
        """Descarta prévias e trava a gravação. Chamado a cada mudança de entrada."""
        self.previas = []
        self.caminho_relatorio = None
        self.fase = Fase.PRONTO if self.entradas_completas else Fase.VAZIO

    def registrar_previas(self, previas: list[PreviaParticipante]) -> None:
        self.previas = previas
        self.fase = Fase.VERIFICADO

    def registrar_gravacao(self, caminho_relatorio: Path | None) -> None:
        self.caminho_relatorio = caminho_relatorio
        self.fase = Fase.GRAVADO

    @property
    def entradas_completas(self) -> bool:
        return bool(self.caminhos_eventlists) and self.marcadores is not None

    @property
    def pode_verificar(self) -> bool:
        return (
            self.fase in (Fase.PRONTO, Fase.VERIFICADO, Fase.GRAVADO)
            and self.entradas_completas
            and self.erro_padrao_saida is None
            and bool(self.pares())
        )

    @property
    def pode_gravar(self) -> bool:
        """Só depois de uma verificação, e só se ela aprovou alguma coisa."""
        return self.fase == Fase.VERIFICADO and self.total_gravavel > 0

    @property
    def total_gravavel(self) -> int:
        return sum(1 for previa in self.previas if previa.gravavel)

    @property
    def total_divergente(self) -> int:
        return sum(1 for previa in self.previas if not previa.gravavel)

    @property
    def total_substituicoes(self) -> int:
        return sum(len(previa.codigos_aplicados) for previa in self.previas)

    @property
    def total_pulados(self) -> int:
        """Arquivos escolhidos que não entram no lote por não terem coluna."""
        return len(self.caminhos_eventlists) - len(self.pares())

    def configuracao(self) -> ConfiguracaoSubstituicao:
        return ConfiguracaoSubstituicao(
            ecode_alvo=self.ecode_alvo,
            pasta_saida=self.pasta_saida,
            padrao_saida=self.padrao_saida,
            gerar_relatorio=self.gerar_relatorio,
            nome_relatorio=self.nome_relatorio,
            extensao_relatorio=self.extensao_relatorio,
            exigir_contagem_exata=True,
        )

    @property
    def erro_padrao_saida(self) -> str | None:
        """Mensagem de recusa do padrão atual, ou None se ele serve."""
        return validar_padrao(self.padrao_saida)

    def caminho_saida_de(self, caminho: Path, participante: str) -> Path | None:
        """O destino de um arquivo com a configuração em vigor, ou None se o
        padrão está inválido.

        A tabela chama isto a cada redesenho para mostrar o nome de saída ao
        vivo — antes da verificação, inclusive. Deliberadamente NÃO lê
        `previa.caminho_saida_previsto`, que só existe depois de verificar e
        descreveria o padrão anterior enquanto o usuário digita o novo.
        """
        if self.erro_padrao_saida is not None:
            return None
        return self.configuracao().caminho_saida_para(caminho, participante)

    def pasta_do_relatorio(self) -> Path | None:
        """Onde o relatório deve cair: a pasta de saída ou a do primeiro arquivo."""
        if self.pasta_saida is not None:
            return self.pasta_saida
        gravaveis = [previa for previa in self.previas if previa.gravavel]
        if not gravaveis:
            return None
        return gravaveis[0].caminho_entrada.parent
