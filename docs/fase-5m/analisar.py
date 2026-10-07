#!/usr/bin/env python
"""Fase 5M / B1–C1 — os cinco portões.

Protocolo: `../FASE-5M.md` §4. Lê as 180 amostras desta fase e as 60 do Caeiro
da 5H, e escreve `03-resultados.json`.

Reutiliza, sem reescrever:
  - `ks` de `fase-5j/analisar.py` (validado lá em três casos de sanidade);
  - `nulo` de `fase-5k/calibrar.py` (sub-amostras reais sem reposição);
  - as contagens do corpus de `fase-5j/01-contagem.json`.

Os nulos correm a **n=16** (pior caso do IC do ICC, §2 do protocolo) e a
**n=30**, e o portão M5 exige que um resultado sobreviva ao de n=16.
"""
from __future__ import annotations

import json
import os
import random
import statistics as st
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "docs", "fase-5j"))
sys.path.insert(0, os.path.join(RAIZ, "docs", "fase-5k"))

from analisar import ks                                   # noqa: E402
from calibrar import nulo                                 # noqa: E402

SEMENTE = 20261007
B_NULO = 10_000
NS = (16, 30)
VOZES = ("caeiro", "campos", "reis", "ortonimo")
MODELOS = {"Q": "qwen2.5", "L": "llama3.1"}
#: §4 M1 — o valor que a 5K publicou para o llama pedido Caeiro.
KS_LLAMA_CAEIRO_5K = 0.347


def carrega() -> tuple[dict, dict]:
    cont = json.load(open(os.path.join(RAIZ, "docs/fase-5j/01-contagem.json"),
                          encoding="utf-8"))
    reais = {v: [p["versos_min3"] for p in cont["por_poema"][v]
                 if p["elegivel"] and p["lingua"] == "pt"]
             for v in VOZES}

    # As tres vozes desta fase + o Caeiro da 5H, que usa o mesmo banco.
    bracos: dict[tuple[str, str], list[int]] = {}
    for caminho, so_caeiro in ((os.path.join(AQUI, "01-cru.jsonl"), False),
                               (os.path.join(RAIZ, "docs/fase-5h/01-cru.jsonl"),
                                True)):
        if not os.path.exists(caminho):
            continue
        for linha in open(caminho, encoding="utf-8"):
            d = json.loads(linha)
            voz = d.get("voz", "caeiro")
            if so_caeiro and voz != "caeiro":
                continue
            bracos.setdefault((voz, d["braco"]), []).append(d["n_versos"])
    return reais, bracos


def main() -> None:
    reais, bracos = carrega()
    rng = random.Random(SEMENTE)

    faltam = [(v, b) for v in VOZES for b in MODELOS
              if (v, b) not in bracos]
    if faltam:
        print(f"AVISO: celulas ausentes: {faltam}")

    # --- nulos por voz, aos dois n ------------------------------------- #
    nulos = {v: {n: nulo(reais[v], n, rng, b=B_NULO) for n in NS}
             for v in VOZES}
    p95 = {v: {n: round(float(np.percentile(nulos[v][n], 95)), 4) for n in NS}
           for v in VOZES}

    # --- B1: cada celula contra todos os corpora ----------------------- #
    celulas: dict = {}
    for (voz, br), xs in sorted(bracos.items()):
        d = {w: round(ks(xs, reais[w]), 4) for w in VOZES}
        mais_perto = min(d, key=d.get)
        celulas[f"{voz}/{br}"] = {
            "voz_pedida": voz, "modelo": MODELOS[br], "n": len(xs),
            "mediana_versos": st.median(xs),
            "min": min(xs), "max": max(xs),
            "ks_a_cada_voz": d,
            "ks_a_voz_pedida": d[voz],
            "voz_mais_proxima": mais_perto,
            "acertou_a_voz_pedida": mais_perto == voz,
            "dentro_do_nulo": {str(n): d[voz] <= p95[voz][n] for n in NS},
        }

    # --- M1: a predicao da 5K ------------------------------------------ #
    lr = celulas.get("reis/L")
    m1 = {"referencia_5K_llama_caeiro": KS_LLAMA_CAEIRO_5K,
          "ks_llama_reis": lr["ks_a_voz_pedida"] if lr else None,
          "dispara": bool(lr and lr["ks_a_voz_pedida"] < KS_LLAMA_CAEIRO_5K)}
    # O mesmo com o Caeiro medido NESTA grelha, para nao depender do valor
    # publicado (deve coincidir: sao as mesmas 60 amostras da 5H).
    lc = celulas.get("caeiro/L")
    if lc:
        m1["ks_llama_caeiro_remedido"] = lc["ks_a_voz_pedida"]
        m1["coincide_com_5K"] = abs(
            lc["ks_a_voz_pedida"] - KS_LLAMA_CAEIRO_5K) < 0.005
        m1["dispara_com_remedido"] = (
            lr is not None
            and lr["ks_a_voz_pedida"] < lc["ks_a_voz_pedida"])

    # --- M2: alguma celula acerta a forma da sua voz -------------------- #
    dentro = {n: [k for k, c in celulas.items()
                  if c["dentro_do_nulo"][str(n)]] for n in NS}
    m2 = {"celulas_dentro_do_nulo": {str(n): dentro[n] for n in NS},
          "p95_por_voz": p95,
          "dispara": bool(dentro[16]),
          "dispara_so_a_n30": bool(dentro[30]) and not bool(dentro[16])}

    # --- M3: o custo de forma da troca e geral? ------------------------- #
    piores = []
    comp: dict = {}
    for v in VOZES:
        q, l = celulas.get(f"{v}/Q"), celulas.get(f"{v}/L")
        if not (q and l):
            continue
        comp[v] = {"ks_qwen": q["ks_a_voz_pedida"],
                   "ks_llama": l["ks_a_voz_pedida"],
                   "llama_pior": l["ks_a_voz_pedida"] > q["ks_a_voz_pedida"],
                   "delta_llama_menos_qwen": round(
                       l["ks_a_voz_pedida"] - q["ks_a_voz_pedida"], 4)}
        if comp[v]["llama_pior"]:
            piores.append(v)
    m3 = {"por_voz": comp, "vozes_onde_o_llama_e_pior": piores,
          "n": len(piores), "dispara": len(piores) >= 3,
          "so_no_caeiro": piores == ["caeiro"]}

    # --- M4: os modelos modulam a forma por voz? ----------------------- #
    m4: dict = {"por_modelo": {}}
    for br, nome in MODELOS.items():
        alvos = {v: celulas[f"{v}/{br}"]["voz_mais_proxima"]
                 for v in VOZES if f"{v}/{br}" in celulas}
        if not alvos:
            continue
        cont = {}
        for w in alvos.values():
            cont[w] = cont.get(w, 0) + 1
        dominante = max(cont, key=cont.get)
        medianas = {v: celulas[f"{v}/{br}"]["mediana_versos"]
                    for v in VOZES if f"{v}/{br}" in celulas}
        m4["por_modelo"][nome] = {
            "voz_mais_proxima_por_celula": alvos,
            "corpus_dominante": dominante, "quantas": cont[dominante],
            "nao_modula": cont[dominante] >= 3,
            "medianas_por_voz_pedida": medianas,
            "amplitude_das_medianas": round(
                max(medianas.values()) - min(medianas.values()), 1),
            "acertos": [v for v in alvos if alvos[v] == v],
        }
    m4["dispara"] = any(c["nao_modula"] for c in m4["por_modelo"].values())

    # --- M5: o que sobrevive so ao n=30 -------------------------------- #
    m5 = {"m2_so_a_n30": m2["dispara_so_a_n30"],
          "dispara": m2["dispara_so_a_n30"],
          "leitura": "um resultado que sobreviva so ao nulo de n=30 le-se como "
                     "«nao mostrado» (§2 e §4 do protocolo)"}

    out = {"_meta": {"protocolo": "docs/FASE-5M.md §4", "semente": SEMENTE,
                     "B_nulo": B_NULO, "ns_do_nulo": list(NS),
                     "caeiro": "reutilizado da 5H, mesmo banco de perguntas",
                     "ks": "fase-5j/analisar.py", "nulo": "fase-5k/calibrar.py"},
           "celulas": celulas, "M1": m1, "M2": m2, "M3": m3, "M4": m4,
           "M5": m5}

    caminho = os.path.join(AQUI, "03-resultados.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print("=== B1 — cada célula contra o corpus da sua voz ===")
    print(f"{'célula':18s} {'n':>3s} {'med':>5s} {'KS alvo':>8s} "
          f"{'p95@16':>7s} {'p95@30':>7s}  mais perto    acerta")
    for k, c in celulas.items():
        v = c["voz_pedida"]
        print(f"{k:18s} {c['n']:3d} {c['mediana_versos']:5} "
              f"{c['ks_a_voz_pedida']:8.3f} {p95[v][16]:7.3f} "
              f"{p95[v][30]:7.3f}  {c['voz_mais_proxima']:12s}  "
              f"{'SIM' if c['acertou_a_voz_pedida'] else 'nao'}")

    print("\n=== M1 — a predição da 5K (llama melhor no Reis que no Caeiro) ===")
    print(f"  KS llama@Caeiro = {m1.get('ks_llama_caeiro_remedido')} "
          f"(5K publicou {KS_LLAMA_CAEIRO_5K}; coincide: "
          f"{m1.get('coincide_com_5K')})")
    print(f"  KS llama@Reis   = {m1['ks_llama_reis']}")
    print(f"  M1 {'DISPARA' if m1['dispara'] else 'nao dispara'}")

    print("\n=== M2 — alguma célula acerta a forma da sua voz ===")
    for n in NS:
        print(f"  n={n}: {m2['celulas_dentro_do_nulo'][str(n)] or 'NENHUMA'}")
    print(f"  M2 {'DISPARA' if m2['dispara'] else 'nao dispara'}")

    print("\n=== M3 — o custo de forma da troca é geral? ===")
    for v, c in m3["por_voz"].items():
        print(f"  {v:10s} qwen {c['ks_qwen']:.3f}  llama {c['ks_llama']:.3f}  "
              f"Δ {c['delta_llama_menos_qwen']:+.3f}  "
              f"{'llama pior' if c['llama_pior'] else 'qwen pior'}")
    print(f"  llama pior em {m3['n']} de 4  "
          f"M3 {'DISPARA' if m3['dispara'] else 'nao dispara'}")

    print("\n=== M4 — os modelos modulam a forma por voz? ===")
    for nome, c in m4["por_modelo"].items():
        print(f"  {nome}: medianas {c['medianas_por_voz_pedida']}  "
              f"amplitude {c['amplitude_das_medianas']}")
        print(f"  {'':10s} mais perto de: {c['voz_mais_proxima_por_celula']}")
        print(f"  {'':10s} dominante {c['corpus_dominante']} "
              f"({c['quantas']}/4)  nao modula: {c['nao_modula']}")
    print(f"  M4 {'DISPARA' if m4['dispara'] else 'nao dispara'}")
    print(f"\nM5 {'DISPARA' if m5['dispara'] else 'nao dispara'}")
    print(f"\n-> {caminho}")


if __name__ == "__main__":
    main()
