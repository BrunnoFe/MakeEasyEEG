"""Diálogos de seleção de arquivos com Tkinter.

Isolados em um módulo próprio porque a futura interface em Flet vai substituir
apenas esta camada — os serviços não sabem que Tkinter existe.
"""

from __future__ import annotations

import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

logger = logging.getLogger(__name__)

TIPOS_PLANILHA = [
    ("Planilhas", "*.csv *.xlsx *.xlsm *.xls"),
    ("Todos os arquivos", "*.*"),
]
TIPOS_EVENTLIST = [("Eventlist do ERPLAB", "*.txt"), ("Todos os arquivos", "*.*")]


def _janela_oculta() -> tk.Tk:
    """Cria a raiz do Tk sem exibir a janela vazia atrás dos diálogos."""
    raiz = tk.Tk()
    raiz.withdraw()
    raiz.attributes("-topmost", True)
    return raiz


def selecionar_eventlists(titulo: str = "Selecione os eventlists (.txt)") -> list[Path]:
    """Abre o diálogo de seleção múltipla de eventlists. Lista vazia se cancelado."""
    raiz = _janela_oculta()
    try:
        selecionados = filedialog.askopenfilenames(title=titulo, filetypes=TIPOS_EVENTLIST)
    finally:
        raiz.destroy()
    return [Path(caminho) for caminho in selecionados]


def selecionar_planilha_marcadores(
    titulo: str = "Selecione a planilha de marcadores",
) -> Path | None:
    """Abre o diálogo de seleção da planilha. None se cancelado."""
    raiz = _janela_oculta()
    try:
        selecionado = filedialog.askopenfilename(title=titulo, filetypes=TIPOS_PLANILHA)
    finally:
        raiz.destroy()
    return Path(selecionado) if selecionado else None


def selecionar_pasta_saida(titulo: str = "Selecione a pasta de saída") -> Path | None:
    """Abre o diálogo de seleção da pasta de destino. None se cancelado."""
    raiz = _janela_oculta()
    try:
        selecionado = filedialog.askdirectory(title=titulo)
    finally:
        raiz.destroy()
    return Path(selecionado) if selecionado else None
