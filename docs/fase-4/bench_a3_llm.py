#!/usr/bin/env python
"""Passo A3, parte LLM — sem encoder carregado.

A primeira versão deste passo fazia as duas metades num processo só, e foi
**morta pelo sistema** (exit 137): o `sentence-transformers` residente mais o
qwen de 4,7 GB não cabem à vontade nos 30 GiB desta máquina com 1,4 GiB de swap
já em uso. As duas metades não precisam de estar vivas ao mesmo tempo — esta
grava em JSON e a do encoder lê.
"""
from __future__ import annotations

import json
import statistics as st
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "docs/fase-4")

from src.corpus.models import Voice
from bench_roteador_llm import rotear_llm  # noqa: E402

MODELO = "qwen2.5:7b-instruct-q4_K_M"


def corre(textos: list[str]) -> tuple[list[str | None], float]:
    rotear_llm(MODELO, "aquecimento")          # descartada
    vozes, tempos = [], []
    for t in textos:
        v, info = rotear_llm(MODELO, t)
        vozes.append(v.value if v else None)
        tempos.append(info["parede_s"])
    return vozes, round(st.median(tempos), 2)


def main() -> None:
    originais = json.load(open("docs/fase-1/08-perguntas.json",
                               encoding="utf-8"))["perguntas"]
    adv = json.load(open("docs/fase-4/03-adversarial.json",
                         encoding="utf-8"))["perguntas"]
    subs = {s["id"]: s["para"] for s in json.load(
        open("docs/fase-4/03-ablacao.json", encoding="utf-8"))["substituicoes"]}

    saida = {}
    print("adversarial (12)...", flush=True)
    v, m = corre([p["q"] for p in adv])
    saida["adversarial"] = {"previstas": v, "parede_mediana_s": m}
    print(f"  mediana {m} s")

    print("ablação (40)...", flush=True)
    v, m = corre([subs.get(p["id"], p["q"]) for p in originais])
    saida["ablacao"] = {"previstas": v, "parede_mediana_s": m}
    print(f"  mediana {m} s")

    with open("docs/fase-4/03-a3-llm.json", "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=1)
    print("escrito: docs/fase-4/03-a3-llm.json")


if __name__ == "__main__":
    main()
