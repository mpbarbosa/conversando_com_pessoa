#!/usr/bin/env python
"""Fase 5G / Passo C1–C2 — os portões G0 a G5.

Protocolo em [`../FASE-5H.md`](../FASE-5H.md) §5. Corre **depois** de as duas
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
POTENCIA = {"dp_das_diferencas_5G": 0.674, "pares": 30,
            "delta_detectavel_80pc": 0.40,
            "semi_largura_ic_esperada": 0.25,
            "margem_nao_inferioridade": -0.25,
            "fonte": "docs/FASE-5I.md §5 e §6"}
MARGEM_I2 = -0.25


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
    c = np.array([pares[k]["A"][crit] for k in ks], dtype=float)
    p = np.array([pares[k]["B"][crit] for k in ks], dtype=float)
    d = p - c
    pro_p, pro_c, emp = int((d > 0).sum()), int((d < 0).sum()), int((d == 0).sum())
    disc = pro_p + pro_c
    lo, hi = bootstrap_ic(d)
    return {"etiqueta": etiqueta,
            "mediana_A": st.median(c), "mediana_B": st.median(p),
            "media_A": round(float(c.mean()), 4),
            "media_B": round(float(p.mean()), 4),
            "delta_medio": round(float(d.mean()), 4),
            "ic95": [round(lo, 4), round(hi, 4)],
            "sinais_pro_B": pro_p, "sinais_pro_A": pro_c, "empates": emp,
            "discordantes": disc,
            "p_binomial": round(binomial_bilateral(pro_p, disc), 5),
            "dp_das_diferencas": round(float(d.std(ddof=1)), 4)}


def portoes(b3: dict, a3: dict, i0: dict) -> tuple[list[str], str]:
    """Os portões do §5. b3 = 3b (primário), a3 = 3a' (não-inferioridade)."""
    disp: list[str] = []
    if not i0["pegou"]:
        disp.append("I0-falhou")
        return disp, "I0-falhou"
    if b3["discordantes"] < PISO_DISCORDANTES:
        disp.append("I3")
        return disp, "I3"
    lo_b, hi_b = b3["ic95"]
    i1 = (b3["p_binomial"] <= 0.05 and not (lo_b <= 0 <= hi_b)
          and b3["sinais_pro_B"] > b3["discordantes"] / 2)
    i2 = a3["ic95"][0] > MARGEM_I2
    if i1:
        disp.append("I1")
    if i2:
        disp.append("I2")
    if i1 and i2:
        return disp, "I1+I2"
    return disp, ("I1-sem-I2" if i1 else ("I2-sem-I1" if i2 else "nenhum"))


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

    out: dict = {"_meta": {"protocolo": "docs/FASE-5I.md §5",
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

    # I0 — a verificação de manipulação, e os automáticos por braço
    auto = {}
    for br in ("A", "B"):
        xs = [chave[i] for i in ids if chave[i]["braco"] == br]
        auto[br] = {"c2_zeros": sum(1 for x in xs if x["c2_pt"] == 0),
                    "plagio": sum(1 for x in xs if x["c5_plagio"] == 0),
                    "nao_verso": sum(1 for x in xs if x["c1_verso"] == 0),
                    "truncadas": sum(1 for x in xs if x["truncada"]),
                    "segundos_mediana": round(st.median(x["segundos"] for x in xs), 1),
                    "versos_mediana": st.median(x["n_versos"] for x in xs)}
        auto[br]["dentro_de_10_20"] = sum(
            1 for x in xs if 10 <= x["n_versos"] <= 20)
        auto[br]["abaixo_de_10"] = sum(1 for x in xs if x["n_versos"] < 10)
    out["automaticos_por_braco"] = auto
    i0 = {"dentro_A": auto["A"]["dentro_de_10_20"],
          "dentro_B": auto["B"]["dentro_de_10_20"],
          "de": 30,
          "pegou": auto["B"]["dentro_de_10_20"] > auto["A"]["dentro_de_10_20"]}
    out["I0_verificacao_de_manipulacao"] = i0

    out["por_leitura"] = {}
    for nome, nota in notas.items():
        pares: dict[tuple[str, int], dict] = {}
        for i in ids:
            k = chave[i]
            pares.setdefault((k["pergunta_id"], k["repeticao"]), {})[k["braco"]] = nota[i]
        completos = {k: v for k, v in pares.items() if {"A", "B"} <= set(v)}
        assert len(completos) == 30, f"{nome}: {len(completos)} pares"
        a3 = corre(completos, "c3a", f"3a' — {nome}")
        b3 = corre(completos, "c3b", f"3b — {nome}")
        disp, principal = portoes(b3, a3, i0)
        out["por_leitura"][nome] = {"c3a": a3, "c3b": b3,
                                    "portoes_disparados": disp,
                                    "portao_principal": principal}

    v = {n: out["por_leitura"][n]["portao_principal"] for n in ("R1", "R2")}
    out["I4_avaliadores_discordam"] = v["R1"] != v["R2"]
    pc = out["por_leitura"]["conjunta"]
    out["veredicto"] = {
        "I0_pegou": i0["pegou"],
        "resultado_da_conjunta": pc["portao_principal"],
        "por_avaliador": v,
        "I4_dispara": out["I4_avaliadores_discordam"],
        "autoriza_o_reforco": bool(pc["portao_principal"] == "I1+I2"
                                   and not out["I4_avaliadores_discordam"]),
    }
    out["notas_por_amostra"] = {
        i: {"braco": chave[i]["braco"], "modelo": chave[i]["modelo"],
            "pergunta": chave[i]["pergunta_id"],
            "rep": chave[i]["repeticao"], "R1": p1[i]["c3a"], "R2": p2[i]["c3a"],
            "conj": notas["conjunta"][i]["c3a"]} for i in ids}

    with open(os.path.join(AQUI, "03-resultados.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print("Fase 5I — portões (§5)\n")
    co = out["concordancia"]
    print(f"concordância 3a': κ_lin={co['kappa_ponderado_linear_3a']:.3f} "
          f"exacta={co['concordancia_exacta_3a']:.1%} máx={co['discordancia_maxima_3a']} "
          f"médias {co['media_R1_3a']:.2f}/{co['media_R2_3a']:.2f}\n")
    for nome in ("conjunta", "R1", "R2"):
        r = out["por_leitura"][nome]
        for crit in ("c3b", "c3a"):
            x = r[crit]
            print(f"  {x['etiqueta']:20s} A={x['mediana_A']:.2f} B={x['mediana_B']:.2f} "
                  f"Δ={x['delta_medio']:+.4f} IC95={x['ic95']} "
                  f"B/A/= {x['sinais_pro_B']}/{x['sinais_pro_A']}/{x['empates']} "
                  f"d={x['discordantes']} p={x['p_binomial']:.4f}")
        print(f"  → portões {r['portoes_disparados']}  **{r['portao_principal']}**\n")
    print(f"I0 manipulação: dentro de 10-20 versos  A={i0['dentro_A']}/30  "
          f"B={i0['dentro_B']}/30  ->  {'PEGOU' if i0['pegou'] else 'NÃO PEGOU'}")
    print(f"automáticos por braço: {out['automaticos_por_braco']}")
    print(f"margem de não-inferioridade de I2: limite inferior do IC de 3a' "
          f"tem de ficar acima de {MARGEM_I2}")
    print(f"potência pré-registada: detecta Δ ≥ {POTENCIA['delta_detectavel_80pc']}; "
          f"semi-largura esperada do IC ≈ {POTENCIA['semi_largura_ic_esperada']}")
    print(f"\nVEREDICTO: {out['veredicto']}")


if __name__ == "__main__":
    main()
