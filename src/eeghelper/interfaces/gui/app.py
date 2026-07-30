"""A janela do EEGHelper: uma bancada de instrumento.

Contrato de direção (semente 7ea9d984, rodada 2, índice 3 da lista fundamentada):

TESE: o lote é a tela de um instrumento de bancada, não uma lista de arquivos
com selos de status. Recusa o painel escuro de ferramenta com pílulas coloridas
e cartões de resumo que esta categoria sempre entrega.
MUNDO: tela quase preta com graticule e traços luminosos à esquerda, coluna de
controle à direita; quatro cores de canal — verde pronto, ciano varrendo, âmbar
sem coluna, coral divergente — e nada mais colorido na janela.
HISTÓRIA: o usuário liga as entradas, varre o lote, lê linha a linha onde cada
participante quebrou, e só então gera os novos eventlists.
PRIMEIRA VISTA: tela elevada ocupando a maior parte da janela, um traço por
participante sobre a mesma base de tempo; à direita, aquisição, leitura de
medição em cifras grandes e as duas ações, com Gerar destravado só depois da
varredura.
FORMA: instrumento de bancada, candidato 3 de 6; staging de vigias recusado.
FINISH: unreviewed and undocumented is unfinished; this build ends with the
finish review, the verdict, and DESIGN.md.

O único momento autoral de movimento é a varredura: durante a verificação a
barra de aquisição corre no alto da tela e os traços acendem um a um, na ordem
das linhas. Não é enfeite — é o progresso real do lote, e é a leitura de que
nada foi gerado ainda.

Esta camada não conhece `argparse` nem Tkinter, e não contém regra de negócio:
ela lê `estado.EstadoLote` e chama `servicos.lote`.

Este módulo é a `Bancada` e nada mais: o esqueleto de layout, as áreas vivas, a
sincronização e os handlers de evento. As vistas de cada região moram em
`aquisicao.py`, `regua.py`, `acoes.py`, `vazio.py` e `tabela.py`, e os primitivos
em `controles.py` — ver `docs/adr/0002-vistas-da-bancada-como-funcoes-livres.md`.
O ponto de entrada é `janela.main`.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import flet as ft

from eeghelper.dominio.modelos import PreviaParticipante
from eeghelper.excecoes import ErroEEGHelper
from eeghelper.interfaces.gui import acoes as vista_acoes
from eeghelper.interfaces.gui import aquisicao, dialogo, marca, regua, tabela, tema, vazio
from eeghelper.interfaces.gui.estado import EstadoLote, Fase
from eeghelper.io_.leitor_marcadores import ler_marcadores
from eeghelper.servicos.lote import gravar_lote, varrer_lote
from eeghelper.servicos.substituicao import inspecionar_destinos

logger = logging.getLogger(__name__)

EXTENSOES_PLANILHA = ["csv", "xlsx", "xlsm", "xls"]


class Bancada:
    """Monta a janela e mantém a tela em sincronia com o `EstadoLote`."""

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.estado = EstadoLote()
        self.seletor = ft.FilePicker()
        page.services.append(self.seletor)
        self.total_a_verificar = 0
        # Só "verificacao" ou "gravacao" no exato `atualizar()` que fecha uma
        # verificação ou uma gravação — é o que faz o pulso dos marcadores de
        # canal (ver `tabela.linha`) tocar uma vez, não a cada redesenho.
        self._foco_pulso: str | None = None
        # Se o campo livre de padrão está aberto. Mora aqui, e não no
        # `EstadoLote`, porque é preferência de tela: o lote não muda de sentido
        # conforme o usuário digitou o padrão ou escolheu um pronto.
        self._nome_personalizado = False
        # Modo da grade. Trocado só quando a largura medida cruza o limiar, e
        # não a cada pixel: remontar a tabela por evento de resize engasgaria a
        # janela num lote de duzentos arquivos.
        self._tabela_estreita = False
        # O campo do marcador procurado, devolvido por `aquisicao` a cada
        # remonte do cartão: `_ao_mudar_ecode` escreve nele para restaurar o
        # valor quando a digitação não é um número.
        self.campo_ecode = ft.TextField()

    # --- Montagem --------------------------------------------------------

    def montar(self) -> ft.Control:
        """Monta a árvore inteira na paleta em vigor.

        É remontada por completo na troca de tema: as cores estão dentro dos
        controles já construídos, e uma atualização parcial deixaria metade da
        janela no modo antigo.
        """
        cor = tema.paleta()
        self.area_tela = ft.Container(expand=True)
        # As duas áreas nascem preenchidas, e não vazias para receber conteúdo
        # depois do `page.add`: um Row que chega numa árvore já montada não
        # refaz o próprio layout, e era isso que deixava a régua de leitura com
        # o rótulo mas sem as cifras.
        self.area_leitura = ft.Column(
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[regua.regua_de_leitura(self.estado)],
        )
        self.area_acoes = ft.Column(
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[self._acoes()],
        )
        # O cartão de configuração vive num contêiner próprio pelo mesmo motivo
        # das ações: `atualizar()` troca só o conteúdo dele, e a Column rolável
        # que o embrulha sobrevive. Quando o cartão era reconstruído por
        # `remontar()`, cada escolha num dropdown recriava aquela Column e a
        # rolagem saltava de volta para o topo.
        self.area_config = ft.Column(
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[self._cartao_de_aquisicao()],
        )
        # Idem para o miolo da tabela, que troca de modo quando a janela cruza
        # o limiar de largura.
        self.area_corpo_tabela = ft.Container(expand=True, content=self._miolo_da_tabela())
        self.varredura = ft.ProgressBar(
            value=0,
            bar_height=3,
            color=cor.varrendo,
            bgcolor=ft.Colors.TRANSPARENT,
            border_radius=0,
            stop_indicator_radius=0,
            track_gap=0,
        )

        return ft.Container(
            expand=True,
            bgcolor=cor.tela,
            padding=ft.Padding.all(tema.ESPACO_5),
            content=ft.Column(
                spacing=tema.ESPACO_4,
                expand=True,
                controls=[
                    self._barra_de_topo(),
                    ft.Row(
                        spacing=tema.ESPACO_4,
                        expand=True,
                        vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                        controls=[self._painel_da_tela(), self._coluna_de_controle()],
                    ),
                ],
            ),
        )

    def _barra_de_topo(self) -> ft.Control:
        """Marca à esquerda, alternador de tema à direita."""
        cor = tema.paleta()
        alternador = ft.Container(
            width=32,
            height=32,
            border_radius=tema.RAIO_CHIP,
            align=ft.Alignment.CENTER,
            animate=tema.animacao(tema.MS_RAPIDO),
            animate_rotation=tema.animacao(tema.MS_TRANSICAO),
            rotate=ft.Rotate(0),
            tooltip="Modo claro" if cor.escura else "Modo escuro",
            on_click=self._alternar_tema,
            content=ft.Icon(
                ft.Icons.LIGHT_MODE_OUTLINED if cor.escura else ft.Icons.DARK_MODE_OUTLINED,
                size=17,
                color=cor.texto_medio,
            ),
        )

        def ao_pairar(evento: ft.Event[ft.Container]) -> None:
            pairando = bool(evento.data)
            alternador.bgcolor = cor.painel_alto if pairando else ft.Colors.TRANSPARENT
            # O giro de -20° é o único movimento gratuito da janela, e ele se paga:
            # é o que diz que o ícone é um interruptor e não um selo de estado.
            alternador.rotate = ft.Rotate(-0.35 if pairando else 0)
            alternador.update()

        alternador.on_hover = ao_pairar

        return ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    expand=True,
                    content=marca.cabecalho_da_marca(
                        "Correção de marcadores de eventlists do ERPLAB"
                    ),
                ),
                alternador,
            ],
        )

    def _painel_da_tela(self) -> ft.Control:
        """A tela do instrumento: a superfície elevada onde o lote é lido."""
        cor = tema.paleta()
        return ft.Container(
            expand=True,
            bgcolor=cor.painel,
            border_radius=tema.RAIO_PAINEL,
            border=ft.Border.all(width=1, color=cor.contorno),
            shadow=tema.sombra(alta=True),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Column(
                spacing=0,
                expand=True,
                controls=[
                    # A pista da barra fica visível sempre, em painel_alto: sem ela
                    # o cabeçalho salta 3 px quando a verificação começa.
                    ft.Container(bgcolor=cor.painel_alto, content=self.varredura),
                    self.area_leitura,
                    self._corpo_da_tabela(),
                ],
            ),
        )

    def _miolo_da_tabela(self) -> ft.Control:
        """Cabeçalho e linhas, num scroller horizontal ÚNICO quando aperta.

        Único é a palavra que importa: se o cabeçalho e a lista rolassem cada um
        por conta própria, o rótulo sairia de cima da coluna que nomeia — o
        exato defeito que `tabela._grade` existe para não ter.
        """
        conteudo = ft.Column(
            spacing=0,
            expand=True,
            controls=[tabela.cabecalho(self._tabela_estreita), self.area_tela],
        )

        if not self._tabela_estreita:
            return conteudo

        conteudo.width = tabela.LARGURA_MINIMA_TABELA
        return ft.Row(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[conteudo],
        )

    def _corpo_da_tabela(self) -> ft.Control:
        """O miolo da tabela dentro do contêiner que mede a largura disponível.

        A medição vem de `on_size_change` neste contêiner, e não de
        `page.width`: assim a largura já chega descontada da coluna de controle
        e dos recheios, sem repetir aqui uma aritmética que mudaria toda vez que
        o layout ao redor mudasse.
        """
        return ft.Container(
            expand=True,
            content=self.area_corpo_tabela,
            size_change_interval=120,
            on_size_change=self._ao_medir_tabela,
        )

    def _coluna_de_controle(self) -> ft.Control:
        """Configurar em cima, agir ao pé — e nada rolando em uso normal.

        Com a leitura movida para a régua do painel, os dois blocos que sobram
        cabem inteiros na janela mínima. A rolagem do primeiro fica só como rede
        de segurança para janelas abaixo do mínimo ou fonte de sistema ampliada;
        se ela precisar disparar, é a configuração que cede, não as ações — os
        botões são o que a janela pede a seguir, e sumir com eles para mostrar
        um campo de arquivo seria trocar o destino pelo caminho.

        A largura mora na própria Column, e não num Container em volta: dentro
        de um Container o `expand` dos filhos não vale, e sem ele nem a altura
        chega à parte rolável — o bloco colapsa e as ações são desenhadas por
        cima dele.

        Os dois blocos recebem a MESMA largura escrita, em vez de esticarem até
        a borda da coluna: só o primeiro rola, e uma barra de rolagem que come
        largura de layout deixaria o cartão de aquisição mais estreito que as
        ações logo abaixo dele. Com a largura escrita, a calha de
        `CALHA_ROLAGEM` à direita absorve a barra — apareça ela por cima do
        conteúdo ou ao lado, as duas bordas direitas coincidem nos dois casos.
        """
        return ft.Column(
            width=tema.LARGURA_COLUNA_CONTROLE,
            spacing=tema.ESPACO_4,
            controls=[
                ft.Column(
                    spacing=tema.ESPACO_4,
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        ft.Container(
                            width=tema.LARGURA_CARTAO_CONTROLE,
                            content=self.area_config,
                        )
                    ],
                ),
                ft.Container(width=tema.LARGURA_CARTAO_CONTROLE, content=self.area_acoes),
            ],
        )

    def _cartao_de_aquisicao(self) -> ft.Control:
        """Pede o cartão a `aquisicao` e guarda a referência ao campo do ecode."""
        cartao = aquisicao.montar_cartao_de_aquisicao(
            self.estado,
            nome_personalizado=self._nome_personalizado,
            ao_escolher_eventlists=self._escolher_eventlists,
            ao_escolher_pasta_eventlists=self._escolher_pasta_eventlists,
            ao_escolher_planilha=self._escolher_planilha,
            ao_escolher_saida=self._escolher_saida,
            ao_limpar_saida=self._limpar_saida,
            ao_mudar_ecode=self._ao_mudar_ecode,
            ao_escolher_preset_de_nome=self._ao_escolher_preset_de_nome,
            ao_editar_padrao_de_nome=self._ao_editar_padrao_de_nome,
            ao_alternar_relatorio=self._ao_alternar_relatorio,
            ao_editar_nome_do_relatorio=self._ao_editar_nome_do_relatorio,
            ao_escolher_formato_do_relatorio=self._ao_escolher_formato_do_relatorio,
        )
        self.campo_ecode = cartao.campo_ecode
        return cartao.controle

    def _tela(self) -> ft.Control:
        estado = self.estado

        if not estado.caminhos_eventlists or estado.marcadores is None:
            return vazio.tela_em_branco(estado)

        colunas = estado.marcadores.participantes
        por_caminho = {par.caminho_eventlist: par.participante for par in estado.pares()}
        previa_por_caminho = {previa.caminho_entrada: previa for previa in estado.previas}
        verificado = estado.fase in (Fase.VERIFICADO, Fase.GRAVADO)
        lote_limpo = estado.total_divergente == 0

        linhas = [
            tabela.linha(
                caminho=caminho,
                participante=por_caminho.get(caminho),
                previa=previa_por_caminho.get(caminho),
                verificado=verificado,
                colunas=colunas,
                ao_escolher=self._ao_escolher_coluna,
                # Calculado da configuração em vigor, e não de
                # `previa.caminho_saida_previsto`: a prévia só existe depois de
                # verificar, e a coluna precisa responder já ao preset novo.
                caminho_saida=(
                    estado.caminho_saida_de(caminho, por_caminho[caminho])
                    if caminho in por_caminho
                    else None
                ),
                foco_pulso=self._foco_pulso,
                lote_limpo=lote_limpo,
                estreita=self._tabela_estreita,
            )
            for caminho in estado.caminhos_eventlists
        ]

        return ft.ListView(
            controls=linhas,
            expand=True,
            build_controls_on_demand=True,
            item_extent=tema.ALTURA_LINHA,
            padding=ft.Padding.symmetric(vertical=tema.ESPACO_2),
        )

    def _acoes(self) -> ft.Control:
        return vista_acoes.acoes(
            self.estado,
            ao_verificar=self._verificar,
            ao_gravar=self._gravar,
        )

    # --- Sincronização ---------------------------------------------------

    def atualizar(self) -> None:
        """Refaz o conteúdo das áreas vivas sem recriar a árvore.

        Preferir isto a `remontar()` em toda ação do usuário é o que preserva a
        posição de rolagem da coluna de controle.
        """
        self.area_tela.content = self._tela()
        self.area_leitura.controls = [regua.regua_de_leitura(self.estado)]
        self.area_acoes.controls = [self._acoes()]
        self.area_config.controls = [self._cartao_de_aquisicao()]
        self._atualizar_varredura()
        self.page.update()

    def _atualizar_varredura(self) -> None:
        """A barra de aquisição no alto da tela.

        Determinada durante a verificação, porque ali existe progresso real a
        mostrar — participante calculado sobre participantes do lote. Na
        geração vira indeterminada: a escrita acontece num único bloco, e
        fingir uma fração seria inventar um progresso que ninguém mediu.
        """
        cor = tema.paleta()
        fase = self.estado.fase
        if fase == Fase.VERIFICANDO:
            self.varredura.color = cor.varrendo
            self.varredura.value = (
                len(self.estado.previas) / self.total_a_verificar if self.total_a_verificar else 0
            )
        elif fase == Fase.GRAVANDO:
            self.varredura.color = cor.pronto
            self.varredura.value = None
        else:
            self.varredura.color = ft.Colors.TRANSPARENT
            self.varredura.value = 0

    def remontar(self) -> None:
        """Reconstrói a janela inteira — usado na entrada e na troca de tema."""
        self.page.theme_mode = tema.modo_flet()
        self.page.bgcolor = tema.paleta().tela
        self.page.controls.clear()
        self.page.add(self.montar())
        self.atualizar()

    # --- Ações -----------------------------------------------------------

    def _alternar_tema(self, _evento: ft.Event[ft.Control]) -> None:
        tema.alternar_modo()
        self.remontar()

    async def _escolher_eventlists(self, _evento: ft.Event[ft.Container]) -> None:
        arquivos = await self.seletor.pick_files(
            dialog_title="Selecione os eventlists (.txt)",
            allow_multiple=True,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["txt"],
        )
        if arquivos:
            self.estado.definir_eventlists([Path(arquivo.path) for arquivo in arquivos])
            self.atualizar()

    async def _escolher_pasta_eventlists(self, _evento: ft.Event[ft.Container]) -> None:
        pasta = await self.seletor.get_directory_path(
            dialog_title="Selecione a pasta com os eventlists"
        )
        if pasta:
            self.estado.definir_eventlists(sorted(Path(pasta).glob("*.txt")))
            self.atualizar()

    async def _escolher_planilha(self, _evento: ft.Event[ft.Container]) -> None:
        arquivos = await self.seletor.pick_files(
            dialog_title="Selecione a planilha de marcadores",
            allow_multiple=False,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=EXTENSOES_PLANILHA,
        )
        if not arquivos:
            return

        caminho = Path(arquivos[0].path)
        try:
            self.estado.definir_marcadores(caminho, ler_marcadores(caminho))
        except ErroEEGHelper as erro:
            logger.error("planilha rejeitada em %s: %s", caminho, erro)
            self.estado.falhar_marcadores(caminho, str(erro))
        self.atualizar()

    async def _escolher_saida(self, _evento: ft.Event[ft.Container]) -> None:
        pasta = await self.seletor.get_directory_path(
            dialog_title="Pasta para salvar os novos eventlists"
        )
        if pasta:
            self.estado.definir_pasta_saida(Path(pasta))
            self.atualizar()

    def _limpar_saida(self, _evento: ft.Event[ft.Container]) -> None:
        self.estado.definir_pasta_saida(None)
        self.atualizar()

    def _ao_mudar_ecode(self, _evento: ft.Event[ft.TextField]) -> None:
        try:
            novo = int(self.campo_ecode.value)
        except (TypeError, ValueError):
            self.campo_ecode.value = str(self.estado.ecode_alvo)
            self.page.update()
            return
        if novo != self.estado.ecode_alvo:
            self.estado.definir_ecode_alvo(novo)
            self.atualizar()

    def _ao_escolher_preset_de_nome(self, evento: ft.Event[ft.Dropdown]) -> None:
        escolha = evento.control.value
        if escolha == aquisicao.CHAVE_PERSONALIZADO:
            self._nome_personalizado = True
        elif escolha:
            self._nome_personalizado = False
            self.estado.definir_padrao_saida(escolha)
        self.atualizar()

    def _ao_editar_padrao_de_nome(self, evento: ft.Event[ft.TextField]) -> None:
        novo = (evento.control.value or "").strip()
        if novo != self.estado.padrao_saida:
            self.estado.definir_padrao_saida(novo)
        self.atualizar()

    def _ao_alternar_relatorio(self, evento: ft.Event[ft.Checkbox]) -> None:
        self.estado.definir_relatorio(bool(evento.control.value))
        self.atualizar()

    def _ao_editar_nome_do_relatorio(self, evento: ft.Event[ft.TextField]) -> None:
        nome = (evento.control.value or "").strip()
        if nome:
            self.estado.definir_relatorio(self.estado.gerar_relatorio, nome)
        self.atualizar()

    def _ao_escolher_formato_do_relatorio(self, evento: ft.Event[ft.Dropdown]) -> None:
        if evento.control.value:
            self.estado.definir_relatorio(
                self.estado.gerar_relatorio, extensao=evento.control.value
            )
        self.atualizar()

    def _ao_medir_tabela(self, evento: ft.LayoutSizeChangeEvent) -> None:
        """Alterna entre grade elástica e grade rolante ao cruzar o limiar."""
        estreita = evento.width < tabela.LARGURA_MINIMA_TABELA
        if estreita != self._tabela_estreita:
            self._tabela_estreita = estreita
            self.area_corpo_tabela.content = self._miolo_da_tabela()
            self.atualizar()

    def _ao_escolher_coluna(self, caminho: Path, participante: str | None) -> None:
        self.estado.escolher_coluna(caminho, participante)
        self.atualizar()

    async def _verificar(self, _evento: ft.Event[ft.Control]) -> None:
        """Varre o lote acendendo os traços em ordem, sem tocar em disco.

        A varredura em si é `servicos.lote.varrer_lote`. O que fica aqui é a
        coreografia da tela: entrar na fase, redesenhar a cada participante que
        chega, e disparar o pulso dos marcadores uma única vez no fim.
        """
        estado = self.estado
        pares = estado.pares()
        config = estado.configuracao()
        marcadores = estado.marcadores
        if marcadores is None or not pares:
            return

        estado.fase = Fase.VERIFICANDO
        estado.previas = []
        self.total_a_verificar = len(pares)
        self.atualizar()

        def acender_traco(previas_parciais: list[PreviaParticipante]) -> None:
            """Redesenha só a tela e a barra: `atualizar()` inteiro a cada
            participante refaria o cartão de aquisição duzentas vezes."""
            estado.previas = previas_parciais
            self.area_tela.content = self._tela()
            self._atualizar_varredura()
            self.page.update()

        previas = await varrer_lote(pares, marcadores, config, ao_progredir=acender_traco)

        estado.registrar_previas(previas)
        self._foco_pulso = "verificacao"
        self.atualizar()
        self._foco_pulso = None

    async def _gravar(self, _evento: ft.Event[ft.Control]) -> None:
        estado = self.estado
        if not estado.pode_gravar:
            return

        # A inspeção toca o disco e roda AGORA, não no fim da verificação: entre
        # uma e outra o usuário pode ter mexido nas pastas pelo explorador, e um
        # aviso calculado antes mentiria justamente sobre o que não volta atrás.
        originais, anteriores = await asyncio.to_thread(inspecionar_destinos, estado.previas)
        pasta = estado.pasta_saida
        pasta_relatorio = estado.pasta_do_relatorio() if estado.gerar_relatorio else None
        if pasta_relatorio is not None:
            caminho = estado.configuracao().caminho_do_relatorio(pasta_relatorio)
            if caminho.exists():
                anteriores.append(caminho)

        decisao = await dialogo.confirmar_sobrescrita(self.page, originais, anteriores, pasta)
        if decisao is None:
            logger.info("gravação cancelada pelo usuário na confirmação de sobrescrita")
            return
        _, substituir_originais = decisao

        estado.fase = Fase.GRAVANDO
        self.atualizar()

        resultado = await gravar_lote(
            estado.previas,
            estado.configuracao(),
            substituir_originais=substituir_originais,
            pasta_relatorio=pasta_relatorio,
        )

        estado.registrar_gravacao(resultado.caminho_relatorio)
        self._foco_pulso = "gravacao"
        self.atualizar()
        self._foco_pulso = None
