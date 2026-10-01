"""Índice denso em `numpy`, com manifesto.

## Por que não FAISS

2290 chunks × 768 dims = **7,0 MB**. Uma busca é um produto matriz-vector de
1,8 M operações: microssegundos. O `IndexFlatIP` do FAISS faz exactamente o
mesmo cálculo — força bruta — com uma dependência a mais. IVF e HNSW existem
para milhões de vectores e aqui só trariam perda de recall.

## Por que o manifesto

Os ids do índice são **posicionais**. O índice só é reutilizável acompanhado da
ordem dos documentos a partir da qual foi construído — sem ela, o id *i* não
aponta para nada. Era o defeito do `retriever.py` original: gravava o índice,
nunca o lia, e se o lesse a ordem arbitrária do `os.listdir()` teria dado
correspondência errada em silêncio.

O manifesto recusa o índice quando o encoder muda, quando a assinatura do corpus
muda, ou quando as contagens não batem. **Recusa é melhor que reconstruir
silenciosamente**, porque um índice velho carregado por engano não dá erro: dá
respostas erradas.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

import numpy as np

from ..corpus.models import Chunk, Lang, Voice
from .encoder import Encoder

CAMINHO = "data/index"


@dataclass(frozen=True)
class Manifesto:
    encoder: str
    dim: int
    assinatura: str          # do corpus.jsonl
    n_chunks: int
    chunk_ids: list[list]    # [[poem_id, chunk_ix], ...] na ordem do índice


class Index:
    def __init__(self, vectores: np.ndarray, chunks: list[Chunk],
                 manifesto: Manifesto):
        if len(vectores) != len(chunks):
            raise ValueError(f"{len(vectores)} vectores para {len(chunks)} chunks")
        self.vectores = vectores
        self.chunks = chunks
        self.manifesto = manifesto

    # --- construção e persistência ----------------------------------------

    @classmethod
    def build(cls, chunks: list[Chunk], encoder: Encoder, assinatura: str,
              progresso: bool = True) -> "Index":
        vectores = encoder.encode_passages(
            [c.indexed_text for c in chunks], progresso=progresso)
        manifesto = Manifesto(
            encoder=encoder.nome, dim=encoder.dim, assinatura=assinatura,
            n_chunks=len(chunks),
            chunk_ids=[[c.poem_id, c.chunk_ix] for c in chunks],
        )
        return cls(vectores, chunks, manifesto)

    def save(self, caminho: str = CAMINHO) -> None:
        os.makedirs(os.path.dirname(caminho) or ".", exist_ok=True)
        np.save(f"{caminho}.npy", self.vectores)
        with open(f"{caminho}.manifest.json", "w", encoding="utf-8") as f:
            json.dump(self.manifesto.__dict__, f, ensure_ascii=False, indent=1)

    @classmethod
    def load(cls, chunks: list[Chunk], encoder: Encoder, assinatura: str,
             caminho: str = CAMINHO) -> "Index | None":
        """Carrega o índice, ou devolve None se não for de confiança."""
        npy, man = f"{caminho}.npy", f"{caminho}.manifest.json"
        if not (os.path.exists(npy) and os.path.exists(man)):
            return None
        try:
            with open(man, encoding="utf-8") as f:
                m = Manifesto(**json.load(f))
        except (OSError, json.JSONDecodeError, TypeError):
            return None

        if m.encoder != encoder.nome:
            return None
        if m.assinatura != assinatura:
            return None
        if m.n_chunks != len(chunks):
            return None
        # A ordem é o que dá sentido aos ids posicionais.
        if m.chunk_ids != [[c.poem_id, c.chunk_ix] for c in chunks]:
            return None

        vectores = np.load(npy)
        if vectores.shape != (len(chunks), m.dim):
            return None
        return cls(vectores, chunks, m)

    @classmethod
    def load_or_build(cls, chunks: list[Chunk], encoder: Encoder,
                      assinatura: str, caminho: str = CAMINHO,
                      progresso: bool = True) -> "Index":
        existente = cls.load(chunks, encoder, assinatura, caminho)
        if existente is not None:
            return existente
        novo = cls.build(chunks, encoder, assinatura, progresso)
        novo.save(caminho)
        return novo

    # --- busca -------------------------------------------------------------

    def mascara(self, voz: Voice | None = None,
                idioma: Lang | None = Lang.PT) -> np.ndarray:
        """Máscara booleana sobre os chunks.

        `idioma=PT` por omissão **porque a resposta é em português**, e
        fundamentá-la em poemas ingleses seria incoerente. Não é juízo sobre o
        corpus: os 152 poemas em inglês são obra de Pessoa — os *35 Sonnets*,
        as *Inscriptions* — e Alexander Search é um heterónimo que escrevia em
        inglês, com 50 poemas aqui.

        `idioma=None` devolve tudo. Servir o Search exigiria persona inglesa e
        guardas conscientes da língua, que hoje são todas específicas do
        português (enclíticas, brasileirismos, fracção de stopwords).
        """
        m = np.ones(len(self.chunks), dtype=bool)
        if voz is not None:
            m &= np.fromiter((c.voice is voz for c in self.chunks), bool, len(self.chunks))
        if idioma is not None:
            m &= np.fromiter((c.language is idioma for c in self.chunks), bool, len(self.chunks))
        return m

    def search(self, vector_consulta: np.ndarray, top_k: int = 10,
               voz: Voice | None = None,
               idioma: Lang | None = Lang.PT) -> list[tuple[Chunk, float]]:
        q = np.asarray(vector_consulta, dtype="float32").reshape(-1)
        if q.shape[0] != self.vectores.shape[1]:
            raise ValueError(f"consulta de dim {q.shape[0]}, índice de dim "
                             f"{self.vectores.shape[1]}")
        pontos = self.vectores @ q
        m = self.mascara(voz, idioma)
        if not m.any():
            return []
        pontos = np.where(m, pontos, -np.inf)
        k = min(top_k, int(m.sum()))
        melhores = np.argpartition(-pontos, k - 1)[:k]
        melhores = melhores[np.argsort(-pontos[melhores])]
        return [(self.chunks[i], float(pontos[i])) for i in melhores]
