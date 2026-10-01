"""Reordenação por cross-encoder.

## O que a Fase 3 Passo 1 mediu

| reranker | params | 3100 tokens | tokens/s |
|---|---|---|---|
| `mmarco-mMiniLMv2-L12-H384-v1` | ~120M | **1,83 s** | 1694 |
| `bge-reranker-base` | 278M | 5,89 s | 526 |
| `bge-reranker-v2-m3` | 568M | **34,59 s** | 90 |

19x entre o mais pequeno e o maior, com 4,7x de diferença em parâmetros: a razão
é a dimensão oculta (384 contra 1024) e o custo das camadas densas escalar com o
quadrado dela.

## A expectativa, calibrada pela Fase 2

A fusão híbrida falhou por um tecto medido: o denso leva 40 documentos de nota 2
no top-5 somado de 20 perguntas, a fusão leva 39 — **trocar respostas boas por
outras respostas boas não melhora o nDCG**, porque há mediana de 3 respostas
certas por pergunta e o top-5 só leva cinco.

O mesmo tecto aplica-se aqui. Reordenar vai mexer em **quais** respostas certas
aparecem, não em **quantas**.
"""
from __future__ import annotations

from typing import Sequence

from ..corpus.models import Chunk

MINILM = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
BGE_BASE = "BAAI/bge-reranker-base"
BGE_M3 = "BAAI/bge-reranker-v2-m3"

PADRAO = MINILM


class Reranker:
    def __init__(self, modelo: str = PADRAO, max_length: int = 512,
                 truncar_tokens: int | None = None):
        from sentence_transformers import CrossEncoder
        self._ce = CrossEncoder(modelo, max_length=max_length)
        self.modelo = modelo
        self.truncar_tokens = truncar_tokens
        self._tok = None

    def _truncar(self, texto: str) -> str:
        if self.truncar_tokens is None:
            return texto
        if self._tok is None:
            from ..tokens import _tokenizador, ENCODER
            self._tok = _tokenizador(ENCODER)
        ids = self._tok(texto, add_special_tokens=False).input_ids
        if len(ids) <= self.truncar_tokens:
            return texto
        return self._tok.decode(ids[:self.truncar_tokens], skip_special_tokens=True)

    def rerank(self, consulta: str, candidatos: Sequence[Chunk],
               top_k: int | None = None) -> list[tuple[Chunk, float]]:
        if not candidatos:
            return []
        pares = [(consulta, self._truncar(c.text)) for c in candidatos]
        pontos = self._ce.predict(pares, show_progress_bar=False)
        ordenados = sorted(zip(candidatos, (float(p) for p in pontos)),
                           key=lambda x: -x[1])
        return ordenados[:top_k] if top_k else ordenados
