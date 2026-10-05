#!/usr/bin/env python
"""Fase 5D / Passo D1–D3 — os portões V1 a V5.

Protocolo em [`../FASE-5D.md`](../FASE-5D.md) §5. Corre **depois** de as duas
contagens estarem commitadas: é este o passo que abre `01-chave.json`.

Estatística sem scipy: permutação (10000, semente 3), AUC por Mann-Whitney
normalizado com IC por bootstrap, ICC(2,1) por decomposição de variâncias, e ρ
de Spearman por Pearson sobre postos.
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(AQUI, "..", "..")))

SEMENTE = 3
N_PERM = 10000

#: §5 do protocolo.
AUC_MIN = 0.75
ICC_MIN = 0.60
RHO_ESPECIFICIDADE_MAX = 0.35
V3_VALORES_MIN = 12
V3_MODAL_MAX = 0.40

CONTADORES = {"R1": "02-contagens.json", "R2": "02-contagens-r2.json"}


def auc(baixos, altos) -> float:
    a = np.asarray(baixos)[:, None]
    b = np.asarray(altos)[None, :]
    return float(((a < b).sum() + 0.5 * (a == b).sum()) / (a.size * b.size))


def auc_ic(baixos, altos, n=2000):
    rng = np.random.default_rng(SEMENTE)
    a, b = np.asarray(baixos), np.asarray(altos)
    v = [auc(a[rng.integers(0, len(a), len(a))],
             b[rng.integers(0, len(b), len(b))]) for _ in range(n)]
    return float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))


def perm_p(x, y) -> float:
    """p bilateral por permutação da diferença de médias."""
    rng = np.random.default_rng(SEMENTE)
    a, b = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    obs = abs(a.mean() - b.mean())
    junto = np.concatenate([a, b])
    n = len(a)
    c = 0
    for _ in range(N_PERM):
        rng.shuffle(junto)
        if abs(junto[:n].mean() - junto[n:].mean()) >= obs:
            c += 1
    return (c + 1) / (N_PERM + 1)


def icc(a, b) -> float:
    """ICC(2,1), concordância absoluta entre dois avaliadores."""
    m = np.column_stack([np.asarray(a, float), np.asarray(b, float)])
    n, k = m.shape
    media = m.mean()
    ms_linhas = k * ((m.mean(axis=1) - media) ** 2).sum() / (n - 1)
    ms_cols = n * ((m.mean(axis=0) - media) ** 2).sum() / (k - 1)
    res = m - m.mean(axis=1, keepdims=True) - m.mean(axis=0, keepdims=True) + media
    ms_erro = (res ** 2).sum() / ((n - 1) * (k - 1))
    den = ms_linhas + (k - 1) * ms_erro + k * (ms_cols - ms_erro) / n
    return float((ms_linhas - ms_erro) / den) if den else float("nan")


def postos(x) -> np.ndarray:
    a = np.asarray(x, float)
    r = np.empty(len(a))
    r[a.argsort()] = np.arange(len(a), dtype=float)
    for v in np.unique(a):
        msk = a == v
        if msk.sum() > 1:
            r[msk] = r[msk].mean()
    return r


def spearman(x, y) -> float:
    rx, ry = postos(x), postos(y)
    if rx.std() == 0 or ry.std() == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def main() -> None:
    chave = {d["id"]: d for d in
             json.load(open(os.path.join(AQUI, "01-chave.json")))["chave"]}
    ids = sorted(chave)
    grupo = {i: chave[i]["grupo"] for i in ids}

    out: dict = {"_meta": {"protocolo": "docs/FASE-5D.md §5",
                           "permutacoes": N_PERM, "semente": SEMENTE,
                           "auc_min": AUC_MIN, "icc_min": ICC_MIN},
                 "por_contador": {}}
    fvv_por: dict[str, dict[str, float]] = {}

    for nome, fich in CONTADORES.items():
        c = json.load(open(os.path.join(AQUI, fich)))["contagens"]
        fvv = {i: len(c[i]["versos_com_volta"]) / c[i]["n_versos"] for i in ids}
        fvv_por[nome] = fvv
        g = {k: [fvv[i] for i in ids if grupo[i] == k] for k in "ROG"}

        # V1 — R abaixo de O
        v1_auc = auc(g["R"], g["O"])
        v1_lo, v1_hi = auc_ic(g["R"], g["O"])
        v1_p = perm_p(g["R"], g["O"])
        v1 = v1_auc >= AUC_MIN and v1_p <= 0.05

        # V2 — G acima de R
        v2_p = perm_p(g["G"], g["R"])
        v2 = st.median(g["G"]) > st.median(g["R"]) and v2_p <= 0.05

        # V3 — resolução
        vals = [round(x, 6) for x in fvv.values()]
        modal = max(vals.count(v) for v in set(vals)) / len(vals)
        v3 = len(set(vals)) >= V3_VALORES_MIN and modal < V3_MODAL_MAX

        # V5 — especificidade
        nv = [c[i]["n_versos"] for i in ids]
        rho_nv = spearman([fvv[i] for i in ids], [float(x) for x in nv])
        v5 = abs(rho_nv) <= RHO_ESPECIFICIDADE_MAX

        out["por_contador"][nome] = {
            "medianas": {k: round(st.median(v), 4) for k, v in g.items()},
            "medias": {k: round(st.mean(v), 4) for k, v in g.items()},
            "V1": {"auc_R_abaixo_de_O": round(v1_auc, 4),
                   "ic95": [round(v1_lo, 4), round(v1_hi, 4)],
                   "p_permutacao": round(v1_p, 5), "passa": bool(v1)},
            "V2": {"mediana_G": round(st.median(g["G"]), 4),
                   "mediana_R": round(st.median(g["R"]), 4),
                   "p_permutacao": round(v2_p, 5),
                   "auc_R_abaixo_de_G": round(auc(g["R"], g["G"]), 4),
                   "passa": bool(v2)},
            "V3": {"valores_distintos": len(set(vals)),
                   "fraccao_no_modal": round(modal, 4), "passa": bool(v3)},
            "V5": {"rho_n_versos": round(rho_nv, 4), "passa": bool(v5)},
        }

    # V4 — concordância
    a = [fvv_por["R1"][i] for i in ids]
    b = [fvv_por["R2"][i] for i in ids]
    v1_igual = (out["por_contador"]["R1"]["V1"]["passa"]
                == out["por_contador"]["R2"]["V1"]["passa"])
    icc_v = icc(a, b)
    out["V4"] = {
        "icc": round(icc_v, 4),
        "rho_spearman": round(spearman(a, b), 4),
        "desvio_absoluto_medio": round(float(np.abs(np.array(a) - np.array(b)).mean()), 4),
        "V1_mesmo_veredicto": bool(v1_igual),
        "passa": bool(icc_v >= ICC_MIN and v1_igual),
    }

    todos = {g: all(out["por_contador"][r][g]["passa"] for r in CONTADORES)
             for g in ("V1", "V2", "V3", "V5")}
    todos["V4"] = out["V4"]["passa"]
    out["veredicto"] = {"portoes": todos, "instrumento_aceite": all(todos.values())}
    out["fvv_por_item"] = {i: {"grupo": grupo[i],
                               "R1": round(fvv_por["R1"][i], 4),
                               "R2": round(fvv_por["R2"][i], 4)} for i in ids}

    with open(os.path.join(AQUI, "03-resultados.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print("Fase 5D — portões (§5)\n")
    for nome, r in out["por_contador"].items():
        print(f"=== {nome} ===  medianas R={r['medianas']['R']:.3f} "
              f"O={r['medianas']['O']:.3f} G={r['medianas']['G']:.3f}")
        print(f"  V1 AUC(R<O)={r['V1']['auc_R_abaixo_de_O']:.3f} "
              f"IC95={r['V1']['ic95']} p={r['V1']['p_permutacao']:.4f}  "
              f"{'PASSA' if r['V1']['passa'] else 'FALHA'}")
        print(f"  V2 G>R? med {r['V2']['mediana_G']:.3f} vs {r['V2']['mediana_R']:.3f} "
              f"p={r['V2']['p_permutacao']:.4f} AUC(R<G)={r['V2']['auc_R_abaixo_de_G']:.3f}  "
              f"{'PASSA' if r['V2']['passa'] else 'FALHA'}")
        print(f"  V3 {r['V3']['valores_distintos']} valores, "
              f"{r['V3']['fraccao_no_modal']:.1%} no modal  "
              f"{'PASSA' if r['V3']['passa'] else 'FALHA'}")
        print(f"  V5 ρ(n.º versos)={r['V5']['rho_n_versos']:+.3f}  "
              f"{'PASSA' if r['V5']['passa'] else 'FALHA'}\n")
    v4 = out["V4"]
    print(f"=== V4 concordância === ICC={v4['icc']:.3f}  ρ={v4['rho_spearman']:+.3f}  "
          f"|Δ| médio={v4['desvio_absoluto_medio']:.3f}  "
          f"V1 mesmo veredicto={v4['V1_mesmo_veredicto']}  "
          f"{'PASSA' if v4['passa'] else 'FALHA'}")
    print(f"\nVEREDICTO: {out['veredicto']['portoes']}")
    print(f"instrumento aceite: {out['veredicto']['instrumento_aceite']}")


if __name__ == "__main__":
    main()
