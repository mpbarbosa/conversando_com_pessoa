#!/usr/bin/env python
"""Fase 5E / Passo D1–D2 — os portões W1 a W4.

Protocolo em [`../FASE-5E.md`](../FASE-5E.md) §4. Corre **depois** de as duas
pontuações estarem commitadas: é este o passo que abre `01-chave.json`.

## Os portões correm sobre a estimativa conjunta

É a correcção que a Fase 5D prescreveu: lá, dois contadores com ICC de 0,671 e ρ
de 0,78 deram veredictos opostos porque a AUC oscilou **0,21** entre eles, mais
do que a distância entre passar e falhar. Aqui o primário é a **média dos dois
por item**; por avaliador corre-se em separado e **relata-se, sem decidir**.
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
SEMENTE = 3
N_PERM = 10000

#: §4 do protocolo.
AUC_MIN = 0.70
KAPPA_MIN = 0.30
CONCORDANCIA_MIN = 0.50
W1_MEDIANA_MAX = 1.0
W1_FRACCAO_DOIS_MAX = 0.50


def auc(baixos, altos) -> float:
    a = np.asarray(baixos, float)[:, None]
    b = np.asarray(altos, float)[None, :]
    return float(((a < b).sum() + 0.5 * (a == b).sum()) / (a.size * b.size))


def auc_ic(baixos, altos, n=2000):
    rng = np.random.default_rng(SEMENTE)
    a, b = np.asarray(baixos, float), np.asarray(altos, float)
    v = [auc(a[rng.integers(0, len(a), len(a))],
             b[rng.integers(0, len(b), len(b))]) for _ in range(n)]
    return float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))


def perm_p(x, y) -> float:
    rng = np.random.default_rng(SEMENTE)
    a, b = np.asarray(x, float), np.asarray(y, float)
    obs = abs(a.mean() - b.mean())
    junto = np.concatenate([a, b])
    n, c = len(a), 0
    for _ in range(N_PERM):
        rng.shuffle(junto)
        if abs(junto[:n].mean() - junto[n:].mean()) >= obs:
            c += 1
    return (c + 1) / (N_PERM + 1)


def kappa_linear(a, b) -> float:
    cats = [0, 1, 2]
    n = len(a)
    obs = np.zeros((3, 3))
    for x, y in zip(a, b):
        obs[cats.index(x), cats.index(y)] += 1
    obs /= n
    esp = np.outer(obs.sum(axis=1), obs.sum(axis=0))
    w = np.array([[abs(i - j) / 2 for j in cats] for i in cats])
    do, de = (w * obs).sum(), (w * esp).sum()
    return float("nan") if de == 0 else 1.0 - do / de


def main() -> None:
    chave = {d["id"]: d for d in
             json.load(open(os.path.join(AQUI, "01-chave.json")))["chave"]}
    ids = sorted(chave)
    grupo = {i: chave[i]["grupo"] for i in ids}
    p1 = json.load(open(os.path.join(AQUI, "02-pontuacoes.json")))["pontuacoes"]
    p2 = json.load(open(os.path.join(AQUI, "02-pontuacoes-r2.json")))["pontuacoes"]
    n1 = {i: p1[i]["c3a"] for i in ids}
    n2 = {i: p2[i]["c3a"] for i in ids}
    conj = {i: (n1[i] + n2[i]) / 2 for i in ids}

    # --- W4, piso de concordância ---------------------------------------
    a, b = [n1[i] for i in ids], [n2[i] for i in ids]
    k = kappa_linear(a, b)
    exacta = sum(x == y for x, y in zip(a, b)) / len(ids)
    w4 = k >= KAPPA_MIN and exacta >= CONCORDANCIA_MIN

    out: dict = {"_meta": {"protocolo": "docs/FASE-5E.md §4",
                           "permutacoes": N_PERM, "semente": SEMENTE,
                           "primario": "estimativa conjunta (média dos dois)"},
                 "W4": {"kappa_ponderado_linear": round(k, 4),
                        "concordancia_exacta": round(exacta, 4),
                        "discordancia_maxima": int(max(abs(x - y) for x, y in zip(a, b))),
                        "passa": bool(w4)}}

    def corre(nota: dict, etiqueta: str) -> dict:
        g = {x: [nota[i] for i in ids if grupo[i] == x] for x in "ROG"}
        # W3 — controlo negativo: ortónimo abaixo do Caeiro real
        w3_auc = auc(g["O"], g["R"])
        w3_lo, w3_hi = auc_ic(g["O"], g["R"])
        w3_p = perm_p(g["O"], g["R"])
        w3 = w3_auc >= AUC_MIN and w3_p <= 0.05
        # W1 — a âncora não premeia o Caeiro real
        med_r = st.median(g["R"])
        frac2 = sum(1 for x in g["R"] if x == 2) / len(g["R"])
        w1 = med_r <= W1_MEDIANA_MAX and frac2 < W1_FRACCAO_DOIS_MAX
        # W2 — distingue autêntico de gerado
        w2_auc = auc(g["G"], g["R"])
        w2_lo, w2_hi = auc_ic(g["G"], g["R"])
        w2_p = perm_p(g["G"], g["R"])
        w2 = w2_auc >= AUC_MIN and w2_p <= 0.05
        return {
            "etiqueta": etiqueta,
            "medianas": {x: round(st.median(v), 3) for x, v in g.items()},
            "medias": {x: round(st.mean(v), 3) for x, v in g.items()},
            "distribuicao": {x: {str(v): sum(1 for y in g[x] if y == v)
                                 for v in sorted(set(g[x]))} for x in "ROG"},
            "W3": {"auc_O_abaixo_de_R": round(w3_auc, 4),
                   "ic95": [round(w3_lo, 4), round(w3_hi, 4)],
                   "p": round(w3_p, 5), "passa": bool(w3)},
            "W1": {"mediana_real": med_r,
                   "fraccao_de_2_no_real": round(frac2, 4),
                   "n_com_2": sum(1 for x in g["R"] if x == 2),
                   "passa": bool(w1)},
            "W2": {"auc_G_abaixo_de_R": round(w2_auc, 4),
                   "ic95": [round(w2_lo, 4), round(w2_hi, 4)],
                   "p": round(w2_p, 5), "passa": bool(w2)},
        }

    out["conjunta"] = corre(conj, "estimativa conjunta — PRIMÁRIA")
    out["por_avaliador"] = {"R1": corre(n1, "R1, sem decidir"),
                            "R2": corre(n2, "R2, sem decidir")}
    c = out["conjunta"]
    out["veredicto"] = {
        "W4_piso_de_concordancia": out["W4"]["passa"],
        "W3_controlo_negativo": c["W3"]["passa"],
        "W1_a_ancora_nao_premeia_o_real": c["W1"]["passa"],
        "W2_distingue_autentico_de_gerado": c["W2"]["passa"],
        "legivel": bool(out["W4"]["passa"] and c["W3"]["passa"]),
    }
    out["notas_por_item"] = {i: {"grupo": grupo[i], "origem": chave[i]["origem"],
                                 "R1": n1[i], "R2": n2[i], "conj": conj[i]}
                             for i in ids}
    with open(os.path.join(AQUI, "03-resultados.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print("Fase 5E — portões (§4)\n")
    w = out["W4"]
    print(f"W4 piso de concordância: κ_lin={w['kappa_ponderado_linear']:.3f} "
          f"exacta={w['concordancia_exacta']:.1%} máx={w['discordancia_maxima']}  "
          f"{'PASSA' if w['passa'] else 'FALHA'}\n")
    for bloco in (out["conjunta"], out["por_avaliador"]["R1"],
                  out["por_avaliador"]["R2"]):
        print(f"=== {bloco['etiqueta']} ===")
        print(f"  medianas R={bloco['medianas']['R']} O={bloco['medianas']['O']} "
              f"G={bloco['medianas']['G']}   médias {bloco['medias']}")
        print(f"  distribuição {bloco['distribuicao']}")
        print(f"  W3 AUC(O<R)={bloco['W3']['auc_O_abaixo_de_R']:.3f} "
              f"IC95={bloco['W3']['ic95']} p={bloco['W3']['p']:.4f}  "
              f"{'PASSA' if bloco['W3']['passa'] else 'FALHA'}")
        print(f"  W1 mediana real={bloco['W1']['mediana_real']} · "
              f"{bloco['W1']['n_com_2']}/20 com 2 "
              f"({bloco['W1']['fraccao_de_2_no_real']:.0%})  "
              f"{'DISPARA' if bloco['W1']['passa'] else 'não dispara'}")
        print(f"  W2 AUC(G<R)={bloco['W2']['auc_G_abaixo_de_R']:.3f} "
              f"IC95={bloco['W2']['ic95']} p={bloco['W2']['p']:.4f}  "
              f"{'PASSA' if bloco['W2']['passa'] else 'FALHA'}\n")
    print(f"VEREDICTO: {out['veredicto']}")


if __name__ == "__main__":
    main()
