"""Recuperação lexical (BM25) sobre os chunks.

Escrita no Passo 8 da Fase 1, antes da Fase 2 que a tem como objectivo, por uma
razão metodológica: o conjunto dourado precisa de **pooling imparcial**. Um
gabarito construído só com candidatos do encoder denso ficaria enviesado a favor
dele, e a Fase 2 existe para comparar os dois.

A normalização ortográfica da Fase 2 (§2 de FASE-2.md) **não está aqui**: é
trabalho dessa fase, com tabela construída do corpus e filtrada à mão. Aqui há
só o mínimo — minúsculas, pontuação fora, stopwords.
"""
from __future__ import annotations

import re
from typing import Sequence

from ..corpus.models import Chunk, Lang, Voice

#: Stopwords portuguesas, **revistas à mão**. Deliberadamente ausentes: «não»,
#: «nada», «tudo», «nunca», «sem», «só», «mais» — em Pessoa são palavras-chave,
#: não ruído. «Não sou nada» é a abertura da Tabacaria.
STOPWORDS = frozenset("""
a o as os um uma uns umas de do da dos das em no na nos nas por para com
que se e ou mas como quando onde qual quais é são era eram foi foram ser
estar tem têm tinha havia há ao aos à às pelo pela pelos pelas me te lhe
nos vos lhes meu minha teu tua seu sua este esta esse essa aquele aquela
isto isso aquilo eu tu ele ela nós vós eles elas já também então assim
""".split())

_RE_PONT = re.compile(r"[^\w\s]")
_RE_ESP = re.compile(r"\s+")


def tokenizar(texto: str) -> list[str]:
    t = _RE_ESP.sub(" ", _RE_PONT.sub(" ", texto.lower())).strip()
    return [p for p in t.split() if p not in STOPWORDS and len(p) > 1]


class IndiceLexical:
    def __init__(self, chunks: Sequence[Chunk]):
        from rank_bm25 import BM25Okapi
        self.chunks = list(chunks)
        corpus = [tokenizar(c.text) for c in self.chunks]
        # Chunks que ficam sem termos depois das stopwords quebrariam o BM25.
        self._vazios = {i for i, d in enumerate(corpus) if not d}
        self._bm25 = BM25Okapi([d or ["\x00"] for d in corpus])

    def search(self, consulta: str, top_k: int = 10,
               voz: Voice | None = None,
               idioma: Lang | None = Lang.PT) -> list[tuple[Chunk, float]]:
        termos = tokenizar(consulta)
        if not termos:
            return []
        import numpy as np
        pontos = np.asarray(self._bm25.get_scores(termos), dtype="float32")

        mascara = np.ones(len(self.chunks), dtype=bool)
        for i in self._vazios:
            mascara[i] = False
        if voz is not None:
            mascara &= np.fromiter((c.voice is voz for c in self.chunks),
                                   bool, len(self.chunks))
        if idioma is not None:
            mascara &= np.fromiter((c.language is idioma for c in self.chunks),
                                   bool, len(self.chunks))
        if not mascara.any():
            return []

        pontos = np.where(mascara, pontos, -np.inf)
        k = min(top_k, int(mascara.sum()))
        melhores = np.argpartition(-pontos, k - 1)[:k]
        melhores = melhores[np.argsort(-pontos[melhores])]
        return [(self.chunks[i], float(pontos[i])) for i in melhores
                if pontos[i] > -np.inf]
