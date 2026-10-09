#!/usr/bin/env python
"""Fase 5Z / A3–B1 — os portões da mecânica da penalização.

Protocolo: [`../FASE-5Z.md`](../FASE-5Z.md) §2–3. **Fixado antes de os dados
existirem**, como o da 5U, da 5W e da 5X.

**Primário**: densidade de rima na **1.ª tentativa** (§2), cujo prompt é
idêntico entre braços por construção. **Secundário**: a saída final.

**Z1 exige duas coisas**: o IC da diferença 0,9 − 1,1 a excluir zero **e** a
**monotonia** 1,1 < 1,0 < 0,9 nas médias — que é o que a mecânica prediz e o que
uma coincidência não prediz (§1.1).

**Z3 com intervalo**, que corrige o `X3` da 5X: um dano conta só se o IC95 da
diferença excluir zero.

Escreve `02-resultados.json`.
"""
from __future__ import annotations

import json
import os
import random
import statistics as st
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "docs", "fase-5v"))
sys.path.insert(0, os.path.join(RAIZ, "docs", "fase-5w"))

from analisar import nulo_letra, rima_letra                 # noqa: E402
from densidade import densidade                             # noqa: E402
from forma import regularidade, versos                      # noqa: E402
from src.guard import e_verso                               # noqa: E402

SEMENTE = 20261009
N_REAMOSTRAS = 4000
#: Ordenados: penaliza -> neutro -> premeia. A ordem e o portao.
ORDEM = ("B", "N", "R")
PENALIDADE = {"B": 1.1, "N": 1.0, "R": 0.9}
#: §1 — o que a 5V/5W mediram no poeta, e entra como regua.
POETA_DENSIDADE = 0.09969
POETA_METRO = 0.7572


def linhas_duplicadas(texto: str) -> float:
    vs = [v.strip().lower() for v in versos(texto)]
    if not vs:
        return 0.0
    vistos: set[str] = set()
    dup = 0
    for v in vs:
        if v in vistos:
            dup += 1
        vistos.add(v)
    return dup / len(vs)


def ic(a: list[float], b: list[float]) -> list[float]:
    rng = random.Random(SEMENTE)
    ds = []
    for _ in range(N_REAMOSTRAS):
        ma = st.mean(a[rng.randrange(len(a))] for _ in a)
        mb = st.mean(b[rng.randrange(len(b))] for _ in b)
        ds.append(ma - mb)
    ds.sort()
    return [round(ds[int(0.025 * len(ds))], 5),
            round(ds[int(0.975 * len(ds)) - 1], 5)]


def bateria(textos: list[str], ds: list[dict], campo: str) -> dict:
    """As medidas do Z3, por amostra, para poderem levar intervalo."""
    return {
        "linhas_duplicadas": [linhas_duplicadas(t) for t in textos],
        "nao_verso": [0.0 if e_verso(t) else 1.0 for t in textos],
        "truncada": [float(bool(d[f"{campo}truncada"])) for d in ds],
        "plagiou": [float(bool(d[f"{campo}plagiou"])) for d in ds],
        "metro_dist": [abs((regularidade(t) or POETA_METRO) - POETA_METRO)
                       for t in textos],
    }


def main() -> None:
    cru = [json.loads(ln) for ln in
           open(os.path.join(AQUI, "01-cru.jsonl"), encoding="utf-8")
           if ln.strip()]
    print(f"{len(cru)} amostras")
    por = {b: [d for d in cru if d["braco"] == b] for b in ORDEM}
    print({b: len(v) for b, v in por.items()})

    # --- o prompt da 1.a tentativa e identico entre bracos? -------------- #
    cel: dict = {}
    for d in cru:
        cel.setdefault((d["pergunta_id"], d["repeticao"]), {})[d["braco"]] = d
    div_primeira = [k for k, v in cel.items()
                    if len({tuple(x["primeira_usados"]) for x in v.values()}) > 1]
    div_final = [k for k, v in cel.items()
                 if len({tuple(x["usados"]) for x in v.values()}) > 1]
    print(f"\nprompt da 1.ª tentativa divergente: {len(div_primeira)}/{len(cel)}"
          f"   (da saída final: {len(div_final)}/{len(cel)})")

    res = {}
    for b in ORDEM:
        ds = por[b]
        prim = [d["primeira_texto"] for d in ds]
        fin = [d["texto_cru"] for d in ds]
        dp = [x for x in map(densidade, prim) if x is not None]
        df = [x for x in map(densidade, fin) if x is not None]
        res[b] = {
            "repeat_penalty": PENALIDADE[b], "n": len(ds),
            # --- primario ---------------------------------------------- #
            "densidade_primeira": round(st.mean(dp), 5),
            "rima_binaria_primeira": round(
                sum(rima_letra(t) for t in prim) / len(prim), 4),
            "nulo_primeira": nulo_letra(prim),
            "razao_ao_poeta": round(POETA_DENSIDADE / st.mean(dp), 1)
            if st.mean(dp) else None,
            "_dp": dp,
            # --- secundario -------------------------------------------- #
            "densidade_final": round(st.mean(df), 5),
            "_df": df,
            # --- Z3 ----------------------------------------------------- #
            "_bat": bateria(prim, ds, "primeira_"),
            "tentativas_2": sum(1 for d in ds if d["tentativas"] > 1),
            "segundos_mediana": round(st.median(d["segundos"] for d in ds), 1),
        }
        bt = res[b]["_bat"]
        res[b].update({f"z3_{k}": round(st.mean(v), 4) for k, v in bt.items()})

    # --- Z1: IC + monotonia --------------------------------------------- #
    medias = [res[b]["densidade_primeira"] for b in ORDEM]
    monotona = medias[0] < medias[1] < medias[2]
    ic_rb = ic(res["R"]["_dp"], res["B"]["_dp"])
    z1 = bool(ic_rb[0] > 0 and monotona)
    # --- Z2: a replicacao da 5X ----------------------------------------- #
    ic_nb = ic(res["N"]["_dp"], res["B"]["_dp"])
    razao_nb = (res["N"]["densidade_primeira"]
                / res["B"]["densidade_primeira"]
                if res["B"]["densidade_primeira"] else None)
    z2 = bool(razao_nb and razao_nb > 1.0)
    # --- Z3: COM intervalo ---------------------------------------------- #
    z3 = {}
    for b in ("N", "R"):
        danos = []
        for k in res[b]["_bat"]:
            i = ic(res[b]["_bat"][k], res["B"]["_bat"][k])
            pior = st.mean(res[b]["_bat"][k]) > st.mean(res["B"]["_bat"][k])
            if pior and i[0] > 0:        # so conta se o IC excluir zero
                danos.append({"medida": k, "ic95": i,
                              "braco": round(st.mean(res[b]["_bat"][k]), 4),
                              "B": round(st.mean(res["B"]["_bat"][k]), 4)})
        z3[b] = {"danos": danos, "dispara": not danos}

    out = {"_meta": {"protocolo": "docs/FASE-5Z.md §2-3",
                     "fixado_antes_dos_dados": True,
                     "primario": "densidade de rima na 1.a tentativa",
                     "z3": "com intervalo: corrige o X3 da 5X",
                     "poeta_densidade": POETA_DENSIDADE,
                     "semente": SEMENTE},
           "prompt_divergente": {
               "primeira_tentativa": len(div_primeira),
               "saida_final": len(div_final), "de": len(cel),
               "leitura": "a 1.a tentativa devia ser 0: o `_repetir_sem` so "
                          "actua depois dela"},
           "por_braco": {b: {k: v for k, v in res[b].items()
                             if not k.startswith("_")} for b in ORDEM},
           "Z1": {"medias_ordenadas": medias, "monotona": monotona,
                  "R_menos_B": round(medias[2] - medias[0], 5),
                  "ic95": ic_rb, "exclui_zero": ic_rb[0] > 0 or ic_rb[1] < 0,
                  "dispara": z1},
           "Z2": {"razao_N_sobre_B": round(razao_nb, 2) if razao_nb else None,
                  "ic95": ic_nb, "referencia_5X": 1.96, "dispara": z2},
           "Z3": z3,
           "Z4": {"dispara": not z1},
           "decisao_pre_escrita": {
               "embarca": False,
               "porque": "o §3.1: o _opcoes e global e o Caeiro e a unica voz "
                         "que funciona. O passo 41 (dano no Caeiro) passa a "
                         "obrigatorio antes de qualquer embarque"}}
    with open(os.path.join(AQUI, "02-resultados.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print(f"\n{'braço':6s} {'rp':>4s} {'dens 1.ª':>9s} {'×poeta':>7s} "
          f"{'rima':>6s} {'nulo':>6s} {'dens fin':>9s} {'dupl':>6s} "
          f"{'plág':>6s} {'trunc':>6s} {'ñverso':>7s} {'t2':>3s} {'seg':>5s}")
    for b in ORDEM:
        r = res[b]
        print(f"{b:6s} {r['repeat_penalty']:4.1f} {r['densidade_primeira']:9.5f} "
              f"{r['razao_ao_poeta']:7.1f} {r['rima_binaria_primeira']:6.3f} "
              f"{r['nulo_primeira']['p99']:6.3f} {r['densidade_final']:9.5f} "
              f"{r['z3_linhas_duplicadas']:6.4f} {r['z3_plagiou']:6.2f} "
              f"{r['z3_truncada']:6.2f} {r['z3_nao_verso']:7.2f} "
              f"{r['tentativas_2']:3d} {r['segundos_mediana']:5.0f}")
    print(f"\npoeta: densidade {POETA_DENSIDADE}")
    print(f"\nZ1 — a mecânica é real")
    print(f"  médias 1,1 / 1,0 / 0,9: {medias}  monótona? **{monotona}**")
    print(f"  R−B {out['Z1']['R_menos_B']:+.5f}  IC95 {ic_rb}  "
          f"{'EXCLUI ZERO' if out['Z1']['exclui_zero'] else 'contém zero'}")
    print(f"  -> {'DISPARA' if z1 else 'nao dispara'}")
    print(f"\nZ2 — a 5X replica: razão N/B = "
          f"{out['Z2']['razao_N_sobre_B']} (5X deu 1,96)  IC {ic_nb}  "
          f"-> {'DISPARA' if z2 else 'nao dispara'}")
    for b in ("N", "R"):
        print(f"\nZ3 braço {b}: "
              f"{'DISPARA (sem dano com IC a excluir zero)' if z3[b]['dispara'] else 'NAO DISPARA'}")
        for d in z3[b]["danos"]:
            print(f"   dano: {d['medida']} {d['braco']} contra {d['B']}  "
                  f"IC {d['ic95']}")
    print(f"\nZ4 {'DISPARA' if not z1 else 'nao dispara'}")
    print(f"\ndecisão do §3.1: embarca **não** — falta o passo 41 (Caeiro)")
    print(f"\n-> {os.path.join(AQUI, '02-resultados.json')}")


if __name__ == "__main__":
    main()
