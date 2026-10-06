#!/usr/bin/env python
"""Fase 5K — chão, escala, detecção e potência para o critério de forma.

Protocolo: `docs/FASE-5K.md` §3-4. Escreve `01-nulo.json` e `03-resultados.json`.

Reutiliza o `ks` de `fase-5j/analisar.py` — o mesmo código, validado lá nos três
casos de sanidade — e as contagens de `fase-5j/01-contagem.json`.

Sem `scipy`, como desde a Fase 3B.
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

from analisar import ks                                   # noqa: E402

SEMENTE = 20261006
B_NULO = 10_000
B_AUC = 2_000
#: Grelha de potencia. O §4.3 pre-registou {10,20,30,60,120} e isto desvia-se
#: em duas coisas, declaradas: **120 sai** (nao se tira uma sub-amostra de 120
#: sem reposicao de 118 poemas, logo o nulo nao existe a esse n), e entram
#: **12, 15 e 25** porque a grelha pre-registada deixava a regiao decisiva
#: (10 -> 20, onde a potencia salta) sem resolucao. Nenhum portao depende
#: desta grelha: a potencia do §4.3 e descritiva e nao tem limiar.
NS = (10, 12, 15, 20, 25, 30, 60)
INTERVALO = (10, 20)
VOZES = ("caeiro", "campos", "reis", "ortonimo")


def carrega() -> tuple[dict, dict]:
    cont = json.load(open(os.path.join(RAIZ, "docs/fase-5j/01-contagem.json"),
                          encoding="utf-8"))
    reais = {
        v: [p["versos_min3"] for p in cont["por_poema"][v]
            if p["elegivel"] and p["lingua"] == "pt"]
        for v in VOZES
    }
    cru = [json.loads(l) for l in
           open(os.path.join(RAIZ, "docs/fase-5h/01-cru.jsonl"))]
    bracos = {
        "qwen2.5": [r for r in cru if r["braco"] == "Q"],
        "llama3.1": [r for r in cru if r["braco"] == "L"],
    }
    return reais, bracos


def conformidade(xs) -> float:
    lo, hi = INTERVALO
    return sum(1 for x in xs if lo <= x <= hi) / len(xs)


def nulo(reais: list[int], n: int, rng: random.Random,
         b: int = B_NULO) -> list[float]:
    """KS de sub-amostras reais (sem reposição) contra o corpus completo.

    Mede-se contra o corpus **inteiro**, exactamente como os braços são medidos
    na 5J — e não contra o complemento, para que a comparação seja a mesma.
    """
    out = []
    for _ in range(b):
        sub = rng.sample(reais, n)
        out.append(ks(sub, reais))
    return out


def auc(pos: list[float], neg: list[float]) -> float:
    """P(score(pos) > score(neg)), empates a meio. Positivo = «é real»."""
    p = np.sort(np.array(pos, dtype=float))
    ng = np.array(neg, dtype=float)
    maiores = np.searchsorted(p, ng, side="right")      # pos < neg
    iguais = maiores - np.searchsorted(p, ng, side="left")
    menores = len(p) - maiores
    return float((menores.sum() + 0.5 * iguais.sum()) / (len(p) * len(ng)))


def ic_bootstrap(pos, neg, rng, b=B_AUC) -> tuple[float, float]:
    xs = []
    for _ in range(b):
        rp = [pos[rng.randrange(len(pos))] for _ in range(len(pos))]
        rn = [neg[rng.randrange(len(neg))] for _ in range(len(neg))]
        xs.append(auc(rp, rn))
    a = np.array(xs)
    return (round(float(np.percentile(a, 2.5)), 4),
            round(float(np.percentile(a, 97.5)), 4))


def main() -> None:
    reais, bracos = carrega()
    cae = reais["caeiro"]
    rng = random.Random(SEMENTE)

    # ---------------- A1: o nulo empirico -------------------------------- #
    nulos = {n: nulo(cae, n, rng) for n in NS if n <= len(cae)}
    nulo_info = {
        str(n): {"n": n, "b": len(v),
                 "mediana": round(float(np.median(v)), 4),
                 "p95": round(float(np.percentile(v, 95)), 4),
                 "p99": round(float(np.percentile(v, 99)), 4)}
        for n, v in nulos.items()
    }
    with open(os.path.join(AQUI, "01-nulo.json"), "w", encoding="utf-8") as f:
        json.dump({"_meta": {"protocolo": "docs/FASE-5K.md §3.1",
                             "semente": SEMENTE,
                             "n_caeiro_real": len(cae),
                             "sem_reposicao": True}, "nulo": nulo_info},
                  f, ensure_ascii=False, indent=1)

    # ---------------- K1: resolucao a n=30 e a n=10 ---------------------- #
    k1: dict = {"nulo": nulo_info, "bracos": {}}
    for nome, rs in bracos.items():
        xs = [r["n_versos"] for r in rs]
        d30 = ks(xs, cae)
        # agrupado: 1 repeticao por pergunta, 10k vezes, KS medio
        perguntas = sorted({r["pergunta_id"] for r in rs})
        porpq = {q: [r["n_versos"] for r in rs if r["pergunta_id"] == q]
                 for q in perguntas}
        d10s = [ks([rng.choice(porpq[q]) for q in perguntas], cae)
                for _ in range(B_NULO)]
        d10 = float(np.mean(d10s))
        k1["bracos"][nome] = {
            "n": len(xs), "ks_n30": round(d30, 4),
            "acima_p95_n30": d30 > nulos[30][0] and
                             d30 > float(np.percentile(nulos[30], 95)),
            "ks_agrupado_n10_medio": round(d10, 4),
            "ks_agrupado_n10_ic95": [
                round(float(np.percentile(d10s, 2.5)), 4),
                round(float(np.percentile(d10s, 97.5)), 4)],
            "acima_p95_n10": d10 > float(np.percentile(nulos[10], 95)),
            "percentil_no_nulo_n30": round(
                100 * float(np.mean(np.array(nulos[30]) < d30)), 2),
            "percentil_no_nulo_n10": round(
                100 * float(np.mean(np.array(nulos[10]) < d10)), 2),
        }
    k1["dispara"] = all(b["acima_p95_n30"] for b in k1["bracos"].values())
    k1["dispara_agrupado"] = all(b["acima_p95_n10"]
                                 for b in k1["bracos"].values())

    # ---------------- K2: a regua entre vozes reais ---------------------- #
    k2: dict = {"entre_vozes_reais": {}, "bracos_contra_cada_voz": {},
                "n_por_voz": {v: len(reais[v]) for v in VOZES},
                "mediana_por_voz": {v: st.median(reais[v]) for v in VOZES}}
    for i, a in enumerate(VOZES):
        for b in VOZES[i + 1:]:
            k2["entre_vozes_reais"][f"{a}_vs_{b}"] = round(
                ks(reais[a], reais[b]), 4)
    # Nulo por voz a n=30: «que KS mostra uma sub-amostra GENUINA desta voz?».
    # Sem isto, «o llama esta mais perto do Reis» e uma ordenacao sem escala e
    # nao diz se ele cabe no intervalo de amostragem de alguma voz real.
    # Descritivo: o K2 nao tem limiar, logo isto nao mexe em portao nenhum.
    nulo_voz = {v: nulo(reais[v], 30, rng, b=2000) for v in VOZES}
    k2["p95_do_nulo_por_voz_n30"] = {
        v: round(float(np.percentile(nulo_voz[v], 95)), 4) for v in VOZES}

    for nome, rs in bracos.items():
        xs = [r["n_versos"] for r in rs]
        d = {v: round(ks(xs, reais[v]), 4) for v in VOZES}
        dentro = [v for v in VOZES
                  if d[v] <= float(np.percentile(nulo_voz[v], 95))]
        k2["bracos_contra_cada_voz"][nome] = {
            **d, "voz_mais_proxima": min(d, key=d.get),
            "vozes_em_cujo_intervalo_cabe": dentro,
            "cabe_em_alguma": bool(dentro)}

    # ---------------- K3/K4: deteccao ------------------------------------ #
    conf_corpus = conformidade(cae)
    pos_sub = [rng.sample(cae, 30) for _ in range(B_NULO)]
    pos = {
        "D1_conformidade_monotona": [conformidade(s) for s in pos_sub],
        "D2_conformidade_dois_lados": [-abs(conformidade(s) - conf_corpus)
                                       for s in pos_sub],
        "D3_ks": [-ks(s, cae) for s in pos_sub],
    }
    k3: dict = {"conformidade_do_corpus": round(conf_corpus, 4),
                "nota": "scores orientados a «maior = mais real»; D2 e D3 "
                        "negados porque sao distancias",
                "ressalva_dos_negativos":
                    "os negativos sao bootstrap dos MESMOS 30 ensaios, nao "
                    "novas amostras do modelo, logo variam menos do que um "
                    "braco novo variaria. Uma AUC de 1,000 mede a separacao "
                    "DESTE perfil de comprimentos, e sobrestima a separacao "
                    "de um braco fresco. O D1 invertido nao depende disto: a "
                    "inversao esta nas medianas (83% contra 39%).",
                "bracos": {}}
    for nome, rs in bracos.items():
        xs = [r["n_versos"] for r in rs]
        neg_sub = [[xs[rng.randrange(len(xs))] for _ in range(30)]
                   for _ in range(B_NULO)]
        neg = {
            "D1_conformidade_monotona": [conformidade(s) for s in neg_sub],
            "D2_conformidade_dois_lados": [-abs(conformidade(s) - conf_corpus)
                                           for s in neg_sub],
            "D3_ks": [-ks(s, cae) for s in neg_sub],
        }
        cel: dict = {}
        for det in pos:
            a = auc(pos[det], neg[det])
            cel[det] = {"auc": round(a, 4),
                        "ic95": ic_bootstrap(pos[det], neg[det], rng)}
        # Delta AUC do D3 contra o D1, com IC emparelhado
        difs = []
        for _ in range(B_AUC):
            ip = [rng.randrange(B_NULO) for _ in range(B_NULO // 10)]
            ineg = [rng.randrange(B_NULO) for _ in range(B_NULO // 10)]
            a3 = auc([pos["D3_ks"][i] for i in ip],
                     [neg["D3_ks"][i] for i in ineg])
            a1 = auc([pos["D1_conformidade_monotona"][i] for i in ip],
                     [neg["D1_conformidade_monotona"][i] for i in ineg])
            difs.append(a3 - a1)
        ic = [round(float(np.percentile(difs, 2.5)), 4),
              round(float(np.percentile(difs, 97.5)), 4)]
        cel["delta_D3_menos_D1"] = {
            "valor": round(cel["D3_ks"]["auc"]
                           - cel["D1_conformidade_monotona"]["auc"], 4),
            "ic95": ic, "exclui_zero": ic[0] > 0 or ic[1] < 0}
        cel["D1_pior_que_moeda"] = cel["D1_conformidade_monotona"]["auc"] < 0.50
        k3["bracos"][nome] = cel

    k3["dispara"] = all(
        c["D3_ks"]["auc"] > c["D1_conformidade_monotona"]["auc"]
        and c["delta_D3_menos_D1"]["exclui_zero"]
        for c in k3["bracos"].values())
    k4 = {"dispara": k3["bracos"]["qwen2.5"]["D1_pior_que_moeda"],
          "auc_D1_qwen": k3["bracos"]["qwen2.5"]
                            ["D1_conformidade_monotona"]["auc"],
          "auc_D1_llama": k3["bracos"]["llama3.1"]
                             ["D1_conformidade_monotona"]["auc"]}

    # ---------------- potencia por n ------------------------------------- #
    pot: dict = {}
    for nome, rs in bracos.items():
        xs = [r["n_versos"] for r in rs]
        linha = {}
        for n in NS:
            assert n <= len(cae), f"nulo sem reposicao impossivel a n={n}"
            if n not in nulos:
                nulos[n] = nulo(cae, n, rng, b=2000)
            lim = float(np.percentile(nulos[n], 95))
            acertos = sum(
                1 for _ in range(2000)
                if ks([xs[rng.randrange(len(xs))] for _ in range(n)], cae) > lim
            )
            linha[str(n)] = {"p95_do_nulo": round(lim, 4),
                             "potencia": round(acertos / 2000, 3)}
        pot[nome] = linha

    out = {"_meta": {"protocolo": "docs/FASE-5K.md §3-4", "semente": SEMENTE,
                     "B_nulo": B_NULO, "B_auc": B_AUC,
                     "gera_amostras": False,
                     "ks": "fase-5j/analisar.py, mesmo codigo"},
           "K1": k1, "K2": k2, "K3": k3, "K4": k4, "potencia": pot}
    out["K5"] = {"dispara": not k1["dispara"],
                 "leitura": ("a n=30 o critério não tem resolução; ver §6.2"
                             if not k1["dispara"] else
                             "o K1 passa, logo o K5 não dispara")}

    caminho = os.path.join(AQUI, "03-resultados.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    # ---------------- impressao ------------------------------------------ #
    print("=== A1 — o nulo empírico (sub-amostras reais vs corpus) ===")
    for n in sorted(nulo_info, key=int):
        v = nulo_info[n]
        print(f"  n={v['n']:3d}  mediana {v['mediana']:.3f}  "
              f"p95 {v['p95']:.3f}  p99 {v['p99']:.3f}")
    print("\n=== K1 — resolução ===")
    for nome, b in k1["bracos"].items():
        print(f"  {nome:10s} KS(n=30) {b['ks_n30']:.3f}  "
              f"-> percentil {b['percentil_no_nulo_n30']:5.1f} do nulo  "
              f"{'ACIMA' if b['acima_p95_n30'] else 'abaixo'} do p95")
        print(f"  {'':10s} KS agrupado(n=10) {b['ks_agrupado_n10_medio']:.3f} "
              f"{b['ks_agrupado_n10_ic95']}  -> percentil "
              f"{b['percentil_no_nulo_n10']:5.1f}  "
              f"{'ACIMA' if b['acima_p95_n10'] else 'abaixo'} do p95")
    print(f"  K1 {'DISPARA' if k1['dispara'] else 'nao dispara'} (n=30)   "
          f"agrupado: {'DISPARA' if k1['dispara_agrupado'] else 'nao dispara'}")

    print("\n=== K2 — a régua entre vozes reais ===")
    for par, d in k2["entre_vozes_reais"].items():
        print(f"  {par:24s} KS {d:.3f}")
    print("  medianas:", {v: float(m) for v, m in
                          k2["mediana_por_voz"].items()})
    print("  p95 do nulo por voz (n=30): " + "  ".join(
        f"{v}={k2['p95_do_nulo_por_voz_n30'][v]:.3f}" for v in VOZES))
    for nome, d in k2["bracos_contra_cada_voz"].items():
        print(f"  {nome:10s} " + "  ".join(
            f"{v}={d[v]:.3f}" for v in VOZES) +
            f"   -> mais perto de {d['voz_mais_proxima'].upper()}"
            f"   cabe em: {d['vozes_em_cujo_intervalo_cabe'] or 'NENHUMA'}")

    print("\n=== K3/K4 — detecção (positivo = é Caeiro real) ===")
    print(f"  conformidade do corpus: {k3['conformidade_do_corpus']:.0%}")
    for nome, c in k3["bracos"].items():
        print(f"  {nome}:")
        for det in ("D1_conformidade_monotona", "D2_conformidade_dois_lados",
                    "D3_ks"):
            print(f"    {det:28s} AUC {c[det]['auc']:.3f}  {c[det]['ic95']}")
        d = c["delta_D3_menos_D1"]
        print(f"    Δ(D3−D1) {d['valor']:+.3f}  IC {d['ic95']}  "
              f"exclui 0: {d['exclui_zero']}")
    print(f"  K3 {'DISPARA' if k3['dispara'] else 'nao dispara'}   "
          f"K4 {'DISPARA' if k4['dispara'] else 'nao dispara'} "
          f"(AUC D1 qwen {k4['auc_D1_qwen']:.3f})")

    print("\n=== Potência por n (detectar o desvio do braço) ===")
    print(f"  {'n':>5s}  " + "  ".join(f"{k:>12s}" for k in pot))
    for n in NS:
        print(f"  {n:5d}  " + "  ".join(
            f"{pot[k][str(n)]['potencia']:>11.0%} " for k in pot))
    print(f"\nK5 {'DISPARA' if out['K5']['dispara'] else 'nao dispara'}")
    print(f"\n-> {caminho}")


if __name__ == "__main__":
    main()
