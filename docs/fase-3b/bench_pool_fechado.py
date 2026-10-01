#!/usr/bin/env python
"""Fase 3B / Passo 2 — remedir tudo no pool fechado.

O gabarito passou de 291 para **433** julgamentos, e o top-20 do denso das 20
perguntas está agora **completamente** coberto. A consequência que importa:
nenhum documento que um reranker sobre o top-20 promova pode contar 0 por falta
de julgamento. O Δ de cada reranker é calculado sobre um pool que **nenhum deles
ajudou a construir** — é definido pela recuperação densa, que não muda.

Mede: denso, oráculo@20 (o tecto de qualquer reordenação do top-20), e as
configurações que a Fase 3 pôs no quadro.
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.avaliacao import Gabarito, _dcg, apt_em, ndcg
from src.corpus.build import load
from src.corpus.models import Voice
from src.retrieval.encoder import Encoder
from src.retrieval.index import Index
from src.retrieval.rerank import BGE_BASE, BGE_M3, MINILM, Reranker

PROFUNDIDADE = 20
K = 5

#: (etiqueta, modelo, n_candidatos, truncagem). O MiniLM entra como **controlo
#: negativo**: a Fase 3 mediu-o a pôr o poema das árvores em último dada «o que
#: vês numa árvore?», e se o pool fechado o mostrar a ganhar, é o pool que está
#: errado.
CONFIGS = [
    ("bge-m3 n=8 trunc120", BGE_M3, 8, 120),
    ("bge-m3 n=8 trunc256", BGE_M3, 8, 256),
    ("bge-m3 n=20 trunc120", BGE_M3, 20, 120),
    ("bge-base n=20 trunc120", BGE_BASE, 20, 120),
    ("MiniLM n=20 trunc120", MINILM, 20, 120),
    # A corrida de 2026-10-01 pôs o n=20 em 6,57 s, logo **fora** do portão de
    # 6 s do protocolo, com o melhor Δ (+0,127). Estes dois existem para achar
    # a profundidade máxima que ainda cabe no portão.
    ("bge-m3 n=12 trunc120", BGE_M3, 12, 120),
    ("bge-m3 n=16 trunc120", BGE_M3, 16, 120),
    # Truncar mais: se 120 já melhora sobre 256, 80 pode baixar o custo do n=20
    # para dentro do portão.
    ("bge-m3 n=20 trunc80", BGE_M3, 20, 80),
]


def gabarito_fechado(meta) -> tuple[Gabarito, int]:
    """Funde os 291 julgamentos das Fases 1-3 com os 142 da 3B."""
    a = json.load(open("docs/fase-1/08-julgamentos.json", encoding="utf-8"))
    b = json.load(open("docs/fase-3b/02-julgamentos-novos.json", encoding="utf-8"))
    notas: dict[str, dict[str, int]] = {}
    for fonte in (a, b):
        for q, d in fonte.items():
            if q.startswith("_"):
                continue
            notas.setdefault(q, {}).update(d)
    n = sum(len(v) for v in notas.values())
    return Gabarito(notas=notas, representantes=meta["representantes"]), n


def notas_ordenadas(resultados, qid, gab, limite=None):
    vistos, out = set(), []
    for c in resultados:
        rep = gab.representantes.get(c.poem_id, c.poem_id)
        if rep in vistos:
            continue
        vistos.add(rep)
        out.append(gab.nota(qid, c.poem_id))
        if limite and len(out) == limite:
            break
    return out


def main() -> None:
    meta, chunks = load()
    gab, n_julg = gabarito_fechado(meta)
    perguntas = [p for p in json.load(open("docs/fase-1/08-perguntas.json",
                                           encoding="utf-8"))["perguntas"]
                 if gab.tem(p["id"])]
    print(f"gabarito fechado: {n_julg} julgamentos · {len(perguntas)} perguntas")
    n2 = sum(1 for d in gab.notas.values() for v in d.values() if v == 2)
    print(f"documentos de nota 2: {n2}")

    enc = Encoder()
    idx = Index.load(chunks, enc, meta["assinatura"])
    if idx is None:
        sys.exit("índice recusado")

    # --- recuperação, uma vez: todos os rerankers partem desta lista -------
    recuperado = {}
    for p in perguntas:
        qv = enc.encode_queries([p["q"]])[0]
        recuperado[p["id"]] = [c for c, _ in idx.search(
            qv, top_k=PROFUNDIDADE, voz=Voice(p["voz"]))]

    saida: dict = {"n_julgamentos": n_julg, "n_perguntas": len(perguntas),
                   "n_nota2": n2}

    # --- denso e oráculo ---------------------------------------------------
    d_ndcg = [ndcg(recuperado[p["id"]], p["id"], gab, K) for p in perguntas]
    d_apt = [apt_em(recuperado[p["id"]], p["id"], gab, 3) for p in perguntas]
    orac = []
    for p in perguntas:
        no20 = notas_ordenadas(recuperado[p["id"]], p["id"], gab, PROFUNDIDADE)
        ideais = sorted(gab.notas[p["id"]].values(), reverse=True)[:K]
        melhor = _dcg(ideais)
        orac.append(_dcg(sorted(no20, reverse=True)[:K]) / melhor if melhor else 0.0)
    denso = sum(d_ndcg) / len(d_ndcg)
    oraculo = sum(orac) / len(orac)
    apt_denso = sum(d_apt) / len(d_apt)
    print(f"\ndenso          nDCG@5={denso:.3f}  apt@3={apt_denso:.0%}")
    print(f"oráculo@20     nDCG@5={oraculo:.3f}"
          f"  (tecto de qualquer reordenação do top-20)")
    saida["denso"] = {"ndcg5": round(denso, 3), "apt3": round(apt_denso, 3)}
    saida["oraculo20"] = round(oraculo, 3)

    # --- rerankers ---------------------------------------------------------
    print(f"\n{'configuração':24s} {'nDCG@5':>8s} {'Δ':>8s} {'apt@3':>7s}"
          f" {'lat/pergunta':>13s}  {'% do tecto':>11s}")
    saida["rerankers"] = {}
    for etiqueta, modelo, n_cand, trunc in CONFIGS:
        rr = Reranker(modelo, truncar_tokens=trunc)
        rr.rerank("aquecimento", recuperado[perguntas[0]["id"]][:2])  # descartada
        ns, apts, lats = [], [], []
        for p in perguntas:
            cands = recuperado[p["id"]][:n_cand]
            t0 = time.perf_counter()
            res = [c for c, _ in rr.rerank(p["q"], cands)]
            lats.append(time.perf_counter() - t0)
            ns.append(ndcg(res, p["id"], gab, K))
            apts.append(apt_em(res, p["id"], gab, 3))
        m = sum(ns) / len(ns)
        a = sum(apts) / len(apts)
        lat = st.median(lats)
        frac = (m - denso) / (oraculo - denso) if oraculo > denso else 0.0
        saida["rerankers"][etiqueta] = {
            "ndcg5": round(m, 3), "delta": round(m - denso, 3),
            "apt3": round(a, 3), "latencia_mediana_s": round(lat, 2),
            "fraccao_do_tecto": round(frac, 3)}
        print(f"{etiqueta:24s} {m:8.3f} {m-denso:+8.3f} {a:6.0%} "
              f"{lat:12.2f}s {frac:10.0%}")
        del rr

    print(f"\n=== troca: segundos por ponto de nDCG@5 ===")
    for etiqueta, r in sorted(saida["rerankers"].items(),
                              key=lambda kv: kv[1]["latencia_mediana_s"]):
        if r["delta"] > 0:
            print(f"  {etiqueta:24s} {r['latencia_mediana_s']:5.2f}s / "
                  f"{r['delta']:+.3f} = {r['latencia_mediana_s']/r['delta']:6.1f} "
                  f"s por ponto"
                  + ("" if r["latencia_mediana_s"] <= 6.0 else "   FORA DO PORTÃO"))

    with open("docs/fase-3b/03-resultados.json", "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=1)
    print("\nescrito: docs/fase-3b/03-resultados.json")


if __name__ == "__main__":
    main()
