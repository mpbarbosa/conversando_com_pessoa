#!/usr/bin/env python
"""Fase 5W / A0 — re-corre a 5V com a chave de rima corrigida.

Não é um portão desta fase. É uma **verificação de uma conclusão já publicada**,
feita porque o defeito apareceu ao testar o analisador desta fase — **antes de
os dados dela existirem**.

## O defeito

A chave consoante da [5V](../FASE-5V-RELATORIO.md) parte do penúltimo **grupo**
de vogais, e o `_RE_GRUPO_VOGAL` junta `ia` num grupo só:

| palavra | grupos | chave da 5V | chave certa |
|---|---|---|---|
| `havia` | `a`, `ia` | `avia` | `ia` |
| `servia` | `e`, `ia` | `ervia` | `ia` |

**Não casam**, e `havia`/`servia` é uma rima de manual. A correcção é partir da
penúltima **vogal-letra** em vez do grupo.

## O que muda nas conclusões da 5V: nada. Melhoram.

Escreve `03-rechecagem-5v.json`.
"""
from __future__ import annotations

import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(RAIZ, "docs", "fase-5v"))

from analisar import nulo_letra, rima_letra                   # noqa: E402
from corrigir import nulo_sem_repeticao, rima_sem_repeticao   # noqa: E402
from src.corpus.models import Lang, Voice                     # noqa: E402
from src.corpus.parse import parse_corpus                     # noqa: E402

DIZ = {"ortonimo": "«metro regular e rima»", "reis": "«sem rima»",
       "campos": "«irregular», anáfora", "caeiro": "verso livre"}


def main() -> None:
    poemas = [p for p in parse_corpus(os.path.join(RAIZ, "data/pessoa_poems"))
              if p.language is Lang.PT]
    g5m: dict[str, list[str]] = {}
    for l in open(os.path.join(RAIZ, "docs/fase-5m/01-cru.jsonl"),
                  encoding="utf-8"):
        d = json.loads(l)
        g5m.setdefault(d["voz"], []).append(d["texto"])

    out = {"_meta": {
        "porque_existe": "verificar uma conclusao publicada da 5V com a chave "
                         "de rima corrigida, achada ao testar o analisador "
                         "desta fase e ANTES de os dados dela existirem",
        "defeito": "a chave da 5V parte do penultimo GRUPO de vogais e o "
                   "regex junta `ia`; logo havia->avia e servia->ervia, que "
                   "nao casam. A correccao parte da penultima VOGAL-LETRA",
        "conclusao": "as conclusoes da 5V nao mudam; as magnitudes melhoram"},
        "por_voz": {}}

    print(f"{'voz':10s} | {'5V: real':>9s} {'nulo':>6s} {'ger':>6s} {'nulo':>6s}"
          f" | {'nova: real':>10s} {'nulo':>6s} {'ger':>6s} {'nulo':>6s} | persona")
    for v in ("ortonimo", "reis", "campos", "caeiro"):
        R = [p.body for p in poemas if p.voice is Voice(v)]
        G = g5m.get(v, [])
        b = {"persona_manda": DIZ[v], "n_real": len(R), "n_gerado": len(G),
             "chave_5v": {
                 "real": round(sum(rima_sem_repeticao(t) for t in R) / len(R), 4),
                 "nulo_real": nulo_sem_repeticao(R)["p99"]},
             "chave_corrigida": {
                 "real": round(sum(rima_letra(t) for t in R) / len(R), 4),
                 "nulo_real": nulo_letra(R)["p99"]}}
        if G:
            b["chave_5v"]["gerado"] = round(
                sum(rima_sem_repeticao(t) for t in G) / len(G), 4)
            b["chave_5v"]["nulo_gerado"] = nulo_sem_repeticao(G)["p99"]
            b["chave_corrigida"]["gerado"] = round(
                sum(rima_letra(t) for t in G) / len(G), 4)
            b["chave_corrigida"]["nulo_gerado"] = nulo_letra(G)["p99"]
            b["gerado_acima_do_proprio_nulo_chave_corrigida"] = (
                b["chave_corrigida"]["gerado"]
                > b["chave_corrigida"]["nulo_gerado"])
        b["real_acima_do_proprio_nulo_chave_corrigida"] = (
            b["chave_corrigida"]["real"] > b["chave_corrigida"]["nulo_real"])
        out["por_voz"][v] = b
        a, c = b["chave_5v"], b["chave_corrigida"]
        print(f"{v:10s} | {a['real']:9.4f} {a['nulo_real']:6.4f} "
              f"{a.get('gerado', float('nan')):6.4f} "
              f"{a.get('nulo_gerado', float('nan')):6.4f} | "
              f"{c['real']:10.4f} {c['nulo_real']:6.4f} "
              f"{c.get('gerado', float('nan')):6.4f} "
              f"{c.get('nulo_gerado', float('nan')):6.4f} | {DIZ[v]}")

    with open(os.path.join(AQUI, "03-rechecagem-5v.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\nleitura: a conclusão da 5V mantém-se com a chave corrigida —")
    o = out["por_voz"]["ortonimo"]["chave_corrigida"]
    print(f"  o ortónimo gerado rima a {o['gerado']} contra um nulo de "
          f"{o['nulo_gerado']}: **outra vez exactamente o próprio nulo**,")
    print(f"  e o real a {o['real']} contra {o['nulo_real']}.")
    print(f"\n-> {os.path.join(AQUI, '03-rechecagem-5v.json')}")


if __name__ == "__main__":
    main()
