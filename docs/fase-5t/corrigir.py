#!/usr/bin/env python
"""Fase 5T / A5 — a correcção **posterior**, declarada como tal, e o instrumento
livre de comprimento.

Protocolo: `../FASE-5T.md` §5.2, que pré-escreveu que um erro na lista de
licenciadores apareceria **no portão de segurança** em vez de se esconder. Foi o
que aconteceu: o T1 marcou **435 de 1926** poemas de Pessoa.

Duas coisas mudam aqui, e **ambas são posteriores aos dados**:

**1. Em verso, o fim da linha não é fronteira de oração.** O §2.1 declarou
«início de linha» como não-licenciador, e isso é certo em prosa e errado em
verso: a oração corre através da quebra. Dos 635 casos marcados no corpus, **88
tinham a quebra de linha como único motivo** — o licenciador estava na linha
anterior. A correcção é prosódica, não ajustada a dados: junta-se o texto numa
só cadeia e só a **pontuação** conta como fronteira.

**2. A taxa por item depende do comprimento, logo não é a taxa.** A medida certa
é a **proporção da construção**: de todas as vezes que o pronome aparece, quantas
são próclise e quantas ênclise. É livre de comprimento e é o que a regra da
persona («colocação enclítica, **sempre**») de facto afirma.

    taxa = próclise / (próclise + ênclise)

Nada aqui é derivado dos dados: não há constante nova, não há limiar escolhido
depois. O que há é um denominador diferente e uma fronteira corrigida.

Escreve `02-correccao.json`.
"""
from __future__ import annotations

import json
import math
import os
import random
import re
import sys
from collections import Counter

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)
sys.path.insert(0, AQUI)

from detectar import (LICENCIADORES, PRONOMES, _FRONTEIRA,  # noqa: E402
                      _RE_TOKEN, wilson)
from src.corpus.models import Lang                          # noqa: E402
from src.corpus.parse import parse_corpus                   # noqa: E402

SEMENTE = 20261008
#: Ênclise: o pronome colado ao verbo por hífen. É a construção que a persona
#: manda e serve de denominador.
_RE_ENCLISE = re.compile(r"[a-zà-ÿ]-(?:" + "|".join(sorted(PRONOMES, key=len,
                                                           reverse=True))
                         + r")\b", re.I)


def proclise_corrigida(texto: str) -> list[str]:
    """Próclise não licenciada, com a quebra de linha a **não** ser fronteira."""
    # A correccao 1: uma so cadeia, logo o licenciador da linha anterior conta.
    toks = _RE_TOKEN.findall(" ".join(texto.split("\n")).lower())
    out = []
    for i, t in enumerate(toks):
        if t not in PRONOMES:
            continue
        ant = toks[i - 1] if i else None
        if ant is not None and ant not in _FRONTEIRA and ant in LICENCIADORES:
            continue
        seg = toks[i + 1] if i + 1 < len(toks) else ""
        out.append(f"{ant or '^'} [{t}] {seg}".strip())
    return out


def conta(texto: str) -> tuple[int, int]:
    """(próclise não licenciada, ênclise)."""
    return len(proclise_corrigida(texto)), len(_RE_ENCLISE.findall(texto))


def proporcao(textos: list[str]) -> dict:
    pares = [conta(t) for t in textos]
    pro = sum(p for p, _ in pares)
    enc = sum(e for _, e in pares)
    tot = pro + enc
    lo, hi = wilson(pro, tot) if tot else (None, None)
    # Bootstrap por item (agrupado): o item e a unidade independente, nao a
    # ocorrencia. Mesma licao que a 5K tirou do n efectivo.
    rng = random.Random(SEMENTE)
    uteis = [(p, e) for p, e in pares if p + e]
    reamostras = []
    for _ in range(2000):
        am = [uteis[rng.randrange(len(uteis))] for _ in range(len(uteis))]
        sp = sum(p for p, _ in am)
        se = sum(e for _, e in am)
        if sp + se:
            reamostras.append(sp / (sp + se))
    reamostras.sort()
    return {"n_itens": len(textos), "itens_com_o_pronome": len(uteis),
            "proclise": pro, "enclise": enc, "ocorrencias": tot,
            "proporcao": round(pro / tot, 4) if tot else None,
            "wilson95_ocorrencias": [round(lo, 4), round(hi, 4)] if tot else None,
            "bootstrap95_itens": [round(reamostras[49], 4),
                                  round(reamostras[1949], 4)]
            if len(reamostras) == 2000 else None}


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

    # ---- o efeito da correccao 1, no corpus, para o registo ------------- #
    antes = sum(1 for p in poemas if proclise_corrigida.__name__ and
                __import__("detectar").proclise(p.body)[0])
    depois = sum(1 for p in poemas if proclise_corrigida(p.body))
    correccao1 = {"poemas_marcados_antes": antes,
                  "poemas_marcados_depois": depois,
                  "n": len(poemas),
                  "taxa_depois": round(depois / len(poemas), 4),
                  "limiar_T1": 0.01,
                  "T1_depois": depois / len(poemas) < 0.01}

    conj = {
        "corpus_pt": proporcao([p.body for p in poemas]),
        "reais_5q": proporcao([c["texto"] for c in rea]),
        "gerados_5q": proporcao([c["texto"] for c in ger]),
        "gerados_5m": proporcao([x["texto"] for x in cru5m]),
    }
    for m in sorted({c["modelo"] for c in ger}):
        conj[f"gerados_5q::{m}"] = proporcao(
            [c["texto"] for c in ger if c["modelo"] == m])
    for v in sorted({x["voz"] for x in cru5m}):
        conj[f"gerados_5m::{v}"] = proporcao(
            [x["texto"] for x in cru5m if x["voz"] == v])

    # ---- o que fica marcado no corpus depois da correccao -------------- #
    ctx = Counter()
    for p in poemas:
        for c in proclise_corrigida(p.body):
            ctx[c.split(" [")[0]] += 1

    out = {"_meta": {"protocolo": "docs/FASE-5T.md §5.2",
                     "correccao": "POSTERIOR aos dados, declarada",
                     "o_que_mudou": ["quebra de linha nao e fronteira de oracao",
                                     "denominador = proclise + enclise"],
                     "nada_derivado_dos_dados": True,
                     "semente_bootstrap": SEMENTE},
           "correccao1_quebra_de_linha": correccao1,
           "proporcao_da_construcao": conj,
           "anteriores_mais_comuns_no_corpus": ctx.most_common(20)}
    with open(os.path.join(AQUI, "02-correccao.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print("=== correccao 1: a quebra de linha nao e fronteira ===")
    print(f"  poemas marcados: {antes} -> {depois} de {len(poemas)} "
          f"({correccao1['taxa_depois']:.1%})")
    print(f"  T1 depois da correccao: "
          f"{'DISPARA' if correccao1['T1_depois'] else 'NAO DISPARA'}")

    print("\n=== a proporcao da construcao: proclise / (proclise + enclise) ===")
    print(f"{'conjunto':28s} {'proclise':>9s} {'enclise':>8s} {'prop':>7s}"
          f"   {'IC95 por item':>18s}")
    for k, v in conj.items():
        ic = v["bootstrap95_itens"]
        print(f"{k:28s} {v['proclise']:9d} {v['enclise']:8d} "
              f"{(v['proporcao'] if v['proporcao'] is not None else -1):7.3f}"
              f"   [{ic[0]:.3f}, {ic[1]:.3f}]" if ic else
              f"{k:28s} {v['proclise']:9d} {v['enclise']:8d}")

    print("\nanteriores mais comuns no corpus, depois da correccao:")
    print(" ", ctx.most_common(14))
    print(f"\n-> {os.path.join(AQUI, '02-correccao.json')}")


if __name__ == "__main__":
    main()
