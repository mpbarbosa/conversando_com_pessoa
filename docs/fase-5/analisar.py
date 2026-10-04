#!/usr/bin/env python
"""Fase 5 / Passo C1 — sinais, bootstrap e medianas dos 20 pares.

A estatística é a da Fase 3B (`../fase-3b/bench_significancia.py`), e pela mesma
razão: com n=20 e critérios em {0,1,2} nada autoriza a assumir normalidade.

- **teste de sinais** emparelhado: em quantas perguntas B supera A, em quantas
  perde, em quantas empata. É o que os portões G1/G2/G4 do protocolo contam.
- **IC95% por bootstrap emparelhado** do Δ médio (B − A), B=10000, semente 3.
- medianas por condição, no total e por voz. Por voz há n=5: lê-se a direcção,
  nunca significância, e o protocolo §7 di-lo antes de os números existirem.

Correr só depois de `02-pontuacoes.json` estar commitado: é este o passo que
abre `01-chave.json`.
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
B = 10000
SEMENTE = 3

#: Os três critérios pontuados à mão. Os automáticos vêm de `01-amostras.json`.
MANUAIS = ("c3a_poetica", "c3b_forma", "c4_responde")
AUTOMATICOS = ("c1_verso", "c2_pt", "c5_plagio")


def bootstrap_ic(d: np.ndarray, b: int = B) -> tuple[float, float]:
    rng = np.random.default_rng(SEMENTE)
    ix = rng.integers(0, len(d), size=(b, len(d)))
    medias = d[ix].mean(axis=1)
    return float(np.percentile(medias, 2.5)), float(np.percentile(medias, 97.5))


def sinais(d: np.ndarray) -> tuple[int, int, int]:
    return (int((d > 0).sum()), int((d < 0).sum()), int((d == 0).sum()))


def portao(crit: str, mais: int, lo: float, hi: float,
           med_a: float, n_max_a: int) -> str:
    """Os portões do §7, aplicados sem margem de interpretação."""
    if crit != "c3a_poetica":
        return "—"
    if med_a == 2.0 and n_max_a >= 18:
        return "G0: chão — a pergunta aberta fecha"
    if mais >= 13 and not (lo <= 0 <= hi):
        return "G1: H confirmada — autoriza intervenção no prompt"
    if mais in (11, 12):
        return "G4: inconclusivo"
    return "G2: H rejeitada"


def main() -> None:
    pont = json.load(open(os.path.join(AQUI, "02-pontuacoes.json")))["pontuacoes"]
    chave = {d["id"]: d for d in json.load(open(os.path.join(AQUI, "01-chave.json")))["chave"]}
    auto = {d["id"]: d for d in json.load(open(os.path.join(AQUI, "01-amostras.json")))["amostras"]}

    # junta: pergunta -> condição -> todos os critérios
    por_pergunta: dict[str, dict[str, dict]] = {}
    for sid, notas in pont.items():
        k = chave[sid]
        linha = dict(notas)
        # O `c5_plagio` não está em `01-amostras.json`: ficou de fora da folha
        # porque plagiar correlaciona com ter contexto, e isso revelaria a
        # condição a quem pontuava. Vem da chave, que a esta altura está aberta.
        linha.update({c: auto[sid].get(c, k.get(c)) for c in AUTOMATICOS})
        linha["id"] = sid
        linha["voz"] = k["voz"]
        linha["truncada"] = k["truncada"]
        linha["tentativas"] = k["tentativas"]
        por_pergunta.setdefault(k["pergunta_id"], {})[k["condicao"]] = linha

    completos = {q: v for q, v in por_pergunta.items() if {"A", "B"} <= set(v)}
    assert len(completos) == 20, f"pares completos: {len(completos)}"

    out: dict = {"_meta": {"protocolo": "docs/FASE-5.md", "n_pares": len(completos),
                           "bootstrap_B": B, "semente": SEMENTE}}
    criterios = MANUAIS + AUTOMATICOS
    out["por_criterio"] = {}

    for crit in criterios:
        a = np.array([completos[q]["A"][crit] for q in sorted(completos)], dtype=float)
        b = np.array([completos[q]["B"][crit] for q in sorted(completos)], dtype=float)
        d = b - a
        mais, menos, iguais = sinais(d)
        lo, hi = bootstrap_ic(d)
        g = portao(crit, mais, lo, hi, st.median(a), int((a == 2).sum()))
        out["por_criterio"][crit] = {
            "A": {"mediana": st.median(a), "media": round(float(a.mean()), 3),
                  "n_com_2": int((a == 2).sum()), "n_com_0": int((a == 0).sum())},
            "B": {"mediana": st.median(b), "media": round(float(b.mean()), 3),
                  "n_com_2": int((b == 2).sum()), "n_com_0": int((b == 0).sum())},
            "delta_medio": round(float(d.mean()), 3),
            "ic95": [round(lo, 3), round(hi, 3)],
            "sinais": {"B_melhor": mais, "A_melhor": menos, "empate": iguais},
            "portao": g,
        }
        print(f"{crit:14s} A={st.median(a):.1f} B={st.median(b):.1f}  "
              f"Δ={d.mean():+.3f} IC95[{lo:+.3f},{hi:+.3f}]  "
              f"sinais B+{mais}/A+{menos}/={iguais}  {g}")

    # --- por voz, só direcção -------------------------------------------
    out["por_voz"] = {}
    vozes = sorted({completos[q]["A"]["voz"] for q in completos})
    print()
    for voz in vozes:
        qs = sorted(q for q in completos if completos[q]["A"]["voz"] == voz)
        linha = {"n": len(qs)}
        for crit in criterios:
            a = [completos[q]["A"][crit] for q in qs]
            b = [completos[q]["B"][crit] for q in qs]
            linha[crit] = {"A": st.median(a), "B": st.median(b),
                           "delta_medio": round(st.mean(b) - st.mean(a), 2)}
        out["por_voz"][voz] = linha
        p = linha["c3a_poetica"]
        f = linha["c3b_forma"]
        print(f"{voz:10s} n={len(qs)}  3a A={p['A']:.1f} B={p['B']:.1f}  "
              f"3b A={f['A']:.1f} B={f['B']:.1f}")

    # --- a pergunta secundária, sem portão ------------------------------
    try:
        res3b = json.load(open(os.path.join(AQUI, "..", "fase-3b", "03-resultados.json")))
        out["_meta"]["ndcg_por_pergunta"] = "ver fase-3b/03-resultados.json"
        del res3b
    except Exception:
        pass

    # --- totais e observações -------------------------------------------
    out["observacoes"] = {
        "truncadas": {c: sum(1 for q in completos if completos[q][c]["truncada"])
                      for c in ("A", "B")},
        "tentativas_acima_de_1": sum(1 for q in completos
                                     if completos[q]["A"]["tentativas"] > 1),
        "total_rubrica": {
            c: round(st.mean([sum(completos[q][c][k] for k in criterios)
                              for q in completos]), 2)
            for c in ("A", "B")},
    }
    print("\ntotal da rubrica (max 12):",
          out["observacoes"]["total_rubrica"],
          "· truncadas:", out["observacoes"]["truncadas"],
          "· A com repetição:", out["observacoes"]["tentativas_acima_de_1"])

    with open(os.path.join(AQUI, "03-resultados.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
