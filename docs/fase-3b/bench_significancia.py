#!/usr/bin/env python
"""Fase 3B / Passo 3 — a escolha da configuração precisa da escala do ruído.

Oito configurações medidas em 20 perguntas, e escolher o máximo sem estimar a
incerteza é precisamente o erro que este projecto tem evitado: a Fase 2 rejeitou
+0,004 **por ser ruído a n=20**, e não por ser pequeno.

Mede, por pergunta, o Δ de nDCG@5 contra o denso, e para cada comparação:

- média e **erro padrão** do Δ emparelhado;
- **teste de sinais** (quantas perguntas melhoram, quantas pioram) — não assume
  normalidade, que com n=20 e uma métrica limitada a [0,1] não é de confiar;
- intervalo de confiança a 95% por **bootstrap** emparelhado, que é o que
  responde à pergunta «este Δ sobreviveria a outras 20 perguntas?».

Também compara as duas candidatas entre si: se o extra do n=20/trunc80 sobre o
n=8/trunc120 não se distingue de zero, escolhe-se a mais barata.
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.avaliacao import apt_em, ndcg
from src.corpus.build import load
from src.corpus.models import Voice
from src.retrieval.encoder import Encoder
from src.retrieval.index import Index
from src.retrieval.rerank import BGE_M3, Reranker
from bench_pool_fechado import PROFUNDIDADE, K, gabarito_fechado

#: As candidatas que ficaram dentro do portão de 6 s, mais a melhor de todas
#: como referência do que se perde por respeitar o portão.
CANDIDATAS = [
    ("n=8 trunc120", 8, 120),
    ("n=12 trunc120", 12, 120),
    ("n=20 trunc80", 20, 80),
    ("n=20 trunc120", 20, 120),
]
B = 10000
SEMENTE = 3


def bootstrap_ic(d: np.ndarray, b: int = B) -> tuple[float, float]:
    rng = np.random.default_rng(SEMENTE)
    ix = rng.integers(0, len(d), size=(b, len(d)))
    medias = d[ix].mean(axis=1)
    return float(np.percentile(medias, 2.5)), float(np.percentile(medias, 97.5))


def sinais(d: np.ndarray) -> tuple[int, int, int]:
    return int((d > 1e-9).sum()), int((d < -1e-9).sum()), int((abs(d) <= 1e-9).sum())


def resumo(nome: str, d: np.ndarray) -> dict:
    lo, hi = bootstrap_ic(d)
    mais, menos, iguais = sinais(d)
    ep = st.stdev(d.tolist()) / len(d) ** 0.5 if len(d) > 1 else 0.0
    distingue = lo > 0 or hi < 0
    print(f"{nome:34s} Δ={d.mean():+.3f} ± {ep:.3f}  "
          f"IC95% [{lo:+.3f}, {hi:+.3f}]  "
          f"sinais +{mais}/−{menos}/={iguais}  "
          f"{'DISTINGUE-SE de 0' if distingue else 'não se distingue de 0'}")
    return {"delta_medio": round(float(d.mean()), 4), "erro_padrao": round(ep, 4),
            "ic95": [round(lo, 4), round(hi, 4)],
            "sinais": {"melhora": mais, "piora": menos, "igual": iguais},
            "distingue_de_zero": bool(distingue)}


def main() -> None:
    meta, chunks = load()
    gab, n_julg = gabarito_fechado(meta)
    perguntas = [p for p in json.load(open("docs/fase-1/08-perguntas.json",
                                           encoding="utf-8"))["perguntas"]
                 if gab.tem(p["id"])]
    enc = Encoder()
    idx = Index.load(chunks, enc, meta["assinatura"])
    if idx is None:
        sys.exit("índice recusado")

    recuperado = {}
    for p in perguntas:
        qv = enc.encode_queries([p["q"]])[0]
        recuperado[p["id"]] = [c for c, _ in idx.search(
            qv, top_k=PROFUNDIDADE, voz=Voice(p["voz"]))]

    denso = np.array([ndcg(recuperado[p["id"]], p["id"], gab, K)
                      for p in perguntas])
    print(f"gabarito fechado: {n_julg} julgamentos · n={len(perguntas)} perguntas")
    print(f"denso: nDCG@5 = {denso.mean():.3f}\n")

    por_config: dict[str, np.ndarray] = {}
    saida: dict = {"n": len(perguntas), "denso": round(float(denso.mean()), 4),
                   "contra_denso": {}, "entre_candidatas": {}}

    print("=== cada configuração contra o denso ===")
    for etiqueta, n_cand, trunc in CANDIDATAS:
        rr = Reranker(BGE_M3, truncar_tokens=trunc)
        rr.rerank("aquecimento", recuperado[perguntas[0]["id"]][:2])
        vals = []
        for p in perguntas:
            res = [c for c, _ in rr.rerank(p["q"],
                                           recuperado[p["id"]][:n_cand])]
            vals.append(ndcg(res, p["id"], gab, K))
        por_config[etiqueta] = np.array(vals)
        saida["contra_denso"][etiqueta] = resumo(etiqueta,
                                                 por_config[etiqueta] - denso)
        del rr

    print("\n=== as candidatas entre si (emparelhado) ===")
    pares = [("n=20 trunc80", "n=8 trunc120"),
             ("n=20 trunc80", "n=12 trunc120"),
             ("n=20 trunc120", "n=20 trunc80")]
    for a, b in pares:
        saida["entre_candidatas"][f"{a} − {b}"] = resumo(
            f"{a} − {b}", por_config[a] - por_config[b])

    with open("docs/fase-3b/04-significancia.json", "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=1)
    print("\nescrito: docs/fase-3b/04-significancia.json")


if __name__ == "__main__":
    main()
