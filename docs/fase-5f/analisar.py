#!/usr/bin/env python
"""Fase 5F / Passo D1–D2 — os portões X1 a X3.

Protocolo em [`../FASE-5F.md`](../FASE-5F.md) §5. Corre **depois** de as duas
pontuações estarem commitadas: é este o passo que abre `01-chave.json`.

Primário na **estimativa conjunta** (média dos dois por item), que é a correcção
prescrita pela Fase 5D. Por avaliador corre em separado e **relata-se, sem
decidir**.

**Os portões correm só sobre os 24 retidos.** Os 39 poemas que eu li ao escrever
a âncora não entram em número nenhum deste ficheiro — é a lição da Fase 5C, que
viu a AUC do FAS cair de 0,869 in-sample para 0,544 retida.
"""
from __future__ import annotations

import json
import os
import statistics as st

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
SEMENTE = 3
N_PERM = 10000

#: §5 do protocolo.
AUC_MIN = 0.70
KAPPA_MIN = 0.30
CONCORDANCIA_MIN = 0.50
X1_MEDIANA_MIN = 1.0
X1_FRACCAO_DOIS_MIN = 0.30

#: Marco da âncora antiga, medido na Fase 5E em **outros** 20 poemas. Comparação
#: entre amostras, nunca dentro — lê-se como tal.
MARCO_ANTIGA = {"fraccao_de_2": 0.15, "mediana": 0.5, "n": 20,
                "fonte": "docs/FASE-5E-RELATORIO.md §2"}


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


def ic_proporcao(k: int, n: int, b=10000) -> tuple[float, float]:
    rng = np.random.default_rng(SEMENTE)
    x = np.array([1] * k + [0] * (n - k))
    v = [x[rng.integers(0, n, n)].mean() for _ in range(b)]
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

    a, b = [n1[i] for i in ids], [n2[i] for i in ids]
    k = kappa_linear(a, b)
    exacta = sum(x == y for x, y in zip(a, b)) / len(ids)
    x3 = k >= KAPPA_MIN and exacta >= CONCORDANCIA_MIN

    out: dict = {"_meta": {"protocolo": "docs/FASE-5F.md §5",
                           "permutacoes": N_PERM, "semente": SEMENTE,
                           "primario": "estimativa conjunta (média dos dois)",
                           "sem_numeros_in_sample": True,
                           "marco_ancora_antiga": MARCO_ANTIGA},
                 "X3": {"kappa_ponderado_linear": round(k, 4),
                        "concordancia_exacta": round(exacta, 4),
                        "discordancia_maxima": int(max(abs(x - y) for x, y in zip(a, b))),
                        "media_R1": round(st.mean(a), 3),
                        "media_R2": round(st.mean(b), 3),
                        "passa": bool(x3)}}

    def corre(nota: dict, etiqueta: str) -> dict:
        g = {x: [nota[i] for i in ids if grupo[i] == x] for x in "ROG"}
        x2_auc = auc(g["O"], g["R"])
        x2_lo, x2_hi = auc_ic(g["O"], g["R"])
        x2_p = perm_p(g["O"], g["R"])
        x2 = x2_auc >= AUC_MIN and x2_p <= 0.05
        med = st.median(g["R"])
        n2s = sum(1 for x in g["R"] if x == 2)
        frac = n2s / len(g["R"])
        flo, fhi = ic_proporcao(n2s, len(g["R"]))
        x1 = med >= X1_MEDIANA_MIN and frac >= X1_FRACCAO_DOIS_MIN
        return {
            "etiqueta": etiqueta,
            "n": {x: len(v) for x, v in g.items()},
            "medianas": {x: round(st.median(v), 3) for x, v in g.items()},
            "medias": {x: round(st.mean(v), 3) for x, v in g.items()},
            "distribuicao": {x: {str(v): sum(1 for y in g[x] if y == v)
                                 for v in sorted(set(g[x]))} for x in "ROG"},
            "X2": {"auc_O_abaixo_de_R": round(x2_auc, 4),
                   "ic95": [round(x2_lo, 4), round(x2_hi, 4)],
                   "p": round(x2_p, 5), "passa": bool(x2)},
            "X1": {"mediana_retidos": med, "n_com_2": n2s,
                   "de": len(g["R"]), "fraccao_de_2": round(frac, 4),
                   "ic95_fraccao": [round(flo, 4), round(fhi, 4)],
                   "passa": bool(x1)},
            "sem_portao_G": {"auc_G_abaixo_de_R": round(auc(g["G"], g["R"]), 4),
                             "p": round(perm_p(g["G"], g["R"]), 5)},
        }

    out["conjunta"] = corre(conj, "estimativa conjunta — PRIMÁRIA")
    out["por_avaliador"] = {"R1": corre(n1, "R1, sem decidir"),
                            "R2": corre(n2, "R2, sem decidir")}
    c = out["conjunta"]
    out["veredicto"] = {
        "X3_piso_de_concordancia": out["X3"]["passa"],
        "X2_discriminacao_sobrevive": c["X2"]["passa"],
        "X1_a_ancora_premeia_o_real": c["X1"]["passa"],
        "legivel": bool(out["X3"]["passa"] and c["X2"]["passa"]),
        "ancora_aceite": bool(out["X3"]["passa"] and c["X2"]["passa"]
                              and c["X1"]["passa"]),
    }
    out["notas_por_item"] = {i: {"grupo": grupo[i], "origem": chave[i]["origem"],
                                 "R1": n1[i], "R2": n2[i], "conj": conj[i]}
                             for i in ids}
    with open(os.path.join(AQUI, "03-resultados.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print("Fase 5F — portões (§5)\n")
    w = out["X3"]
    print(f"X3 piso de concordância: κ_lin={w['kappa_ponderado_linear']:.3f} "
          f"exacta={w['concordancia_exacta']:.1%} máx={w['discordancia_maxima']} "
          f"médias {w['media_R1']:.2f}/{w['media_R2']:.2f}  "
          f"{'PASSA' if w['passa'] else 'FALHA'}\n")
    for bloco in (out["conjunta"], out["por_avaliador"]["R1"],
                  out["por_avaliador"]["R2"]):
        print(f"=== {bloco['etiqueta']} ===")
        print(f"  medianas R={bloco['medianas']['R']} O={bloco['medianas']['O']} "
              f"G={bloco['medianas']['G']}   médias {bloco['medias']}")
        print(f"  distribuição {bloco['distribuicao']}")
        print(f"  X2 AUC(O<R)={bloco['X2']['auc_O_abaixo_de_R']:.3f} "
              f"IC95={bloco['X2']['ic95']} p={bloco['X2']['p']:.4f}  "
              f"{'PASSA' if bloco['X2']['passa'] else 'FALHA'}")
        print(f"  X1 mediana={bloco['X1']['mediana_retidos']} · "
              f"{bloco['X1']['n_com_2']}/{bloco['X1']['de']} com 2 "
              f"({bloco['X1']['fraccao_de_2']:.0%}, IC95 {bloco['X1']['ic95_fraccao']})  "
              f"{'PASSA' if bloco['X1']['passa'] else 'FALHA'}")
        print(f"  [sem portão] AUC(G<R)={bloco['sem_portao_G']['auc_G_abaixo_de_R']:.3f} "
              f"p={bloco['sem_portao_G']['p']:.4f}\n")
    print(f"marco da âncora antiga (5E, outros 20 poemas): "
          f"15% com 2, mediana 0,5\n")
    print(f"VEREDICTO: {out['veredicto']}")


if __name__ == "__main__":
    main()
