#!/usr/bin/env python
"""Fase 5U / A7 — análise de sensibilidade, **posterior e declarada**.

Protocolo: [`../FASE-5U.md`](../FASE-5U.md) §4.3.

## O que a motivou, e é uma linha de um texto ablado

Ao ler as amostras do braço A para verificar que continuavam em português
europeu, encontrei esta:

    Em cada instante te vejo a ti mesma.

O detector da [5T](../FASE-5T-RELATORIO.md) **não a marca**, e a razão é a regra
de atracção: «Em» é preposição, está na mesma oração, logo licencia. Mas **uma
preposição só atrai no infinitivo preposicionado** — «para se ver», «sem me
dizer» — e não em geral. A regra de atracção da 5T é, nesse ponto, **permissiva
de mais**.

## As duas réguas, e porque as duas vão ao relatório

| | preposição licencia |
|---|---|
| **permissiva** — a da 5T, pré-registada nesta fase | em **qualquer** ponto anterior da oração |
| **estrita** — esta, posterior | só **adjacente** ao pronome |

Os outros atractores — negação, subordinação, advérbios de foco — continuam a
licenciar **à distância** nas duas, porque aí a atracção é real.

**A régua estrita é a melhor gramática e marca defeitos verdadeiros**: «pedra
**me** dói», «cigarro **me** bate», «tu **me** deixas». A permissiva é a que
estava pré-registada. O resultado que vale é **o que as duas partilham**.

## E uma segunda leitura, que a primeira passagem não tinha

A contagem total de clíticos — próclise **mais** ênclise — difere entre braços.
O bloco de língua traz **três exemplos com clítico** («dói-me», «estende-se»,
«chama-a»), e exemplos escorvam. Se o bloco aumenta o uso de pronomes clíticos,
aumenta também a exposição ao erro, e isso é um efeito **com sinal próprio** que
nenhum dos portões do §3 previu.

Escreve `03-sensibilidade.json`.
"""
from __future__ import annotations

import json
import os
import random
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "docs", "fase-5t"))

from detectar import (LICENCIADORES, PRONOMES, _RE_TOKEN,   # noqa: E402
                      wilson)
from atraccao import FORTE, _e_infinitivo                   # noqa: E402
from src.corpus.models import Lang                          # noqa: E402
from src.corpus.parse import parse_corpus                   # noqa: E402

SEMENTE = 20261008
N_REAMOSTRAS = 4000
#: §3 U1' do protocolo.
LIMIAR_U1_LINHA = 0.15

#: As preposicoes, que na regua estrita licenciam **so adjacentes**.
PREPOSICOES = frozenset((
    "a de em por para com sem sobre sob entre até ate ante após apos contra "
    "desde perante trás tras ao à aos às do da dos das no na nos nas pelo "
    "pela pelos pelas num numa nuns numas dum duma duns dumas pra").split())
#: Os atractores que licenciam A DISTANCIA: negacao, subordinacao, foco.
ATRACTORES = LICENCIADORES - PREPOSICOES

_RE_ENCLISE = re.compile(r"[a-zà-ÿ]-(?:lhes|lhe|me|te)\b", re.I)


def proclise_estrita(texto: str) -> list[str]:
    toks = _RE_TOKEN.findall(" ".join(texto.split("\n")).lower())
    out: list[str] = []
    inicio = 0
    for i, t in enumerate(toks):
        if t and t[0] in FORTE:
            inicio = i + 1
            continue
        if t not in PRONOMES:
            continue
        seg = toks[i + 1] if i + 1 < len(toks) else ""
        ant = toks[i - 1] if i else None
        if _e_infinitivo(seg):
            continue
        if ant in PREPOSICOES:          # «para se ver»: adjacente
            continue
        if any(x in ATRACTORES for x in toks[inicio:i]):
            continue
        out.append(f"{ant or '^'} [{t}] {seg}".strip())
    return out


def conta(texto: str) -> tuple[int, int]:
    return len(proclise_estrita(texto)), len(_RE_ENCLISE.findall(texto))


def ic_emparelhado(grupos: dict, estat) -> dict:
    chaves = sorted(grupos)
    rng = random.Random(SEMENTE)
    a = estat([x for k in chaves for x in grupos[k]["A"]])
    c = estat([x for k in chaves for x in grupos[k]["C"]])
    if a is None or c is None:
        return {"A": a, "C": c, "diferenca": None}
    am = []
    for _ in range(N_REAMOSTRAS):
        esc = [chaves[rng.randrange(len(chaves))] for _ in chaves]
        va = estat([x for k in esc for x in grupos[k]["A"]])
        vc = estat([x for k in esc for x in grupos[k]["C"]])
        if va is not None and vc is not None:
            am.append(va - vc)
    am.sort()
    lo, hi = am[int(0.025 * len(am))], am[int(0.975 * len(am)) - 1]
    return {"A": round(a, 4), "C": round(c, 4), "diferenca": round(a - c, 4),
            "ic95": [round(lo, 4), round(hi, 4)],
            "exclui_zero": lo > 0 or hi < 0, "n_agrupamentos": len(chaves)}


def main() -> None:
    cru = [json.loads(l) for l in
           open(os.path.join(AQUI, "01-cru.jsonl"), encoding="utf-8")
           if l.strip()]
    for d in cru:
        p, e = conta(d["texto_cru"])
        d["pro"], d["enc"] = p, e
        d["ex"] = proclise_estrita(d["texto_cru"])

    grupos: dict = {}
    for d in cru:
        grupos.setdefault((d["voz"], d["pergunta_id"]),
                          {"C": [], "A": []})[d["braco"]].append(d)
    grupos = {k: v for k, v in grupos.items() if v["C"] and v["A"]}

    def prop(xs):
        p = sum(x["pro"] for x in xs)
        e = sum(x["enc"] for x in xs)
        return p / (p + e) if p + e else None

    def cliticos_por_item(xs):
        return sum(x["pro"] + x["enc"] for x in xs) / len(xs) if xs else None

    def frac_marcados(xs):
        return sum(1 for x in xs if x["pro"]) / len(xs) if xs else None

    # ---- o nulo: o corpus, a mesma regua estrita ---------------------- #
    poemas = [p for p in parse_corpus(os.path.join(RAIZ, "data/pessoa_poems"))
              if p.language is Lang.PT]
    cp = sum(len(proclise_estrita(p.body)) for p in poemas)
    ce = sum(len(_RE_ENCLISE.findall(p.body)) for p in poemas)
    cm = sum(1 for p in poemas if proclise_estrita(p.body))

    res = {}
    for b in ("C", "A"):
        s = [d for d in cru if d["braco"] == b]
        p = sum(d["pro"] for d in s)
        e = sum(d["enc"] for d in s)
        lo, hi = wilson(p, p + e)
        res[b] = {"n": len(s), "proclise": p, "enclise": e,
                  "cliticos": p + e, "proporcao": round(p / (p + e), 4),
                  "wilson95": [round(lo, 4), round(hi, 4)],
                  "itens_marcados": sum(1 for d in s if d["pro"]),
                  "exemplos": [x for d in s for x in d["ex"]]}

    out = {"_meta": {"protocolo": "docs/FASE-5U.md §4.3",
                     "analise": "SENSIBILIDADE, posterior e declarada",
                     "motivada_por": "«Em cada instante te vejo a ti mesma» — "
                                     "a regua da 5T nao a marca porque «Em» e "
                                     "preposicao e licencia a distancia",
                     "diferenca": "preposicao licencia SO adjacente; os outros "
                                  "atractores continuam a licenciar a distancia",
                     "reamostras": N_REAMOSTRAS, "semente": SEMENTE},
           "nulo_corpus_regua_estrita": {
               "poemas_marcados": cm, "n_poemas": len(poemas),
               "taxa_por_poema": round(cm / len(poemas), 4),
               "proclise": cp, "enclise": ce,
               "proporcao": round(cp / (cp + ce), 4)},
           "por_braco": {b: {k: v for k, v in res[b].items()
                             if k != "exemplos"} for b in res},
           "U1_regua_estrita": ic_emparelhado(grupos, prop),
           "U1_por_itens": ic_emparelhado(grupos, frac_marcados),
           "U1_linha_regua_estrita": {
               "limiar": LIMIAR_U1_LINHA,
               "A": res["A"]["proporcao"],
               "wilson_sup_A": res["A"]["wilson95"][1],
               "exclui_sistematico": res["A"]["wilson95"][1] < LIMIAR_U1_LINHA},
           "cliticos_por_item": ic_emparelhado(grupos, cliticos_por_item),
           "exemplos_C": res["C"]["exemplos"], "exemplos_A": res["A"]["exemplos"]}
    with open(os.path.join(AQUI, "03-sensibilidade.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    n = out["nulo_corpus_regua_estrita"]
    print(f"nulo (corpus, régua estrita): {n['poemas_marcados']}/{n['n_poemas']}"
          f" = {n['taxa_por_poema']:.2%} dos poemas   proporção "
          f"{n['proporcao']:.4f}")
    print(f"\n{'braço':6s} {'n':>3s} {'pró':>4s} {'ênc':>4s} {'clít':>5s} "
          f"{'prop':>7s}  Wilson95          itens")
    for b in ("C", "A"):
        r = res[b]
        print(f"{b:6s} {r['n']:3d} {r['proclise']:4d} {r['enclise']:4d} "
              f"{r['cliticos']:5d} {r['proporcao']:7.4f}  "
              f"[{r['wilson95'][0]:.4f}, {r['wilson95'][1]:.4f}]  "
              f"{r['itens_marcados']:2d}/{r['n']}")
    print(f"\nU1 (proporção, régua estrita): {out['U1_regua_estrita']}")
    print(f"U1 (fracção de itens):         {out['U1_por_itens']}")
    print(f"U1′ («sistemático»): sup de Wilson de A = "
          f"{out['U1_linha_regua_estrita']['wilson_sup_A']:.4f} contra "
          f"{LIMIAR_U1_LINHA} -> exclui = "
          f"{out['U1_linha_regua_estrita']['exclui_sistematico']}")
    print(f"\nclíticos por item (o efeito de escorva): "
          f"{out['cliticos_por_item']}")
    print(f"\npróclise no braço C: {out['exemplos_C']}")
    print(f"próclise no braço A: {out['exemplos_A']}")
    print(f"\n-> {os.path.join(AQUI, '03-sensibilidade.json')}")


if __name__ == "__main__":
    main()
