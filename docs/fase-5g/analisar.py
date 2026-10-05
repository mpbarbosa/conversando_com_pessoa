#!/usr/bin/env python
"""Fase 5G / Passo C1–C2 — os portões G0 a G5.

Protocolo em [`../FASE-5G.md`](../FASE-5G.md) §5. Corre **depois** de as duas
pontuações estarem commitadas: é este o passo que abre `01-chave.json`.

Primário na **estimativa conjunta** (média dos dois por amostra) — a correcção da
Fase 5D, confirmada pela 5F. Por avaliador corre em separado, e **G5 verifica se
chegam ao mesmo veredicto**.

Teste de sinais exacto sobre os **pares discordantes** (a correcção que a 5B fez
ao seu próprio desenho) e IC95% por bootstrap emparelhado, B=10000, semente 3.
"""
from __future__ import annotations

import json
import math
import os
import statistics as st

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
B_BOOT = 10000
SEMENTE = 3
PISO_DISCORDANTES = 8

#: §3.2 do protocolo: o efeito mínimo detectável, calculado antes de medir.
POTENCIA = {"dp_grupo_gerado_5F": 0.657, "pares": 30,
            "delta_detectavel_80pc": 0.50,
            "delta_nao_detectavel": 0.375,
            "fonte": "docs/FASE-5G.md §3.2"}


def binomial_bilateral(k: int, d: int) -> float:
    if d == 0:
        return 1.0
    t = 2.0 ** d
    ab = sum(math.comb(d, i) for i in range(0, k + 1)) / t
    ac = sum(math.comb(d, i) for i in range(k, d + 1)) / t
    return min(1.0, 2.0 * min(ab, ac))


def bootstrap_ic(d: np.ndarray) -> tuple[float, float]:
    rng = np.random.default_rng(SEMENTE)
    ix = rng.integers(0, len(d), size=(B_BOOT, len(d)))
    m = d[ix].mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def kappa_linear(a, b) -> float:
    cats = [0, 1, 2]
    obs = np.zeros((3, 3))
    for x, y in zip(a, b):
        obs[cats.index(x), cats.index(y)] += 1
    obs /= len(a)
    esp = np.outer(obs.sum(axis=1), obs.sum(axis=0))
    w = np.array([[abs(i - j) / 2 for j in cats] for i in cats])
    do, de = (w * obs).sum(), (w * esp).sum()
    return float("nan") if de == 0 else 1.0 - do / de


def corre(pares: dict, crit: str, etiqueta: str) -> dict:
    ks = sorted(pares)
    c = np.array([pares[k]["C"][crit] for k in ks], dtype=float)
    p = np.array([pares[k]["P"][crit] for k in ks], dtype=float)
    d = p - c
    pro_p, pro_c, emp = int((d > 0).sum()), int((d < 0).sum()), int((d == 0).sum())
    disc = pro_p + pro_c
    lo, hi = bootstrap_ic(d)
    return {"etiqueta": etiqueta,
            "mediana_C": st.median(c), "mediana_P": st.median(p),
            "media_C": round(float(c.mean()), 4),
            "media_P": round(float(p.mean()), 4),
            "delta_medio": round(float(d.mean()), 4),
            "ic95": [round(lo, 4), round(hi, 4)],
            "sinais_pro_P": pro_p, "sinais_pro_C": pro_c, "empates": emp,
            "discordantes": disc,
            "p_binomial": round(binomial_bilateral(pro_p, disc), 5),
            "dp_das_diferencas": round(float(d.std(ddof=1)), 4)}


def portoes(a3: dict, b3: dict) -> tuple[list[str], str]:
    disp: list[str] = []
    if a3["mediana_C"] >= 1:
        disp.append("G0")
    d3a, d3b = a3["delta_medio"], b3["delta_medio"]
    g3 = abs(d3b) >= abs(d3a) and d3a != 0 and (d3a > 0) == (d3b > 0)
    if g3:
        disp.append("G3")
    if a3["discordantes"] < PISO_DISCORDANTES:
        disp.append("G4")
        return disp, "G4"
    lo, hi = a3["ic95"]
    if (a3["p_binomial"] <= 0.05 and not (lo <= 0 <= hi)
            and a3["sinais_pro_P"] > a3["discordantes"] / 2 and not g3):
        disp.append("G1")
        return disp, "G1"
    disp.append("G2")
    return disp, "G2"


def main() -> None:
    chave = {d["id"]: d for d in
             json.load(open(os.path.join(AQUI, "01-chave.json")))["chave"]}
    p1 = json.load(open(os.path.join(AQUI, "02-pontuacoes.json")))["pontuacoes"]
    p2 = json.load(open(os.path.join(AQUI, "02-pontuacoes-r2.json")))["pontuacoes"]
    ids = sorted(chave)

    notas = {
        "conjunta": {i: {"c3a": (p1[i]["c3a"] + p2[i]["c3a"]) / 2,
                         "c3b": (p1[i]["c3b"] + p2[i]["c3b"]) / 2} for i in ids},
        "R1": {i: {"c3a": p1[i]["c3a"], "c3b": p1[i]["c3b"]} for i in ids},
        "R2": {i: {"c3a": p2[i]["c3a"], "c3b": p2[i]["c3b"]} for i in ids},
    }

    out: dict = {"_meta": {"protocolo": "docs/FASE-5G.md §5",
                           "bootstrap_B": B_BOOT, "semente": SEMENTE,
                           "piso_discordantes": PISO_DISCORDANTES,
                           "primario": "estimativa conjunta",
                           "potencia_pre_registada": POTENCIA}}

    a, b = [p1[i]["c3a"] for i in ids], [p2[i]["c3a"] for i in ids]
    out["concordancia"] = {
        "kappa_ponderado_linear_3a": round(kappa_linear(a, b), 4),
        "concordancia_exacta_3a": round(sum(x == y for x, y in zip(a, b)) / len(ids), 4),
        "discordancia_maxima_3a": int(max(abs(x - y) for x, y in zip(a, b))),
        "media_R1_3a": round(st.mean(a), 3), "media_R2_3a": round(st.mean(b), 3),
    }

    out["por_leitura"] = {}
    for nome, nota in notas.items():
        pares: dict[tuple[str, int], dict] = {}
        for i in ids:
            k = chave[i]
            pares.setdefault((k["pergunta_id"], k["repeticao"]), {})[k["braco"]] = nota[i]
        completos = {k: v for k, v in pares.items() if {"C", "P"} <= set(v)}
        assert len(completos) == 30, f"{nome}: {len(completos)} pares"
        a3 = corre(completos, "c3a", f"3a' — {nome}")
        b3 = corre(completos, "c3b", f"3b — {nome}")
        disp, principal = portoes(a3, b3)
        out["por_leitura"][nome] = {"c3a": a3, "c3b": b3,
                                    "portoes_disparados": disp,
                                    "portao_principal": principal}

    v = {n: out["por_leitura"][n]["portao_principal"] for n in ("R1", "R2")}
    out["G5_avaliadores_discordam"] = v["R1"] != v["R2"]
    out["veredicto"] = {
        "portao_da_conjunta": out["por_leitura"]["conjunta"]["portao_principal"],
        "portoes_por_avaliador": v,
        "G5_dispara": out["G5_avaliadores_discordam"],
        "autoriza": bool(out["por_leitura"]["conjunta"]["portao_principal"] == "G1"
                         and not out["G5_avaliadores_discordam"]),
    }
    out["notas_por_amostra"] = {
        i: {"braco": chave[i]["braco"], "pergunta": chave[i]["pergunta_id"],
            "rep": chave[i]["repeticao"], "R1": p1[i]["c3a"], "R2": p2[i]["c3a"],
            "conj": notas["conjunta"][i]["c3a"]} for i in ids}

    with open(os.path.join(AQUI, "03-resultados.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print("Fase 5G — portões (§5)\n")
    co = out["concordancia"]
    print(f"concordância 3a': κ_lin={co['kappa_ponderado_linear_3a']:.3f} "
          f"exacta={co['concordancia_exacta_3a']:.1%} máx={co['discordancia_maxima_3a']} "
          f"médias {co['media_R1_3a']:.2f}/{co['media_R2_3a']:.2f}\n")
    for nome in ("conjunta", "R1", "R2"):
        r = out["por_leitura"][nome]
        for crit in ("c3a", "c3b"):
            x = r[crit]
            print(f"  {x['etiqueta']:20s} C={x['mediana_C']:.2f} P={x['mediana_P']:.2f} "
                  f"Δ={x['delta_medio']:+.4f} IC95={x['ic95']} "
                  f"P/C/= {x['sinais_pro_P']}/{x['sinais_pro_C']}/{x['empates']} "
                  f"d={x['discordantes']} p={x['p_binomial']:.4f}")
        print(f"  → portões {r['portoes_disparados']}  **{r['portao_principal']}**\n")
    print(f"potência pré-registada: detecta Δ ≥ {POTENCIA['delta_detectavel_80pc']}, "
          f"não detecta Δ ≤ {POTENCIA['delta_nao_detectavel']}")
    print(f"\nVEREDICTO: {out['veredicto']}")


if __name__ == "__main__":
    main()
