#!/usr/bin/env python
"""Fase 5X / A3–B1 — os portões da descodificação.

Protocolo: [`../FASE-5X.md`](../FASE-5X.md) §2.1–3. **Fixado antes de os dados
existirem**, como o da 5U e o da 5W.

**Desfecho**: a **densidade de rima** da [5W §1](../FASE-5W-RELATORIO.md) —
pares de versos que partilham a chave sobre pares possíveis, com os pares de
palavra igual excluídos. Contínua de propósito: o binário «o poema rima» deitava
fora um factor de dez.

**X3 tem veto**, e a bateria é histórica: o `repeat_penalty` existe porque um
8B degenerou em ciclo na Fase 0. Mede-se **linhas duplicadas**, plágio,
truncatura, falhas de guarda, `e_verso` e metro.

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

from analisar import chave_letra, nulo_letra, rima_letra     # noqa: E402
from densidade import densidade                              # noqa: E402
from forma import regularidade, versos                       # noqa: E402
from src.corpus.build import load                            # noqa: E402
from src.corpus.models import Lang, Voice                    # noqa: E402
from src.corpus.parse import parse_corpus                     # noqa: E402
from src.guard import e_verso                                # noqa: E402
from src.plagio import analisar as analisar_plagio           # noqa: E402

SEMENTE = 20261009
N_REAMOSTRAS = 4000
BRACOS = ("B", "P", "T")
#: §1 — o que a 5V e a 5W mediram no poeta, e entra como regua.
POETA_DENSIDADE = 0.09969
POETA_METRO = 0.7572
POETA_RIMA_BINARIA = 0.8367


def linhas_duplicadas(texto: str) -> float:
    """§4.1 — fracção de versos que repetem um verso anterior do mesmo poema.

    É a medida do modo de falha que criou o `repeat_penalty`: o ciclo.
    """
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
    """IC95 de média(a) − média(b), reamostrando itens."""
    rng = random.Random(SEMENTE)
    ds = []
    for _ in range(N_REAMOSTRAS):
        ma = st.mean(a[rng.randrange(len(a))] for _ in a)
        mb = st.mean(b[rng.randrange(len(b))] for _ in b)
        ds.append(ma - mb)
    ds.sort()
    return [round(ds[int(0.025 * len(ds))], 5),
            round(ds[int(0.975 * len(ds)) - 1], 5)]


def main() -> None:
    cru = [json.loads(ln) for ln in
           open(os.path.join(AQUI, "01-cru.jsonl"), encoding="utf-8")
           if ln.strip()]
    print(f"{len(cru)} amostras")
    por = {b: [d for d in cru if d["braco"] == b] for b in BRACOS}
    print({b: len(v) for b, v in por.items()})
    _, chunks = load()
    poemas = [p for p in parse_corpus(os.path.join(RAIZ, "data/pessoa_poems"))
              if p.language is Lang.PT and p.voice is Voice.ORTONIMO]

    res = {}
    for b in BRACOS:
        ds = por[b]
        ts = [d["texto_cru"] for d in ds]
        dens = [x for x in map(densidade, ts) if x is not None]
        met = [x for x in map(regularidade, ts) if x is not None]
        plg = [analisar_plagio(d["texto_limpo"], tuple(
            c for c in chunks if c.poem_id in d["usados"])) for d in ds]
        res[b] = {
            "n": len(ts),
            "opcoes": ds[0]["opcoes"] if ds else None,
            # --- desfecho ------------------------------------------------ #
            "densidade": round(st.mean(dens), 5) if dens else None,
            "nulo_permutacao": nulo_letra(ts),
            "rima_binaria": round(sum(rima_letra(t) for t in ts) / len(ts), 4),
            "razao_ao_poeta": (round(POETA_DENSIDADE / st.mean(dens), 1)
                               if dens and st.mean(dens) else None),
            "_dens": dens,
            # --- X3: a bateria de degeneracao ---------------------------- #
            "linhas_duplicadas": round(
                st.mean(map(linhas_duplicadas, ts)), 4),
            "plagiou": sum(1 for a in plg if a.plagiou),
            "fracao_copiada_mediana": round(
                st.median(a.fracao_copiada for a in plg), 4),
            "truncadas": sum(1 for d in ds if d["truncada"]),
            "falhas_guarda": sum(len(d["motivos_guarda"]) for d in ds),
            "suspeitas": sum(len(d["suspeitas"]) for d in ds),
            "e_verso": round(sum(e_verso(t) for t in ts) / len(ts), 4),
            "metro": round(st.mean(met), 4) if met else None,
            "metro_dist_ao_poeta": (round(abs(st.mean(met) - POETA_METRO), 4)
                                    if met else None),
            "versos_mediana": st.median(len(versos(t)) for t in ts),
            "decode_tokens_mediana": st.median(d["decode_tokens"] for d in ds),
            "segundos_mediana": round(
                st.median(d["segundos"] for d in ds), 1)}

    B = res["B"]
    portoes = {}
    for b in ("P", "T"):
        r = res[b]
        i = ic(r["_dens"], B["_dens"])
        sobe = (r["densidade"] or 0) > (B["densidade"] or 0)
        x = bool(sobe and i[0] > 0)
        danos = []
        if r["linhas_duplicadas"] > B["linhas_duplicadas"]:
            danos.append(f"linhas duplicadas: {r['linhas_duplicadas']} "
                         f"contra {B['linhas_duplicadas']}")
        for campo, nome in (("plagiou", "plágio"),
                            ("truncadas", "truncatura"),
                            ("falhas_guarda", "falhas de guarda"),
                            ("suspeitas", "palavras suspeitas")):
            if r[campo] > B[campo]:
                danos.append(f"{nome}: {r[campo]} contra {B[campo]}")
        if r["e_verso"] < B["e_verso"]:
            danos.append(f"e_verso: {r['e_verso']} contra {B['e_verso']}")
        if (r["metro_dist_ao_poeta"] or 0) > (B["metro_dist_ao_poeta"] or 0):
            danos.append(f"metro afasta-se do poeta: {r['metro']} contra "
                         f"{B['metro']} (poeta {POETA_METRO})")
        portoes[b] = {
            "densidade": r["densidade"], "densidade_B": B["densidade"],
            "diferenca": round((r["densidade"] or 0) - (B["densidade"] or 0), 5),
            "ic95": i, "exclui_zero": i[0] > 0 or i[1] < 0,
            "acima_do_proprio_nulo_binario":
                r["rima_binaria"] > r["nulo_permutacao"]["p99"],
            "dispara": x,
            "X3": {"danos": danos, "dispara": not danos}}

    x1 = portoes["P"]["dispara"]
    x2 = portoes["T"]["dispara"]
    passa = [b for b in ("P", "T")
             if portoes[b]["dispara"] and portoes[b]["X3"]["dispara"]]

    out = {"_meta": {"protocolo": "docs/FASE-5X.md §2.1-3",
                     "fixado_antes_dos_dados": True,
                     "desfecho": "densidade de rima (5W §1)",
                     "potencia": "medida na 5W: meia-largura ~0,008 com 20 por "
                                 "braco, logo detecta uma DUPLICACAO",
                     "regua": {"poeta_densidade": POETA_DENSIDADE,
                               "poeta_metro": POETA_METRO,
                               "poeta_rima_binaria": POETA_RIMA_BINARIA},
                     "semente": SEMENTE},
           "por_braco": {b: {k: v for k, v in res[b].items()
                             if not k.startswith("_")} for b in BRACOS},
           "X1_penalizacao": portoes["P"],
           "X2_temperatura": portoes["T"],
           "X4": {"dispara": not (x1 or x2),
                  "leitura": "nem o prompt nem a descodificacao alcancam a "
                             "forma; sobra afinacao ou aceitar uma voz"},
           "decisao_pre_escrita": {
               "bracos_que_passam_X_e_X3": passa,
               "embarca": False,
               "porque": "o §3.1: o _opcoes e GLOBAL e o Caeiro e a unica voz "
                         "que funciona (AUC 0,526). O que isto autoriza e "
                         "abrir uma fase de verificacao de dano no Caeiro"}}
    with open(os.path.join(AQUI, "02-resultados.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print(f"\n{'braço':6s} {'rp':>4s} {'temp':>5s} {'densid':>8s} {'×poeta':>7s} "
          f"{'rima':>6s} {'nulo':>6s} {'dupl':>6s} {'plág':>5s} {'trunc':>6s} "
          f"{'guar':>5s} {'verso':>6s} {'metro':>6s} {'seg':>5s}")
    for b in BRACOS:
        r = res[b]
        o = r["opcoes"] or {}
        print(f"{b:6s} {o.get('repeat_penalty', 0):4.1f} "
              f"{o.get('temperature', 0):5.1f} {r['densidade']:8.5f} "
              f"{r['razao_ao_poeta']:7.1f} {r['rima_binaria']:6.3f} "
              f"{r['nulo_permutacao']['p99']:6.3f} {r['linhas_duplicadas']:6.3f} "
              f"{r['plagiou']:5d} {r['truncadas']:6d} {r['falhas_guarda']:5d} "
              f"{r['e_verso']:6.2f} {r['metro']:6.3f} {r['segundos_mediana']:5.0f}")
    print(f"\npoeta: densidade {POETA_DENSIDADE}  metro {POETA_METRO}  "
          f"rima binária {POETA_RIMA_BINARIA}")
    for b, nome in (("P", "X1 — a penalização proíbe a rima"),
                    ("T", "X2 — menos entropia dá mais rima")):
        p = portoes[b]
        print(f"\n{nome}")
        print(f"  densidade {p['densidade']:.5f} contra {p['densidade_B']:.5f} "
              f"-> {p['diferenca']:+.5f}   IC95 {p['ic95']}  "
              f"{'EXCLUI ZERO' if p['exclui_zero'] else 'contém zero'}")
        print(f"  -> {'DISPARA' if p['dispara'] else 'nao dispara'}")
        print(f"  X3 {'DISPARA (sem dano)' if p['X3']['dispara'] else 'NAO DISPARA'}")
        for d in p["X3"]["danos"]:
            print(f"     dano: {d}")
    print(f"\nX4 {'DISPARA' if not (x1 or x2) else 'nao dispara'}")
    print(f"\ndecisão do §3.1: passam {passa} · embarca "
          f"**não** (o `_opcoes` é global; falta o dano no Caeiro)")
    print(f"\n-> {os.path.join(AQUI, '02-resultados.json')}")


if __name__ == "__main__":
    main()
