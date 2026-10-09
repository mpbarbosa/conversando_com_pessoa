#!/usr/bin/env python
"""Fase 5Y — auditoria: o que é que o mediador da repetição faz às conclusões já publicadas.

**Não há protocolo pré-registado, e a razão está declarada:** não há medição
nova, não há portão a escrever, e a pergunta nasceu dos dados — a emenda da
[5X](../FASE-5X-RELATORIO.md) descobriu que **a repetição re-recupera**, logo um
braço que repetiu tem prompt diferente de um que não repetiu.

A protecção contra escolher o resultado que me convém **não é um portão: é
cobertura**. Esta auditoria corre sobre **as nove fases emparelhadas** e reporta
**todas** as células e **todas** as conclusões que consegue recalcular, incluindo
as que sobrevivem.

## O mecanismo, para o registo

O `Pipeline._repetir_sem` ([`src/pipeline.py`](../../src/pipeline.py)) é
deliberado e está documentado: quando o modelo plagia, a repetição **tira do
contexto os poemas de que ele copiou** e deixa entrar os seguintes da
recuperação. Foi desenhado contra um ciclo observado a correr.

Consequência para uma fase emparelhada: **o prompt final diverge entre braços
sempre que os braços plagiarem de forma diferente** — e isso é *a jusante* do
tratamento. Não é um confundidor a declarar; é um **mediador**.

Escreve `01-auditoria.json`.
"""
from __future__ import annotations

import glob
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
sys.path.insert(0, os.path.join(RAIZ, "docs", "fase-5k"))

SEMENTE = 20261009
VOZES = ("caeiro", "campos", "reis", "ortonimo")


def celulas(caminho: str) -> dict:
    d = [json.loads(ln) for ln in open(caminho, encoding="utf-8") if ln.strip()]
    cel: dict = {}
    for r in d:
        k = (r.get("voz", "-"), r["pergunta_id"], r["repeticao"])
        cel.setdefault(k, {})[r["braco"]] = r
    return cel


def contaminadas(cel: dict) -> set:
    """Células em que o prompt FINAL difere entre braços."""
    return {k for k, v in cel.items()
            if len({tuple(x["usados"]) for x in v.values()}) > 1}


def ks(a, b) -> float:
    a = np.sort(np.asarray(a, float))
    b = np.sort(np.asarray(b, float))
    xs = np.union1d(a, b)
    fa = np.searchsorted(a, xs, "right") / len(a)
    fb = np.searchsorted(b, xs, "right") / len(b)
    return float(np.max(np.abs(fa - fb)))


def binomial(k: int, n: int) -> float:
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, j) for j in range(k, n + 1)) / 2 ** n)


def ic(d: list[float]) -> list[float]:
    rng = random.Random(SEMENTE)
    bs = sorted(st.mean(d[rng.randrange(len(d))] for _ in d)
                for _ in range(4000))
    return [round(bs[100], 4), round(bs[3899], 4)]


# --------------------------------------------------------------------------- #
def inventario() -> dict:
    out = {}
    for p in sorted(glob.glob(os.path.join(RAIZ, "docs/fase-*/01-cru.jsonl"))):
        fase = p.split(os.sep)[-2]
        cel = celulas(p)
        tdif = {k for k, v in cel.items()
                if len({x["tentativas"] for x in v.values()}) > 1}
        pdif = contaminadas(cel)
        out[fase] = {
            "celulas": len(cel),
            "bracos": len({b for v in cel.values() for b in v}),
            "tentativas_desiguais": len(tdif),
            "prompt_divergente": len(pdif),
            "prompt_divergente_sem_tentativas_desiguais":
                len(pdif - tdif),
            "fraccao_contaminada": round(len(pdif) / len(cel), 4),
            "nota": ("prompt divergente COM tentativas iguais: os bracos "
                     "repetiram o mesmo numero de vezes mas plagiaram poemas "
                     "DIFERENTES, logo removeram poemas diferentes"
                     if pdif - tdif else "")}
    return out


def auditar_5h() -> dict:
    """O +0,700 que decidiu o modelo em produção."""
    ch = {c["id"]: c for c in json.load(
        open(os.path.join(RAIZ, "docs/fase-5h/01-chave.json"),
             encoding="utf-8"))["chave"]}
    p1 = json.load(open(os.path.join(RAIZ, "docs/fase-5h/02-pontuacoes.json"),
                        encoding="utf-8"))["pontuacoes"]
    p2 = json.load(open(os.path.join(RAIZ,
                                     "docs/fase-5h/02-pontuacoes-r2.json"),
                        encoding="utf-8"))["pontuacoes"]
    cel: dict = {}
    for c in ch.values():
        cel.setdefault((c["pergunta_id"], c["repeticao"]), {})[c["braco"]] = c
    pdif = {k for k, v in cel.items()
            if len({tuple(x["usados"]) for x in v.values()}) > 1}

    def conj(i):
        return (p1[i]["c3a"] + p2[i]["c3a"]) / 2

    res = {"celulas_contaminadas": sorted("/".join(map(str, k))
                                          for k in pdif)}
    for nome, ks_ in (("todas", sorted(cel)),
                      ("limpas", sorted(set(cel) - pdif))):
        d = [conj(cel[k]["L"]["id"]) - conj(cel[k]["Q"]["id"])
             for k in ks_ if "Q" in cel[k] and "L" in cel[k]]
        pos = sum(1 for x in d if x > 0)
        neg = sum(1 for x in d if x < 0)
        res[nome] = {"n": len(d), "delta_medio": round(st.mean(d), 4),
                     "ic95": ic(d), "sinais_pro_L": pos, "sinais_pro_Q": neg,
                     "empates": len(d) - pos - neg,
                     "p_binomial": round(binomial(max(pos, neg), pos + neg), 5)}
    res["veredicto"] = ("SOBREVIVE" if res["limpas"]["ic95"][0] > 0
                        else "NAO SOBREVIVE")
    return res


def auditar_5m() -> dict:
    """A forma por voz, e a célula `reis/L` que era a mais citada da sequência."""
    from calibrar import nulo
    cont = json.load(open(os.path.join(RAIZ, "docs/fase-5j/01-contagem.json"),
                          encoding="utf-8"))
    reais = {v: [p["versos_min3"] for p in cont["por_poema"][v]
                 if p["elegivel"] and p["lingua"] == "pt"] for v in VOZES}
    cel = celulas(os.path.join(RAIZ, "docs/fase-5m/01-cru.jsonl"))
    pdif = contaminadas(cel)
    rng = random.Random(20261007)
    out = {"celulas_contaminadas_por_voz": {
        v: sum(1 for k in pdif if k[0] == v) for v in VOZES if any(
            k[0] == v for k in cel)}}
    for voz in ("campos", "reis", "ortonimo"):
        for br in ("Q", "L"):
            bloco = {}
            for rot, ks_ in (("todas", [k for k in cel if k[0] == voz]),
                             ("limpas", [k for k in cel
                                         if k[0] == voz and k not in pdif])):
                vs = [cel[k][br]["n_versos"] for k in sorted(ks_)
                      if br in cel[k]]
                k_ = ks(vs, reais[voz])
                p95 = float(np.percentile(nulo(reais[voz], len(vs), rng,
                                               b=2000), 95))
                bloco[rot] = {"n": len(vs), "ks": round(k_, 4),
                              "p95_do_nulo": round(p95, 4),
                              "dentro_do_nulo": k_ <= p95}
            bloco["inverte"] = (bloco["todas"]["dentro_do_nulo"]
                                != bloco["limpas"]["dentro_do_nulo"])
            out[f"{voz}/{br}"] = bloco
    return out


def main() -> None:
    inv = inventario()
    h = auditar_5h()
    m = auditar_5m()
    out = {"_meta": {
        "o_que_e": "auditoria posterior, sem protocolo pre-registado: nao ha "
                   "medicao nova nem portao a escrever, e a pergunta nasceu "
                   "dos dados (emenda da 5X)",
        "proteccao": "cobertura, nao portao: corre as nove fases emparelhadas "
                     "e reporta todas as celulas e todas as conclusoes "
                     "recalculaveis, incluindo as que sobrevivem",
        "mecanismo": "Pipeline._repetir_sem tira do contexto os poemas "
                     "plagiados; logo o prompt final diverge entre bracos "
                     "sempre que os bracos plagiarem de forma diferente",
        "semente": SEMENTE},
        "inventario": inv,
        "5H_o_delta_que_decidiu_o_modelo": h,
        "5M_a_forma_por_voz": m}
    with open(os.path.join(AQUI, "01-auditoria.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print(f"{'fase':10s} {'cél':>4s} {'br':>3s} {'tent≠':>6s} {'prompt≠':>8s} "
          f"{'%':>6s}  nota")
    for fase, b in inv.items():
        print(f"{fase:10s} {b['celulas']:4d} {b['bracos']:3d} "
              f"{b['tentativas_desiguais']:6d} {b['prompt_divergente']:8d} "
              f"{b['fraccao_contaminada']:6.1%}  "
              f"{'+' + str(b['prompt_divergente_sem_tentativas_desiguais']) + ' por plágio diferente' if b['prompt_divergente_sem_tentativas_desiguais'] else ''}")

    print("\n=== 5H — o +0,700 que decidiu o modelo em produção ===")
    for nome in ("todas", "limpas"):
        r = h[nome]
        print(f"  {nome:7s} n={r['n']:2d}  delta {r['delta_medio']:+.4f}  "
              f"IC {r['ic95']}  sinais {r['sinais_pro_L']}/{r['sinais_pro_Q']}"
              f"  p={r['p_binomial']:.5f}")
    print(f"  -> **{h['veredicto']}**")

    print("\n=== 5M — a forma por voz ===")
    print(f"{'célula':12s} {'n':>3s} {'KS':>7s} {'p95':>7s} dentro   "
          f"{'n':>3s} {'KS':>7s} {'p95':>7s} dentro   inverte?")
    for k, b in m.items():
        if "/" not in k:
            continue
        a, c = b["todas"], b["limpas"]
        print(f"{k:12s} {a['n']:3d} {a['ks']:7.4f} {a['p95_do_nulo']:7.4f} "
              f"{'SIM ':6s}   {c['n']:3d} {c['ks']:7.4f} "
              f"{c['p95_do_nulo']:7.4f} {'SIM ' if c['dentro_do_nulo'] else 'não'}"
              f"      {'**INVERTE**' if b['inverte'] else ''}"
              if a["dentro_do_nulo"] else
              f"{k:12s} {a['n']:3d} {a['ks']:7.4f} {a['p95_do_nulo']:7.4f} "
              f"{'não':6s}   {c['n']:3d} {c['ks']:7.4f} "
              f"{c['p95_do_nulo']:7.4f} {'SIM ' if c['dentro_do_nulo'] else 'não'}"
              f"      {'**INVERTE**' if b['inverte'] else ''}")
    print(f"\n-> {os.path.join(AQUI, '01-auditoria.json')}")


if __name__ == "__main__":
    main()
