#!/usr/bin/env python
"""Fase 5N / B2–C1 — os portões. Abre a chave.

Protocolo: `../FASE-5N.md` §3. Lê `03-pontuacoes.json` e `01-chave.json` e
escreve `04-resultados.json`.

**Primário: sem os 5 pares contaminados** (§2.3 do protocolo, ids nomeados lá
antes de eu pontuar). A análise com os 30 vai como sensibilidade.

Reutiliza o `ks` da 5J e o `nulo` da 5K sem os reescrever.
"""
from __future__ import annotations

import json
import math
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
B = 10_000
#: §3 N2 — o que a 5H obteve com +5% de parametros.
DELTA_5H = 0.700
#: §2.3 — os 5 itens do braco Q cujo texto eu vi nesta sessao.
CONTAMINADOS = [("Q", "q01", 0), ("Q", "q06", 2),
                ("Q", "q07", 0), ("Q", "q07", 1), ("Q", "q07", 2)]


def binomial_bilateral(k: int, d: int) -> float:
    """p bilateral para k sucessos em d pares discordantes, p=0,5."""
    if d == 0:
        return 1.0
    c = lambda n, i: math.comb(n, i)
    cauda = sum(c(d, i) for i in range(0, min(k, d - k) + 1)) / 2 ** d
    return min(1.0, 2 * cauda)


def bootstrap_ic(difs, rng) -> list[float]:
    xs = []
    for _ in range(B):
        am = [difs[rng.randrange(len(difs))] for _ in range(len(difs))]
        xs.append(st.mean(am))
    return [round(float(np.percentile(xs, 2.5)), 4),
            round(float(np.percentile(xs, 97.5)), 4)]


def corre(pares: list[tuple[int, int]], rotulo: str, rng) -> dict:
    """pares = [(nota_Q, nota_T)]. Positivo = Q melhor."""
    difs = [q - t for q, t in pares]
    disc = [d for d in difs if d != 0]
    k = sum(1 for d in disc if d > 0)
    ic = bootstrap_ic(difs, rng) if difs else [0.0, 0.0]
    return {"rotulo": rotulo, "n_pares": len(pares),
            "media_Q": round(st.mean(q for q, _ in pares), 4),
            "media_T": round(st.mean(t for _, t in pares), 4),
            "delta_Q_menos_T": round(st.mean(difs), 4),
            "discordantes": len(disc), "a_favor_de_Q": k,
            "a_favor_de_T": len(disc) - k,
            "binomial_p": round(binomial_bilateral(k, len(disc)), 5),
            "ic95": ic, "ic_exclui_zero": ic[0] > 0 or ic[1] < 0}


def kappa_linear(a, b) -> float:
    cats = sorted(set(a) | set(b))
    n = len(a)
    if n == 0 or len(cats) < 2:
        return float("nan")
    peso = lambda x, y: 1 - abs(x - y) / (max(cats) - min(cats))
    obs = st.mean(peso(x, y) for x, y in zip(a, b))
    pa = {c: sum(1 for x in a if x == c) / n for c in cats}
    pb = {c: sum(1 for y in b if y == c) / n for c in cats}
    esp = sum(pa[x] * pb[y] * peso(x, y) for x in cats for y in cats)
    return (obs - esp) / (1 - esp) if esp < 1 else float("nan")


def main() -> None:
    pon = json.load(open(os.path.join(AQUI, "03-pontuacoes.json"),
                         encoding="utf-8"))["pontuacoes"]
    chave = json.load(open(os.path.join(AQUI, "01-chave.json"),
                           encoding="utf-8"))["chave"]
    por_id = {c["id"]: c for c in chave}

    # (braco, pergunta, repeticao) -> notas
    notas: dict[tuple[str, str, int], dict] = {}
    for sid, s in pon.items():
        c = por_id[sid]
        notas[(c["braco"], c["pergunta_id"], c["repeticao"])] = {
            "id": sid, "c3a": s["c3a"], "c3b": s["c3b"],
            "n_versos": c["n_versos"], "truncada": c["truncada"]}

    chaves_q = sorted(k for k in notas if k[0] == "Q")
    rng = random.Random(SEMENTE)

    out: dict = {"_meta": {"protocolo": "docs/FASE-5N.md §3",
                           "semente": SEMENTE, "B": B,
                           "primario": "sem os 5 pares contaminados do §2.3",
                           "contaminados": [list(c) for c in CONTAMINADOS]},
                 "3a_primo": {}, "3b": {}}

    for crit in ("c3a", "c3b"):
        rot = "3a_primo" if crit == "c3a" else "3b"
        for etiqueta, excluir in (("primario_sem_contaminados", True),
                                  ("sensibilidade_todos", False)):
            pares = []
            for (_, q, r) in chaves_q:
                if excluir and ("Q", q, r) in CONTAMINADOS:
                    continue
                if ("T", q, r) not in notas:
                    continue
                pares.append((notas[("Q", q, r)][crit],
                              notas[("T", q, r)][crit]))
            out[rot][etiqueta] = corre(pares, etiqueta, rng)

    pri = out["3a_primo"]["primario_sem_contaminados"]

    # --- N1 ----------------------------------------------------------- #
    n1 = {"binomial_p": pri["binomial_p"], "ic95": pri["ic95"],
          "delta": pri["delta_Q_menos_T"],
          "dispara": (pri["binomial_p"] <= 0.05 and pri["ic_exclui_zero"]
                      and pri["delta_Q_menos_T"] > 0)}

    # --- N2: dose-resposta -------------------------------------------- #
    n2 = {"delta_3b_para_7b": pri["delta_Q_menos_T"],
          "salto_de_capacidade": "+145% (3,1B -> 7,6B)",
          "delta_7b_para_llama8b_na_5H": DELTA_5H,
          "salto_de_capacidade_da_5H": "+5% (7,6B -> 8,0B)",
          "razao": (round(pri["delta_Q_menos_T"] / DELTA_5H, 3)
                    if DELTA_5H else None),
          "dispara": pri["delta_Q_menos_T"] < DELTA_5H}

    # --- N3 ------------------------------------------------------------ #
    n3 = {"discordantes": pri["discordantes"],
          "dispara": pri["discordantes"] < 8}

    # --- N4: forma, mecanico ------------------------------------------- #
    cont = json.load(open(os.path.join(RAIZ, "docs/fase-5j/01-contagem.json"),
                          encoding="utf-8"))
    cae = [p["versos_min3"] for p in cont["por_poema"]["caeiro"]
           if p["elegivel"] and p["lingua"] == "pt"]
    vt = [v["n_versos"] for k, v in notas.items() if k[0] == "T"]
    vq = [v["n_versos"] for k, v in notas.items() if k[0] == "Q"]
    nulo30 = nulo(cae, 30, rng, b=B)
    p95 = float(np.percentile(nulo30, 95))
    n4 = {"ks_T_ao_caeiro": round(ks(vt, cae), 4),
          "ks_Q_ao_caeiro": round(ks(vq, cae), 4),
          "p95_do_nulo_n30": round(p95, 4),
          "mediana_T": st.median(vt), "mediana_Q": st.median(vq),
          "mediana_real": st.median(cae),
          "dispara": ks(vt, cae) > ks(vq, cae)}

    # --- bonus: eu contra R1 e R2 da 5H, nos 30 itens do braco Q ------- #
    bonus: dict = {}
    for quem, ficheiro in (("R1_da_5H", "02-pontuacoes.json"),
                           ("R2_da_5H", "02-pontuacoes-r2.json")):
        caminho = os.path.join(RAIZ, "docs", "fase-5h", ficheiro)
        if not os.path.exists(caminho):
            continue
        p5h = json.load(open(caminho, encoding="utf-8"))["pontuacoes"]
        ch5h = json.load(open(os.path.join(RAIZ, "docs/fase-5h/01-chave.json"),
                              encoding="utf-8"))["chave"]
        mapa = {(c["braco"], c["pergunta_id"], c["repeticao"]): c["id"]
                for c in ch5h}
        meus, deles = [], []
        for k in chaves_q:
            hid = mapa.get(k)
            if hid and hid in p5h and "c3a" in p5h[hid]:
                meus.append(notas[k]["c3a"])
                deles.append(p5h[hid]["c3a"])
        if not meus:
            continue
        exacta = sum(1 for x, y in zip(meus, deles) if x == y) / len(meus)
        bonus[quem] = {
            "n": len(meus), "kappa_linear": round(kappa_linear(meus, deles), 4),
            "concordancia_exacta": round(exacta, 4),
            "media_minha": round(st.mean(meus), 4),
            "media_dele": round(st.mean(deles), 4),
            "discordancias_acima_de_1": sum(
                1 for x, y in zip(meus, deles) if abs(x - y) > 1)}
    out["bonus_reprodutibilidade_entre_sessoes"] = bonus
    out["N1"], out["N2"], out["N3"], out["N4"] = n1, n2, n3, n4

    caminho = os.path.join(AQUI, "04-resultados.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print("=== 3a′ — primário (sem os 5 contaminados) ===")
    for k, v in (("primário", pri),
                 ("sensibilidade (30)",
                  out["3a_primo"]["sensibilidade_todos"])):
        print(f"  {k:20s} n={v['n_pares']:2d}  média Q={v['media_Q']:.3f}  "
              f"T={v['media_T']:.3f}  Δ={v['delta_Q_menos_T']:+.3f}  "
              f"IC{v['ic95']}  d={v['discordantes']} "
              f"({v['a_favor_de_Q']} Q / {v['a_favor_de_T']} T)  "
              f"p={v['binomial_p']:.4f}")
    print("\n=== 3b (âncora nova) ===")
    v = out["3b"]["primario_sem_contaminados"]
    print(f"  média Q={v['media_Q']:.3f}  T={v['media_T']:.3f}  "
          f"Δ={v['delta_Q_menos_T']:+.3f}  IC{v['ic95']}  "
          f"p={v['binomial_p']:.4f}")

    print(f"\nN1 (capacidade tem tracção)  "
          f"{'DISPARA' if n1['dispara'] else 'nao dispara'}")
    print(f"N2 (capacidade nao explica a 5H) "
          f"{'DISPARA' if n2['dispara'] else 'nao dispara'}"
          f"   Δ(3b→7b)={n2['delta_3b_para_7b']:+.3f} com +145% "
          f"contra Δ=+0,700 da 5H com +5%"
          + (f"   razão={n2['razao']}" if n2['razao'] is not None else ""))
    print(f"N3 (inconclusivo)           "
          f"{'DISPARA' if n3['dispara'] else 'nao dispara'}  "
          f"(d={n3['discordantes']})")
    print(f"N4 (3b perde na forma)      "
          f"{'DISPARA' if n4['dispara'] else 'nao dispara'}  "
          f"KS T={n4['ks_T_ao_caeiro']:.3f} Q={n4['ks_Q_ao_caeiro']:.3f} "
          f"p95={n4['p95_do_nulo_n30']:.3f}  medianas "
          f"T={n4['mediana_T']} Q={n4['mediana_Q']} real={n4['mediana_real']}")

    print("\n=== bónus: reprodutibilidade entre sessões (3a′, braço Q) ===")
    for quem, b in bonus.items():
        print(f"  eu contra {quem:10s} n={b['n']}  κ={b['kappa_linear']:+.3f}  "
              f"exacta {b['concordancia_exacta']:.0%}  "
              f"médias {b['media_minha']:.2f} vs {b['media_dele']:.2f}  "
              f">1 ponto: {b['discordancias_acima_de_1']}")
    print(f"\n-> {caminho}")


if __name__ == "__main__":
    main()
