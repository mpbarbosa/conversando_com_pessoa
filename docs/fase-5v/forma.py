#!/usr/bin/env python
"""Fase 5V / A1–A3 — rima e metro, calibrados nos poemas reais antes do gerado.

Protocolo: [`../FASE-5V.md`](../FASE-5V.md) §2–4.

**I-R** rima: existe, dentro do poema, um par de versos cuja chave **consoante**
coincide — acima do que o acaso dá, medido por **permutação** dos finais de
verso entre poemas da mesma voz (§2.1).

**I-M** metro: fracção de versos a **±1 sílaba** da mediana do poema, por
contagem de grupos de vogais, **sem elisão** (§2.2).

A ordem é a do protocolo e é a lição da 5T: **V1 e V2 correm nos poemas reais
antes de o alvo ser olhado.** Se a ordenação entre vozes autênticas não
aparecer, o instrumento morre e a fase acaba ali.

Escreve `01-forma.json`.
"""
from __future__ import annotations

import json
import os
import random
import re
import statistics as st
import sys
import unicodedata
from collections import Counter

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)

from src.corpus.models import Lang, Voice                   # noqa: E402
from src.corpus.parse import parse_corpus                   # noqa: E402

SEMENTE = 20261008
N_PERMUTACOES = 2000
N_REAMOSTRAS = 4000
#: §2.2 — a tolerancia do metro regular.
TOLERANCIA_SILABAS = 1

_VOGAIS = "aeiouàáâãèéêìíîòóôõùúûy"
_RE_PALAVRA = re.compile(r"[a-zà-ÿ]+(?:-[a-zà-ÿ]+)*", re.I)
#: Grupo de vogais = uma silaba, por aproximacao. Subconta (sem hiato) e
#: subconta igual nos dois lados da comparacao (§5.1).
_RE_GRUPO_VOGAL = re.compile(f"[{_VOGAIS}]+", re.I)


def _sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s.lower())
                   if not unicodedata.combining(c))


def versos(texto: str) -> list[str]:
    return [l.strip() for l in texto.split("\n") if l.strip()]


def silabas(verso: str) -> int:
    """§2.2 — grupos de vogais na linha."""
    return sum(len(_RE_GRUPO_VOGAL.findall(p))
               for p in _RE_PALAVRA.findall(verso))


def chaves(verso: str) -> tuple[str, str] | None:
    """(toante, consoante) da última palavra do verso. §2.1.

    **toante**: do último grupo de vogais até ao fim.
    **consoante**: do penúltimo grupo de vogais até ao fim — aproxima a rima a
    partir da tónica, que acerta nas paroxítonas e erra nas oxítonas (§5.2).
    """
    pals = _RE_PALAVRA.findall(verso)
    if not pals:
        return None
    w = _sem_acento(pals[-1])
    gs = list(_RE_GRUPO_VOGAL.finditer(w))
    if not gs:
        return None
    toante = w[gs[-1].start():]
    consoante = w[gs[-2].start():] if len(gs) >= 2 else toante
    return toante, consoante


def rima(texto: str, qual: int = 1) -> bool:
    """Há um par de versos com a mesma chave? `qual` 0 = toante, 1 = consoante."""
    ks = [c[qual] for c in (chaves(v) for v in versos(texto)) if c]
    return len(ks) != len(set(ks))


def regularidade(texto: str) -> float | None:
    """§2.2 — fracção de versos a ±1 sílaba da mediana do poema."""
    ns = [silabas(v) for v in versos(texto)]
    ns = [n for n in ns if n]
    if len(ns) < 3:
        return None
    m = st.median(ns)
    return sum(1 for n in ns if abs(n - m) <= TOLERANCIA_SILABAS) / len(ns)


# --------------------------------------------------------------------------- #
def nulo_por_permutacao(textos: list[str], qual: int = 1) -> dict:
    """§2.1 — embaralha os finais de verso ENTRE poemas e recalcula a rima.

    Preserva o número de versos de cada poema e a bolsa de terminações da voz,
    logo mede exactamente a taxa de rima **por acaso** nesta língua e nesta voz.
    """
    porpoema = []
    bolsa: list[str] = []
    for t in textos:
        ks = [c[qual] for c in (chaves(v) for v in versos(t)) if c]
        porpoema.append(len(ks))
        bolsa.extend(ks)
    rng = random.Random(SEMENTE)
    taxas = []
    for _ in range(N_PERMUTACOES):
        rng.shuffle(bolsa)
        i = 0
        acertos = 0
        for n in porpoema:
            fatia = bolsa[i:i + n]
            i += n
            if len(fatia) != len(set(fatia)):
                acertos += 1
        taxas.append(acertos / len(porpoema))
    taxas.sort()
    return {"media": round(st.mean(taxas), 4),
            "p95": round(taxas[int(0.95 * len(taxas))], 4),
            "p99": round(taxas[int(0.99 * len(taxas))], 4)}


def ic_bootstrap(a: list[float], b: list[float]) -> dict:
    """IC95 da diferença de médias (a − b), reamostrando itens."""
    if not a or not b:
        return {"diferenca": None}
    rng = random.Random(SEMENTE)
    dif = []
    for _ in range(N_REAMOSTRAS):
        ma = st.mean(a[rng.randrange(len(a))] for _ in a)
        mb = st.mean(b[rng.randrange(len(b))] for _ in b)
        dif.append(ma - mb)
    dif.sort()
    lo, hi = dif[int(0.025 * len(dif))], dif[int(0.975 * len(dif)) - 1]
    return {"a": round(st.mean(a), 4), "b": round(st.mean(b), 4),
            "diferenca": round(st.mean(a) - st.mean(b), 4),
            "ic95": [round(lo, 4), round(hi, 4)],
            "exclui_zero": lo > 0 or hi < 0, "n_a": len(a), "n_b": len(b)}


def perfil(textos: list[str]) -> dict:
    reg = [r for r in (regularidade(t) for t in textos) if r is not None]
    return {"n": len(textos),
            "rima_consoante": round(sum(rima(t, 1) for t in textos)
                                    / len(textos), 4) if textos else None,
            "rima_toante": round(sum(rima(t, 0) for t in textos)
                                 / len(textos), 4) if textos else None,
            "regularidade_media": round(st.mean(reg), 4) if reg else None,
            "versos_mediana": (st.median(len(versos(t)) for t in textos)
                               if textos else None),
            "silabas_mediana": (st.median(
                [s for t in textos for s in map(silabas, versos(t)) if s])
                if textos else None)}


def main() -> None:
    poemas = [p for p in parse_corpus(os.path.join(RAIZ, "data/pessoa_poems"))
              if p.language is Lang.PT]
    reais = {v: [p.body for p in poemas if p.voice is v]
             for v in (Voice.REIS, Voice.CAMPOS, Voice.ORTONIMO, Voice.CAEIRO)}
    print({v.value: len(t) for v, t in reais.items()})

    # ================= A2: calibracao, SO em poemas reais ================ #
    cal = {}
    for v, ts in reais.items():
        p = perfil(ts)
        p["nulo_permutacao_consoante"] = nulo_por_permutacao(ts, 1)
        cal[v.value] = p

    r_reis = cal["reis"]["rima_consoante"]
    nulo_reis = cal["reis"]["nulo_permutacao_consoante"]
    v1 = (r_reis > nulo_reis["p99"]
          and r_reis > cal["caeiro"]["rima_consoante"])
    v2 = cal["reis"]["regularidade_media"] > cal["campos"]["regularidade_media"]

    print("\n=== A2 — calibração nos poemas REAIS (§3) ===")
    print(f"{'voz':10s} {'n':>5s} {'rima cons':>10s} {'nulo p99':>9s} "
          f"{'rima toan':>10s} {'regular.':>9s} {'versos':>7s} {'síl':>5s}")
    for v, p in cal.items():
        print(f"{v:10s} {p['n']:5d} {p['rima_consoante']:10.4f} "
              f"{p['nulo_permutacao_consoante']['p99']:9.4f} "
              f"{p['rima_toante']:10.4f} {p['regularidade_media']:9.4f} "
              f"{p['versos_mediana']:7.1f} {p['silabas_mediana']:5.1f}")
    print(f"\nV1 (rima: Reis > nulo p99 E Reis > Caeiro): "
          f"{'DISPARA' if v1 else 'NAO DISPARA'}")
    print(f"V2 (metro: Reis mais regular que Campos):   "
          f"{'DISPARA' if v2 else 'NAO DISPARA'}")

    out = {"_meta": {"protocolo": "docs/FASE-5V.md §2-4",
                     "semente": SEMENTE, "permutacoes": N_PERMUTACOES,
                     "reamostras": N_REAMOSTRAS,
                     "silabas": "grupos de vogais, sem elisao (§5.1)",
                     "chave_consoante": "desde a penultima vogal (§5.2)"},
           "A2_calibracao_reais": cal,
           "V1": {"rima_reis": r_reis, "nulo_p99": nulo_reis["p99"],
                  "rima_caeiro": cal["caeiro"]["rima_consoante"],
                  "dispara": v1},
           "V2": {"regularidade_reis": cal["reis"]["regularidade_media"],
                  "regularidade_campos": cal["campos"]["regularidade_media"],
                  "dispara": v2}}

    # ================= A3: real contra gerado, por voz =================== #
    if not (v1 or v2):
        out["V3"] = {"corrido": False,
                     "razao": "nenhum instrumento calibrou (§4)"}
        print("\nnenhum instrumento calibrou: o V3 não corre (§4)")
    else:
        ger: dict[str, list[str]] = {}
        # 5U braco C: configuracao de producao, 60 amostras
        for l in open(os.path.join(RAIZ, "docs/fase-5u/01-cru.jsonl"),
                      encoding="utf-8"):
            d = json.loads(l)
            if d["braco"] == "C":
                ger.setdefault(d["voz"], []).append(d["texto_cru"])
        n5u = {k: len(v) for k, v in ger.items()}
        # 5M: 180, dois modelos
        g5m: dict[str, list[str]] = {}
        for l in open(os.path.join(RAIZ, "docs/fase-5m/01-cru.jsonl"),
                      encoding="utf-8"):
            d = json.loads(l)
            g5m.setdefault(d["voz"], []).append(d["texto"])
        print(f"\ngerado: 5U braço C {n5u}  ·  5M {{k: len(v) for...}} "
              f"{ {k: len(v) for k, v in g5m.items()} }")

        v3 = {}
        for voz, ts_ger in sorted(ger.items()):
            ts_real = reais[Voice(voz)]
            bloco = {"n_gerado_5u": len(ts_ger), "n_real": len(ts_real),
                     "perfil_gerado_5u": perfil(ts_ger),
                     "perfil_gerado_5m": perfil(g5m.get(voz, [])),
                     "perfil_real": perfil(ts_real)}
            if v1:
                bloco["rima"] = ic_bootstrap(
                    [float(rima(t, 1)) for t in ts_real],
                    [float(rima(t, 1)) for t in ts_ger])
                bloco["rima_5m"] = ic_bootstrap(
                    [float(rima(t, 1)) for t in ts_real],
                    [float(rima(t, 1)) for t in g5m.get(voz, [])])
            if v2:
                bloco["metro"] = ic_bootstrap(
                    [r for r in map(regularidade, ts_real) if r is not None],
                    [r for r in map(regularidade, ts_ger) if r is not None])
                bloco["metro_5m"] = ic_bootstrap(
                    [r for r in map(regularidade, ts_real) if r is not None],
                    [r for r in map(regularidade, g5m.get(voz, []))
                     if r is not None])
            v3[voz] = bloco
        out["V3"] = v3
        algum = any(bloco.get(k, {}).get("exclui_zero")
                    for bloco in v3.values() for k in ("rima", "metro"))
        out["V3_dispara"] = algum
        out["V4"] = {"dispara": not algum}

        print("\n=== A3 — real contra gerado, por voz (5U braço C) ===")
        for voz, b in v3.items():
            print(f"\n  {voz}  (real n={b['n_real']}, gerado n={b['n_gerado_5u']})")
            for k in ("rima", "metro"):
                if k in b and b[k]["diferenca"] is not None:
                    r = b[k]
                    print(f"    {k:6s} real={r['a']:.4f} gerado={r['b']:.4f} "
                          f"dif={r['diferenca']:+.4f} "
                          f"IC95=[{r['ic95'][0]:+.4f}, {r['ic95'][1]:+.4f}]  "
                          f"{'EXCLUI ZERO' if r['exclui_zero'] else 'contém zero'}")
                    r2 = b[k + "_5m"]
                    if r2["diferenca"] is not None:
                        print(f"    {'':6s} 5M: gerado={r2['b']:.4f} "
                              f"dif={r2['diferenca']:+.4f} "
                              f"IC95=[{r2['ic95'][0]:+.4f}, "
                              f"{r2['ic95'][1]:+.4f}]  "
                              f"{'EXCLUI ZERO' if r2['exclui_zero'] else 'contém zero'}")
        print(f"\nV3 {'DISPARA' if algum else 'nao dispara'}   ·   "
              f"V4 {'DISPARA' if not algum else 'nao dispara'}")

    with open(os.path.join(AQUI, "01-forma.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"\n-> {os.path.join(AQUI, '01-forma.json')}")


if __name__ == "__main__":
    main()
