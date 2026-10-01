#!/usr/bin/env python
"""Passo A1 da Fase 4 — roteador de voz, três variantes, custo zero de máquina.

Tudo o que isto precisa já está no disco: `index.npy` tem os 2290 vectores,
cada chunk sabe a sua voz, e as 40 perguntas de `08-perguntas.json` estão
rotuladas 10 por voz.

Três variantes, porque todas saem do mesmo produto matriz-vector e medir as três
custa o mesmo que medir uma:

- **centróide**: média normalizada dos vectores de cada voz. Insensível ao
  tamanho da classe por construção.
- **vizinho**: a voz do chunk mais próximo. Sensível ao tamanho da classe — com
  1250 chunks do ortónimo contra 127 do Caeiro, há mais bilhetes de lotaria.
- **voto@k**: entre os k chunks mais próximos de todo o corpus, a voz mais
  frequente, ponderada pela similaridade.
"""
from __future__ import annotations

import collections
import json
import sys

import numpy as np

sys.path.insert(0, ".")

from src.corpus.build import load
from src.corpus.models import Lang, Voice
from src.retrieval.encoder import Encoder
from src.retrieval.index import Index

PERGUNTAS = "docs/fase-1/08-perguntas.json"
VOZES = (Voice.CAEIRO, Voice.CAMPOS, Voice.REIS, Voice.ORTONIMO)


def centroides(idx: Index) -> tuple[np.ndarray, tuple[Voice, ...]]:
    """Média normalizada por voz, só sobre chunks em português."""
    cs = []
    for v in VOZES:
        m = np.fromiter((c.voice is v and c.language is Lang.PT
                         for c in idx.chunks), bool, len(idx.chunks))
        c = idx.vectores[m].mean(axis=0)
        cs.append(c / np.linalg.norm(c))
    return np.vstack(cs), VOZES


def _mascara_pt(idx: Index) -> np.ndarray:
    return np.fromiter((c.language is Lang.PT for c in idx.chunks),
                       bool, len(idx.chunks))


def rotear_centroide(qv, cent, vozes, **_):
    s = cent @ qv
    o = np.argsort(-s)
    return vozes[o[0]], float(s[o[0]] - s[o[1]])


def rotear_vizinho(qv, idx, mpt, **_):
    s = np.where(mpt, idx.vectores @ qv, -np.inf)
    o = np.argsort(-s)
    vencedora = idx.chunks[o[0]].voice
    # margem: até onde é preciso descer para encontrar outra voz
    for i in o[1:]:
        if idx.chunks[i].voice is not vencedora:
            return vencedora, float(s[o[0]] - s[i])
    return vencedora, float("inf")


def rotear_voto(qv, idx, mpt, k=20, **_):
    s = np.where(mpt, idx.vectores @ qv, -np.inf)
    top = np.argsort(-s)[:k]
    pontos: dict[Voice, float] = collections.defaultdict(float)
    for i in top:
        pontos[idx.chunks[i].voice] += float(s[i])
    ordenado = sorted(pontos.items(), key=lambda kv: -kv[1])
    margem = (ordenado[0][1] - ordenado[1][1]) if len(ordenado) > 1 else float("inf")
    return ordenado[0][0], margem


VARIANTES = {
    "centroide": rotear_centroide,
    "vizinho": rotear_vizinho,
    "voto@20": rotear_voto,
}


def confusao(pares: list[tuple[Voice, Voice]]) -> str:
    """Linhas = esperada, colunas = prevista."""
    cab = "esperada \\ prevista".ljust(20) + "".join(v.value.ljust(11) for v in VOZES)
    linhas = [cab]
    for esperada in VOZES:
        cel = []
        for prevista in VOZES:
            n = sum(1 for e, p in pares if e is esperada and p is prevista)
            cel.append((str(n) if n else "·").ljust(11))
        linhas.append(esperada.value.ljust(20) + "".join(cel))
    return "\n".join(linhas)


def main() -> None:
    meta, chunks = load()
    enc = Encoder()
    idx = Index.load(chunks, enc, meta["assinatura"])
    if idx is None:
        sys.exit("índice recusado pelo manifesto — reconstruir antes de medir")

    perguntas = json.load(open(PERGUNTAS, encoding="utf-8"))["perguntas"]
    qvs = enc.encode_queries([p["q"] for p in perguntas])
    cent, vozes = centroides(idx)
    mpt = _mascara_pt(idx)

    resultados = {}
    for nome, rotear in VARIANTES.items():
        pares, margens, erros = [], [], []
        for p, qv in zip(perguntas, qvs):
            esperada = Voice(p["voz"])
            prevista, margem = rotear(qv, cent=cent, vozes=vozes, idx=idx, mpt=mpt)
            pares.append((esperada, prevista))
            margens.append(margem)
            if prevista is not esperada:
                erros.append({"id": p["id"], "q": p["q"],
                              "esperada": esperada.value,
                              "prevista": prevista.value,
                              "margem": round(margem, 4)})

        certos = sum(1 for e, p in pares if e is p)
        por_voz = {v.value: round(
            sum(1 for e, p in pares if e is v and p is v)
            / sum(1 for e, _ in pares if e is v), 2) for v in VOZES}
        finitas = [m for m in margens if np.isfinite(m)]
        resultados[nome] = {
            "exactidao": round(certos / len(pares), 3),
            "certos": certos, "n": len(pares),
            "por_voz": por_voz,
            "margem_mediana": round(float(np.median(finitas)), 4) if finitas else None,
            "erros": erros,
        }

        print(f"\n=== {nome} ===")
        print(f"exactidão: {certos}/{len(pares)} = {certos/len(pares):.0%}")
        print(f"por voz: {por_voz}")
        if finitas:
            certas_m = [m for (e, p), m in zip(pares, margens)
                        if e is p and np.isfinite(m)]
            erradas_m = [m for (e, p), m in zip(pares, margens)
                         if e is not p and np.isfinite(m)]
            print(f"margem mediana: {np.median(finitas):.4f}"
                  f"  (certas {np.median(certas_m):.4f}"
                  f" · erradas {np.median(erradas_m):.4f})"
                  if erradas_m else
                  f"margem mediana: {np.median(finitas):.4f} (nenhum erro)")
        print(confusao(pares))
        for e in erros:
            print(f"  {e['id']} {e['esperada']} -> {e['prevista']}"
                  f" (margem {e['margem']:.4f}): {e['q'][:60]}")

    with open("docs/fase-4/01-roteador.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=1)
    print("\nescrito: docs/fase-4/01-roteador.json")


if __name__ == "__main__":
    main()
