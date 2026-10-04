#!/usr/bin/env python
"""Fase 5C — o FAS: derivação da lista, validação retida, e os portões.

Protocolo em [`../FASE-5C.md`](../FASE-5C.md), commitado **antes** de este
ficheiro produzir qualquer número de validação.

**FAS(texto)** = fracção de versos não vazios que contêm ≥ 1 termo de uma lista
de 40 palavras **depletadas no Caeiro real**, derivada por log-odds contra os
poemas portugueses das outras três vozes.

## A retenção, que é o ponto desta fase

A AUC de 0,809 do piloto é **in-sample**: a lista foi derivada dos mesmos poemas
que depois separou. Aqui os 78 poemas limpos de Caeiro — limpos = nunca
recuperados para as perguntas da Fase 5B — partem-se **39/39** por semente fixa,
e o contraste também. A lista deriva-se **só** da metade de derivação, e a AUC
mede-se **só** na metade retida.

## Porque é que o inglês sai

A regra 1 do §2.1 do protocolo restringe o contraste ao português, e não é um
detalhe: com todo o corpus, as 20 primeiras palavras da lista eram `the`, `and`,
`of`, `i`, `that`… O Caeiro não tem um poema em inglês, logo toda palavra
inglesa é maximamente depletada nele, e a lista mediria língua em vez de
poética.
"""
from __future__ import annotations

import collections
import json
import math
import os
import random
import re
import statistics as st
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(AQUI, "..", "..")))

from src.corpus.build import load

#: §2.1 do protocolo.
TOKEN = re.compile(r"[a-zà-ÿ]{3,}")
MIN_OCORRENCIAS = 8
N_LISTA = 40

#: §3. Partição e estatística.
SEMENTE = 3
B_BOOT = 10000
N_PERM = 10000

#: §3, portões.
AUC_MIN = 0.70
RHO_CONVERGENTE_MAX = -0.25
RHO_ESPECIFICIDADE_MAX = 0.35

VOZES_CONTRASTE = ("ortonimo", "campos", "reis")


def toks(texto: str) -> list[str]:
    return TOKEN.findall(texto.lower())


def versos(texto: str) -> list[str]:
    return [l for l in texto.splitlines() if l.strip()]


def derivar_lista(caeiro: list[str], contraste: list[str],
                  n: int = N_LISTA) -> list[tuple[str, float, int, int]]:
    """As `n` palavras de log-odds mais alto: depletadas no Caeiro.

    `log(p_outros / p_caeiro)` com suavização de Laplace sobre os candidatos.
    Positivo = o Caeiro real evita a palavra.
    """
    fc = collections.Counter(w for t in caeiro for w in toks(t))
    fo = collections.Counter(w for t in contraste for w in toks(t))
    nc, no = sum(fc.values()), sum(fo.values())
    cand = [w for w in set(fc) | set(fo)
            if fc[w] + fo[w] >= MIN_OCORRENCIAS]
    k = len(cand)

    def lo(w: str) -> float:
        pc = (fc[w] + 0.5) / (nc + 0.5 * k)
        po = (fo[w] + 0.5) / (no + 0.5 * k)
        return math.log(po / pc)

    cand.sort(key=lo, reverse=True)
    return [(w, round(lo(w), 3), fc[w], fo[w]) for w in cand[:n]]


def fas(texto: str, lista: set[str]) -> float | None:
    vs = versos(texto)
    if not vs:
        return None
    return sum(1 for v in vs if lista & set(toks(v))) / len(vs)


def auc(baixos: list[float], altos: list[float]) -> float:
    """P(x de `baixos` < y de `altos`), empates a meio. Mann-Whitney / n1·n2."""
    a = np.asarray(baixos)[:, None]
    b = np.asarray(altos)[None, :]
    return float(((a < b).sum() + 0.5 * (a == b).sum()) / (a.size * b.size))


def auc_ic(baixos: list[float], altos: list[float]) -> tuple[float, float]:
    rng = np.random.default_rng(SEMENTE)
    a, b = np.asarray(baixos), np.asarray(altos)
    vals = []
    for _ in range(1000):
        va = a[rng.integers(0, len(a), len(a))]
        vb = b[rng.integers(0, len(b), len(b))]
        vals.append(auc(list(va), list(vb)))
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def perm_p(baixos: list[float], altos: list[float]) -> float:
    """p bilateral por permutação da diferença de médias."""
    rng = np.random.default_rng(SEMENTE)
    a, b = np.asarray(baixos), np.asarray(altos)
    obs = abs(a.mean() - b.mean())
    junto = np.concatenate([a, b])
    n = len(a)
    cnt = 0
    for _ in range(N_PERM):
        rng.shuffle(junto)
        if abs(junto[:n].mean() - junto[n:].mean()) >= obs:
            cnt += 1
    return (cnt + 1) / (N_PERM + 1)


def postos(x: list[float]) -> np.ndarray:
    """Postos médios, para o ρ de Spearman com empates."""
    a = np.asarray(x, dtype=float)
    ordem = a.argsort()
    r = np.empty(len(a), dtype=float)
    r[ordem] = np.arange(len(a), dtype=float)
    # média dos postos nos empates
    for v in np.unique(a):
        m = a == v
        if m.sum() > 1:
            r[m] = r[m].mean()
    return r


def spearman(x: list[float], y: list[float]) -> float:
    rx, ry = postos(x), postos(y)
    if rx.std() == 0 or ry.std() == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def main() -> None:
    meta, chunks = load()
    poemas: dict[str, object] = {}
    for c in chunks:
        poemas.setdefault(c.poem_id, c)
    voz = lambda p: getattr(p.voice, "value", str(p.voice))
    lng = lambda p: getattr(p.language, "value", str(p.language))

    chave = json.load(open(os.path.join(AQUI, "..", "fase-5b",
                                        "01-chave.json")))["chave"]
    contaminados: set[str] = set()
    for d in chave:
        contaminados.update(d["recuperados"])

    cae = sorted((p for p in poemas.values()
                  if voz(p) == "caeiro" and p.poem_id not in contaminados),
                 key=lambda p: p.poem_id)
    out = sorted((p for p in poemas.values()
                  if voz(p) in VOZES_CONTRASTE and lng(p) == "pt"),
                 key=lambda p: p.poem_id)
    orto = [p for p in out if voz(p) == "ortonimo"]
    print(f"Caeiro limpos: {len(cae)} (de 119; {len(contaminados & {p.poem_id for p in poemas.values() if voz(p)=='caeiro'})} contaminados)")
    print(f"contraste PT: {len(out)}  (ortónimo {len(orto)})\n")

    # --- B1: partição 39/39, semente fixa ---------------------------
    rng = random.Random(SEMENTE)
    ic = list(range(len(cae)))
    io = list(range(len(out)))
    rng.shuffle(ic)
    rng.shuffle(io)
    cae_der = [cae[i] for i in ic[: len(cae) // 2]]
    cae_ret = [cae[i] for i in ic[len(cae) // 2:]]
    out_der = [out[i] for i in io[: len(out) // 2]]
    out_ret = [out[i] for i in io[len(out) // 2:]]
    print(f"B1  derivação: {len(cae_der)} Caeiro · {len(out_der)} contraste")
    print(f"    retidos  : {len(cae_ret)} Caeiro · {len(out_ret)} contraste\n")

    # --- B2: a lista, só da metade de derivação ---------------------
    tabela = derivar_lista([p.text for p in cae_der], [p.text for p in out_der])
    lista = {w for w, *_ in tabela}
    print("B2  lista de 40 (log-odds, derivação só):")
    print("   ", ", ".join(w for w, *_ in tabela), "\n")

    # --- C1: V1, AUC retida ----------------------------------------
    a_ret = [x for x in (fas(p.text, lista) for p in cae_ret) if x is not None]
    b_ret = [x for x in (fas(p.text, lista) for p in out_ret) if x is not None]
    v1_auc = auc(a_ret, b_ret)
    v1_lo, v1_hi = auc_ic(a_ret, b_ret)
    v1_p = perm_p(a_ret, b_ret)
    v1 = v1_auc >= AUC_MIN and v1_p <= 0.05
    print(f"C1  V1 retido: AUC={v1_auc:.3f} IC95=[{v1_lo:.3f}, {v1_hi:.3f}] "
          f"p_perm={v1_p:.4f}")
    print(f"    Caeiro retido mediana={st.median(a_ret):.3f} media={st.mean(a_ret):.3f}")
    print(f"    contraste     mediana={st.median(b_ret):.3f} media={st.mean(b_ret):.3f}")
    print(f"    V1 {'PASSA' if v1 else 'FALHA'} (exige AUC>={AUC_MIN} e p<=0,05)\n")

    # in-sample, para mostrar a inflação que a retenção corrige
    a_in = [x for x in (fas(p.text, lista) for p in cae_der) if x is not None]
    b_in = [x for x in (fas(p.text, lista) for p in out_der) if x is not None]
    print(f"    (in-sample, para comparar: AUC={auc(a_in, b_in):.3f})\n")

    # --- C2/C3: V3 e V4 nas 60 amostras da 5B ----------------------
    r1 = json.load(open(os.path.join(AQUI, "..", "fase-5b",
                                     "02-pontuacoes.json")))["pontuacoes"]
    r2 = json.load(open(os.path.join(AQUI, "..", "fase-5b",
                                     "02-pontuacoes-r2.json")))["pontuacoes"]
    ger = {d["id"]: d for d in chave}
    ids = sorted(ger)
    f_ger = [fas(ger[i]["texto"], lista) for i in ids]
    assert all(x is not None for x in f_ger)
    n_versos = [len(versos(ger[i]["texto"])) for i in ids]

    rho = {}
    for nome, p in (("R1", r1), ("R2", r2)):
        rho[nome] = spearman(f_ger, [p[i]["c3a_poetica"] for i in ids])
    v3 = all(r <= RHO_CONVERGENTE_MAX for r in rho.values())
    rho_len = spearman(f_ger, [float(x) for x in n_versos])
    v4 = abs(rho_len) <= RHO_ESPECIFICIDADE_MAX
    print(f"C2  V3 convergente: ρ(FAS, 3a) R1={rho['R1']:+.3f}  R2={rho['R2']:+.3f}")
    print(f"    V3 {'PASSA' if v3 else 'FALHA'} (exige ρ<={RHO_CONVERGENTE_MAX} nos dois)")
    print(f"C3  V4 especificidade: ρ(FAS, n.º de versos)={rho_len:+.3f}")
    print(f"    V4 {'PASSA' if v4 else 'FALHA'} (exige |ρ|<={RHO_ESPECIFICIDADE_MAX})\n")

    # resolução, propriedade declarada (§3.1) — não é portão
    q = sorted(f_ger)
    resolucao = {
        "valores_distintos": len(set(f_ger)),
        "mediana": round(st.median(f_ger), 4),
        "media": round(st.mean(f_ger), 4),
        "iqr": [round(q[len(q) // 4], 4), round(q[3 * len(q) // 4], 4)],
        "max": round(max(f_ger), 4),
        "zeros": sum(1 for x in f_ger if x == 0),
    }
    print(f"    resolução nas 60 geradas (não é portão): "
          f"{resolucao['valores_distintos']} valores, "
          f"{resolucao['zeros']}/60 a zero, máx {resolucao['max']}")

    # --- D1: variante de contraste só-ortónimo, sem portão ----------
    orto_der = [p for p in out_der if voz(p) == "ortonimo"]
    orto_ret = [p for p in out_ret if voz(p) == "ortonimo"]
    tab_o = derivar_lista([p.text for p in cae_der], [p.text for p in orto_der])
    lista_o = {w for w, *_ in tab_o}
    ao = [x for x in (fas(p.text, lista_o) for p in cae_ret) if x is not None]
    bo = [x for x in (fas(p.text, lista_o) for p in orto_ret) if x is not None]
    auc_o = auc(ao, bo)
    rho_o = {n: spearman([fas(ger[i]["texto"], lista_o) for i in ids],
                         [p[i]["c3a_poetica"] for i in ids])
             for n, p in (("R1", r1), ("R2", r2))}
    print(f"\nD1  variante só-ortónimo: AUC retida={auc_o:.3f}  "
          f"ρ(3a) R1={rho_o['R1']:+.3f} R2={rho_o['R2']:+.3f}")
    print(f"    sobreposição das duas listas: "
          f"{len(lista & lista_o)}/40 palavras")

    # --- E1: EXPLORATÓRIO. Não decide H5B (§7 do protocolo) ---------
    pares: dict[tuple[str, int], dict[str, float]] = {}
    for i in ids:
        d = ger[i]
        pares.setdefault((d["pergunta_id"], d["repeticao"]), {})[d["braco"]] = \
            fas(d["texto"], lista)
    completos = {k: v for k, v in pares.items() if {"C", "P"} <= set(v)}
    assert len(completos) == 30
    ks = sorted(completos)
    cc = np.array([completos[k]["C"] for k in ks])
    pp = np.array([completos[k]["P"] for k in ks])
    dd = pp - cc
    rngb = np.random.default_rng(SEMENTE)
    ix = rngb.integers(0, len(dd), size=(B_BOOT, len(dd)))
    medias = dd[ix].mean(axis=1)
    e1 = {
        "mediana_C": round(float(np.median(cc)), 4),
        "mediana_P": round(float(np.median(pp)), 4),
        "media_C": round(float(cc.mean()), 4),
        "media_P": round(float(pp.mean()), 4),
        "delta_medio": round(float(dd.mean()), 4),
        "ic95": [round(float(np.percentile(medias, 2.5)), 4),
                 round(float(np.percentile(medias, 97.5)), 4)],
        "pro_P": int((dd < 0).sum()),   # FAS menor = melhor poética
        "pro_C": int((dd > 0).sum()),
        "empates": int((dd == 0).sum()),
        "discordantes": int((dd != 0).sum()),
        "desvio_das_diferencas": round(float(dd.std(ddof=1)), 4),
    }
    # n por braço para 80% de potência num teste t emparelhado bilateral a 0,05
    if dd.std(ddof=1) > 0 and dd.mean() != 0:
        e1["d_de_cohen"] = round(float(abs(dd.mean()) / dd.std(ddof=1)), 4)
        e1["n_pares_para_80pc"] = int(math.ceil((2.8 / e1["d_de_cohen"]) ** 2))
    print("\nE1  EXPLORATÓRIO — não decide H5B (§7 do protocolo)")
    print(f"    FAS  C={e1['media_C']:.4f}  P={e1['media_P']:.4f}  "
          f"Δ={e1['delta_medio']:+.4f}  IC95={e1['ic95']}")
    print(f"    pares a favor de P (FAS menor) / de C / empates: "
          f"{e1['pro_P']}/{e1['pro_C']}/{e1['empates']}  d={e1['discordantes']}")
    if "d_de_cohen" in e1:
        print(f"    d de Cohen={e1['d_de_cohen']:.3f}  →  "
              f"~{e1['n_pares_para_80pc']} pares para 80% de potência")

    saida = {
        "_meta": {"protocolo": "docs/FASE-5C.md", "semente": SEMENTE,
                  "bootstrap_B": B_BOOT, "permutacoes": N_PERM},
        "corpos": {"caeiro_limpos": len(cae), "contraste_pt": len(out),
                   "contaminados_excluidos": len(contaminados),
                   "derivacao": [len(cae_der), len(out_der)],
                   "retidos": [len(cae_ret), len(out_ret)]},
        "lista": [{"palavra": w, "log_odds": l, "caeiro": c, "outros": o}
                  for w, l, c, o in tabela],
        "V1": {"auc_retida": round(v1_auc, 4),
               "ic95": [round(v1_lo, 4), round(v1_hi, 4)],
               "p_permutacao": round(v1_p, 5),
               "auc_in_sample": round(auc(a_in, b_in), 4),
               "mediana_caeiro_retido": round(st.median(a_ret), 4),
               "mediana_contraste_retido": round(st.median(b_ret), 4),
               "passa": bool(v1)},
        "V3": {"rho_3a": {k: round(v, 4) for k, v in rho.items()},
               "passa": bool(v3)},
        "V4": {"rho_n_versos": round(rho_len, 4), "passa": bool(v4)},
        "resolucao_nas_geradas": resolucao,
        "D1_variante_ortonimo": {
            "auc_retida": round(auc_o, 4),
            "rho_3a": {k: round(v, 4) for k, v in rho_o.items()},
            "palavras_comuns": len(lista & lista_o),
            "lista": [w for w, *_ in tab_o]},
        "E1_exploratorio": dict(
            e1, aviso="NÃO decide H5B. Estimativa para dimensionar a Fase 5D; "
                      "ver o §7 do protocolo."),
        "fas_por_amostra": {i: round(fas(ger[i]["texto"], lista), 4) for i in ids},
    }
    with open(os.path.join(AQUI, "01-validacao.json"), "w") as f:
        json.dump(saida, f, ensure_ascii=False, indent=1)
    print("\n01-validacao.json escrito.")
    print(f"PORTÕES: V1 {'passa' if v1 else 'FALHA'} · "
          f"V3 {'passa' if v3 else 'FALHA'} · V4 {'passa' if v4 else 'FALHA'}")


if __name__ == "__main__":
    main()
