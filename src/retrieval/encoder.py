"""Encoder e5, com os prefixos impostos pela API.

O e5 **exige** `query: ` nas consultas e `passage: ` nos documentos. Sem eles
funciona e devolve resultados piores, sem avisar — é a falha silenciosa clássica
deste modelo.

A defesa aqui não é uma asserção: são **dois métodos distintos** que aplicam o
prefixo certo. Não há caminho para encodar texto sem prefixo, logo não há como
esquecer.
"""
from __future__ import annotations

import numpy as np

from ..tokens import ENCODER

#: Medido na Fase 0 (correcção A.3): lote 8 é 1,6x mais rápido que lote 64
#: nesta CPU, o inverso do esperado. Corpus em 3,2 min.
BATCH_SIZE = 8


class Encoder:
    def __init__(self, nome: str = ENCODER, batch_size: int = BATCH_SIZE):
        from sentence_transformers import SentenceTransformer
        self._modelo = SentenceTransformer(nome)
        self.nome = nome
        self.batch_size = batch_size

    @property
    def dim(self) -> int:
        # `get_sentence_embedding_dimension` foi renomeado em
        # sentence-transformers 6.x; manter o antigo como recurso.
        obter = getattr(self._modelo, "get_embedding_dimension", None)
        if obter is None:
            obter = self._modelo.get_sentence_embedding_dimension
        return obter()

    def _encode(self, textos: list[str], prefixo: str,
                progresso: bool = False) -> np.ndarray:
        emb = self._modelo.encode(
            [prefixo + t for t in textos],
            convert_to_numpy=True, batch_size=self.batch_size,
            show_progress_bar=progresso,
        )
        emb = np.asarray(emb, dtype="float32")
        # Normalizar: a busca é por produto interno, que sobre vectores
        # normalizados é cosseno — a métrica para que estes embeddings foram
        # treinados. L2 cru não é.
        normas = np.linalg.norm(emb, axis=1, keepdims=True)
        normas[normas == 0] = 1.0
        return emb / normas

    def encode_passages(self, textos: list[str], progresso: bool = False) -> np.ndarray:
        return self._encode(textos, "passage: ", progresso)

    def encode_queries(self, textos: list[str]) -> np.ndarray:
        return self._encode(textos, "query: ")
