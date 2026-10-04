#!/usr/bin/env python
"""Fase 5B / Passo C1–C3 e D1 — portões, concordância e instrumento II.

Protocolo em [`../FASE-5B.md`](../FASE-5B.md) §7. Escrito **antes** de existir
pontuação, para que a estatística não possa ser afinada depois de ver os dados.

A estatística é a da Fase 3B e da Fase 5, sem scipy, que não está instalado:

- **teste de sinais exacto sobre os pares discordantes.** É a mudança
  deliberada ao desenho da Fase 5, e está no §7: aquela escreveu os portões
  sobre **todos** os 20 pares («≥13 dos 20») e depois mediu 12 empates, logo o
  portão de confirmação ficou inalcançável por construção. O teste de sinais
  como ele é ignora os empates, e a potência protege-se com o piso de d ≥ 8.
- **IC95% por bootstrap emparelhado** do Δ médio (P − C) sobre os **30** pares,
  B=10000, semente 3. Os empates contam aqui, e é por isso que os dois
  instrumentos não são redundantes.
- **medianas** por braço, e por estrato (§5.1).

Correr só depois de as **duas** pontuações estarem commitadas: é este o passo
que abre `01-chave.json`.
"""
from __future__ import annotations

import json
import math
import os
import statistics as st

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
B = 10000
SEMENTE = 3

#: §7, portão G4. Pré-registado, e não negociável depois de ver os dados.
PISO_DISCORDANTES = 8

#: Os três critérios pontuados à mão.
MANUAIS = ("c3a_poetica", "c3b_forma", "c4_responde")
AUTOMATICOS = ("c1_verso", "c2_pt", "c5_plagio")

#: §5.1. Os estratos são descritivos e não decidem nada.
ESTRATO_FASE5 = {"q01", "q02", "q03", "q04", "q05"}

AVALIADORES = {"R1": "02-pontuacoes.json", "R2": "02-pontuacoes-r2.json"}


def binomial_bilateral(k: int, d: int) -> float:
    """p exacto bilateral de k sucessos em d provas contra p=0,5.

    Sem scipy. Para p=0,5 a distribuição é simétrica, logo o p bilateral é
    `2·min(P(X≤k), P(X≥k))`, truncado a 1.
    """
    if d == 0:
        return 1.0
    total = 2.0 ** d
    abaixo = sum(math.comb(d, i) for i in range(0, k + 1)) / total
    acima = sum(math.comb(d, i) for i in range(k, d + 1)) / total
    return min(1.0, 2.0 * min(abaixo, acima))


def bootstrap_ic(d: np.ndarray, b: int = B) -> tuple[float, float]:
    rng = np.random.default_rng(SEMENTE)
    ix = rng.integers(0, len(d), size=(b, len(d)))
    medias = d[ix].mean(axis=1)
    return float(np.percentile(medias, 2.5)), float(np.percentile(medias, 97.5))


def kappa(a: list[int], b: list[int], pesos: str = "nenhum") -> float:
    """κ de Cohen entre dois avaliadores numa escala {0,1,2}.

    `pesos='linear'` dá o κ ponderado linearmente, que é o que uma escala
    **ordinal** pede: discordar 0 contra 2 é pior que 0 contra 1, e o κ simples
    trata as duas como o mesmo erro. O protocolo pré-registou o κ simples; o
    ponderado vai a par, declarado como acrescento.
    """
    cats = [0, 1, 2]
    n = len(a)
    obs = np.zeros((3, 3))
    for x, y in zip(a, b):
        obs[cats.index(x), cats.index(y)] += 1
    obs /= n
    ma, mb = obs.sum(axis=1), obs.sum(axis=0)
    esp = np.outer(ma, mb)
    if pesos == "linear":
        w = np.array([[abs(i - j) / 2 for j in cats] for i in cats])
    else:
        w = 1.0 - np.eye(3)
    do, de = (w * obs).sum(), (w * esp).sum()
    return float("nan") if de == 0 else 1.0 - do / de


def portoes(crit3a: dict, crit3b: dict, med_c_3a: float) -> list[str]:
    """Os portões do §7, aplicados sem margem de interpretação."""
    disparados: list[str] = []

    # G0 — o chão da Fase 5 não se reproduziu
    if med_c_3a >= 1:
        disparados.append("G0")

    d = crit3a["discordantes"]
    pro_p = crit3a["sinais_pro_P"]
    p_val = crit3a["p_binomial"]
    lo, hi = crit3a["ic95"]
    ic_exclui_zero = not (lo <= 0 <= hi)

    # G3 — especificidade. A `forma` é byte a byte igual nos dois braços, logo
    # mover 3b tanto como 3a é perturbação geral do prompt e não efeito na
    # poética. Avalia-se antes de G1 porque G1 depende dele.
    d3a, d3b = crit3a["delta_medio"], crit3b["delta_medio"]
    g3 = abs(d3b) >= abs(d3a) and d3a != 0 and (d3a > 0) == (d3b > 0)
    if g3:
        disparados.append("G3")

    # G4 — inconclusivo por potência. Tem prioridade: um veredicto com menos de
    # 8 pares discordantes não se lê em nenhuma direcção.
    if d < PISO_DISCORDANTES:
        disparados.append("G4")
        return disparados

    if p_val <= 0.05 and ic_exclui_zero and pro_p > d / 2 and not g3:
        disparados.append("G1")
    else:
        disparados.append("G2")
    return disparados


def principal(disparados: list[str]) -> str:
    """O portão que decide, entre G1, G2 e G4. G0 e G3 qualificam, não decidem."""
    for g in ("G4", "G1", "G2"):
        if g in disparados:
            return g
    return "—"


def main() -> None:
    chave = {d["id"]: d for d in
             json.load(open(os.path.join(AQUI, "01-chave.json")))["chave"]}
    auto = {d["id"]: d for d in
            json.load(open(os.path.join(AQUI, "01-amostras.json")))["amostras"]}

    pontuacoes: dict[str, dict] = {}
    for r, fich in AVALIADORES.items():
        caminho = os.path.join(AQUI, fich)
        if os.path.exists(caminho):
            pontuacoes[r] = json.load(open(caminho))["pontuacoes"]
        else:
            print(f"aviso: {fich} ausente — {r} fica de fora")
    assert pontuacoes, "nenhuma pontuação encontrada"

    out: dict = {"_meta": {
        "protocolo": "docs/FASE-5B.md §7", "bootstrap_B": B, "semente": SEMENTE,
        "piso_discordantes": PISO_DISCORDANTES,
        "avaliadores": sorted(pontuacoes),
    }, "por_avaliador": {}}

    for r, pont in sorted(pontuacoes.items()):
        # pares: (pergunta, repetição) -> braço -> critérios
        pares: dict[tuple[str, int], dict[str, dict]] = {}
        for sid, notas in pont.items():
            k = chave[sid]
            linha = dict(notas)
            linha.update({c: auto[sid].get(c, k.get(c)) for c in AUTOMATICOS})
            linha["id"] = sid
            linha["truncada"] = k["truncada"]
            linha["tentativas"] = k["tentativas"]
            pares.setdefault((k["pergunta_id"], k["repeticao"]), {})[k["braco"]] = linha

        completos = {q: v for q, v in pares.items() if {"C", "P"} <= set(v)}
        assert len(completos) == 30, f"{r}: pares completos {len(completos)}, esperava 30"
        chaves = sorted(completos)

        res: dict = {"n_pares": len(completos), "por_criterio": {}}
        for crit in MANUAIS + AUTOMATICOS:
            c = np.array([completos[q]["C"][crit] for q in chaves], dtype=float)
            p = np.array([completos[q]["P"][crit] for q in chaves], dtype=float)
            d = p - c
            pro_p, pro_c, emp = int((d > 0).sum()), int((d < 0).sum()), int((d == 0).sum())
            disc = pro_p + pro_c
            lo, hi = bootstrap_ic(d)
            res["por_criterio"][crit] = {
                "mediana_C": st.median(c), "mediana_P": st.median(p),
                "media_C": round(float(c.mean()), 3),
                "media_P": round(float(p.mean()), 3),
                "delta_medio": round(float(d.mean()), 3),
                "ic95": [round(lo, 3), round(hi, 3)],
                "sinais_pro_P": pro_p, "sinais_pro_C": pro_c, "empates": emp,
                "discordantes": disc,
                "p_binomial": round(binomial_bilateral(pro_p, disc), 4),
            }

        c3a, c3b = res["por_criterio"]["c3a_poetica"], res["por_criterio"]["c3b_forma"]
        disparados = portoes(c3a, c3b, c3a["mediana_C"])
        res["portoes_disparados"] = disparados
        res["portao_principal"] = principal(disparados)

        # --- estratos (§5.1), descritivos ------------------------------
        res["estratos"] = {}
        for nome, filtro in (("q01-q05", lambda q: q in ESTRATO_FASE5),
                             ("q06-q10", lambda q: q not in ESTRATO_FASE5)):
            ks = [q for q in chaves if filtro(q[0])]
            c = np.array([completos[q]["C"]["c3a_poetica"] for q in ks], dtype=float)
            p = np.array([completos[q]["P"]["c3a_poetica"] for q in ks], dtype=float)
            d = p - c
            res["estratos"][nome] = {
                "n_pares": len(ks),
                "mediana_C": st.median(c), "mediana_P": st.median(p),
                "delta_medio": round(float(d.mean()), 3),
                "sinais_pro_P": int((d > 0).sum()),
                "sinais_pro_C": int((d < 0).sum()),
                "empates": int((d == 0).sum()),
            }

        # --- variância dentro da célula (§7.2) --------------------------
        # A primeira medição disto no projecto. Uma «célula» é
        # (pergunta, braço), com as 3 repetições dentro.
        por_celula: dict[tuple[str, str], list[float]] = {}
        for (q, rep), v in completos.items():
            for braco in ("C", "P"):
                por_celula.setdefault((q, braco), []).append(v[braco]["c3a_poetica"])
        desvios = {b: [st.pstdev(v) for (q, bb), v in por_celula.items()
                       if bb == b and len(v) > 1] for b in ("C", "P")}
        res["variancia_na_celula"] = {
            b: {"desvio_medio": round(st.mean(ds), 3) if ds else None,
                "celulas_com_3_notas_iguais": sum(1 for x in ds if x == 0),
                "n_celulas": len(ds)}
            for b, ds in desvios.items()}
        res["amplitude_na_celula"] = {
            b: sorted({(max(v) - min(v)) for (q, bb), v in por_celula.items()
                       if bb == b})
            for b in ("C", "P")}

        out["por_avaliador"][r] = res

    # --- concordância entre avaliadores (§7.2) --------------------------
    if len(pontuacoes) == 2:
        ids = sorted(set(pontuacoes["R1"]) & set(pontuacoes["R2"]))
        conc: dict = {"n_amostras": len(ids)}
        for crit in MANUAIS:
            a = [pontuacoes["R1"][i][crit] for i in ids]
            b = [pontuacoes["R2"][i][crit] for i in ids]
            conc[crit] = {
                "kappa": round(kappa(a, b), 3),
                "kappa_ponderado_linear": round(kappa(a, b, "linear"), 3),
                "concordancia_exacta": round(
                    sum(x == y for x, y in zip(a, b)) / len(ids), 3),
                "discordancia_maxima": int(max(abs(x - y) for x, y in zip(a, b))),
                "media_R1": round(st.mean(a), 3), "media_R2": round(st.mean(b), 3),
            }
        g1 = out["por_avaliador"]["R1"]["portao_principal"]
        g2 = out["por_avaliador"]["R2"]["portao_principal"]
        conc["portao_R1"], conc["portao_R2"] = g1, g2
        conc["G5_discordam"] = g1 != g2
        out["concordancia"] = conc

    # --- instrumento II: contagem lexical (§7.1) ------------------------
    from verificar_personas import contar_referentes
    inst2: dict = {"nota": "sem portão. Ver o §7.1: P não contém estas palavras "
                           "por construção, e este instrumento não separa eco "
                           "de priming."}
    for braco in ("C", "P"):
        textos = [d["texto"] for d in chave.values() if d["braco"] == braco]
        contagens = [sum(contar_referentes(t).values()) for t in textos]
        agregado: dict[str, int] = {}
        for t in textos:
            for w, n in contar_referentes(t).items():
                agregado[w] = agregado.get(w, 0) + n
        inst2[braco] = {
            "n_amostras": len(textos),
            "total_ocorrencias": sum(contagens),
            "amostras_com_pelo_menos_uma": sum(1 for x in contagens if x),
            "media_por_amostra": round(st.mean(contagens), 3),
            "por_palavra": dict(sorted(agregado.items(), key=lambda kv: -kv[1])),
        }
    inst2["delta_total"] = inst2["P"]["total_ocorrencias"] - inst2["C"]["total_ocorrencias"]
    out["instrumento_II"] = inst2

    with open(os.path.join(AQUI, "03-resultados.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    # ---------------------------- impressão ----------------------------
    print("Fase 5B — portões (§7)\n")
    for r, res in sorted(out["por_avaliador"].items()):
        c = res["por_criterio"]["c3a_poetica"]
        print(f"=== {r} === {res['n_pares']} pares")
        print(f"  3a  C={c['mediana_C']:.1f} P={c['mediana_P']:.1f}  "
              f"Δ={c['delta_medio']:+.3f}  IC95={c['ic95']}")
        print(f"      sinais P/C/= : {c['sinais_pro_P']}/{c['sinais_pro_C']}/"
              f"{c['empates']}   d={c['discordantes']}  p={c['p_binomial']}")
        for crit in ("c3b_forma", "c4_responde", "c1_verso", "c2_pt", "c5_plagio"):
            x = res["por_criterio"][crit]
            print(f"  {crit:13s} C={x['mediana_C']:.1f} P={x['mediana_P']:.1f}  "
                  f"Δ={x['delta_medio']:+.3f}  IC95={x['ic95']}  "
                  f"{x['sinais_pro_P']}/{x['sinais_pro_C']}/{x['empates']}")
        print(f"  portões: {res['portoes_disparados']}  →  "
              f"**{res['portao_principal']}**")
        for nome, e in res["estratos"].items():
            print(f"  estrato {nome}: C={e['mediana_C']:.1f} P={e['mediana_P']:.1f} "
                  f"Δ={e['delta_medio']:+.3f} {e['sinais_pro_P']}/"
                  f"{e['sinais_pro_C']}/{e['empates']}")
        print(f"  variância na célula: {res['variancia_na_celula']}\n")

    if "concordancia" in out:
        co = out["concordancia"]
        print("=== concordância R1/R2 ===")
        for crit in MANUAIS:
            k = co[crit]
            print(f"  {crit:13s} κ={k['kappa']:+.3f}  κ_lin={k['kappa_ponderado_linear']:+.3f}  "
                  f"exacta={k['concordancia_exacta']:.1%}  "
                  f"máx={k['discordancia_maxima']}  "
                  f"médias {k['media_R1']:.2f}/{k['media_R2']:.2f}")
        print(f"  portões: R1={co['portao_R1']}  R2={co['portao_R2']}  "
              f"→ G5 {'DISPARA' if co['G5_discordam'] else 'não dispara'}\n")

    i2 = out["instrumento_II"]
    print("=== instrumento II — referentes nomeados (sem portão) ===")
    for b in ("C", "P"):
        print(f"  {b}: {i2[b]['total_ocorrencias']} ocorrências em "
              f"{i2[b]['amostras_com_pelo_menos_uma']}/{i2[b]['n_amostras']} amostras "
              f"({i2[b]['media_por_amostra']:.2f}/amostra)")
    print(f"  Δ (P−C) = {i2['delta_total']:+d}")
    print("\n03-resultados.json escrito.")


if __name__ == "__main__":
    main()
