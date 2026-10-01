"""Pipeline de ingestão -> `data/corpus.jsonl`.

`corpus.jsonl` é a **fronteira do sistema**: tudo a jusante consome-o, nunca os
`.txt`. Isso torna a ingestão testável isoladamente e evita repetir a
deduplicação (35 s) a cada arranque.

Idempotente: correr duas vezes dá o mesmo ficheiro.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict

from ..tokens import ENCODER, contador
from .chunk import LIMITE_TOKENS, chunk_corpus
from .dedupe import detectar
from .models import Chunk, Lang, Voice
from .parse import parse_corpus
from .dedupe import marcar

CAMINHO = "data/corpus.jsonl"


def _assinatura(chunks: list[Chunk], encoder: str, limite: int) -> str:
    """Impressão digital do conteúdo indexável.

    Usa o **texto dos chunks**, não nomes e tamanhos de ficheiro como fazia o
    `retriever.py` antigo. A diferença importa: uma alteração ao parsing, à
    deduplicação ou ao chunking muda os chunks sem mudar um único `.txt`, e a
    versão antiga não a detectaria.
    """
    h = hashlib.sha256()
    h.update(f"{encoder}|{limite}".encode())
    for c in chunks:
        h.update(f"{c.poem_id}|{c.chunk_ix}|{c.indexed_text}".encode("utf-8"))
    return h.hexdigest()


def build(data_dir: str = "data/pessoa_poems", caminho: str = CAMINHO,
          encoder: str = ENCODER, limite: int = LIMITE_TOKENS,
          verboso: bool = True) -> dict:
    def log(*a):
        if verboso:
            print(*a, flush=True)

    log("1/4 parsing...")
    poemas = parse_corpus(data_dir)
    log(f"     {len(poemas)} poemas")

    log("2/4 deduplicação...")
    relatorio = detectar(poemas)
    poemas = marcar(poemas, relatorio)
    log(f"     {len(relatorio.grupos_exactos)} grupos exactos, "
        f"{len(relatorio.grupos_variantes)} grupos de variantes, "
        f"{relatorio.n_marcados} poemas marcados")
    log(f"     {len(relatorio.grupos_incipit)} grupos de incipit partilhado (não colapsados)")

    log("3/4 chunking...")
    n_tok = contador(encoder)
    chunks = chunk_corpus(poemas, n_tok, limite)
    log(f"     {len(chunks)} chunks de {sum(1 for p in poemas if not p.is_duplicate)} poemas")

    log("4/4 escrita...")
    assinatura = _assinatura(chunks, encoder, limite)
    os.makedirs(os.path.dirname(caminho) or ".", exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "_meta": {
                "encoder": encoder, "limite_tokens": limite,
                "assinatura": assinatura,
                "n_poemas": len(poemas),
                "n_poemas_indexados": sum(1 for p in poemas if not p.is_duplicate),
                "n_chunks": len(chunks),
                "grupos_exactos": relatorio.grupos_exactos,
                "grupos_variantes": relatorio.grupos_variantes,
                "grupos_incipit": relatorio.grupos_incipit,
                "representantes": relatorio.representantes,
            }
        }, ensure_ascii=False) + "\n")
        for c in chunks:
            d = asdict(c)
            d["voice"] = c.voice.value
            d["language"] = c.language.value
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    log(f"     {caminho}  ({os.path.getsize(caminho)/1e6:.1f} MB)")
    return {"assinatura": assinatura, "n_chunks": len(chunks)}


def load(caminho: str = CAMINHO) -> tuple[dict, list[Chunk]]:
    """Lê `corpus.jsonl`. A ordem das linhas **é** a ordem dos ids do índice."""
    with open(caminho, encoding="utf-8") as f:
        meta = json.loads(f.readline())["_meta"]
        chunks = []
        for linha in f:
            d = json.loads(linha)
            chunks.append(Chunk(
                poem_id=d["poem_id"], chunk_ix=d["chunk_ix"],
                text=d["text"], indexed_text=d["indexed_text"],
                voice=Voice(d["voice"]), language=Lang(d["language"]),
                n_words=d["n_words"],
            ))
    return meta, chunks
