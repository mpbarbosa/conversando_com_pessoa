"""Fusão de listas por Reciprocal Rank Fusion.

Cormack, Clarke & Buettcher, *Reciprocal Rank Fusion outperforms Condorcet and
Individual Rank Learning Methods*, SIGIR 2009.

    score(d) = Σᵢ 1 / (k + rankᵢ(d))

Combina rankings **sem normalizar pontuações**, que é o ponto: o cosseno do e5
anda em 0,80–0,86 e o BM25 em 5–11. Não são comparáveis em escala, e qualquer
normalização seria uma invenção.

## Por que há margem aqui

Medido no Passo 8 da Fase 1: a sobreposição entre o top-5 denso e o top-5 BM25
é de **mediana 1/5**, e **zero em 9 das 40 perguntas**. Duas listas que
concordam tão pouco são o caso em que o RRF costuma dar mais.

## k = 60

O valor do artigo original, com uma década de validação. **Mantido sem o
afinar**: o conjunto dourado tem 20 perguntas julgadas, demasiado pouco para
ajustar um parâmetro sem sobreajustar.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Callable, Sequence

from ..corpus.models import Chunk

K = 60


def rrf(listas: Sequence[Sequence[Chunk]], k: int = K,
        pesos: Sequence[float] | None = None,
        chave: Callable[[Chunk], str] | None = None) -> list[tuple[Chunk, float]]:
    """Funde rankings. A chave por omissão é o id do poema.

    Desduplicar por **poema** e não por chunk é deliberado: dois chunks do mesmo
    poema são a mesma resposta, e contá-los duas vezes dar-lhes-ia o dobro do
    peso na fusão.
    """
    if pesos is None:
        pesos = [1.0] * len(listas)
    if len(pesos) != len(listas):
        raise ValueError(f"{len(pesos)} pesos para {len(listas)} listas")
    id_de = chave or (lambda c: c.poem_id)

    pontos: dict[str, float] = defaultdict(float)
    primeiro: dict[str, Chunk] = {}
    for lista, peso in zip(listas, pesos):
        vistos: set[str] = set()
        posicao = 0
        for c in lista:
            cid = id_de(c)
            if cid in vistos:
                continue
            vistos.add(cid)
            posicao += 1
            pontos[cid] += peso / (k + posicao)
            primeiro.setdefault(cid, c)

    ordenados = sorted(pontos.items(), key=lambda x: (-x[1], x[0]))
    return [(primeiro[cid], p) for cid, p in ordenados]
