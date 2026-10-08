#!/usr/bin/env python
"""Fase 5V / A4–A6 — a calibração corrigida, e o que o metro mede de facto.

Protocolo: [`../FASE-5V.md`](../FASE-5V.md). **Tudo aqui é posterior aos dados e
declarado como tal.**

## A1. O erro que o V1 apanhou era meu, e não do detector

O §1 do protocolo escreveu «o Reis manda *metro regular e rima*». **Não manda.**
`src/voices.py`, que é anterior a esta fase e independente dos dados que ela
mede:

| voz | o que a persona manda de forma |
|---|---|
| **Reis** | «Ode breve. Estrofes curtas e regulares … **sem rima**.» |
| **ortónimo** | «**Metro regular e rima.** Quadras ou quintilhas.» |

Atribuí ao Reis a instrução do **ortónimo**. As odes de Ricardo Reis são verso
branco, e o par de calibração certo é **ortónimo (rima) contra Reis (sem
rima)** — não Reis contra Caeiro.

**O V1, como o pré-registei, não dispara. E não dispara por eu ter nomeado as
vozes erradas**, o que é diferente de o detector não funcionar. Corre-se aqui a
calibração certa, com a premissa a vir do `voices.py` e não do resultado.

## A2. E a chave de rima pode estar a contar repetição

Caeiro — verso livre — rima a 0,6417 contra um nulo de 0,4167. A suspeita tem
mecanismo: Caeiro **repete palavras** («uma árvore é uma árvore») e Campos faz
**anáfora por instrução**. Dois versos que acabam na **mesma palavra** dão
chaves idênticas e contam como rima. Testa-se excluindo os pares cuja última
**palavra** coincide.

## A3. O metro: a AUC e a amplitude entre vozes

O V3 pré-registado já disparou pelo IC. A AUC e a amplitude são **descritivas e
posteriores**, e servem para uma coisa só: ver se a forma tem tamanho para
explicar o 0,938–1,000 da [5Q](../FASE-5Q-RELATORIO.md).

Escreve `02-correccao.json`.
"""
from __future__ import annotations

import json
import os
import random
import re
import statistics as st
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)
sys.path.insert(0, AQUI)

from forma import (_RE_GRUPO_VOGAL, _RE_PALAVRA, _sem_acento,  # noqa: E402
                   chaves, nulo_por_permutacao, regularidade, versos)
from src.corpus.models import Lang, Voice                       # noqa: E402
from src.corpus.parse import parse_corpus                       # noqa: E402

SEMENTE = 20261008
N_REAMOSTRAS = 4000


def rima_sem_repeticao(texto: str) -> bool:
    """Rima consoante, **excluindo** pares que acabam na mesma palavra (A2)."""
    pares = []
    for v in versos(texto):
        pals = _RE_PALAVRA.findall(v)
        c = chaves(v)
        if c and pals:
            pares.append((c[1], _sem_acento(pals[-1])))
    for i in range(len(pares)):
        for j in range(i + 1, len(pares)):
            if pares[i][0] == pares[j][0] and pares[i][1] != pares[j][1]:
                return True
    return False


def nulo_sem_repeticao(textos: list[str]) -> dict:
    """Nulo de permutação para a chave sem repetição."""
    porpoema, bolsa = [], []
    for t in textos:
        ps = []
        for v in versos(t):
            pals = _RE_PALAVRA.findall(v)
            c = chaves(v)
            if c and pals:
                ps.append((c[1], _sem_acento(pals[-1])))
        porpoema.append(len(ps))
        bolsa.extend(ps)
    rng = random.Random(SEMENTE)
    taxas = []
    for _ in range(2000):
        rng.shuffle(bolsa)
        i, acertos = 0, 0
        for n in porpoema:
            f = bolsa[i:i + n]
            i += n
            ok = any(f[a][0] == f[b][0] and f[a][1] != f[b][1]
                     for a in range(len(f)) for b in range(a + 1, len(f)))
            acertos += ok
        taxas.append(acertos / len(porpoema))
    taxas.sort()
    return {"media": round(st.mean(taxas), 4),
            "p99": round(taxas[int(0.99 * len(taxas))], 4)}


def auc(baixos: list[float], altos: list[float]) -> float:
    """Mann-Whitney, sem scipy. P(alto > baixo) + meio empate."""
    n = 0.0
    for a in altos:
        for b in baixos:
            n += 1.0 if a > b else 0.5 if a == b else 0.0
    return n / (len(altos) * len(baixos))


def auc_ic(baixos: list[float], altos: list[float]) -> dict:
    rng = random.Random(SEMENTE)
    vs = []
    for _ in range(2000):
        a = [altos[rng.randrange(len(altos))] for _ in altos]
        b = [baixos[rng.randrange(len(baixos))] for _ in baixos]
        vs.append(auc(b, a))
    vs.sort()
    return {"auc": round(auc(baixos, altos), 4),
            "ic95": [round(vs[49], 4), round(vs[1949], 4)]}


def main() -> None:
    poemas = [p for p in parse_corpus(os.path.join(RAIZ, "data/pessoa_poems"))
              if p.language is Lang.PT]
    VS = (Voice.ORTONIMO, Voice.REIS, Voice.CAMPOS, Voice.CAEIRO)
    reais = {v: [p.body for p in poemas if p.voice is v] for v in VS}

    ger5u: dict[str, list[str]] = {}
    for l in open(os.path.join(RAIZ, "docs/fase-5u/01-cru.jsonl"),
                  encoding="utf-8"):
        d = json.loads(l)
        if d["braco"] == "C":
            ger5u.setdefault(d["voz"], []).append(d["texto_cru"])
    ger5m: dict[str, list[str]] = {}
    for l in open(os.path.join(RAIZ, "docs/fase-5m/01-cru.jsonl"),
                  encoding="utf-8"):
        d = json.loads(l)
        ger5m.setdefault(d["voz"], []).append(d["texto"])

    # ---------- A1 + A2: a calibracao corrigida -------------------------- #
    cal = {}
    for v in VS:
        ts = reais[v]
        cal[v.value] = {
            "n": len(ts),
            "rima_com_repeticao": round(
                sum(1 for t in ts if (lambda k: len(k) != len(set(k)))(
                    [c[1] for c in map(chaves, versos(t)) if c])) / len(ts), 4),
            "rima_sem_repeticao": round(
                sum(rima_sem_repeticao(t) for t in ts) / len(ts), 4),
            "nulo_sem_repeticao": nulo_sem_repeticao(ts)}

    o, r = cal["ortonimo"], cal["reis"]
    v1c = (o["rima_sem_repeticao"] > o["nulo_sem_repeticao"]["p99"]
           and o["rima_sem_repeticao"] > r["rima_sem_repeticao"])

    print("=== A1/A2 — calibração CORRIGIDA: ortónimo (rima) vs Reis (sem) ===")
    print(f"{'voz':10s} {'n':>5s} {'c/ repet':>9s} {'s/ repet':>9s} "
          f"{'nulo p99':>9s}  persona")
    diz = {"ortonimo": "«metro regular e rima»", "reis": "«sem rima»",
           "campos": "«irregular», anáfora", "caeiro": "verso livre"}
    for k, c in cal.items():
        print(f"{k:10s} {c['n']:5d} {c['rima_com_repeticao']:9.4f} "
              f"{c['rima_sem_repeticao']:9.4f} "
              f"{c['nulo_sem_repeticao']['p99']:9.4f}  {diz[k]}")
    print(f"\nV1 corrigido (ortónimo > nulo p99 E ortónimo > Reis): "
          f"{'DISPARA' if v1c else 'NAO DISPARA'}")

    # ---------- A3: o metro, AUC e amplitude ---------------------------- #
    metro = {}
    for voz in ("campos", "reis", "ortonimo"):
        rr = [x for x in map(regularidade, reais[Voice(voz)]) if x is not None]
        g5u = [x for x in map(regularidade, ger5u[voz]) if x is not None]
        g5m = [x for x in map(regularidade, ger5m[voz]) if x is not None]
        metro[voz] = {
            "real_media": round(st.mean(rr), 4),
            "gerado_5u_media": round(st.mean(g5u), 4),
            "gerado_5m_media": round(st.mean(g5m), 4),
            # AUC do lado em que o gerado difere: |real - gerado| orientada
            "auc_5u": auc_ic(g5u, rr) if st.mean(rr) > st.mean(g5u)
            else auc_ic(rr, g5u),
            "auc_5m": auc_ic(g5m, rr) if st.mean(rr) > st.mean(g5m)
            else auc_ic(rr, g5m),
            "direccao": ("real mais regular" if st.mean(rr) > st.mean(g5m)
                         else "gerado mais regular")}
    amp = {"real": round(max(m["real_media"] for m in metro.values())
                         - min(m["real_media"] for m in metro.values()), 4),
           "gerado_5m": round(max(m["gerado_5m_media"] for m in metro.values())
                              - min(m["gerado_5m_media"]
                                    for m in metro.values()), 4),
           "gerado_5u": round(max(m["gerado_5u_media"] for m in metro.values())
                              - min(m["gerado_5u_media"]
                                    for m in metro.values()), 4)}

    print("\n=== A3 — o metro: AUC e amplitude entre vozes ===")
    print(f"{'voz':10s} {'real':>7s} {'5U':>7s} {'5M':>7s} {'AUC 5U':>8s} "
          f"{'AUC 5M':>8s}  direcção")
    for voz, m in metro.items():
        print(f"{voz:10s} {m['real_media']:7.4f} {m['gerado_5u_media']:7.4f} "
              f"{m['gerado_5m_media']:7.4f} {m['auc_5u']['auc']:8.3f} "
              f"{m['auc_5m']['auc']:8.3f}  {m['direccao']}")
    print(f"\namplitude entre as três vozes:  real **{amp['real']}**  ·  "
          f"gerado 5M {amp['gerado_5m']}  ·  gerado 5U {amp['gerado_5u']}")
    print(f"o poeta varia {amp['real']/max(amp['gerado_5m'],1e-9):.1f}× mais "
          f"que o modelo")

    out = {"_meta": {"protocolo": "docs/FASE-5V.md",
                     "tudo_posterior": True,
                     "erro_corrigido": "o §1 atribuiu ao Reis a instrucao do "
                                       "ortonimo; o Reis manda «sem rima»",
                     "fonte_da_premissa": "src/voices.py, anterior a esta fase"},
           "A1_A2_calibracao_corrigida": cal,
           "V1_corrigido": {"ortonimo": o["rima_sem_repeticao"],
                            "reis": r["rima_sem_repeticao"],
                            "nulo_p99_ortonimo": o["nulo_sem_repeticao"]["p99"],
                            "dispara": v1c},
           "A3_metro": metro, "amplitude_entre_vozes": amp}
    with open(os.path.join(AQUI, "02-correccao.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"\n-> {os.path.join(AQUI, '02-correccao.json')}")


if __name__ == "__main__":
    main()
