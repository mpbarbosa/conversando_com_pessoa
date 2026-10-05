#!/usr/bin/env python
"""Fase 5I / Passo A2 — a regra de reescrita da forma cumpre-se?

Protocolo em [`../FASE-5I.md`](../FASE-5I.md) §3.1. Corre **antes** de existir
amostra, e o resultado entra no relatório.

Quatro verificações mecânicas:

1. a `poetica` é **byte a byte igual** nos dois braços — é o activo que a Fase
   5H mediu valer +0,700 e que esta fase não pode gastar;
2. todas as orações da `forma` de serviço sobrevivem em B, normalizando só o
   espaço;
3. o requisito de comprimento está em **primeira** posição em B e não estava em A;
4. tudo o resto do `system_prompt` é igual fora do intervalo da `forma`.

A regra «nenhum conteúdo poético novo» **não é mecanizável**, e o §3.1 do
protocolo mostra as duas cláusulas lado a lado para o leitor julgar.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from personas_5i import CAEIRO_A, CAEIRO_B

AQUI = os.path.dirname(os.path.abspath(__file__))
RAZAO_MIN, RAZAO_MAX = 1.0, 2.0


def norm(t: str) -> str:
    return " ".join(t.split())


def main() -> None:
    a, b = CAEIRO_A, CAEIRO_B
    na, nb = norm(a.forma), norm(b.forma)

    oracoes = ("Verso livre, linhas curtas, sem rima.",
               "Linguagem simples, quase seca.",
               "Poucas imagens, e nenhuma decorativa.")
    preservadas = {o: (o in na and o in nb) for o in oracoes}

    razao = len(nb) / len(na)
    comprimento_primeiro = nb.index("dez e vinte") < nb.index("Verso livre")
    comprimento_ultimo_em_a = na.index("dez e vinte") > na.index("Verso livre")

    sa, sb = a.system_prompt(), b.system_prompt()
    resto_a = sa.replace(a.forma, "\x00FORMA\x00", 1)
    resto_b = sb.replace(b.forma, "\x00FORMA\x00", 1)

    ok = [
        ("regra 1 · a poetica é byte a byte igual", a.poetica == b.poetica),
        ("regra 2 · todas as orações de A sobrevivem em B", all(preservadas.values())),
        ("regra 3 · o comprimento passa para primeiro em B", comprimento_primeiro),
        ("regra 3 · e estava em último em A", comprimento_ultimo_em_a),
        ("regra 4 · comprimento em [1,0; 2,0] do original",
         RAZAO_MIN <= razao <= RAZAO_MAX),
        ("regra 5 · resto do system byte a byte igual", resto_a == resto_b),
    ]

    print("Fase 5I / A2 — verificação da regra de reescrita (§3.1)\n")
    print(f"A  {len(na):4d} car.  «{na}»\n")
    print(f"B  {len(nb):4d} car.  «{nb}»\n")
    print(f"razão B/A = {razao:.3f}\n")
    for rotulo, passou in ok:
        print(f"  {'[x]' if passou else '[ ]'} {rotulo}")

    saida = {"protocolo": "docs/FASE-5I.md §3.1",
             "A_forma": na, "B_forma": nb,
             "caracteres": {"A": len(na), "B": len(nb)},
             "razao_comprimento": round(razao, 3),
             "poetica_igual": a.poetica == b.poetica,
             "oracoes_preservadas": preservadas,
             "resto_do_system_igual": resto_a == resto_b,
             "regras_cumpridas": {r: bool(v) for r, v in ok},
             "nao_mecanizavel": "nenhum conteúdo poético novo (ver §3.1)"}
    with open(os.path.join(AQUI, "00-personas.json"), "w") as f:
        json.dump(saida, f, ensure_ascii=False, indent=1)

    falhou = [r for r, v in ok if not v]
    print("\n00-personas.json escrito."
          + (f"\nFALHOU: {falhou}" if falhou else "\nA regra cumpre-se."))
    if falhou:
        sys.exit(1)


if __name__ == "__main__":
    main()
