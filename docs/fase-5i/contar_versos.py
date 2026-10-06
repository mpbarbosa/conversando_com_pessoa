#!/usr/bin/env python
"""Fase 5I / adenda — a contagem de versos do §9.2, nas duas definições.

Este ficheiro existe porque o número do §9.2 foi calculado **ad hoc na sessão** e
a definição não ficou registada em nenhum sítio. Uma sessão paralela apanhou a
omissão e a ambiguidade que ela esconde, e tinha razão nas duas:

> «`src/plagio.py` tem `MIN_PALAVRAS = 3`, logo `_versos` deixa cair toda a linha
> com menos de 3 palavras, e é esse o `n_versos` que o teu `gerar_amostras.py`
> gravou para as amostras geradas. O Caeiro escreve linhas curtas.»

**Era verdade:** os 119 poemas reais foram contados por **linhas não vazias** e as
amostras geradas por **`plagio._versos`**, que filtra a <3 palavras. A tabela do
§9.2 comparava duas definições.

## O que a correcção muda, medido

| | linhas não vazias | `_versos` (≥3 palavras) |
|---|---|---|
| Caeiro real, dentro de 10–20 | **51/119 (43%)** | **46/119 (39%)** |
| qwen2.5 (5H) | 25/30 | 25/30 |
| llama3.1 (5H) | 9/30 | 9/30 |
| llama3.1 (5I, braço A) | 12/30 | 12/30 |

As amostras **geradas dão o mesmo nas duas definições** — raramente têm linhas
com menos de três palavras. Logo o único número que se move é o dos poemas reais,
de 43% para **39%**, e move-se **a favor** da conclusão do §9.2: o Caeiro real
(39%) e o llama3.1 (40%) ficam praticamente coincidentes, contra os 83% do
qwen2.5.

A tabela corrigida é a que vai no §9.2, e usa `_versos` nas duas colunas.
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(AQUI, "..", "..")))

from src.corpus.parse import parse_corpus
from src.plagio import _versos

DENTRO = (10, 20)


def nao_vazias(texto: str) -> int:
    return len([l for l in texto.splitlines() if l.strip()])


def filtradas(texto: str) -> int:
    return len(_versos(texto))


def main() -> None:
    # **A fonte é o `body` do `parse_poem`, e não os chunks.** Este ficheiro
    # errou duas vezes antes de chegar aqui, as duas apanhadas por uma sessão
    # paralela:
    #
    # 1. `setdefault(c.poem_id, c)` contava o **primeiro chunk** e não o poema;
    # 2. juntar os chunks com `"\n".join(...)` conta a mais, porque
    #    `chunk.py` tem **`SOBREPOSICAO = 1`** e repete **uma estrofe** em cada
    #    fronteira. No `poem_1487` (5 chunks, 4 fronteiras) isso duplica 23
    #    ocorrências de linha e dá 181 em vez de 161.
    #
    # O `body` é o texto do poema antes de ser partido para indexação, e é a
    # única fonte que não tem nenhum dos dois problemas.
    poemas = parse_corpus()
    voz = lambda p: getattr(p.voice, "value", str(p.voice))
    cae = [p.body for p in poemas if voz(p) == "caeiro"]

    out: dict = {"_meta": {
        "porque_existe": "o número do §9.2 foi calculado ad hoc; a definição "
                         "não estava registada. Ver o docstring.",
        "intervalo": list(DENTRO),
        "fonte": "Poem.body do parse_corpus — nem o 1.º chunk nem os chunks juntados; ver o comentário em main()"}}

    print(f"Caeiro real: {len(cae)} poemas (o `body` do parse_poem)\n")
    for rot, fn in (("linhas_nao_vazias", nao_vazias), ("versos_min3", filtradas)):
        nv = [fn(t) for t in cae]
        dentro = sum(1 for x in nv if DENTRO[0] <= x <= DENTRO[1])
        out[rot] = {"n": len(nv), "mediana": st.median(nv),
                    "min": min(nv), "max": max(nv),
                    "dentro_de_10_20": dentro,
                    "fraccao": round(dentro / len(nv), 4),
                    "abaixo_de_10": sum(1 for x in nv if x < DENTRO[0]),
                    "acima_de_20": sum(1 for x in nv if x > DENTRO[1]),
                    "composicao_pct": {
                        "abaixo": round(sum(1 for x in nv if x < DENTRO[0]) / len(nv), 3),
                        "dentro": round(dentro / len(nv), 3),
                        "acima": round(sum(1 for x in nv if x > DENTRO[1]) / len(nv), 3)}}
        print(f"  {rot:20s} mediana {st.median(nv):4.1f}  "
              f"dentro {dentro}/{len(nv)} ({dentro/len(nv):.0%})  "
              f"abaixo de 10: {out[rot]['abaixo_de_10']}")

    # as geradas: as duas definições dão o mesmo?
    out["geradas"] = {}
    print("\namostras geradas — `n_versos` gravado vs recontado:")
    for fase, braco, rot in (("fase-5h", "Q", "qwen_5H"),
                             ("fase-5h", "L", "llama_5H"),
                             ("fase-5i", "A", "llama_5I_A"),
                             ("fase-5i", "B", "llama_5I_B")):
        caminho = os.path.join(AQUI, "..", fase, "01-cru.jsonl")
        with open(caminho) as f:
            xs = [json.loads(l) for l in f if l.strip()]
        xs = [x for x in xs if x["braco"] == braco]
        grav = sum(1 for x in xs if DENTRO[0] <= x["n_versos"] <= DENTRO[1])
        rec = sum(1 for x in xs
                  if DENTRO[0] <= nao_vazias(x["texto"]) <= DENTRO[1])
        out["geradas"][rot] = {"n": len(xs), "dentro_gravado_versos_min3": grav,
                               "dentro_linhas_nao_vazias": rec,
                               "coincidem": grav == rec}
        print(f"  {rot:12s} gravado {grav}/{len(xs)}  recontado {rec}/{len(xs)}  "
              f"{'iguais' if grav == rec else 'DIFEREM'}")

    with open(os.path.join(AQUI, "04-contagem-de-versos.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\n04-contagem-de-versos.json escrito.")


if __name__ == "__main__":
    main()
