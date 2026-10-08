#!/usr/bin/env python
"""Fase 5S / A1 — o roteador de voz com o `llama3.1:8b`.

Protocolo: `../FASE-5S.md` §3.

**Reutiliza o harness da Fase 4 em vez de o alterar.** O
`fase-4/bench_roteador_llm.py` é o registo do que aquela fase mediu — o
`qwen2.5:3b` a 42% e o `qwen2.5:7b` a **72%** — e reescrevê-lo apagava-o. Daqui
importam-se o `rotear_llm`, o `SYSTEM` e as `VOZES`, e corre-se o **mesmo
gabarito**: as 40 perguntas etiquetadas de `fase-1/08-perguntas.json`.

`temperature=0`, logo determinista: não há repetições a fazer.

Escreve `01-roteador.json`.
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "docs", "fase-4"))

from bench_roteador_llm import VOZES, rotear_llm                 # noqa: E402
from src.corpus.models import Voice                              # noqa: E402

#: §4 — o modelo que a troca poria no lugar do qwen.
MODELO = "llama3.1:8b-instruct-q4_K_M"
#: Os numeros publicados pela Fase 4, com o MESMO gabarito.
QWEN_7B_EXACTIDAO = 0.72
LIMIAR_S1 = 0.65          # §4: «o qwen menos tres perguntas em 40»


def main() -> None:
    perguntas = json.load(open(os.path.join(RAIZ,
                                            "docs/fase-1/08-perguntas.json"),
                               encoding="utf-8"))["perguntas"]
    esperadas = [Voice(p["voz"]) for p in perguntas]
    assert len(perguntas) == 40, len(perguntas)

    print(f"{MODELO}, {len(perguntas)} perguntas, temperature=0")
    rotear_llm(MODELO, "aquecimento, para o modelo carregar")   # descartada

    previstas, tempos, brutos = [], [], []
    for p in perguntas:
        v, info = rotear_llm(MODELO, p["q"])
        previstas.append(v)
        tempos.append(info)
        if v is None:
            brutos.append({"id": p["id"], "bruto": info["bruto"]})

    certos = sum(1 for e, pv in zip(esperadas, previstas) if e is pv)
    exact = certos / len(previstas)
    por_voz = {v.value: round(
        sum(1 for e, pv in zip(esperadas, previstas) if e is v and pv is v)
        / sum(1 for e in esperadas if e is v), 2) for v in VOZES}
    erros = [{"id": perguntas[i]["id"], "q": perguntas[i]["q"],
              "esperada": esperadas[i].value,
              "prevista": previstas[i].value if previstas[i] else None}
             for i in range(len(previstas)) if esperadas[i] is not previstas[i]]

    s1 = exact >= LIMIAR_S1
    out = {"_meta": {"protocolo": "docs/FASE-5S.md §3-4", "modelo": MODELO,
                     "gabarito": "docs/fase-1/08-perguntas.json (40, etiquetadas)",
                     "determinista": "temperature=0, uma corrida",
                     "harness": "fase-4/bench_roteador_llm.py, reutilizado"},
           "exactidao": round(exact, 3), "certos": certos,
           "n": len(previstas), "por_voz": por_voz, "erros": erros,
           "sem_voz_reconhecida": brutos,
           "parede_mediana_s": round(
               st.median(t["parede_s"] for t in tempos), 2),
           "prefill_mediana_s": round(
               st.median(t["prefill_s"] for t in tempos), 2),
           "referencia_qwen7b": QWEN_7B_EXACTIDAO,
           "S1": {"limiar": LIMIAR_S1, "dispara": s1},
           "S3": {"bate_o_qwen": exact > QWEN_7B_EXACTIDAO}}

    with open(os.path.join(AQUI, "01-roteador.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print(f"\nllama3.1:8b   {certos}/{len(previstas)} = {exact:.0%}   {por_voz}")
    print(f"qwen2.5:7b    (Fase 4)        = {QWEN_7B_EXACTIDAO:.0%}")
    print(f"parede mediana {out['parede_mediana_s']:.2f} s · prefill "
          f"{out['prefill_mediana_s']:.2f} s")
    print(f"\nS1 (>= {LIMIAR_S1:.0%}): {'DISPARA' if s1 else 'nao dispara'}"
          f"   ·   S3 (> {QWEN_7B_EXACTIDAO:.0%}): "
          f"{'DISPARA' if out['S3']['bate_o_qwen'] else 'nao dispara'}")
    if brutos:
        print(f"\n{len(brutos)} respostas sem voz reconhecida:")
        for b in brutos[:5]:
            print(f"  {b['id']}: {b['bruto'][:60]!r}")
    print(f"\n-> {os.path.join(AQUI, '01-roteador.json')}")


if __name__ == "__main__":
    main()
