"""Recuperação: denso, lexical, ou a fusão dos dois."""
from __future__ import annotations

from typing import Sequence

from ..corpus.models import Chunk, Lang, Voice
from .encoder import Encoder
from .fusion import K, rrf
from .index import Index
from .lexical import IndiceLexical


class BuscaHibrida:
    """Denso + BM25, fundidos por RRF.

    O `top_k` interno é maior que o devolvido de propósito: a fusão só pode
    reordenar o que lhe dão, e listas curtas desperdiçam o mecanismo.
    """

    def __init__(self, index: Index, encoder: Encoder, lexical: IndiceLexical,
                 k_rrf: int = K, profundidade: int = 20,
                 pesos: Sequence[float] | None = None):
        self.index = index
        self.encoder = encoder
        self.lexical = lexical
        self.k_rrf = k_rrf
        self.profundidade = profundidade
        self.pesos = pesos

    def search(self, consulta: str, top_k: int = 10,
               voz: Voice | None = None,
               idioma: Lang | None = Lang.PT) -> list[tuple[Chunk, float]]:
        qv = self.encoder.encode_queries([consulta])[0]
        densos = [c for c, _ in self.index.search(
            qv, top_k=self.profundidade, voz=voz, idioma=idioma)]
        lexicais = [c for c, _ in self.lexical.search(
            consulta, top_k=self.profundidade, voz=voz, idioma=idioma)]
        return rrf([densos, lexicais], k=self.k_rrf, pesos=self.pesos)[:top_k]
