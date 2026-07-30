"""O padrão de nome dos eventlists corrigidos.

Até aqui o nome de saída era imposto pelo programa e, por isso, seguro por
construção: ele sempre carregava o nome do arquivo de entrada, e dois arquivos
na mesma pasta nunca têm o mesmo nome. Abrir o padrão para o usuário abre junto
a possibilidade de um padrão *colapsado* — `novos.txt` sem nenhum token que
varie faz duzentos participantes disputarem um único arquivo.

Este módulo não tenta impedir isso. Não há como: nem o nome dos eventlists nem
os cabeçalhos da planilha seguem uma estrutura confiável, então qualquer regra
esperta erraria em algum laboratório. A defesa mora em `servicos.substituicao`,
que confere se os nomes do lote são todos distintos e trava a gravação quando
não são. Aqui só ficam a expansão e as recusas que dependem apenas do padrão em
si — texto vazio, token inexistente, caractere que o sistema de arquivos não
aceita.
"""

from __future__ import annotations

import re
from pathlib import Path

TOKEN_NOME = "nome"
TOKEN_PARTICIPANTE = "participante"

TOKENS_VALIDOS = frozenset({TOKEN_NOME, TOKEN_PARTICIPANTE})

# A extensão não é escolha do usuário: eventlist do ERPLAB é .txt, e um arquivo
# corrigido com outra extensão não seria lido de volta por nada na cadeia. Ela é
# acrescentada sempre, e o padrão trata só do nome.
EXTENSAO_EVENTLIST = ".txt"

PADRAO_SAIDA_PADRAO = "{nome}_corrigido"
PADRAO_MANTER_NOME = "{nome}"
PADRAO_PARTICIPANTE = "{participante}"

# Proibidos em nome de arquivo no Windows, que é o piso do projeto. Manter a
# lista igual nos três sistemas evita que um padrão criado numa máquina gere
# arquivos irrecuperáveis noutra.
CARACTERES_PROIBIDOS = '\\/:*?"<>|'

_TOKEN = re.compile(r"\{([^{}]*)\}")

# Valores de sondagem para validar um padrão sem ter um participante real em mãos.
_ENTRADA_SONDA = Path("B0001_eventos.txt")
_PARTICIPANTE_SONDA = "B0001"


def tokens_do_padrao(padrao: str) -> list[str]:
    """Os nomes de token escritos no padrão, na ordem em que aparecem."""
    return _TOKEN.findall(padrao)


def _higienizar(valor: str) -> str:
    """Troca por `_` os caracteres que o sistema de arquivos recusa.

    Aplicado apenas aos valores substituídos, nunca ao texto literal do padrão:
    o literal é responsabilidade do usuário e `validar_padrao` o recusa antes,
    mas o participante vem do cabeçalho da planilha e pode trazer qualquer
    coisa — uma coluna chamada `P01/P02` não deve derrubar o lote inteiro.
    """
    return "".join("_" if caractere in CARACTERES_PROIBIDOS else caractere for caractere in valor)


def expandir_padrao(padrao: str, caminho_entrada: Path, participante: str) -> str:
    """Resolve o padrão no nome de arquivo de um participante.

    Args:
        padrao: template do NOME, com os tokens `{nome}` e `{participante}`. Sem
            extensão: `EXTENSAO_EVENTLIST` é acrescentada no fim.
        caminho_entrada: eventlist de origem, de onde sai `{nome}`.
        participante: coluna da planilha casada com esse eventlist.

    Returns:
        O nome do arquivo com extensão, sem pasta.

    Raises:
        ValueError: se o padrão citar um token que não existe. É erro de
            programação: a interface valida antes com `validar_padrao`.
    """
    valores = {
        TOKEN_NOME: caminho_entrada.stem,
        TOKEN_PARTICIPANTE: participante,
    }

    def substituir(achado: re.Match[str]) -> str:
        token = achado.group(1)
        if token not in valores:
            raise ValueError(f"token desconhecido no padrão de saída: {{{token}}}")
        return _higienizar(valores[token])

    return _TOKEN.sub(substituir, padrao).strip() + EXTENSAO_EVENTLIST


def validar_padrao(padrao: str) -> str | None:
    """Confere se o padrão pode gerar nomes de arquivo válidos.

    Returns:
        Uma mensagem em português explicando a recusa, ou None se o padrão
        serve. Não detecta colisão entre arquivos: isso depende do lote inteiro
        e é conferido por `servicos.substituicao.marcar_colisoes`.
    """
    if not padrao.strip():
        return "O nome dos novos arquivos não pode ficar em branco."

    desconhecidos = [token for token in tokens_do_padrao(padrao) if token not in TOKENS_VALIDOS]
    if desconhecidos:
        citados = ", ".join(f"{{{token}}}" for token in desconhecidos)
        aceitos = ", ".join(f"{{{token}}}" for token in sorted(TOKENS_VALIDOS))
        return f"Token desconhecido: {citados}. Os disponíveis são {aceitos}."

    literal = _TOKEN.sub("", padrao)
    proibidos = sorted({caractere for caractere in literal if caractere in CARACTERES_PROIBIDOS})
    if proibidos:
        return f"O nome do arquivo não pode conter {' '.join(proibidos)}."

    # Recusar o ponto é o que impede `{nome}.txt` de virar `B0001.txt.txt`. O
    # usuário não escolhe a extensão, então escrevê-la é sempre engano.
    if "." in literal:
        return f"Não escreva a extensão: {EXTENSAO_EVENTLIST} é acrescentada automaticamente."

    if not expandir_padrao(padrao, _ENTRADA_SONDA, _PARTICIPANTE_SONDA).removesuffix(
        EXTENSAO_EVENTLIST
    ):
        return "O nome dos novos arquivos não pode ficar em branco."

    return None
