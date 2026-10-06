#!/usr/bin/env python
"""Fase 5J / A1-A2 — contagem de versos e elegibilidade, por voz.

Protocolo: `docs/FASE-5J.md` §4.1-4.3.

Conta sobre `parse_poem(...).body` — o **poema inteiro** — e não sobre o texto
do chunk, que é o defeito do `fase-5i/contar_versos.py` apanhado no §2.2 do
protocolo (5 poemas de Caeiro são multi-chunk e o `max` publicado veio errado).

Duas definições de verso, as duas reportadas:
  - `versos_min3`  -> `plagio._versos`, MIN_PALAVRAS=3. **Primária**, porque é a
    que todos os harnesses desta sequência gravaram para as amostras geradas.
  - `nao_vazias`   -> linhas não vazias. Sensibilidade.

Elegibilidade (§4.3): exclui só o que a transcrição marca como texto **ausente**.
**Nenhum critério olha para o comprimento** — filtrar poemas curtos porque são
curtos pressupõe a conclusão desta fase.

Escreve `01-contagem.json`.
"""
from __future__ import annotations

import json
import os
import re
import statistics as st
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)

from src.corpus.models import Voice                       # noqa: E402
from src.corpus.parse import parse_corpus                 # noqa: E402
from src.plagio import _versos                            # noqa: E402

#: Intervalos do 3b, da Fase 5 §5.2. Reis é «<=12», logo o limite inferior é 1.
INTERVALOS: dict[Voice, tuple[int, int]] = {
    Voice.CAEIRO: (10, 20),
    Voice.CAMPOS: (15, 30),
    Voice.REIS: (1, 12),
    Voice.ORTONIMO: (12, 20),
}

#: Lacuna marcada pela transcrição: parênteses/rectos com só pontos, ou uma
#: linha composta apenas por três ou mais pontos. Ver §4.3.
_RE_LACUNA = re.compile(r"[\[(]\s*[.…]{2,}\s*[)\]]|^\s*[.…]{3,}\s*$", re.M)


def tem_lacuna(corpo: str) -> bool:
    return _RE_LACUNA.search(corpo) is not None


def nao_vazias(corpo: str) -> int:
    return len([l for l in corpo.splitlines() if l.strip()])


def versos_min3(corpo: str) -> int:
    return len(_versos(corpo))


DEFS = {"versos_min3": versos_min3, "nao_vazias": nao_vazias}


def descreve(xs: list[int], intervalo: tuple[int, int]) -> dict:
    lo, hi = intervalo
    return {
        "n": len(xs),
        "dentro": sum(1 for x in xs if lo <= x <= hi),
        "abaixo": sum(1 for x in xs if x < lo),
        "acima": sum(1 for x in xs if x > hi),
        "mediana": st.median(xs) if xs else None,
        "media": round(st.mean(xs), 2) if xs else None,
        "min": min(xs) if xs else None,
        "max": max(xs) if xs else None,
    }


def main() -> None:
    indexados = set()
    for linha in open(os.path.join(RAIZ, "data/corpus.jsonl")):
        d = json.loads(linha)
        if "_meta" not in d:
            indexados.add(d["poem_id"])

    todos = [p for p in parse_corpus(os.path.join(RAIZ, "data/pessoa_poems"))
             if p.id in indexados]

    out: dict = {"_meta": {
        "protocolo": "docs/FASE-5J.md §4.1-4.3",
        "conta_sobre": "parse_poem(...).body — poema inteiro, nao o chunk",
        "indexados": len(todos),
        "intervalos": {v.value: list(i) for v, i in INTERVALOS.items()},
        "definicao_primaria": "versos_min3 (plagio._versos, MIN_PALAVRAS=3)",
    }, "vozes": {}, "por_poema": {}}

    for voz, intervalo in INTERVALOS.items():
        da_voz = [p for p in todos if p.voice is voz]
        cel: dict = {"intervalo": list(intervalo)}

        for lingua, conj in (("pt", [p for p in da_voz
                                     if p.language.value == "pt"]),
                             ("todas", da_voz)):
            elegiveis = [p for p in conj if not tem_lacuna(p.body)]
            excluidos = [p for p in conj if tem_lacuna(p.body)]
            bloco: dict = {"n_total": len(conj),
                           "n_elegiveis": len(elegiveis),
                           "n_excluidos": len(excluidos)}
            for nome, fn in DEFS.items():
                bloco[nome] = {
                    "elegiveis": descreve([fn(p.body) for p in elegiveis],
                                          intervalo),
                    "todos": descreve([fn(p.body) for p in conj], intervalo),
                    # A2: ortogonalidade — os excluidos sao os curtos?
                    "excluidos": descreve([fn(p.body) for p in excluidos],
                                          intervalo) if excluidos else None,
                }
            cel[lingua] = bloco
        out["vozes"][voz.value] = cel

        # Contagens por poema, para o J4 e para ser verificavel.
        out["por_poema"][voz.value] = sorted(
            ({"id": p.id, "lingua": p.language.value,
              "elegivel": not tem_lacuna(p.body),
              "versos_min3": versos_min3(p.body),
              "nao_vazias": nao_vazias(p.body)} for p in da_voz),
            key=lambda d: d["id"])

    caminho = os.path.join(AQUI, "01-contagem.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print(f"{len(todos)} poemas indexados\n")
    for voz, cel in out["vozes"].items():
        lo, hi = cel["intervalo"]
        b = cel["pt"]
        e = b["versos_min3"]["elegiveis"]
        print(f"{voz:10s} [{lo:2d}-{hi:2d}]  pt n={b['n_total']:4d}  "
              f"elegiveis={b['n_elegiveis']:4d}  "
              f"dentro={e['dentro']:4d} ({e['dentro']/max(e['n'],1):.0%})  "
              f"abaixo={e['abaixo']:4d}  acima={e['acima']:4d}  "
              f"mediana={e['mediana']}")
    print(f"\n-> {caminho}")


if __name__ == "__main__":
    main()
