"""Interface desktop do EEGHelper, em Flet.

Casca sobre `eeghelper.servicos`: nenhuma regra de negócio vive aqui. O ponto
de entrada é `janela.main`.

O arranjo dos módulos, e a regra de que cada vista é uma função livre que recebe
`EstadoLote` e callbacks, estão em
`docs/adr/0002-vistas-da-bancada-como-funcoes-livres.md`.
"""
