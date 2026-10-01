"""`Poem` -> `[Chunk]`.

A estrofe é a unidade natural: medido com o tokenizador real do e5, 95,3% dos
poemas cabem inteiros em 480 tokens, e das 6619 estrofes do corpus apenas 12
excedem esse limite sozinhas.

Nunca se parte um verso. Parte-se uma estrofe só quando ela sozinha excede o
limite — e nesse caso por grupos de versos contíguos.

## O limite de 480

Derivado, não escolhido: o e5 tem `model_max_length=512`, e o texto indexado
leva prefixos que consomem orçamento:

    512 - 2 ("passage: ") - 27 (pior caso de "Autor — Título") - 2 (especiais)
        = 481  ->  480

## Dois textos por chunk

`text` é o que vai no **prompt**: verso puro, sem metadados, porque o gerador
deve ver poesia e não fichas bibliográficas.

`indexed_text` é o que vai no **índice**: leva «Autor — Título» à cabeça, que dá
ao encoder contexto que o verso sozinho não carrega. São campos distintos do
mesmo objecto, de propósito.
"""
from __future__ import annotations

from typing import Callable

from .models import Chunk, Poem

LIMITE_TOKENS = 480

#: Sobreposição entre janelas consecutivas, em unidades (estrofes).
SOBREPOSICAO = 1


def _partir_estrofe(estrofe: str, n_tokens: Callable[[str], int],
                    limite: int) -> list[str]:
    """Parte uma estrofe grande em grupos de versos contíguos.

    Só chamado para as 12 estrofes do corpus que sozinhas excedem o limite —
    a maior tem 2147 tokens (a abertura da *Ode Marítima*).
    """
    versos = [v for v in estrofe.split("\n") if v.strip()]
    grupos: list[list[str]] = []
    actual: list[str] = []
    for verso in versos:
        candidato = actual + [verso]
        if actual and n_tokens("\n".join(candidato)) > limite:
            grupos.append(actual)
            actual = [verso]
        else:
            actual = candidato
    if actual:
        grupos.append(actual)
    return ["\n".join(g) for g in grupos]


def _unidades(poema: Poem, n_tokens: Callable[[str], int],
              limite: int) -> list[str]:
    """Estrofes, já normalizadas para que nenhuma exceda o limite."""
    saida: list[str] = []
    for estrofe in poema.stanzas:
        if n_tokens(estrofe) <= limite:
            saida.append(estrofe)
        else:
            saida.extend(_partir_estrofe(estrofe, n_tokens, limite))
    return saida


def _indexar(poema: Poem, texto: str) -> str:
    return f"{poema.author} — {poema.title}\n\n{texto}"


def chunk_poem(poema: Poem, n_tokens: Callable[[str], int],
               limite: int = LIMITE_TOKENS) -> list[Chunk]:
    def monta(ix: int, texto: str) -> Chunk:
        return Chunk(
            poem_id=poema.id, chunk_ix=ix, text=texto,
            indexed_text=_indexar(poema, texto),
            voice=poema.voice, language=poema.language,
            n_words=len(texto.split()),
        )

    corpo = poema.body.strip()
    if not corpo:
        return []
    if n_tokens(corpo) <= limite:
        return [monta(0, corpo)]

    unidades = _unidades(poema, n_tokens, limite)
    chunks: list[Chunk] = []
    i = 0
    while i < len(unidades):
        janela = [unidades[i]]
        j = i + 1
        while j < len(unidades):
            candidato = janela + [unidades[j]]
            if n_tokens("\n\n".join(candidato)) > limite:
                break
            janela = candidato
            j += 1
        chunks.append(monta(len(chunks), "\n\n".join(janela)))
        if j >= len(unidades):
            break
        # Sobreposição de uma unidade, garantindo progresso: quando uma só
        # unidade enche a janela, avança sem sobrepor (senão: ciclo infinito).
        i = max(i + 1, j - SOBREPOSICAO)
    return chunks


def chunk_corpus(poemas: list[Poem], n_tokens: Callable[[str], int],
                 limite: int = LIMITE_TOKENS,
                 incluir_duplicados: bool = False) -> list[Chunk]:
    """Chunks de todo o corpus.

    Por omissão exclui os duplicados marcados no Passo 2 — indexar um poema e
    a sua variante devolve o mesmo poema duas vezes nos resultados.
    """
    saida: list[Chunk] = []
    for p in poemas:
        if p.is_duplicate and not incluir_duplicados:
            continue
        saida.extend(chunk_poem(p, n_tokens, limite))
    return saida
