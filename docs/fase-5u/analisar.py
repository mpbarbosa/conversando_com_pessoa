#!/usr/bin/env python
"""Fase 5U / A3–B2 — os quatro instrumentos, e os portões.

Protocolo: [`../FASE-5U.md`](../FASE-5U.md) §1.1, §3.

Quatro leituras, uma por regra do bloco ablado, **todas no texto cru** (§2.1):

| regra | instrumento | origem |
|---|---|---|
| ortografia pré-1990 | o detector da 5R a **20×** | `fase-5r/derivar.py`, reutilizado |
| ênclise | próclise por **atracção** | `fase-5t/atraccao.py`, reutilizado |
| «tu» não «você» | `guard.tratamento_indevido` | `src/guard.py`, o que a 5T pôs lá |
| sem gerúndio | perífrase progressiva | `fase-5t/detectar.py`, reutilizado |

**Nenhum é escrito aqui.** Todos vêm de fases que os mediram no corpus antes de
os apontar a alguma coisa — 0,73%, 2,65%, 0,21% e 5,24% — e é a única razão por
que servem (§4.3).

O emparelhamento é por **célula** `(voz, pergunta, repetição)` e o *bootstrap*
reamostra **agrupamentos** `(voz, pergunta)`, não amostras: a lição do n
efectivo da [5K](../FASE-5K-RELATORIO.md).

Escreve `02-resultados.json`.
"""
from __future__ import annotations

import collections
import json
import os
import random
import re
import statistics as st
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "docs", "fase-5r"))
sys.path.insert(0, os.path.join(RAIZ, "docs", "fase-5t"))

from derivar import deriva, marca, palavras                 # noqa: E402
from detectar import gerundio                               # noqa: E402
from atraccao import proclise_por_atraccao                  # noqa: E402
from corrigir import _RE_ENCLISE                            # noqa: E402
from src.corpus.models import Lang                          # noqa: E402
from src.corpus.parse import parse_corpus                   # noqa: E402
from src.guard import e_verso, tratamento_indevido          # noqa: E402

SEMENTE = 20261008
N_REAMOSTRAS = 4000
#: §1.1 — a razao a que a 5R mediu 0,73% de falsos positivos retidos e **zero**
#: poemas reais marcados. Razao = freq(canonica) / max(freq(variante), 1).
RAZAO = 20
#: §3 U1' — tres vezes a taxa do poeta (0,045), fora de todos os intervalos
#: que a 5T mediu.
LIMIAR_U1_LINHA = 0.15
#: As taxas no corpus, publicadas pelas fases que construiram os instrumentos.
NULOS = {"ortografia_5r20x": 0.0073, "proclise": 0.0265,
         "voce": 0.0021, "gerundio": 0.0524}


def lista_ortografica() -> dict:
    poemas = [p for p in parse_corpus(os.path.join(RAIZ, "data/pessoa_poems"))
              if p.language is Lang.PT]
    vocab = collections.Counter()
    for p in poemas:
        vocab.update(palavras(p.body))
    todas = deriva(vocab)
    return {v: d for v, d in todas.items()
            if d["freq_canonica"] / max(d["freq_variante"], 1) >= RAZAO}


def medir(texto: str, orto: dict) -> dict:
    pro = proclise_por_atraccao(texto)
    enc = _RE_ENCLISE.findall(texto)
    return {"proclise_n": len(pro), "enclise_n": len(enc),
            "proclise_ex": pro[:4],
            "orto": marca(texto, orto),
            "voce": list(tratamento_indevido(texto)),
            "gerundio": gerundio(texto),
            "e_verso": e_verso(texto),
            "n_linhas": len([l for l in texto.split("\n") if l.strip()])}


def _prop(itens: list[dict]) -> float | None:
    p = sum(i["proclise_n"] for i in itens)
    e = sum(i["enclise_n"] for i in itens)
    return p / (p + e) if p + e else None


def _frac(itens: list[dict], campo: str) -> float:
    return sum(1 for i in itens if i[campo]) / len(itens) if itens else 0.0


def bootstrap_emparelhado(grupos: dict, estat) -> dict:
    """IC95 da diferença A − C, reamostrando **agrupamentos** (voz, pergunta)."""
    chaves = sorted(grupos)
    rng = random.Random(SEMENTE)
    reais = estat([g for k in chaves for g in grupos[k]["A"]]), \
        estat([g for k in chaves for g in grupos[k]["C"]])
    if reais[0] is None or reais[1] is None:
        return {"A": reais[0], "C": reais[1], "diferenca": None}
    amostras = []
    for _ in range(N_REAMOSTRAS):
        esc = [chaves[rng.randrange(len(chaves))] for _ in chaves]
        a = estat([g for k in esc for g in grupos[k]["A"]])
        c = estat([g for k in esc for g in grupos[k]["C"]])
        if a is not None and c is not None:
            amostras.append(a - c)
    amostras.sort()
    lo = amostras[int(0.025 * len(amostras))]
    hi = amostras[int(0.975 * len(amostras)) - 1]
    return {"A": round(reais[0], 4), "C": round(reais[1], 4),
            "diferenca": round(reais[0] - reais[1], 4),
            "ic95": [round(lo, 4), round(hi, 4)],
            "exclui_zero": lo > 0 or hi < 0,
            "n_agrupamentos": len(chaves)}


def main() -> None:
    cru = [json.loads(l) for l in
           open(os.path.join(AQUI, "01-cru.jsonl"), encoding="utf-8")
           if l.strip()]
    print(f"{len(cru)} amostras no diário")
    orto = lista_ortografica()
    print(f"detector da 5R a {RAZAO}×: {len(orto)} variantes "
          f"(0,73% de falsos positivos retidos, zero reais marcados)\n")

    for d in cru:
        d["m"] = medir(d["texto_cru"], orto)

    grupos: dict = {}
    for d in cru:
        k = (d["voz"], d["pergunta_id"])
        grupos.setdefault(k, {"C": [], "A": []})[d["braco"]].append(d["m"])
    completos = {k: v for k, v in grupos.items() if v["C"] and v["A"]}
    print(f"{len(completos)} agrupamentos (voz, pergunta) com os dois braços")

    portoes = {
        "U1_proclise": bootstrap_emparelhado(completos, _prop),
        "U2_ortografia": bootstrap_emparelhado(
            completos, lambda xs: _frac(xs, "orto")),
    }
    descritivo = {
        "voce": bootstrap_emparelhado(completos, lambda xs: _frac(xs, "voce")),
        "gerundio": bootstrap_emparelhado(completos,
                                          lambda xs: _frac(xs, "gerundio")),
        "e_verso": bootstrap_emparelhado(
            completos, lambda xs: sum(1 for i in xs if i["e_verso"]) / len(xs)),
    }
    u1 = bool(portoes["U1_proclise"].get("exclui_zero")
              and (portoes["U1_proclise"]["diferenca"] or 0) > 0)
    u1l = (portoes["U1_proclise"]["A"] or 0) > LIMIAR_U1_LINHA
    u2 = bool(portoes["U2_ortografia"].get("exclui_zero")
              and (portoes["U2_ortografia"]["diferenca"] or 0) > 0)

    por_voz = {}
    for v in sorted({d["voz"] for d in cru}):
        sub = {k: g for k, g in completos.items() if k[0] == v}
        por_voz[v] = {"proclise": bootstrap_emparelhado(sub, _prop),
                      "ortografia": bootstrap_emparelhado(
                          sub, lambda xs: _frac(xs, "orto"))}

    def lat(b):
        return round(st.median(d["segundos"] for d in cru
                               if d["braco"] == b), 1)

    out = {"_meta": {"protocolo": "docs/FASE-5U.md §3",
                     "n_amostras": len(cru),
                     "n_agrupamentos": len(completos),
                     "razao_ortografica": RAZAO,
                     "n_variantes_ortograficas": len(orto),
                     "lido_no_texto": "cru (§2.1)",
                     "nulos_publicados_das_fases_anteriores": NULOS,
                     "reamostras": N_REAMOSTRAS, "semente": SEMENTE},
           "portoes": {"U1": {**portoes["U1_proclise"], "dispara": u1},
                       "U1_linha": {"limiar": LIMIAR_U1_LINHA,
                                    "proporcao_A": portoes["U1_proclise"]["A"],
                                    "dispara": u1l},
                       "U2": {**portoes["U2_ortografia"], "dispara": u2},
                       "U3": {"dispara": not (u1 or u2),
                              "leitura": "o bloco e decoracao; o passo 34 sai "
                                         "do prompt"}},
           "descritivo": descritivo,
           "por_voz": por_voz,
           "tokens_system": {b: sorted({d["tokens_system"] for d in cru
                                        if d["braco"] == b}) for b in "CA"},
           "latencia_mediana_s": {b: lat(b) for b in "CA"},
           "truncadas": {b: sum(1 for d in cru if d["braco"] == b
                                and d["truncada"]) for b in "CA"},
           "tentativas_2": {b: sum(1 for d in cru if d["braco"] == b
                                   and d["tentativas"] > 1) for b in "CA"},
           "exemplos_proclise_A": [e for d in cru if d["braco"] == "A"
                                   for e in d["m"]["proclise_ex"]][:12],
           "exemplos_orto_A": sorted({w for d in cru if d["braco"] == "A"
                                      for w in d["m"]["orto"]}),
           "exemplos_orto_C": sorted({w for d in cru if d["braco"] == "C"
                                      for w in d["m"]["orto"]})}
    with open(os.path.join(AQUI, "02-resultados.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print(f"\n{'instrumento':16s} {'nulo':>7s} {'C':>7s} {'A':>7s} "
          f"{'A-C':>8s}   IC95 da diferença")
    for nome, chave, nulo in (("próclise", "U1_proclise", "proclise"),
                              ("ortografia 20×", "U2_ortografia",
                               "ortografia_5r20x")):
        r = portoes[chave]
        print(f"{nome:16s} {NULOS[nulo]:7.4f} {r['C']:7.4f} {r['A']:7.4f} "
              f"{r['diferenca']:+8.4f}   [{r['ic95'][0]:+.4f}, "
              f"{r['ic95'][1]:+.4f}]  "
              f"{'EXCLUI ZERO' if r['exclui_zero'] else 'contém zero'}")
    for nome, r in descritivo.items():
        if r["diferenca"] is None:
            continue
        print(f"{nome:16s} {NULOS.get(nome, float('nan')):7.4f} "
              f"{r['C']:7.4f} {r['A']:7.4f} {r['diferenca']:+8.4f}   "
              f"[{r['ic95'][0]:+.4f}, {r['ic95'][1]:+.4f}]")

    print(f"\nU1  (a regra sustenta a ênclise):   "
          f"{'DISPARA' if u1 else 'nao dispara'}")
    print(f"U1′ (o efeito é «sistemático», A > {LIMIAR_U1_LINHA}): "
          f"{'DISPARA' if u1l else 'nao dispara'}")
    print(f"U2  (a regra sustenta a ortografia): "
          f"{'DISPARA' if u2 else 'nao dispara'}")
    print(f"U3  (o bloco é decoração):          "
          f"{'DISPARA' if not (u1 or u2) else 'nao dispara'}")
    print(f"\ntokens do system: {out['tokens_system']}")
    print(f"latência mediana: {out['latencia_mediana_s']} s   "
          f"truncadas {out['truncadas']}   2 tentativas {out['tentativas_2']}")
    print(f"\nortografia marcada no braço A: {out['exemplos_orto_A']}")
    print(f"ortografia marcada no braço C: {out['exemplos_orto_C']}")
    print(f"próclise no braço A: {out['exemplos_proclise_A'][:8]}")
    print("\npor voz:")
    for v, r in por_voz.items():
        print(f"  {v:9s} próclise  C={r['proclise']['C']} A={r['proclise']['A']}"
              f"   ortografia C={r['ortografia']['C']} A={r['ortografia']['A']}")
    print(f"\n-> {os.path.join(AQUI, '02-resultados.json')}")


if __name__ == "__main__":
    main()
