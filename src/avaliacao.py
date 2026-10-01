"""Métricas de recuperação, com gabarito de relevância graduada.

## Por que não recall com gabarito único

A §6.1 do plano especificava «1–3 poemas esperados» por pergunta. A Fase 0
mostrou que isso é inválido neste corpus: Pessoa escreveu dezenas de quadras
sobre cada tema, e para «ofereço-lhe o meu afecto e ela nem repara» o encoder
devolveu «Entreguei-te o coração, / E que tratos tu lhe deste!» — casamento
igualmente bom, contado como erro.

Aqui a relevância é **graduada**: 2 = responde bem, 1 = aproveitável, 0 = não
serve. A métrica principal é nDCG@5, que usa a graduação.

## Consciência de grupos

A deduplicação (Passo 2) marcou 21 poemas como duplicados de outro, e o
`poem_1000` — gabarito de uma pergunta do conjunto de fumo — passou a
não-representante de `poem_629`. Uma resposta conta se estiver **no mesmo grupo**
que um id do gabarito, nunca por igualdade de id.

## O aperto da nota 1

Na Fase 0 fui permissivo e o `util@3` saturou: até o controlo inglês fez 9/10,
porque o corpus é tematicamente tão uniforme que «adjacente» é quase sempre
verdade. Aqui `1` significa «serviria se nada melhor houvesse», não «também é
sobre melancolia».
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Sequence

from .corpus.models import Chunk


@dataclass(frozen=True)
class Gabarito:
    """Julgamentos por pergunta: id do poema -> nota 0/1/2."""
    notas: Mapping[str, Mapping[str, int]]        # pergunta_id -> poema_id -> nota
    representantes: Mapping[str, str]             # poema_id -> representante

    def nota(self, pergunta_id: str, poema_id: str) -> int:
        """Nota de um poema, resolvendo o grupo de deduplicação."""
        julgados = self.notas.get(pergunta_id, {})
        if poema_id in julgados:
            return julgados[poema_id]
        rep = self.representantes.get(poema_id, poema_id)
        if rep in julgados:
            return julgados[rep]
        # um dos julgados pode ser outro membro do mesmo grupo
        for pid, n in julgados.items():
            if self.representantes.get(pid, pid) == rep:
                return n
        return 0

    def tem(self, pergunta_id: str) -> bool:
        return bool(self.notas.get(pergunta_id))

    @property
    def perguntas_julgadas(self) -> tuple[str, ...]:
        return tuple(q for q, v in self.notas.items() if v)


def _dcg(notas: Sequence[int]) -> float:
    return sum((2 ** n - 1) / math.log2(i + 2) for i, n in enumerate(notas))


def ndcg(resultados: Sequence[Chunk], pergunta_id: str, gabarito: Gabarito,
         k: int = 5) -> float:
    """nDCG@k. Desduplica por poema: dois chunks do mesmo poema contam uma vez."""
    vistos: set[str] = set()
    obtidas: list[int] = []
    for c in resultados:
        rep = gabarito.representantes.get(c.poem_id, c.poem_id)
        if rep in vistos:
            continue
        vistos.add(rep)
        obtidas.append(gabarito.nota(pergunta_id, c.poem_id))
        if len(obtidas) == k:
            break

    ideais = sorted(gabarito.notas.get(pergunta_id, {}).values(), reverse=True)[:k]
    melhor = _dcg(ideais)
    return _dcg(obtidas) / melhor if melhor else 0.0


def apt_em(resultados: Sequence[Chunk], pergunta_id: str, gabarito: Gabarito,
           k: int = 3) -> bool:
    """Há pelo menos um poema de nota 2 no top-k?"""
    vistos: set[str] = set()
    for c in resultados:
        rep = gabarito.representantes.get(c.poem_id, c.poem_id)
        if rep in vistos:
            continue
        vistos.add(rep)
        if gabarito.nota(pergunta_id, c.poem_id) == 2:
            return True
        if len(vistos) == k:
            break
    return False


@dataclass(frozen=True)
class Resultado:
    n_perguntas: int
    ndcg5: float
    apt3: float

    def __str__(self) -> str:
        return (f"n={self.n_perguntas}  nDCG@5={self.ndcg5:.3f}  "
                f"apt@3={self.apt3:.0%}")


def avaliar(recuperar, perguntas: Sequence[dict], gabarito: Gabarito,
            k: int = 5) -> Resultado:
    """`recuperar(pergunta, voz) -> [Chunk]`, só nas perguntas julgadas."""
    ndcgs, apts = [], []
    for p in perguntas:
        if not gabarito.tem(p["id"]):
            continue
        res = recuperar(p["q"], p["voz"])
        ndcgs.append(ndcg(res, p["id"], gabarito, k))
        apts.append(apt_em(res, p["id"], gabarito, 3))
    n = len(ndcgs)
    return Resultado(
        n_perguntas=n,
        ndcg5=sum(ndcgs) / n if n else 0.0,
        apt3=sum(apts) / n if n else 0.0,
    )
