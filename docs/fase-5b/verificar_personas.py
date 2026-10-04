#!/usr/bin/env python
"""Fase 5B / Passo A2 — a regra de reescrita cumpre-se?

Protocolo em [`../FASE-5B.md`](../FASE-5B.md) §4.1–4.2. Corre **antes** de
existir amostra, e o resultado entra no relatório.

A regra de reescrita é a única defesa contra a variante afirmativa ter sido
afinada até funcionar, e uma regra que não se verifica não defende nada. Este
ficheiro torna-a mecânica:

1. **zero** partículas negativas em P, com fronteira de palavra;
2. comprimento de P entre **0,80** e **1,20** do de C;
3. `forma` e as três regras do §3.1 **byte a byte** iguais, verificado por
   comparação dos `system_prompt` fora do intervalo da cláusula poética.

A regra 1 do §4.1 — cláusula a cláusula, mesmo referente — e a regra 4 —
nenhum conteúdo poético novo — **não são mecanizáveis**, e o §4.3 do protocolo é
o mapa que as expõe ao leitor. Fica declarado aqui para que ninguém leia este
ficheiro como se verificasse as cinco.
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from personas_5b import (CAEIRO_C, CAEIRO_P, PARTICULAS_NEGATIVAS,
                         REFERENTES_NOMEADOS)

AQUI = os.path.dirname(os.path.abspath(__file__))

#: §4.1 regra 3.
RAZAO_MIN, RAZAO_MAX = 0.80, 1.20


def normalizar(t: str) -> str:
    """Colapsa o espaço: as mudanças de linha do fonte não são conteúdo."""
    return " ".join(t.split())


def negativas(texto: str) -> dict[str, int]:
    """Partículas negativas com fronteira de palavra, sem distinção de caixa.

    A fronteira importa: «nem» é substring de nada neste texto, mas «sem» é de
    «sempre» e «nada» de «nadador». Uma contagem por substring reprovaria texto
    correcto e seria uma regra diferente da que está pré-registada.
    """
    t = normalizar(texto)
    out: dict[str, int] = {}
    for p in PARTICULAS_NEGATIVAS:
        n = len(re.findall(rf"(?<!\w){re.escape(p)}(?!\w)", t, re.IGNORECASE))
        if n:
            out[p] = n
    return out


def contar_referentes(texto: str) -> dict[str, int]:
    """§7.1 — os referentes que a persona C nomeia, no texto dado."""
    t = normalizar(texto)
    out: dict[str, int] = {}
    for r in REFERENTES_NOMEADOS:
        n = len(re.findall(rf"(?<!\w){re.escape(r)}(?!\w)", t, re.IGNORECASE))
        if n:
            out[r] = n
    return out


def main() -> None:
    c, p = CAEIRO_C, CAEIRO_P
    nc, np_ = normalizar(c.poetica), normalizar(p.poetica)
    neg_c, neg_p = negativas(c.poetica), negativas(p.poetica)
    razao = len(np_) / len(nc)

    # Regra 5: tudo menos a cláusula poética é byte a byte igual. Verifica-se
    # nos `system_prompt` completos, e não campo a campo, porque é o
    # `system_prompt` que o modelo recebe — é aí que a igualdade tem de valer.
    sc, sp = c.system_prompt(), p.system_prompt()
    assert c.poetica in sc and p.poetica in sp, "a poética não está no system"
    resto_c = sc.replace(c.poetica, "\x00POETICA\x00", 1)
    resto_p = sp.replace(p.poetica, "\x00POETICA\x00", 1)
    resto_igual = resto_c == resto_p

    ok = [
        ("regra 2 · zero partículas negativas em P", not neg_p),
        ("regra 3 · comprimento em [0,80; 1,20]", RAZAO_MIN <= razao <= RAZAO_MAX),
        ("regra 5 · resto do system byte a byte igual", resto_igual),
        ("C tem interdições (senão não há contraste)", bool(neg_c)),
        ("forma byte a byte igual", c.forma == p.forma),
    ]

    print("Fase 5B / A2 — verificação da regra de reescrita (§4.1)\n")
    print(f"C  {len(nc):4d} car.  negativas: {neg_c}")
    print(f"P  {len(np_):4d} car.  negativas: {neg_p or '{}'}")
    print(f"razão P/C = {razao:.3f}\n")
    print(f"referentes nomeados em C: {contar_referentes(c.poetica)}")
    print(f"referentes nomeados em P: {contar_referentes(p.poetica) or '{}'}\n")
    for rotulo, passou in ok:
        print(f"  {'[x]' if passou else '[ ]'} {rotulo}")

    saida = {
        "protocolo": "docs/FASE-5B.md §4.2",
        "C": {"caracteres": len(nc), "negativas": neg_c,
              "total_negativas": sum(neg_c.values()),
              "referentes": contar_referentes(c.poetica)},
        "P": {"caracteres": len(np_), "negativas": neg_p,
              "total_negativas": sum(neg_p.values()),
              "referentes": contar_referentes(p.poetica)},
        "razao_comprimento": round(razao, 3),
        "forma_igual": c.forma == p.forma,
        "resto_do_system_igual": resto_igual,
        "regras_cumpridas": {r: bool(v) for r, v in ok},
        "nao_mecanizaveis": [
            "regra 1 · cláusula a cláusula com o mesmo referente (§4.3)",
            "regra 4 · nenhum conteúdo poético novo",
        ],
    }
    with open(os.path.join(AQUI, "00-personas.json"), "w") as f:
        json.dump(saida, f, ensure_ascii=False, indent=1)

    falhou = [r for r, v in ok if not v]
    print(f"\n00-personas.json escrito."
          + (f"\nFALHOU: {falhou}" if falhou else "\nA regra cumpre-se."))
    if falhou:
        sys.exit(1)


if __name__ == "__main__":
    main()
