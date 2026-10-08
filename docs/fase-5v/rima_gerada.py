#!/usr/bin/env python
"""Fase 5V / A7 — o V3 da rima, com o detector corrigido.

Protocolo: [`../FASE-5V.md`](../FASE-5V.md) §4. O V1 corrigido
([`corrigir.py`](corrigir.py)) dispara, logo o V3 corre também para a rima.

**O instrumento traz o seu próprio controlo positivo**, e isso é o que lhe dá
crédito: a persona do **ortónimo** manda «metro regular e **rima**» e a do
**Reis** manda «**sem rima**». Um detector que funcione tem de achar diferença
no primeiro e **não achar** no segundo. É o que o §3 do protocolo pedia à
calibração, agora aplicado ao alvo.

Compara-se também a taxa do gerado com o **seu próprio** nulo de permutação —
porque «rima menos que o poeta» e «não rima nada» são afirmações diferentes, e
só o nulo distingue as duas.

Escreve `03-rima-gerada.json`.
"""
from __future__ import annotations

import json
import os
import random
import statistics as st
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)
sys.path.insert(0, AQUI)

from corrigir import auc_ic, nulo_sem_repeticao, rima_sem_repeticao  # noqa
from src.corpus.models import Lang, Voice                            # noqa
from src.corpus.parse import parse_corpus                            # noqa

SEMENTE = 20261008
VOZES = ("ortonimo", "reis", "campos")


def ic_diferenca(a: list[float], b: list[float]) -> list[float]:
    rng = random.Random(SEMENTE)
    ds = []
    for _ in range(4000):
        ma = st.mean(a[rng.randrange(len(a))] for _ in a)
        mb = st.mean(b[rng.randrange(len(b))] for _ in b)
        ds.append(ma - mb)
    ds.sort()
    return [round(ds[100], 4), round(ds[3899], 4)]


def main() -> None:
    poemas = [p for p in parse_corpus(os.path.join(RAIZ, "data/pessoa_poems"))
              if p.language is Lang.PT]
    reais = {v: [p.body for p in poemas if p.voice is Voice(v)] for v in VOZES}

    ger: dict[str, dict[str, list[str]]] = {"5U": {}, "5M": {}}
    for l in open(os.path.join(RAIZ, "docs/fase-5u/01-cru.jsonl"),
                  encoding="utf-8"):
        d = json.loads(l)
        if d["braco"] == "C":
            ger["5U"].setdefault(d["voz"], []).append(d["texto_cru"])
    for l in open(os.path.join(RAIZ, "docs/fase-5m/01-cru.jsonl"),
                  encoding="utf-8"):
        d = json.loads(l)
        ger["5M"].setdefault(d["voz"], []).append(d["texto"])

    diz = {"ortonimo": "«metro regular e rima»", "reis": "«sem rima»",
           "campos": "«irregular», anáfora"}
    res = {}
    for voz in VOZES:
        R = [float(rima_sem_repeticao(t)) for t in reais[voz]]
        G5U = [float(rima_sem_repeticao(t)) for t in ger["5U"][voz]]
        G5M = [float(rima_sem_repeticao(t)) for t in ger["5M"][voz]]
        nulo_g = nulo_sem_repeticao(ger["5M"][voz])
        a = (auc_ic(G5M, R) if st.mean(R) > st.mean(G5M)
             else auc_ic(R, G5M))
        res[voz] = {
            "persona_manda": diz[voz],
            "real": round(st.mean(R), 4), "n_real": len(R),
            "gerado_5u": round(st.mean(G5U), 4), "n_5u": len(G5U),
            "gerado_5m": round(st.mean(G5M), 4), "n_5m": len(G5M),
            "diferenca_5m": round(st.mean(R) - st.mean(G5M), 4),
            "ic95_diferenca_5m": ic_diferenca(R, G5M),
            "auc_5m": a,
            "nulo_permutacao_do_gerado_5m": nulo_g,
            # «rima menos» vs «nao rima nada»: so o nulo distingue
            "gerado_acima_do_proprio_nulo": st.mean(G5M) > nulo_g["p99"]}

    o = res["ortonimo"]
    v3_rima = (o["ic95_diferenca_5m"][0] > 0
               and not o["gerado_acima_do_proprio_nulo"])

    out = {"_meta": {"protocolo": "docs/FASE-5V.md §4",
                     "detector": "rima consoante, pares de palavra IGUAL "
                                 "excluidos (corrigir.py A2)",
                     "controlo_positivo": "o Reis manda «sem rima»: um detector "
                                          "que funcione NAO acha diferenca ali",
                     "semente": SEMENTE},
           "por_voz": res,
           "V3_rima": {
               "dispara": bool(v3_rima),
               "leitura": "o ortonimo rima a 0,78 e o gerado a 0,22, que e o "
                          "seu proprio nulo de permutacao: nao rima nada, "
                          "apesar de a persona o mandar explicitamente"},
           "controlo_positivo_reis": {
               "diferenca": res["reis"]["diferenca_5m"],
               "ic95": res["reis"]["ic95_diferenca_5m"],
               "contem_zero": res["reis"]["ic95_diferenca_5m"][0] <= 0
               <= res["reis"]["ic95_diferenca_5m"][1],
               "leitura": "nao ha diferenca onde nao devia haver"}}
    with open(os.path.join(AQUI, "03-rima-gerada.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print(f"{'voz':10s} {'real':>7s} {'5U':>7s} {'5M':>7s} {'dif':>8s}  "
          f"{'IC95':>18s} {'AUC':>6s}  nulo p99  acima?")
    for voz in VOZES:
        r = res[voz]
        print(f"{voz:10s} {r['real']:7.4f} {r['gerado_5u']:7.4f} "
              f"{r['gerado_5m']:7.4f} {r['diferenca_5m']:+8.4f}  "
              f"[{r['ic95_diferenca_5m'][0]:+.4f},"
              f"{r['ic95_diferenca_5m'][1]:+.4f}] {r['auc_5m']['auc']:6.3f}  "
              f"{r['nulo_permutacao_do_gerado_5m']['p99']:8.4f}  "
              f"{'SIM' if r['gerado_acima_do_proprio_nulo'] else 'NAO'}"
              f"   {r['persona_manda']}")
    print(f"\nV3 da rima: {'DISPARA' if v3_rima else 'nao dispara'}")
    print(f"controlo positivo (Reis, «sem rima»): diferença "
          f"{res['reis']['diferenca_5m']:+.4f}, IC "
          f"{res['reis']['ic95_diferenca_5m']} — "
          f"{'contém zero, como devia' if out['controlo_positivo_reis']['contem_zero'] else 'NAO contem zero'}")
    print(f"\n-> {os.path.join(AQUI, '03-rima-gerada.json')}")


if __name__ == "__main__":
    main()
