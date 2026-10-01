#!/usr/bin/env python
"""Passo A3, parte do encoder e pontuação — lê o que a parte LLM gravou."""
from __future__ import annotations

import json
import sys

import numpy as np

sys.path.insert(0, ".")

from src.corpus.build import load
from src.corpus.models import Lang, Voice
from src.retrieval.encoder import Encoder
from src.retrieval.index import Index

VOZES = (Voice.CAEIRO, Voice.CAMPOS, Voice.REIS, Voice.ORTONIMO)


def _norm(a):
    n = np.linalg.norm(a, axis=-1, keepdims=True)
    return a / np.where(n == 0, 1.0, n)


def main() -> None:
    originais = json.load(open("docs/fase-1/08-perguntas.json",
                               encoding="utf-8"))["perguntas"]
    adv = json.load(open("docs/fase-4/03-adversarial.json",
                         encoding="utf-8"))["perguntas"]
    subs = {s["id"]: s["para"] for s in json.load(
        open("docs/fase-4/03-ablacao.json", encoding="utf-8"))["substituicoes"]}
    llm = json.load(open("docs/fase-4/03-a3-llm.json", encoding="utf-8"))
    a2 = json.load(open("docs/fase-4/02-roteador-llm.json", encoding="utf-8"))

    meta, chunks = load()
    enc = Encoder()
    idx = Index.load(chunks, enc, meta["assinatura"])
    if idx is None:
        sys.exit("índice recusado")
    ix = {v: [i for i, c in enumerate(idx.chunks)
              if c.voice is v and c.language is Lang.PT] for v in VOZES}
    cent = _norm(np.vstack([idx.vectores[ix[v]].mean(axis=0) for v in VOZES]))

    def centroide(textos):
        return [VOZES[int(np.argmax(cent @ q))] for q in enc.encode_queries(textos)]

    def vz(s):
        return Voice(s) if s else None

    saida: dict = {}

    # --- A3.1 adversarial --------------------------------------------------
    print("=== A3.1 conjunto adversarial (12 perguntas, etiqueta múltipla) ===")
    prim = [Voice(p["primaria"]) for p in adv]
    aceit = [{Voice(x) for x in p["aceitaveis"]} for p in adv]
    controlos = [i for i, p in enumerate(adv) if len(p["aceitaveis"]) == 1]
    prev = {"llm 7b": [vz(s) for s in llm["adversarial"]["previstas"]],
            "centroide": centroide([p["q"] for p in adv])}
    res = {}
    for nome, pv in prev.items():
        est = sum(1 for e, p in zip(prim, pv) if e is p)
        amp = sum(1 for a, p in zip(aceit, pv) if p in a)
        ctrl = sum(1 for i in controlos if pv[i] in aceit[i])
        res[nome] = {"primaria": f"{est}/12", "primaria_pct": round(est / 12, 3),
                     "aceitavel": f"{amp}/12", "aceitavel_pct": round(amp / 12, 3),
                     "controlos": f"{ctrl}/{len(controlos)}",
                     "previstas": [p.value if p else None for p in pv]}
        print(f"{nome:12s} primária {est:2d}/12 = {est/12:4.0%}   "
              f"aceitável {amp:2d}/12 = {amp/12:4.0%}   "
              f"controlos {ctrl}/{len(controlos)}")
    res["llm 7b"]["parede_mediana_s"] = llm["adversarial"]["parede_mediana_s"]
    for p, pv in zip(adv, prev["llm 7b"]):
        ok = pv and pv.value in p["aceitaveis"]
        print(f"  {'ok  ' if ok else 'ERRO'} {p['id']} -> "
              f"{pv.value if pv else '?':9s} (aceitáveis: "
              f"{','.join(p['aceitaveis'])})  {p['q']}")
    saida["adversarial"] = res

    # --- A3.2 ablação ------------------------------------------------------
    print("\n=== A3.2 ablação de indícios nas 40 originais ===")
    esperadas = [Voice(p["voz"]) for p in originais]
    tocadas = [i for i, p in enumerate(originais) if p["id"] in subs]
    abl = {}

    # llm: o «antes» é a corrida do A2 sobre as perguntas cruas
    errados_a2 = {e["id"] for e in a2["llm 7b"]["erros"]}
    antes_llm = [Voice(p["voz"]) if p["id"] not in errados_a2 else None
                 for p in originais]
    pares = {
        "llm 7b": (antes_llm, [vz(s) for s in llm["ablacao"]["previstas"]]),
        "centroide": (centroide([p["q"] for p in originais]),
                      centroide([subs.get(p["id"], p["q"]) for p in originais])),
    }
    for nome, (pa, pd) in pares.items():
        a = sum(1 for e, p in zip(esperadas, pa) if e is p)
        d = sum(1 for e, p in zip(esperadas, pd) if e is p)
        at = sum(1 for i in tocadas if esperadas[i] is pa[i])
        dt = sum(1 for i in tocadas if esperadas[i] is pd[i])
        abl[nome] = {"antes": f"{a}/40", "depois": f"{d}/40", "queda": a - d,
                     "nas_15_tocadas": {"antes": f"{at}/15", "depois": f"{dt}/15",
                                        "queda": at - dt}}
        print(f"{nome:12s} 40 perguntas: {a}/40 = {a/40:4.0%}  ->  "
              f"{d}/40 = {d/40:4.0%}   (queda {a-d:+d})")
        print(f"{'':12s} só nas 15 tocadas: {at}/15 -> {dt}/15"
              f"   (queda {at-dt:+d})")
        viradas = [originais[i]["id"] for i in tocadas
                   if esperadas[i] is pa[i] and esperadas[i] is not pd[i]]
        recuperadas = [originais[i]["id"] for i in tocadas
                       if esperadas[i] is not pa[i] and esperadas[i] is pd[i]]
        abl[nome]["perdidas"] = viradas
        abl[nome]["ganhas"] = recuperadas
        print(f"{'':12s} perdidas: {viradas or '—'} · ganhas: {recuperadas or '—'}")
    abl["llm 7b"]["parede_mediana_s"] = llm["ablacao"]["parede_mediana_s"]
    saida["ablacao"] = abl

    # --- linhas de base ---------------------------------------------------
    print("\n=== linhas de base ===")
    base = {
        "acaso_4_classes": 0.25,
        "sempre_ortonimo_40": round(sum(1 for e in esperadas
                                        if e is Voice.ORTONIMO) / 40, 3),
        "sempre_ortonimo_12_primaria": round(
            sum(1 for e in prim if e is Voice.ORTONIMO) / 12, 3),
        "sempre_ortonimo_12_aceitavel": round(
            sum(1 for a in aceit if Voice.ORTONIMO in a) / 12, 3),
    }
    for k, v in base.items():
        print(f"  {k:32s} {v:.0%}")
    saida["linhas_de_base"] = base

    with open("docs/fase-4/03-a3.json", "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=1)
    print("\nescrito: docs/fase-4/03-a3.json")


if __name__ == "__main__":
    main()
