#!/usr/bin/env python
"""Fase 5Q / B2–C1 — os portões. Abre a chave.

Protocolo: `../FASE-5Q.md` §3. AUC(real > gerado) por braço e por voz, com o
bootstrap a reamostrar os reais **uma vez** por repetição e a aplicá-los aos dois
braços, que os partilham.

Reporta o Q1 **com e sem** os itens reais que trazem marca de reconstituição
editorial — a fuga que o §2 do commit dos juízos declarou.
"""
from __future__ import annotations

import json
import os
import random
import re
import statistics as st

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))

SEMENTE = 20261007
B = 10_000
VOZES = ("campos", "reis", "ortonimo")
LIMIAR_Q1 = 0.65

#: Marcas de reconstituicao editorial que denunciam um poema real sem ser pela
#: voz: rectos/parenteses com uma palavra ou «?», e palavras coladas ou espacos
#: duplos (artefactos de transcricao).
_RE_EDITORIAL = re.compile(r"\[[^\]]{1,30}\]|\([a-zà-ú]{1,20}\)|  |"
                           r"[a-zà-ú][A-ZÀ-Ú][a-zà-ú]")


def auc(pos, neg) -> float:
    """P(pos > neg), empates a meio. pos = reais, neg = gerados."""
    p = np.sort(np.array(pos, dtype=float))
    ng = np.array(neg, dtype=float)
    maiores = np.searchsorted(p, ng, side="right")
    iguais = maiores - np.searchsorted(p, ng, side="left")
    menores = len(p) - maiores
    return float((menores.sum() + 0.5 * iguais.sum()) / (len(p) * len(ng)))


def main() -> None:
    juizos = json.load(open(os.path.join(AQUI, "02-juizos.json"),
                            encoding="utf-8"))["juizos"]
    chave = {c["id"]: c for c in
             json.load(open(os.path.join(AQUI, "01-chave.json"),
                            encoding="utf-8"))["chave"]}

    # (voz, grupo) -> [notas]; e os reais com marca editorial a parte
    notas: dict[tuple[str, str], list[int]] = {}
    editorial: dict[str, list[int]] = {"com_marca": [], "sem_marca": []}
    reais_limpos: dict[str, list[int]] = {v: [] for v in VOZES}
    for sid, j in juizos.items():
        c = chave[sid]
        notas.setdefault((c["voz"], c["grupo"]), []).append(j["real"])
        if c["grupo"] == "R":
            marcado = bool(_RE_EDITORIAL.search(c["texto"]))
            editorial["com_marca" if marcado else "sem_marca"].append(j["real"])
            if not marcado:
                reais_limpos[c["voz"]].append(j["real"])

    rng = random.Random(SEMENTE)

    # ---------------- Q1: resolucao ------------------------------------- #
    reais_todos = [x for v in VOZES for x in notas[(v, "R")]]
    gerados_todos = [x for v in VOZES for g in ("Q", "L") for x in notas[(v, g)]]
    limpos_todos = [x for v in VOZES for x in reais_limpos[v]]
    q1 = {"auc_pooled": round(auc(reais_todos, gerados_todos), 4),
          "n_reais": len(reais_todos), "n_gerados": len(gerados_todos),
          "limiar": LIMIAR_Q1,
          "fuga_editorial": {
              "n_com_marca": len(editorial["com_marca"]),
              "n_sem_marca": len(editorial["sem_marca"]),
              "media_com_marca": (round(st.mean(editorial["com_marca"]), 3)
                                  if editorial["com_marca"] else None),
              "media_sem_marca": (round(st.mean(editorial["sem_marca"]), 3)
                                  if editorial["sem_marca"] else None),
              "auc_so_com_reais_sem_marca": (
                  round(auc(limpos_todos, gerados_todos), 4)
                  if limpos_todos else None)},
          }
    q1["dispara"] = q1["auc_pooled"] > LIMIAR_Q1

    # ---------------- Q2: a decisao ------------------------------------- #
    qw = [x for v in VOZES for x in notas[(v, "Q")]]
    ll = [x for v in VOZES for x in notas[(v, "L")]]
    a_q, a_l = auc(reais_todos, qw), auc(reais_todos, ll)
    difs = []
    for _ in range(B):
        r = [reais_todos[rng.randrange(len(reais_todos))]
             for _ in range(len(reais_todos))]
        bq = [qw[rng.randrange(len(qw))] for _ in range(len(qw))]
        bl = [ll[rng.randrange(len(ll))] for _ in range(len(ll))]
        difs.append(auc(r, bl) - auc(r, bq))
    ic = [round(float(np.percentile(difs, 2.5)), 4),
          round(float(np.percentile(difs, 97.5)), 4)]
    q2 = {"auc_real_vs_qwen": round(a_q, 4),
          "auc_real_vs_llama": round(a_l, 4),
          "delta_llama_menos_qwen": round(a_l - a_q, 4),
          "ic95_do_delta": ic, "ic_exclui_zero": ic[0] > 0 or ic[1] < 0,
          "media_qwen": round(st.mean(qw), 3), "media_llama": round(st.mean(ll), 3),
          "nota": "AUC mais BAIXA = mais perto do poeta (mais vezes tomado por real)",
          "dispara": a_l < a_q and (ic[0] > 0 or ic[1] < 0)}

    # ---------------- Q3: por voz --------------------------------------- #
    por_voz = {}
    for v in VOZES:
        aq, al = auc(notas[(v, "R")], notas[(v, "Q")]), \
                 auc(notas[(v, "R")], notas[(v, "L")])
        por_voz[v] = {"auc_qwen": round(aq, 4), "auc_llama": round(al, 4),
                      "delta": round(al - aq, 4), "llama_mais_perto": al < aq,
                      "media_qwen": round(st.mean(notas[(v, "Q")]), 3),
                      "media_llama": round(st.mean(notas[(v, "L")]), 3),
                      "media_real": round(st.mean(notas[(v, "R")]), 3)}
    n_fav = sum(1 for v in VOZES if por_voz[v]["llama_mais_perto"])
    q3 = {"por_voz": por_voz, "vozes_a_favor_do_llama": n_fav,
          "dispara": n_fav >= 2}

    q4 = {"dispara": not q2["ic_exclui_zero"],
          "leitura": "«nao se mostrou»; a prescricao e acrescentar as duas "
                     "repeticoes que a 5M tem e esta fase nao usou"}

    out = {"_meta": {"protocolo": "docs/FASE-5Q.md §3", "semente": SEMENTE,
                     "B": B},
           "Q1": q1, "Q2": q2, "Q3": q3, "Q4": q4}
    with open(os.path.join(AQUI, "03-resultados.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print("=== Q1 — o instrumento tem resolução? ===")
    print(f"  AUC(real > gerado) pooled = {q1['auc_pooled']:.3f}  "
          f"(limiar {LIMIAR_Q1})   n={q1['n_reais']} reais, "
          f"{q1['n_gerados']} gerados")
    f = q1["fuga_editorial"]
    print(f"  fuga editorial: {f['n_com_marca']} reais com marca "
          f"(média {f['media_com_marca']}) contra {f['n_sem_marca']} sem "
          f"(média {f['media_sem_marca']})")
    print(f"  AUC só com os reais SEM marca = {f['auc_so_com_reais_sem_marca']}")
    print(f"  Q1 {'DISPARA' if q1['dispara'] else 'nao dispara'}")

    print("\n=== Q2 — o llama está mais perto do poeta? ===")
    print(f"  AUC(real > qwen)  = {q2['auc_real_vs_qwen']:.3f}   "
          f"média do qwen  {q2['media_qwen']:.2f}")
    print(f"  AUC(real > llama) = {q2['auc_real_vs_llama']:.3f}   "
          f"média do llama {q2['media_llama']:.2f}")
    print(f"  Δ = {q2['delta_llama_menos_qwen']:+.3f}   IC95 {ic}   "
          f"exclui 0: {q2['ic_exclui_zero']}")
    print(f"  Q2 {'DISPARA' if q2['dispara'] else 'nao dispara'}")

    print("\n=== Q3 — e está nas três vozes? ===")
    print(f"  {'voz':10s} {'AUC qwen':>9s} {'AUC llama':>10s} {'Δ':>7s}   "
          f"{'med Q':>6s} {'med L':>6s} {'med R':>6s}")
    for v in VOZES:
        c = por_voz[v]
        print(f"  {v:10s} {c['auc_qwen']:9.3f} {c['auc_llama']:10.3f} "
              f"{c['delta']:+7.3f}   {c['media_qwen']:6.2f} "
              f"{c['media_llama']:6.2f} {c['media_real']:6.2f}"
              f"   {'llama' if c['llama_mais_perto'] else 'qwen'}")
    print(f"  a favor do llama em {n_fav} de 3   "
          f"Q3 {'DISPARA' if q3['dispara'] else 'nao dispara'}")
    print(f"\nQ4 {'DISPARA' if q4['dispara'] else 'nao dispara'}")
    print(f"\n-> {os.path.join(AQUI, '03-resultados.json')}")


if __name__ == "__main__":
    main()
