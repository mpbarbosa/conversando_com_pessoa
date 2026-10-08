#!/usr/bin/env python
"""Fase 5W / A3–B1 — os portões da intervenção.

Protocolo: [`../FASE-5W.md`](../FASE-5W.md) §3–4. **Fixado antes de os dados
existirem**, como o da 5U.

**Desfecho** (§3): rima pelo detector da 5V, com os pares de **palavra igual
excluídos** — logo imune à maneira mais barata de fingir. Duas chaves
co-primárias, cada uma contra o **nulo de permutação do seu braço**:

- **consoante**, que a 5V calibrou contra as quatro poéticas. **É a que decide.**
- **toante**, que vê as oxítonas que a consoante não vê (ponto cego declarado
  no §3) e colide mais por acaso — daí o nulo.

**W3 tem veto** (§4): rimar escrevendo pior não é rimar. As medidas que o
vigiam já existiam todas antes desta fase.

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

from forma import (_RE_PALAVRA, _sem_acento, chaves,          # noqa: E402
                   nulo_por_permutacao, regularidade, versos)
from corrigir import nulo_sem_repeticao, rima_sem_repeticao    # noqa: E402
from src.corpus.build import load                              # noqa: E402
from src.corpus.models import Lang, Voice                      # noqa: E402
from src.corpus.parse import parse_corpus                       # noqa: E402
from src.guard import e_verso                                  # noqa: E402
from src.plagio import analisar                                # noqa: E402

SEMENTE = 20261008
N_REAMOSTRAS = 4000
#: §4 W1 — o meio do caminho entre o 0,2167 medido e o 0,7769 do poeta, e
#: acima de qualquer nulo que a 5V viu (0,21-0,32).
LIMIAR_W1 = 0.50
#: §1 — o que a 5V mediu, e entra como dado.
REAL_RIMA = 0.7769
REAL_METRO = 0.7572
GERADO_RIMA_5V = 0.2167
BRACOS = ("C", "R", "X")


#: ## A chave corrigida, encontrada **antes** de os dados desta fase existirem
#:
#: A chave consoante da 5V parte do penultimo **grupo** de vogais, e o
#: `_RE_GRUPO_VOGAL` junta `ia` num grupo so. Consequencia: em `havia` os grupos
#: sao `a` e `ia`, logo a chave e `avia`; em `servia` e `ervia`. **Nao casam** —
#: e `havia`/`servia` e uma rima de manual.
#:
#: A correccao e partir da penultima **vogal-letra**: `havia` -> `ia`,
#: `servia` -> `ia`. Casa.
#:
#: **Re-corri a 5V com esta chave e as conclusoes dela nao mudam — melhoram.**
#: Ortonimo real 0,8367 contra um nulo de 0,3549; ortonimo gerado 0,3833 contra
#: um nulo de **0,3833** (outra vez exactamente o proprio nulo). Reis real
#: 0,2709 contra nulo 0,2709 («sem rima», e cumpre). Caeiro real 0,1917
#: **abaixo** do nulo 0,3500. Ver `03-rechecagem-5v.json`.
#:
#: Aqui vai como **co-primaria**: o §3 do protocolo diz que a consoante decide,
#: e a decisao de embarcar exige que **as duas concordem** — que e conservador
#: na direccao certa.
def chave_letra(verso: str) -> str | None:
    """Chave consoante a partir da penúltima **vogal-letra**."""
    pals = _RE_PALAVRA.findall(verso)
    if not pals:
        return None
    w = _sem_acento(pals[-1])
    idx = [i for i, ch in enumerate(w) if ch in "aeiouy"]
    if not idx:
        return None
    return w[idx[-2]:] if len(idx) >= 2 else w[idx[-1]:]


def _pares(texto: str, chave) -> list[tuple[str, str]]:
    out = []
    for v in versos(texto):
        k = chave(v)
        pals = _RE_PALAVRA.findall(v)
        if k and pals:
            out.append((k if isinstance(k, str) else k[1],
                        _sem_acento(pals[-1])))
    return out


def rima_letra(texto: str) -> bool:
    ps = _pares(texto, chave_letra)
    return any(ps[i][0] == ps[j][0] and ps[i][1] != ps[j][1]
               for i in range(len(ps)) for j in range(i + 1, len(ps)))


def nulo_letra(textos: list[str], n: int = 1500) -> dict:
    por, bolsa = [], []
    for t in textos:
        ps = _pares(t, chave_letra)
        por.append(len(ps))
        bolsa.extend(ps)
    rng = random.Random(SEMENTE)
    taxas = []
    for _ in range(n):
        rng.shuffle(bolsa)
        i, a = 0, 0
        for m in por:
            f = bolsa[i:i + m]
            i += m
            a += any(f[x][0] == f[y][0] and f[x][1] != f[y][1]
                     for x in range(len(f)) for y in range(x + 1, len(f)))
        taxas.append(a / len(por))
    taxas.sort()
    return {"media": round(st.mean(taxas), 4),
            "p99": round(taxas[int(0.99 * len(taxas))], 4)}


def rima_toante_sem_repeticao(texto: str) -> bool:
    """Como a `rima_sem_repeticao` da 5V, mas com a chave **toante**."""
    pares = []
    for v in versos(texto):
        pals = _RE_PALAVRA.findall(v)
        c = chaves(v)
        if c and pals:
            pares.append((c[0], _sem_acento(pals[-1])))
    for i in range(len(pares)):
        for j in range(i + 1, len(pares)):
            if pares[i][0] == pares[j][0] and pares[i][1] != pares[j][1]:
                return True
    return False


def ic_diferenca(a: list[float], b: list[float]) -> list[float]:
    """IC95 de média(a) − média(b), reamostrando itens."""
    rng = random.Random(SEMENTE)
    ds = []
    for _ in range(N_REAMOSTRAS):
        ma = st.mean(a[rng.randrange(len(a))] for _ in a)
        mb = st.mean(b[rng.randrange(len(b))] for _ in b)
        ds.append(ma - mb)
    ds.sort()
    return [round(ds[int(0.025 * len(ds))], 4),
            round(ds[int(0.975 * len(ds)) - 1], 4)]


def terminacoes(textos: list[str]) -> list:
    from collections import Counter
    c = Counter()
    for t in textos:
        for v in versos(t):
            k = chaves(v)
            if k:
                c[k[1]] += 1
    return c.most_common(8)


def main() -> None:
    cru = [json.loads(l) for l in
           open(os.path.join(AQUI, "01-cru.jsonl"), encoding="utf-8")
           if l.strip()]
    print(f"{len(cru)} amostras")
    porbraco = {b: [d for d in cru if d["braco"] == b] for b in BRACOS}
    print({b: len(v) for b, v in porbraco.items()})

    _, chunks = load()
    poemas = [p for p in parse_corpus(os.path.join(RAIZ, "data/pessoa_poems"))
              if p.language is Lang.PT and p.voice is Voice.ORTONIMO]
    assert poemas, "sem poemas do ortónimo"

    res = {}
    for b in BRACOS:
        ts = [d["texto_cru"] for d in porbraco[b]]
        ds = porbraco[b]
        rc = [float(rima_sem_repeticao(t)) for t in ts]
        rt = [float(rima_toante_sem_repeticao(t)) for t in ts]
        rl = [float(rima_letra(t)) for t in ts]
        met = [x for x in map(regularidade, ts) if x is not None]
        plg = [analisar(d["texto_limpo"], tuple(
            c for c in chunks if c.poem_id in d["usados"])) for d in ds]
        res[b] = {
            "n": len(ts),
            "rima_consoante": round(st.mean(rc), 4),
            "nulo_consoante": nulo_sem_repeticao(ts),
            "rima_letra": round(st.mean(rl), 4),
            "nulo_letra": nulo_letra(ts),
            "rima_toante": round(st.mean(rt), 4),
            "nulo_toante": nulo_por_permutacao(ts, 0),
            "_rc": rc, "_rt": rt, "_rl": rl, "_met": met,
            # ---- W3: o dano colateral ---------------------------------- #
            "metro_medio": round(st.mean(met), 4) if met else None,
            "metro_dist_ao_poeta": (round(abs(st.mean(met) - REAL_METRO), 4)
                                    if met else None),
            "e_verso": round(sum(e_verso(t) for t in ts) / len(ts), 4),
            "plagiou": sum(1 for a in plg if a.plagiou),
            "fracao_copiada_mediana": round(
                st.median(a.fracao_copiada for a in plg), 4),
            "truncadas": sum(1 for d in ds if d["truncada"]),
            "tentativas_2": sum(1 for d in ds if d["tentativas"] > 1),
            "falhas_guarda": sum(len(d["motivos_guarda"]) for d in ds),
            "suspeitas": sum(len(d["suspeitas"]) for d in ds),
            "versos_mediana": st.median(len(versos(t)) for t in ts),
            "tokens_system": sorted({d["tokens_system"] for d in ds}),
            "segundos_mediana": round(st.median(d["segundos"] for d in ds), 1),
            "terminacoes_mais_usadas": terminacoes(ts)}

    C = res["C"]
    portoes = {}
    for b in ("R", "X"):
        r = res[b]
        acima_nulo = r["rima_consoante"] > r["nulo_consoante"]["p99"]
        ic = ic_diferenca(r["_rc"], C["_rc"])
        passa_limiar = r["rima_consoante"] > LIMIAR_W1
        w1 = bool(passa_limiar and acima_nulo and ic[0] > 0)
        # a chave-letra, co-primaria: a decisao exige que as duas concordem
        acima_nulo_l = r["rima_letra"] > r["nulo_letra"]["p99"]
        ic_l = ic_diferenca(r["_rl"], C["_rl"])
        w1_letra = bool(r["rima_letra"] > LIMIAR_W1 and acima_nulo_l
                        and ic_l[0] > 0)
        # ---- W3, com veto ------------------------------------------------ #
        danos = []
        if (r["metro_dist_ao_poeta"] or 0) > (C["metro_dist_ao_poeta"] or 0):
            danos.append(f"metro afasta-se do poeta ({r['metro_medio']} "
                         f"contra {C['metro_medio']}, poeta {REAL_METRO})")
        for campo, nome in (("plagiou", "plágio"), ("truncadas", "truncatura"),
                            ("falhas_guarda", "falhas de guarda"),
                            ("suspeitas", "palavras suspeitas")):
            if r[campo] > C[campo]:
                danos.append(f"{nome}: {r[campo]} contra {C[campo]}")
        if r["e_verso"] < C["e_verso"]:
            danos.append(f"e_verso: {r['e_verso']} contra {C['e_verso']}")
        portoes[b] = {
            "W1": {"rima": r["rima_consoante"], "limiar": LIMIAR_W1,
                   "passa_limiar": passa_limiar,
                   "nulo_p99": r["nulo_consoante"]["p99"],
                   "acima_do_nulo": acima_nulo,
                   "ic95_contra_C": ic, "exclui_zero": ic[0] > 0,
                   "dispara": w1},
            "W1_chave_letra": {"rima": r["rima_letra"],
                               "nulo_p99": r["nulo_letra"]["p99"],
                               "acima_do_nulo": acima_nulo_l,
                               "ic95_contra_C": ic_l, "dispara": w1_letra},
            "as_duas_chaves_concordam": w1 == w1_letra,
            "W3": {"danos": danos, "dispara": not danos}}

    ic_xr = ic_diferenca(res["X"]["_rc"], res["R"]["_rc"])
    w2 = bool(res["X"]["rima_consoante"] > res["R"]["rima_consoante"]
              and ic_xr[0] > 0)
    # §4.1 com a co-primaria: embarcar exige W1 nas DUAS chaves, e W3
    algum = [b for b in ("R", "X")
             if portoes[b]["W1"]["dispara"]
             and portoes[b]["W1_chave_letra"]["dispara"]
             and portoes[b]["W3"]["dispara"]]
    if len(algum) == 2:
        escolhido = max(algum, key=lambda b: res[b]["rima_consoante"])
        if ic_xr[0] <= 0 <= ic_xr[1]:
            escolhido = "R"          # §4.1: empate -> o mais curto
    else:
        escolhido = algum[0] if algum else None

    out = {"_meta": {"protocolo": "docs/FASE-5W.md §3-4",
                     "fixado_antes_dos_dados": True,
                     "decide": "chave consoante (§3)",
                     "dados_da_5V": {"real_rima": REAL_RIMA,
                                     "real_metro": REAL_METRO,
                                     "gerado_rima_5V": GERADO_RIMA_5V},
                     "semente": SEMENTE, "reamostras": N_REAMOSTRAS},
           "por_braco": {b: {k: v for k, v in res[b].items()
                             if not k.startswith("_")} for b in BRACOS},
           "portoes": portoes,
           "W2": {"X": res["X"]["rima_consoante"],
                  "R": res["R"]["rima_consoante"],
                  "ic95_X_menos_R": ic_xr, "dispara": w2,
                  "predicao_registada": "5U §1.3, a escorva por exemplos"},
           "W4": {"dispara": not algum},
           "decisao_pre_escrita": {"bracos_que_passam": algum,
                                   "escolhido": escolhido}}
    with open(os.path.join(AQUI, "02-resultados.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print(f"\n{'braço':6s} {'n':>3s} {'rima c':>7s} {'nulo':>6s} "
          f"{'rima L':>7s} {'nulo':>6s} {'rima t':>7s} {'nulo':>6s} "
          f"{'metro':>6s} {'verso':>6s} "
          f"{'plág':>5s} {'trunc':>6s} {'guar':>5s} {'susp':>5s} {'tok':>5s}")
    for b in BRACOS:
        r = res[b]
        print(f"{b:6s} {r['n']:3d} {r['rima_consoante']:7.4f} "
              f"{r['nulo_consoante']['p99']:6.4f} {r['rima_letra']:7.4f} "
              f"{r['nulo_letra']['p99']:6.4f} {r['rima_toante']:7.4f} "
              f"{r['nulo_toante']['p99']:6.4f} {r['metro_medio']:6.4f} "
              f"{r['e_verso']:6.2f} {r['plagiou']:5d} {r['truncadas']:6d} "
              f"{r['falhas_guarda']:5d} {r['suspeitas']:5d} "
              f"{r['tokens_system'][0]:5d}")
    print(f"\npoeta (5V): rima {REAL_RIMA}   metro {REAL_METRO}")
    for b in ("R", "X"):
        p = portoes[b]
        print(f"\n--- braço {b} ---")
        w = p["W1"]
        print(f"  W1  rima {w['rima']:.4f} > {LIMIAR_W1} ? "
              f"{w['passa_limiar']}   > nulo {w['nulo_p99']:.4f} ? "
              f"{w['acima_do_nulo']}   IC contra C {w['ic95_contra_C']} "
              f"exclui zero? {w['exclui_zero']}")
        print(f"      -> {'DISPARA' if w['dispara'] else 'nao dispara'}")
        wl = p["W1_chave_letra"]
        print(f"  W1' chave-letra {wl['rima']:.4f} > {LIMIAR_W1}, "
              f"nulo {wl['nulo_p99']:.4f}, IC {wl['ic95_contra_C']} "
              f"-> {'DISPARA' if wl['dispara'] else 'nao dispara'}"
              f"   (concordam? {p['as_duas_chaves_concordam']})")
        print(f"  W3  {'DISPARA (sem dano)' if p['W3']['dispara'] else 'NAO DISPARA'}")
        for d in p["W3"]["danos"]:
            print(f"      dano: {d}")
    print(f"\nW2 (X > R, a escorva da 5U): X {res['X']['rima_consoante']:.4f} "
          f"contra R {res['R']['rima_consoante']:.4f}, IC {ic_xr} -> "
          f"{'DISPARA' if w2 else 'nao dispara'}")
    print(f"W4 {'DISPARA' if not algum else 'nao dispara'}")
    print(f"\ndecisão do §4.1: braços que passam {algum} -> **{escolhido}**")
    for b in BRACOS:
        print(f"\nterminações mais usadas, {b}: "
              f"{res[b]['terminacoes_mais_usadas']}")
    print(f"\n-> {os.path.join(AQUI, '02-resultados.json')}")


if __name__ == "__main__":
    main()
