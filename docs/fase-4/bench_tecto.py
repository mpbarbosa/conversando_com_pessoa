#!/usr/bin/env python
"""Passo B1 — a falta do nDCG@5 é recuperável? Medir antes de gastar máquina.

O aceite do plano para o enriquecimento é «`recall@5` melhora no conjunto
dourado». O enriquecimento custa 3,2 a 7,5 h de máquina (§3.3 da `FASE-4.md`).
Este passo decide se esse número **pode** melhorar, antes de se pagar.

O denso faz nDCG@5 = 0,677. Falta 0,323, e essa falta parte-se em duas metades
com destinos opostos:

| | o que é | quem a resolve |
|---|---|---|
| `oráculo@20 − denso` | notas 2 que o denso **traz** e põe abaixo da 5.ª posição | reordenação — a Fase 3, que falhou |
| `1,0 − oráculo@20` | notas 2 que o denso **não traz** nem na 20.ª | mudar o que está indexado — o enriquecimento |

E uma terceira medida, que é a do §3.1: quantas perguntas têm o top-5 **saturado**,
isto é, já levam todas as notas 2 que o gabarito conhece. Numa pergunta saturada,
nenhum sistema melhora o nDCG@5 sem que se julguem candidatos novos — e um poema
nunca julgado conta 0 por omissão, logo o enriquecimento é **penalizado** por
trazer o que o instrumento não viu.
"""
from __future__ import annotations

import json
import sys

sys.path.insert(0, ".")

from src.avaliacao import Gabarito, _dcg, ndcg
from src.corpus.build import load
from src.corpus.models import Voice
from src.retrieval.encoder import Encoder
from src.retrieval.index import Index

PERGUNTAS = "docs/fase-1/08-perguntas.json"
JULGAMENTOS = "docs/fase-1/08-julgamentos.json"
K = 5
PROFUNDIDADE = 20


def notas_unicas(resultados, pergunta_id, gabarito, limite=None):
    """Notas na ordem dada, uma por grupo de deduplicação."""
    vistos, out = set(), []
    for c in resultados:
        rep = gabarito.representantes.get(c.poem_id, c.poem_id)
        if rep in vistos:
            continue
        vistos.add(rep)
        out.append(gabarito.nota(pergunta_id, c.poem_id))
        if limite and len(out) == limite:
            break
    return out


def main() -> None:
    meta, chunks = load()
    j = json.load(open(JULGAMENTOS, encoding="utf-8"))
    gabarito = Gabarito(notas={k: v for k, v in j.items()
                               if not k.startswith("_")},
                        representantes=meta["representantes"])
    perguntas = json.load(open(PERGUNTAS, encoding="utf-8"))["perguntas"]

    enc = Encoder()
    idx = Index.load(chunks, enc, meta["assinatura"])
    if idx is None:
        sys.exit("índice recusado")

    linhas, soma = [], {"denso": 0.0, "oraculo20": 0.0}
    print("pergunta  n2 no    n2 no    n2 no    nDCG@5   oráculo@20   top-5")
    print("          gabarito top-5    top-20   denso    (reordenado) saturado")
    for p in perguntas:
        if not gabarito.tem(p["id"]):
            continue
        qv = enc.encode_queries([p["q"]])[0]
        res = [c for c, _ in idx.search(qv, top_k=PROFUNDIDADE,
                                        voz=Voice(p["voz"]))]
        n2_gab = sum(1 for n in gabarito.notas[p["id"]].values() if n == 2)
        no5 = notas_unicas(res, p["id"], gabarito, K)
        no20 = notas_unicas(res, p["id"], gabarito, PROFUNDIDADE)
        n2_5, n2_20 = no5.count(2), no20.count(2)

        d = ndcg(res, p["id"], gabarito, K)
        # Oráculo@20: o melhor que qualquer reordenação da lista de 20 consegue.
        ideais = sorted(gabarito.notas[p["id"]].values(), reverse=True)[:K]
        melhor = _dcg(ideais)
        o20 = (_dcg(sorted(no20, reverse=True)[:K]) / melhor) if melhor else 0.0

        saturado = n2_5 == min(K, n2_gab)
        soma["denso"] += d
        soma["oraculo20"] += o20
        linhas.append({"id": p["id"], "voz": p["voz"], "n2_gabarito": n2_gab,
                       "n2_top5": n2_5, "n2_top20": n2_20,
                       "ndcg5": round(d, 3), "oraculo20": round(o20, 3),
                       "saturado": saturado})
        print(f"{p['id']:9s} {n2_gab:6d}   {n2_5:6d}   {n2_20:6d}   "
              f"{d:6.3f}   {o20:10.3f}   {'sim' if saturado else 'NÃO'}")

    n = len(linhas)
    denso = soma["denso"] / n
    orac = soma["oraculo20"] / n
    saturadas = sum(1 for x in linhas if x["saturado"])
    reord = orac - denso
    fundo = 1.0 - orac
    falta = 1.0 - denso

    print(f"\n=== decomposição da falta, n={n} perguntas julgadas ===")
    print(f"  nDCG@5 do denso ................... {denso:.3f}")
    print(f"  nDCG@5 do oráculo sobre o top-20 .. {orac:.3f}")
    print(f"  falta até 1,0 ..................... {falta:.3f}")
    print(f"    recuperável por REORDENAR ....... {reord:.3f}"
          f"  ({reord/falta:.0%} da falta)")
    print(f"    exige TRAZER o que não vem ...... {fundo:.3f}"
          f"  ({fundo/falta:.0%} da falta)")
    print(f"\n  perguntas com o top-5 saturado .... {saturadas}/{n}"
          f"  ({saturadas/n:.0%})")
    print(f"  notas 2 no gabarito ............... "
          f"{sum(x['n2_gabarito'] for x in linhas)}"
          f" (mediana {sorted(x['n2_gabarito'] for x in linhas)[n//2]})")

    saida = {"n": n, "ndcg5_denso": round(denso, 3),
             "ndcg5_oraculo20": round(orac, 3),
             "falta": round(falta, 3),
             "recuperavel_reordenando": round(reord, 3),
             "fracao_reordenando": round(reord / falta, 3),
             "exige_trazer": round(fundo, 3),
             "fracao_trazer": round(fundo / falta, 3),
             "saturadas": f"{saturadas}/{n}",
             "por_pergunta": linhas}
    with open("docs/fase-4/05-tecto.json", "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=1)
    print("\nescrito: docs/fase-4/05-tecto.json")


if __name__ == "__main__":
    main()
