#!/usr/bin/env python
"""Passo A3 — a ressalva do §2.1, medida em vez de afirmada.

Duas medições que separam «o roteador sabe» de «a pergunta diz»:

1. **Conjunto adversarial** (`03-adversarial.json`): 12 perguntas escritas sem
   voz em mente, com o **conjunto** de vozes aceitáveis. Pré-registado e
   commitado antes de qualquer roteador correr sobre ele.
2. **Ablação de indícios** (`03-ablacao.json`): nas 40 originais, 15
   substantivos-assinatura trocados por paráfrase neutra. A queda é a medida da
   contaminação.

E duas linhas de base sem as quais 72% não quer dizer nada: o acaso (25% num
conjunto equilibrado de 4 classes) e **o que o sistema faz hoje** — `--voz
pessoa` por omissão, logo ortónimo sempre, logo 25% nas 40 e 25% nas 12.
"""
from __future__ import annotations

import json
import statistics as st
import sys
import time

sys.path.insert(0, ".")

import numpy as np
import requests

from src.corpus.build import load
from src.corpus.models import Lang, Voice
from src.retrieval.encoder import Encoder
from src.retrieval.index import Index

sys.path.insert(0, "docs/fase-4")
from bench_roteador_llm import SYSTEM, rotear_llm  # noqa: E402

MODELO = "qwen2.5:7b-instruct-q4_K_M"
VOZES = (Voice.CAEIRO, Voice.CAMPOS, Voice.REIS, Voice.ORTONIMO)


def _norm(a):
    n = np.linalg.norm(a, axis=-1, keepdims=True)
    return a / np.where(n == 0, 1.0, n)


def main() -> None:
    saida: dict = {}
    originais = json.load(open("docs/fase-1/08-perguntas.json",
                               encoding="utf-8"))["perguntas"]
    adv = json.load(open("docs/fase-4/03-adversarial.json",
                         encoding="utf-8"))["perguntas"]
    subs = {s["id"]: s["para"] for s in json.load(
        open("docs/fase-4/03-ablacao.json", encoding="utf-8"))["substituicoes"]}

    meta, chunks = load()
    enc = Encoder()
    idx = Index.load(chunks, enc, meta["assinatura"])
    if idx is None:
        sys.exit("índice recusado")
    ix = {v: [i for i, c in enumerate(idx.chunks)
              if c.voice is v and c.language is Lang.PT] for v in VOZES}
    cent = _norm(np.vstack([idx.vectores[ix[v]].mean(axis=0) for v in VOZES]))

    def centroide(textos: list[str]) -> list[Voice]:
        return [VOZES[int(np.argmax(cent @ q))] for q in enc.encode_queries(textos)]

    def llm(textos: list[str]) -> tuple[list[Voice | None], float]:
        rotear_llm(MODELO, "aquecimento")
        out, tempos = [], []
        for t in textos:
            v, info = rotear_llm(MODELO, t)
            out.append(v)
            tempos.append(info["parede_s"])
        return out, round(st.median(tempos), 2)

    # --- 1. conjunto adversarial ------------------------------------------
    print("=== A3.1 conjunto adversarial (12 perguntas, etiqueta múltipla) ===")
    textos_adv = [p["q"] for p in adv]
    prim = [Voice(p["primaria"]) for p in adv]
    aceit = [{Voice(x) for x in p["aceitaveis"]} for p in adv]
    controlos = [i for i, p in enumerate(adv) if len(p["aceitaveis"]) == 1]

    adv_res = {}
    prev_llm, mediana = llm(textos_adv)
    for nome, prev in (("llm 7b", prev_llm), ("centroide", centroide(textos_adv))):
        estrito = sum(1 for e, p in zip(prim, prev) if e is p)
        amplo = sum(1 for a, p in zip(aceit, prev) if p in a)
        ctrl = sum(1 for i in controlos if prev[i] in aceit[i])
        adv_res[nome] = {"estrito": f"{estrito}/12", "estrito_pct": round(estrito/12, 3),
                         "aceitavel": f"{amplo}/12", "aceitavel_pct": round(amplo/12, 3),
                         "controlos": f"{ctrl}/{len(controlos)}",
                         "previstas": [p.value if p else None for p in prev]}
        print(f"{nome:12s} primária {estrito:2d}/12 = {estrito/12:4.0%}   "
              f"aceitável {amplo:2d}/12 = {amplo/12:4.0%}   "
              f"controlos {ctrl}/{len(controlos)}")
    adv_res["llm 7b"]["parede_mediana_s"] = mediana
    for p, prev in zip(adv, prev_llm):
        marca = "ok " if prev and prev.value in p["aceitaveis"] else "ERRO"
        print(f"  {marca} {p['id']} -> {prev.value if prev else '?':9s} "
              f"(aceitáveis: {','.join(p['aceitaveis'])})  {p['q']}")
    saida["adversarial"] = adv_res

    # --- 2. ablação de indícios -------------------------------------------
    print("\n=== A3.2 ablação de indícios nas 40 originais ===")
    esperadas = [Voice(p["voz"]) for p in originais]
    textos_crus = [p["q"] for p in originais]
    textos_abl = [subs.get(p["id"], p["q"]) for p in originais]
    tocadas = [i for i, p in enumerate(originais) if p["id"] in subs]

    abl = {}
    prev_abl, med_abl = llm(textos_abl)
    for nome, pc, pa in (("llm 7b", None, prev_abl),
                         ("centroide", None, centroide(textos_abl))):
        pc = ({"llm 7b": None}.get(nome)
              or (centroide(textos_crus) if nome == "centroide" else None))
        if pc is None:  # llm sobre as cruas já foi medido no A2
            crus = json.load(open("docs/fase-4/02-roteador-llm.json",
                                  encoding="utf-8"))["llm 7b"]
            antes = crus["certos"]
            antes_tocadas = sum(
                1 for i in tocadas
                if originais[i]["id"] not in {e["id"] for e in crus["erros"]})
        else:
            antes = sum(1 for e, p in zip(esperadas, pc) if e is p)
            antes_tocadas = sum(1 for i in tocadas if esperadas[i] is pc[i])
        depois = sum(1 for e, p in zip(esperadas, pa) if e is p)
        depois_tocadas = sum(1 for i in tocadas if esperadas[i] is pa[i])
        abl[nome] = {
            "antes": f"{antes}/40", "depois": f"{depois}/40",
            "queda": antes - depois,
            "nas_15_tocadas": {"antes": f"{antes_tocadas}/15",
                               "depois": f"{depois_tocadas}/15",
                               "queda": antes_tocadas - depois_tocadas},
        }
        print(f"{nome:12s} 40 perguntas: {antes}/40 = {antes/40:4.0%}  ->  "
              f"{depois}/40 = {depois/40:4.0%}   (queda {antes-depois:+d})")
        print(f"{'':12s} só nas 15 tocadas: {antes_tocadas}/15 -> "
              f"{depois_tocadas}/15   (queda {antes_tocadas-depois_tocadas:+d})")
    abl["llm 7b"]["parede_mediana_s"] = med_abl
    saida["ablacao"] = abl

    # --- 3. linhas de base -------------------------------------------------
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
