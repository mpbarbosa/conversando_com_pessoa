#!/usr/bin/env python
"""Fase 5O / B2–C1 — os portões. Abre a chave.

Protocolo: `../FASE-5O.md` §3. Lê `02-pontuacoes.json` (minhas, às cegas), a
chave desta fase, e as minhas notas do braço **Q** vindas da
[5N](../FASE-5N.md), que já estavam commitadas.
"""
from __future__ import annotations

import json
import math
import os
import random
import statistics as st

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))

SEMENTE = 20261007
B = 10_000
DELTA_5H = 0.700            # §3 O2
MEDIA_R1_5F = 1.50          # §3 O3 — nos 24 reais
MEDIA_R2_5F = 1.71
FAIXA_O3 = (1.30, 1.90)


def binomial_bilateral(k: int, d: int) -> float:
    if d == 0:
        return 1.0
    cauda = sum(math.comb(d, i) for i in range(0, min(k, d - k) + 1)) / 2 ** d
    return min(1.0, 2 * cauda)


def ic_media(xs, rng) -> list[float]:
    bs = [st.mean(xs[rng.randrange(len(xs))] for _ in range(len(xs)))
          for _ in range(B)]
    return [round(float(np.percentile(bs, 2.5)), 4),
            round(float(np.percentile(bs, 97.5)), 4)]


def auc(pos, neg) -> float:
    p = np.sort(np.array(pos, dtype=float))
    ng = np.array(neg, dtype=float)
    maiores = np.searchsorted(p, ng, side="right")
    iguais = maiores - np.searchsorted(p, ng, side="left")
    menores = len(p) - maiores
    return float((menores.sum() + 0.5 * iguais.sum()) / (len(p) * len(ng)))


def main() -> None:
    rng = random.Random(SEMENTE)
    minhas = json.load(open(os.path.join(AQUI, "02-pontuacoes.json"),
                            encoding="utf-8"))["pontuacoes"]
    chave = {c["id"]: c for c in
             json.load(open(os.path.join(AQUI, "01-chave.json"),
                            encoding="utf-8"))["chave"]}

    L = {}   # origem "qNNrR" -> nota
    R = {}   # poem_id -> nota
    for sid, s in minhas.items():
        c = chave[sid]
        (L if c["grupo"] == "L" else R)[c["origem"]] = s["c3a"]
    assert len(L) == 30 and len(R) == 24, (len(L), len(R))

    # As minhas notas do braco Q, da 5N (ja commitadas, as cegas).
    pon5n = json.load(open(os.path.join(RAIZ, "docs/fase-5n/03-pontuacoes.json"),
                           encoding="utf-8"))["pontuacoes"]
    ch5n = {c["id"]: c for c in
            json.load(open(os.path.join(RAIZ, "docs/fase-5n/01-chave.json"),
                           encoding="utf-8"))["chave"]}
    Q = {f'{ch5n[s]["pergunta_id"]}r{ch5n[s]["repeticao"]}': v["c3a"]
         for s, v in pon5n.items() if ch5n[s]["braco"] == "Q"}
    assert len(Q) == 30, len(Q)

    comuns = sorted(set(L) & set(Q))
    pares = [(L[k], Q[k]) for k in comuns]
    difs = [l - q for l, q in pares]
    disc = [d for d in difs if d != 0]
    k = sum(1 for d in disc if d > 0)
    ic = ic_media(difs, rng)

    o1 = {"n_pares": len(pares), "media_L": round(st.mean(L[x] for x in comuns), 4),
          "media_Q": round(st.mean(Q[x] for x in comuns), 4),
          "delta_L_menos_Q": round(st.mean(difs), 4),
          "discordantes": len(disc), "a_favor_de_L": k,
          "a_favor_de_Q": len(disc) - k,
          "binomial_p": round(binomial_bilateral(k, len(disc)), 5),
          "ic95": ic, "ic_exclui_zero": ic[0] > 0 or ic[1] < 0}
    o1["dispara"] = (o1["delta_L_menos_Q"] > 0
                     and o1["binomial_p"] <= 0.05 and o1["ic_exclui_zero"])

    o2 = {"delta_5H": DELTA_5H, "meu_delta": o1["delta_L_menos_Q"],
          "meu_ic95": ic, "ic_contem_0_700": ic[0] <= DELTA_5H <= ic[1],
          "dispara": ic[0] <= DELTA_5H <= ic[1]}

    reais = [R[x] for x in sorted(R)]
    m_reais = st.mean(reais)
    ic_r = ic_media(reais, rng)
    o3 = {"media_minha_nos_24_reais": round(m_reais, 4), "ic95": ic_r,
          "media_R1_da_5F": MEDIA_R1_5F, "media_R2_da_5F": MEDIA_R2_5F,
          "faixa_pre_registada": list(FAIXA_O3),
          "dispara": FAIXA_O3[0] <= m_reais <= FAIXA_O3[1],
          "distribuicao": {str(n): sum(1 for x in reais if x == n)
                           for n in (0, 1, 2)}}

    com2 = sum(1 for x in reais if x == 2)
    o4 = {"mediana": st.median(reais), "com_nota_2": com2,
          "fraccao_com_2": round(com2 / len(reais), 4),
          "condicao": "mediana >= 1 e >= 30% com 2 (X1 da 5F)",
          "dispara": st.median(reais) >= 1 and com2 / len(reais) >= 0.30}

    o5 = {"discordantes": o1["discordantes"], "dispara": o1["discordantes"] < 8}

    gerados = [L[x] for x in sorted(L)]
    novo_auc = {
        "auc_real_acima_de_llama": round(auc(reais, gerados), 4),
        "nota": "numero NOVO: a 5F contrastou real contra qwen (0,851). "
                "Aqui o contraste e real contra llama, logo nao e replicacao.",
        "media_real": round(m_reais, 4),
        "media_llama": round(st.mean(gerados), 4)}

    out = {"_meta": {"protocolo": "docs/FASE-5O.md §3", "semente": SEMENTE,
                     "B": B,
                     "notas_do_Q": "vindas da 5N, as cegas, ja commitadas"},
           "O1": o1, "O2": o2, "O3": o3, "O4": o4, "O5": o5,
           "auc_real_contra_llama": novo_auc}
    with open(os.path.join(AQUI, "03-resultados.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print("=== O1 / O2 — o Δ(L − Q) nas minhas notas ===")
    print(f"  média L (llama) = {o1['media_L']:.3f}   "
          f"média Q (qwen)  = {o1['media_Q']:.3f}")
    print(f"  Δ = {o1['delta_L_menos_Q']:+.3f}   IC95 {ic}   "
          f"d={o1['discordantes']} ({o1['a_favor_de_L']} L / "
          f"{o1['a_favor_de_Q']} Q)   p={o1['binomial_p']:.4f}")
    print(f"  O1 {'DISPARA' if o1['dispara'] else 'nao dispara'}"
          f"   ·   O2 {'DISPARA' if o2['dispara'] else 'nao dispara'} "
          f"(o IC {'contém' if o2['ic_contem_0_700'] else 'NAO contém'} +0,700)")

    print("\n=== O3 — o meu nível nos 24 poemas reais ===")
    print(f"  eu = {o3['media_minha_nos_24_reais']:.3f} {ic_r}   "
          f"R1 da 5F = {MEDIA_R1_5F}   R2 da 5F = {MEDIA_R2_5F}")
    print(f"  distribuição 0/1/2: {o3['distribuicao']}")
    print(f"  O3 {'DISPARA' if o3['dispara'] else 'nao dispara'} "
          f"(faixa {FAIXA_O3})")

    print("\n=== O4 — a âncora premeia o original? (X1 da 5F) ===")
    print(f"  mediana {o4['mediana']}  com nota 2: {o4['com_nota_2']}/24 "
          f"({o4['fraccao_com_2']:.0%})   "
          f"O4 {'DISPARA' if o4['dispara'] else 'nao dispara'}")
    print(f"\nO5 {'DISPARA' if o5['dispara'] else 'nao dispara'} "
          f"(d={o5['discordantes']})")
    print(f"\n=== número novo: AUC(real > llama) = "
          f"{novo_auc['auc_real_acima_de_llama']:.3f} ===")
    print(f"  média real {novo_auc['media_real']:.3f} contra "
          f"llama {novo_auc['media_llama']:.3f}")
    print(f"\n-> {os.path.join(AQUI, '03-resultados.json')}")


if __name__ == "__main__":
    main()
