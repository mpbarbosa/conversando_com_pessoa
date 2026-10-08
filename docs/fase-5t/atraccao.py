#!/usr/bin/env python
"""Fase 5T / A6 — a próclise por **atracção**, que é o que a gramática diz.

Protocolo: `../FASE-5T.md` §5.2. **Terceira passagem, e a correcção é posterior
aos dados** — declarada, como a do §2 da 5R.

## O que as linhas reais do corpus mostraram

Ao olhar para o que o detector do §2.1 marcou em Pessoa, três classes eram
**português europeu correcto** e o detector marcava-as por ter olhado só para o
*token* imediatamente anterior:

| linha do corpus | o detector marcou | mas |
|---|---|---|
| «Por tu **me escolheres** para **te ter** e **te amar**» | `tu [me] escolheres`, `e [te] amar` | é **infinitivo** (e infinitivo pessoal): a próclise é obrigatória |
| «Só tu, Senhor, **me dás** viver.» | `, [me] dás` | o atractor «Só» está **três *tokens* atrás**, com um vocativo pelo meio |
| «Se eu interrogasse e **me espantasse**» | `e [me] espantasse` | o «Se» governa a oração **coordenada** também |

As três têm a mesma causa: **a próclise é licenciada por atracção, e o atractor
não tem de estar colado ao pronome.** Está em qualquer ponto anterior da mesma
oração.

## A correcção, e é uma regra só

Licencia-se quando:

  **(a)** há um licenciador **em qualquer ponto anterior da mesma oração** — o
  intervalo desde a última pontuação **forte** (`.` `;` `!` `?` `:` `—`); a
  vírgula **não** fecha oração, logo não interrompe a atracção;
  **(b)** ou o *token* seguinte é um **infinitivo** (`-ar/-er/-ir/-or` e as
  formas do infinitivo pessoal).

Isto subsume as três classes com uma regra de gramática, e **não tem constante
nenhuma ajustada aos dados**. Afrouxa o detector, logo baixa a taxa nos **dois**
lados — no corpus e nos gerados. Se o T1 passar a disparar, a verdade é que a
primeira passagem estava errada e o relatório di-lo assim.

Escreve `03-atraccao.json`.
"""
from __future__ import annotations

import json
import os
import random
import re
import sys
from collections import Counter

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)
sys.path.insert(0, AQUI)

from detectar import (LICENCIADORES, LIMIAR_T1, NIVEL_REJEICAO,  # noqa: E402
                      PRONOMES, _RE_TOKEN, wilson)
from corrigir import _RE_ENCLISE                                 # noqa: E402
from src.corpus.models import Lang                               # noqa: E402
from src.corpus.parse import parse_corpus                        # noqa: E402

SEMENTE = 20261008
#: Pontuacao que **fecha oracao**. A virgula nao esta aqui: nao interrompe a
#: atraccao, e e por isso que «So tu, Senhor, me das» e correcto.
FORTE = frozenset(".;!?:—–")
#: (b) — terminacoes de infinitivo, incluindo o infinitivo pessoal.
_INF = ("ar", "er", "ir", "or", "ares", "eres", "ires", "armos", "ermos",
        "irmos", "arem", "erem", "irem")


def _e_infinitivo(t: str) -> bool:
    return len(t) >= 3 and t.endswith(_INF)


def proclise_por_atraccao(texto: str) -> list[str]:
    """Próclise **não** licenciada por atracção nem por infinitivo."""
    toks = _RE_TOKEN.findall(" ".join(texto.split("\n")).lower())
    out: list[str] = []
    inicio = 0                      # inicio da oracao corrente
    for i, t in enumerate(toks):
        if t and t[0] in FORTE:
            inicio = i + 1
            continue
        if t not in PRONOMES:
            continue
        seg = toks[i + 1] if i + 1 < len(toks) else ""
        # (b) infinitivo seguinte
        if _e_infinitivo(seg):
            continue
        # (a) atractor em qualquer ponto anterior da MESMA oracao
        if any(x in LICENCIADORES for x in toks[inicio:i]):
            continue
        ant = toks[i - 1] if i else None
        out.append(f"{ant or '^'} [{t}] {seg}".strip())
    return out


def conta(texto: str) -> tuple[int, int]:
    return len(proclise_por_atraccao(texto)), len(_RE_ENCLISE.findall(texto))


def proporcao(textos: list[str]) -> dict:
    pares = [conta(t) for t in textos]
    pro = sum(p for p, _ in pares)
    enc = sum(e for _, e in pares)
    tot = pro + enc
    rng = random.Random(SEMENTE)
    uteis = [(p, e) for p, e in pares if p + e]
    re_ = []
    for _ in range(2000):
        am = [uteis[rng.randrange(len(uteis))] for _ in range(len(uteis))]
        sp, se = sum(p for p, _ in am), sum(e for _, e in am)
        if sp + se:
            re_.append(sp / (sp + se))
    re_.sort()
    return {"n_itens": len(textos), "itens_marcados":
            sum(1 for p, _ in pares if p),
            "taxa_por_item": round(sum(1 for p, _ in pares if p) / len(textos),
                                   5) if textos else None,
            "proclise": pro, "enclise": enc,
            "proporcao": round(pro / tot, 4) if tot else None,
            "bootstrap95_itens": [round(re_[49], 4), round(re_[1949], 4)]
            if len(re_) == 2000 else None}


def main() -> None:
    poemas = [p for p in parse_corpus(os.path.join(RAIZ, "data/pessoa_poems"))
              if p.language is Lang.PT]
    chave = json.load(open(os.path.join(RAIZ, "docs/fase-5q/01-chave.json"),
                           encoding="utf-8"))["chave"]
    ger = [c for c in chave if c["grupo"] != "R"]
    rea = [c for c in chave if c["grupo"] == "R"]
    cru5m = [json.loads(l) for l in
             open(os.path.join(RAIZ, "docs/fase-5m/01-cru.jsonl"),
                  encoding="utf-8")]

    conj = {"corpus_pt": proporcao([p.body for p in poemas]),
            "reais_5q": proporcao([c["texto"] for c in rea]),
            "gerados_5q": proporcao([c["texto"] for c in ger]),
            "gerados_5m": proporcao([x["texto"] for x in cru5m])}
    for m in sorted({c["modelo"] for c in ger}):
        conj[f"gerados_5q::{m}"] = proporcao(
            [c["texto"] for c in ger if c["modelo"] == m])

    cp = conj["corpus_pt"]
    t1 = cp["taxa_por_item"] < LIMIAR_T1
    gq = conj["gerados_5q"]
    lo, _ = wilson(gq["itens_marcados"], gq["n_itens"])
    t2 = lo > cp["taxa_por_item"]
    trat = ("nao entra (T1 nao dispara)" if not t1 else
            "nao entra (T2 nao dispara)" if not t2 else
            "REJEICAO" if cp["taxa_por_item"] <= NIVEL_REJEICAO
            else "AVISO em suspeitas")

    ctx = Counter()
    for p in poemas:
        for c in proclise_por_atraccao(p.body):
            ctx[c.split(" [")[0]] += 1

    out = {"_meta": {"protocolo": "docs/FASE-5T.md §5.2",
                     "passagem": 3,
                     "correccao": "POSTERIOR aos dados, declarada",
                     "regra": "licenciado se ha atractor em qualquer ponto "
                              "anterior da mesma oracao, ou se o token "
                              "seguinte e infinitivo",
                     "virgula_nao_fecha_oracao": True,
                     "nada_derivado_dos_dados": True},
           "proporcao_da_construcao": conj,
           "portao": {"T1": {"taxa_por_item_corpus": cp["taxa_por_item"],
                             "limiar": LIMIAR_T1, "dispara": t1},
                      "T2": {"taxa_gerados": gq["taxa_por_item"],
                             "wilson_inf": round(lo, 5), "dispara": t2},
                      "tratamento_pre_escrito": trat},
           "anteriores_mais_comuns_no_corpus": ctx.most_common(20)}
    with open(os.path.join(AQUI, "03-atraccao.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print("=== 3.a passagem: proclise por ATRACCAO ===")
    print(f"{'conjunto':28s} {'itens':>12s} {'prop':>7s}   IC95 por item")
    for k, v in conj.items():
        ic = v["bootstrap95_itens"]
        s = (f"{k:28s} {v['itens_marcados']:4d}/{v['n_itens']:<6d} "
             f"{(v['proporcao'] if v['proporcao'] is not None else -1):7.3f}")
        print(s + (f"   [{ic[0]:.3f}, {ic[1]:.3f}]" if ic else ""))
    print(f"\nT1  corpus {cp['taxa_por_item']:.2%} de {cp['n_itens']} poemas "
          f"(limiar {LIMIAR_T1:.0%}): {'DISPARA' if t1 else 'nao dispara'}")
    print(f"T2  gerados {gq['taxa_por_item']:.2%}, Wilson inf {lo:.4f}: "
          f"{'DISPARA' if t2 else 'nao dispara'}")
    print(f"-> {trat}")
    print("\nanteriores mais comuns no corpus:")
    print(" ", ctx.most_common(14))
    print(f"\n-> {os.path.join(AQUI, '03-atraccao.json')}")


if __name__ == "__main__":
    main()
