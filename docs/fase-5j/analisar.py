#!/usr/bin/env python
"""Fase 5J / B1-C1 — os quatro portões.

Protocolo: `docs/FASE-5J.md` §3 e §4. Lê `01-contagem.json` (de `contar.py`) e
as amostras da 5H, e escreve `03-resultados.json`.

Sem `scipy`, como toda a sequência desde a Fase 3B: Wilson, KS de duas amostras
e bootstrap à mão com `numpy`.
"""
from __future__ import annotations

import json
import math
import os
import random
import statistics as st
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)

SEMENTE = 20261005        # §4.5, fixada no protocolo
B = 10_000               # reamostragens, §4.4
INTERVALO_CAEIRO = (10, 20)

#: §4.4 — a regra heuristica que o protocolo declarou. **Corrigida a meio**: o
#: harness JA GRAVA `truncada`, de `done_reason == "length"` (ver
#: `src/generation/ollama.py:107`), e eu escrevi no protocolo que nao havia
#: campo. O primario passa a ser o campo gravado; a heuristica fica como
#: contra-verificacao, e o relatorio reporta onde discordam.
_TERMINAL = tuple(".!?:;…\"'»)")


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """IC de Wilson para uma proporção. §3.1 usa o limite superior."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / d
    meio = (z / d) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, centro - meio), min(1.0, centro + meio))


def ks(a: list[int], b: list[int]) -> float:
    """Estatística KS de duas amostras: max |F_a - F_b|."""
    if not a or not b:
        return float("nan")
    xs = np.array(sorted(set(a) | set(b)), dtype=float)
    av, bv = np.array(a, dtype=float), np.array(b, dtype=float)
    fa = np.searchsorted(np.sort(av), xs, side="right") / len(av)
    fb = np.searchsorted(np.sort(bv), xs, side="right") / len(bv)
    return float(np.max(np.abs(fa - fb)))


def heuristica_truncada(texto: str) -> bool:
    """A regra declarada no §4.4. Guardada só para a contra-verificação."""
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]
    return bool(linhas) and not linhas[-1].endswith(_TERMINAL)


# --------------------------------------------------------------------------- #

def portao_j1(cont: dict) -> dict:
    """§3 J1 — o defeito é das quatro vozes."""
    por_voz: dict = {}
    for voz, cel in cont["vozes"].items():
        lo, hi = cel["intervalo"]
        linha: dict = {"intervalo": [lo, hi],
                       "um_lado": lo <= 1}      # Reis: «<=12», sem piso
        # Primario: pt + versos_min3. As outras tres celulas sao as
        # sensibilidades que o §4.1 e o §4.2 declararam.
        for lingua in ("pt", "todas"):
            for defn in ("versos_min3", "nao_vazias"):
                e = cel[lingua][defn]["elegiveis"]
                inf, sup = wilson(e["dentro"], e["n"])
                bloco = {
                    "n": e["n"], "dentro": e["dentro"],
                    "fraccao": (round(e["dentro"] / e["n"], 4)
                                if e["n"] else None),
                    "wilson95": [round(inf, 4), round(sup, 4)],
                    "falha_o_intervalo": sup < 0.50,
                    "mediana": e["mediana"], "abaixo": e["abaixo"],
                    "acima": e["acima"], "min": e["min"], "max": e["max"],
                }
                if lingua == "pt" and defn == "versos_min3":
                    linha["pt"] = bloco          # primario, nome curto
                linha[f"{lingua}__{defn}"] = bloco
        por_voz[voz] = linha

    falham = [v for v, l in por_voz.items() if l["pt"]["falha_o_intervalo"]]
    # O portao aguenta as quatro combinacoes de lingua x definicao?
    robusto = {
        f"{lingua}__{defn}": sorted(
            v for v, l in por_voz.items()
            if l[f"{lingua}__{defn}"]["falha_o_intervalo"])
        for lingua in ("pt", "todas") for defn in ("versos_min3", "nao_vazias")
    }
    return {"por_voz": por_voz, "vozes_que_falham": falham,
            "n_falham": len(falham), "dispara": len(falham) >= 3,
            "sensibilidades": robusto,
            "dispara_em_todas_as_sensibilidades":
                all(len(v) >= 3 for v in robusto.values())}


def portao_j3(cont: dict) -> dict:
    """§4.3 — ortogonalidade: os excluídos são os curtos?"""
    por_voz: dict = {}
    for voz, cel in cont["vozes"].items():
        b = cel["pt"]["versos_min3"]
        exc, ret = b["excluidos"], b["elegiveis"]
        todos = b["todos"]
        inf_t, sup_t = wilson(todos["dentro"], todos["n"])
        por_voz[voz] = {
            "n_excluidos": 0 if exc is None else exc["n"],
            "mediana_excluidos": None if exc is None else exc["mediana"],
            "mediana_retidos": ret["mediana"],
            "excluidos_sao_mais_curtos": (
                None if exc is None or exc["n"] < 5
                else exc["mediana"] < ret["mediana"]),
            # sem filtro nenhum, o J1 muda de leitura?
            "sem_filtro_falha_o_intervalo": sup_t < 0.50,
            "com_filtro_falha_o_intervalo":
                wilson(ret["dentro"], ret["n"])[1] < 0.50,
        }
    informativos = [v for v, l in por_voz.items()
                    if l["excluidos_sao_mais_curtos"] is not None]
    curtos = [v for v in informativos
              if por_voz[v]["excluidos_sao_mais_curtos"]]
    estavel = all(por_voz[v]["sem_filtro_falha_o_intervalo"]
                  == por_voz[v]["com_filtro_falha_o_intervalo"]
                  for v in por_voz)
    return {"por_voz": por_voz, "conclusao_estavel": estavel,
            "vozes_informativas": informativos,
            "vozes_com_excluidos_mais_curtos": curtos,
            "dispara": estavel and not curtos}


def portao_j2(cont: dict) -> dict:
    """§4.4 — a inversão, nos braços emparelhados da 5H."""
    lo, hi = INTERVALO_CAEIRO
    reais = [p["versos_min3"] for p in cont["por_poema"]["caeiro"]
             if p["elegivel"] and p["lingua"] == "pt"]

    cru = [json.loads(l) for l in
           open(os.path.join(RAIZ, "docs/fase-5h/01-cru.jsonl"))]
    for r in cru:
        r["heur"] = heuristica_truncada(r["texto"])

    saida: dict = {"n_reais": len(reais),
                   "mediana_real": st.median(reais),
                   "regra_truncatura": "campo gravado `truncada` "
                                       "(done_reason == 'length')",
                   "correccao_ao_protocolo":
                       "o §4.4 dizia que nao havia campo gravado e dizia mal; "
                       "a heuristica declarada fica como contra-verificacao",
                   "contra_verificacao_heuristica": {
                       "marcadas_pela_heuristica":
                           sum(1 for r in cru if r["heur"]),
                       "gravadas": sum(1 for r in cru if r["truncada"]),
                       "falsos_positivos_da_heuristica":
                           sum(1 for r in cru if r["heur"]
                               and not r["truncada"]),
                       "falsos_negativos_da_heuristica":
                           sum(1 for r in cru if r["truncada"]
                               and not r["heur"]),
                   },
                   "truncadas": {}, "cenarios": {}}

    for cenario, filtro in (("sem_truncadas", lambda r: not r["truncada"]),
                            ("com_truncadas", lambda r: True)):
        bracos: dict = {}
        for br, rotulo in (("Q", "qwen2.5"), ("L", "llama3.1")):
            xs = [r["n_versos"] for r in cru if r["braco"] == br and filtro(r)]
            dentro = sum(1 for x in xs if lo <= x <= hi)
            inf, sup = wilson(dentro, len(xs))
            bracos[br] = {
                "modelo": rotulo, "n": len(xs),
                "conformidade": round(dentro / len(xs), 4) if xs else None,
                "conformidade_wilson95": [round(inf, 4), round(sup, 4)],
                "dentro": dentro, "mediana": st.median(xs) if xs else None,
                "ks_ao_real": round(ks(xs, reais), 4),
            }
        dq, dl = bracos["Q"]["ks_ao_real"], bracos["L"]["ks_ao_real"]
        cq, cl = bracos["Q"]["conformidade"], bracos["L"]["conformidade"]

        # Bootstrap por AGRUPAMENTO na pergunta: 3 repeticoes por pergunta sao
        # correlacionadas, logo reamostra-se a pergunta e nao a amostra. O
        # bootstrap ingenuo vai como sensibilidade.
        perguntas = sorted({r["pergunta_id"] for r in cru})
        porpq = {(br, q): [r["n_versos"] for r in cru
                           if r["braco"] == br and r["pergunta_id"] == q
                           and filtro(r)]
                 for br in ("Q", "L") for q in perguntas}
        rng = random.Random(SEMENTE)
        difs_cl, difs_ing = [], []
        aq = [r["n_versos"] for r in cru if r["braco"] == "Q" and filtro(r)]
        al = [r["n_versos"] for r in cru if r["braco"] == "L" and filtro(r)]
        for _ in range(B):
            qs = [rng.choice(perguntas) for _ in perguntas]
            bq = [v for q in qs for v in porpq[("Q", q)]]
            bl = [v for q in qs for v in porpq[("L", q)]]
            br_ = [rng.choice(reais) for _ in reais]
            if bq and bl:
                difs_cl.append(ks(bq, br_) - ks(bl, br_))
            iq = [rng.choice(aq) for _ in aq]
            il = [rng.choice(al) for _ in al]
            difs_ing.append(ks(iq, br_) - ks(il, br_))

        def ic(xs):
            a = np.array(xs)
            return [round(float(np.percentile(a, 2.5)), 4),
                    round(float(np.percentile(a, 97.5)), 4)]

        ic_cl, ic_ing = ic(difs_cl), ic(difs_ing)
        saida["cenarios"][cenario] = {
            "bracos": bracos,
            "conformidade_L_menor": cl < cq,
            "ks_L_menor": dl < dq,
            "dif_ks_Q_menos_L": round(dq - dl, 4),
            "ic95_agrupado_na_pergunta": ic_cl,
            "ic95_ingenuo": ic_ing,
            "ic_exclui_zero": ic_cl[0] > 0 or ic_cl[1] < 0,
            "dispara": (cl < cq) and (dl < dq),
        }

    for br in ("Q", "L"):
        ts = [r for r in cru if r["braco"] == br and r["truncada"]]
        saida["truncadas"][br] = {
            "n": len(ts),
            "ids": [f'{r["pergunta_id"]}r{r["repeticao"]}' for r in ts],
            "versos": [r["n_versos"] for r in ts],
        }

    # O tecto do harness: `num_predict` e uma constante, logo ha uma regiao do
    # comprimento que nenhum braco PODE alcancar. 19% do Caeiro real esta acima
    # de 20 versos; se nenhum braco produz nada acima, o fosso superior e do
    # harness e nao do modelo. Medido, nao assumido.
    saida["tecto_do_harness"] = {
        "num_predict": 150,
        "maximo_observado": {br: max(r["n_versos"] for r in cru
                                     if r["braco"] == br)
                             for br in ("Q", "L")},
        "amostras_acima_de_20": {br: sum(1 for r in cru if r["braco"] == br
                                         and r["n_versos"] > 20)
                                 for br in ("Q", "L")},
        "reais_acima_de_20": sum(1 for x in reais if x > 20),
        "fraccao_real_acima_de_20": round(
            sum(1 for x in reais if x > 20) / len(reais), 4),
    }
    return saida


def portao_j4(cont: dict) -> dict:
    """§4.5 — derivar em metade, validar UMA vez na retida."""
    poemas = [p for p in cont["por_poema"]["caeiro"]
              if p["elegivel"] and p["lingua"] == "pt"]
    ordem = sorted(poemas, key=lambda d: d["id"])
    random.Random(SEMENTE).shuffle(ordem)
    meio = len(ordem) // 2
    derivar, retida = ordem[:meio], ordem[meio:]

    xs = [p["versos_min3"] for p in derivar]
    p10 = float(np.percentile(xs, 10))
    p90 = float(np.percentile(xs, 90))
    lo, hi = int(math.floor(p10)), int(math.ceil(p90))     # para fora

    cob_d = sum(1 for p in derivar if lo <= p["versos_min3"] <= hi) / len(derivar)
    dentro_r = sum(1 for p in retida if lo <= p["versos_min3"] <= hi)
    cob_r = dentro_r / len(retida)
    inf, sup = wilson(dentro_r, len(retida))

    ant_lo, ant_hi = INTERVALO_CAEIRO
    ant_r = sum(1 for p in retida if ant_lo <= p["versos_min3"] <= ant_hi)

    # §6.4 materializado: o intervalo descritivamente certo ainda discrimina?
    # Le-se das quantidades ja pre-registadas (o intervalo derivado e as
    # amostras da 5H), nao de uma analise nova.
    cru = [json.loads(l) for l in
           open(os.path.join(RAIZ, "docs/fase-5h/01-cru.jsonl"))]
    sob_novo = {}
    for br, rot in (("Q", "qwen2.5"), ("L", "llama3.1")):
        xs = [r["n_versos"] for r in cru if r["braco"] == br]
        sob_novo[rot] = {
            "n": len(xs),
            "dentro_do_novo": sum(1 for x in xs if lo <= x <= hi),
            "conformidade_nova": round(
                sum(1 for x in xs if lo <= x <= hi) / len(xs), 4),
            "conformidade_antiga": round(
                sum(1 for x in xs
                    if ant_lo <= x <= ant_hi) / len(xs), 4),
        }
    return {
        "consequencia_sobre_as_amostras": sob_novo,
        "cobertura_retida_real_vs_modelos":
            "o intervalo novo premeia os modelos ACIMA do poeta se "
            "conformidade_nova > cobertura_retida",
        "semente": SEMENTE,
        "n_derivar": len(derivar), "n_retida": len(retida),
        "percentis_na_metade_de_derivacao": {"p10": round(p10, 2),
                                            "p90": round(p90, 2)},
        "intervalo_derivado": [lo, hi],
        "cobertura_in_sample": round(cob_d, 4),
        "cobertura_retida": round(cob_r, 4),
        "cobertura_retida_wilson95": [round(inf, 4), round(sup, 4)],
        "intervalo_antigo": [ant_lo, ant_hi],
        "cobertura_retida_do_antigo": round(ant_r / len(retida), 4),
        "ganho_na_retida": round(cob_r - ant_r / len(retida), 4),
        "dispara": cob_r >= 0.70,
    }


def main() -> None:
    cont = json.load(open(os.path.join(AQUI, "01-contagem.json"),
                          encoding="utf-8"))
    j1 = portao_j1(cont)
    j3 = portao_j3(cont)
    j2 = portao_j2(cont)
    j4 = portao_j4(cont)

    pri = j2["cenarios"]["sem_truncadas"]
    j5 = {"dispara": not pri["ic_exclui_zero"],
          "leitura": ("o J2 le-se como «nao se mostrou que a distancia difere»"
                      if not pri["ic_exclui_zero"] else
                      "o IC exclui 0; o J5 nao dispara")}

    out = {"_meta": {"protocolo": "docs/FASE-5J.md §3-4",
                     "semente": SEMENTE, "B": B,
                     "definicao_verso": "plagio._versos (MIN_PALAVRAS=3)",
                     "gera_amostras": False},
           "J1": j1, "J2": j2, "J3": j3, "J4": j4, "J5": j5}

    caminho = os.path.join(AQUI, "03-resultados.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print("=== J1 — o defeito é das quatro vozes ===")
    for voz, l in j1["por_voz"].items():
        p = l["pt"]
        marca = "FALHA" if p["falha_o_intervalo"] else "passa"
        um = " (um lado)" if l["um_lado"] else ""
        print(f"  {voz:10s} [{l['intervalo'][0]:2d}-{l['intervalo'][1]:2d}]"
              f"{um:11s} {p['dentro']:4d}/{p['n']:4d} = {p['fraccao']:.0%}  "
              f"Wilson95 [{p['wilson95'][0]:.2f}; {p['wilson95'][1]:.2f}]  "
              f"mediana {p['mediana']:>5}  {marca}")
    print(f"  -> {j1['n_falham']} de 4 falham  "
          f"J1 {'DISPARA' if j1['dispara'] else 'nao dispara'}\n")

    print("=== J2 — o instrumento penaliza a fidelidade ===")
    for cen, c in j2["cenarios"].items():
        print(f"  [{cen}]  real mediana {j2['mediana_real']}  (n={j2['n_reais']})")
        for br in ("Q", "L"):
            b = c["bracos"][br]
            print(f"    {b['modelo']:10s} n={b['n']:2d}  "
                  f"conformidade {b['conformidade']:.0%}  "
                  f"mediana {b['mediana']:>4}  KS ao real {b['ks_ao_real']:.3f}")
        print(f"    D(Q)-D(L) = {c['dif_ks_Q_menos_L']:+.3f}  "
              f"IC95 agrupado {c['ic95_agrupado_na_pergunta']}  "
              f"ingenuo {c['ic95_ingenuo']}")
        print(f"    J2 {'DISPARA' if c['dispara'] else 'nao dispara'}"
              f"   (IC exclui 0: {c['ic_exclui_zero']})")
    print(f"  truncadas: Q={j2['truncadas']['Q']['n']}  "
          f"L={j2['truncadas']['L']['n']}\n")

    print("=== J3 — a elegibilidade não explica o J1 ===")
    for voz, l in j3["por_voz"].items():
        print(f"  {voz:10s} excluidos={l['n_excluidos']:4d}  "
              f"mediana excl={str(l['mediana_excluidos']):>6s} vs "
              f"retidos={l['mediana_retidos']:>5}  "
              f"mais curtos: {l['excluidos_sao_mais_curtos']}")
    print(f"  conclusao estavel: {j3['conclusao_estavel']}  "
          f"J3 {'DISPARA' if j3['dispara'] else 'nao dispara'}\n")

    print("=== J4 — intervalo validado fora da amostra ===")
    print(f"  derivar n={j4['n_derivar']}  retida n={j4['n_retida']}  "
          f"semente {j4['semente']}")
    print(f"  [p10,p90] = {j4['percentis_na_metade_de_derivacao']}  "
          f"-> intervalo {j4['intervalo_derivado']}")
    print(f"  cobertura: in-sample {j4['cobertura_in_sample']:.0%}  "
          f"RETIDA {j4['cobertura_retida']:.0%} "
          f"{j4['cobertura_retida_wilson95']}")
    print(f"  antigo {j4['intervalo_antigo']} na retida: "
          f"{j4['cobertura_retida_do_antigo']:.0%}  "
          f"ganho {j4['ganho_na_retida']:+.0%}")
    print(f"  J4 {'DISPARA' if j4['dispara'] else 'nao dispara'}\n")
    print(f"J5 (inconclusivo por potencia): "
          f"{'DISPARA' if j5['dispara'] else 'nao dispara'}")
    print(f"\n-> {caminho}")


if __name__ == "__main__":
    main()
