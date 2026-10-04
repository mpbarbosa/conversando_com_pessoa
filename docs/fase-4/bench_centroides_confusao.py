#!/usr/bin/env python
"""Correcção à Fase 4, 2.ª parte — a confusão e a coerência, sem o nome.

A 1.ª parte mediu a exactidão e refutou a afirmação publicada. Faltam as duas
coisas que eu usei para **explicar** o resultado, e que foram medidas sobre os
mesmos vectores contaminados:

1. **O «colapso no Caeiro»** — 17 dos 22 erros do centróide sobre perguntas
   apontavam para o Caeiro, e eu construí uma explicação em cima disso.
2. **A tabela de coerência interna** (0,9339 / 0,9381 / 0,9386 / 0,9359), com
   que refutei a minha própria hipótese da dispersão de classe. Foi calculada
   sobre `idx.vectores`, logo sobre texto que leva o nome do heterónimo.

Se o colapso desaparecer ao tirar o nome, a explicação explicava um artefacto.

Guarda as codificações em `.npy` no scratchpad, para não haver uma terceira
corrida de 10 min se faltar outro número.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.corpus.build import load
from src.corpus.models import Lang, Voice
from src.retrieval.encoder import Encoder
from src.retrieval.index import Index

VOZES = (Voice.CAEIRO, Voice.CAMPOS, Voice.REIS, Voice.ORTONIMO)
N_POR_VOZ = 20
SEMENTE = 4
CACHE = os.environ.get("CACHE_DIR", "/tmp")


def _norm(a):
    n = np.linalg.norm(a, axis=-1, keepdims=True)
    return a / np.where(n == 0, 1.0, n)


def _cache(nome: str, fn):
    caminho = os.path.join(CACHE, f"{nome}.npy")
    if os.path.exists(caminho):
        print(f"  {nome}: do cache", flush=True)
        return np.load(caminho)
    t0 = time.perf_counter()
    a = fn()
    np.save(caminho, a)
    print(f"  {nome}: {time.perf_counter()-t0:.0f} s", flush=True)
    return a


def matriz(pares) -> str:
    cab = "esperada\\prevista".ljust(20) + "".join(v.value.ljust(11) for v in VOZES)
    out = [cab]
    for e in VOZES:
        cel = []
        for p in VOZES:
            n = sum(1 for a, b in pares if a is e and b is p)
            cel.append((str(n) if n else "·").ljust(11))
        out.append(e.value.ljust(20) + "".join(cel))
    return "\n".join(out)


def main() -> None:
    meta, chunks = load()
    enc = Encoder()
    idx = Index.load(chunks, enc, meta["assinatura"])
    if idx is None:
        sys.exit("índice recusado")

    perguntas = json.load(open("docs/fase-1/08-perguntas.json",
                               encoding="utf-8"))["perguntas"]
    pt = [i for i, c in enumerate(idx.chunks) if c.language is Lang.PT]
    pos = {i: k for k, i in enumerate(pt)}
    ix_voz = {v: [i for i in pt if idx.chunks[i].voice is v] for v in VOZES}

    rng = np.random.default_rng(SEMENTE)
    teste = []
    for v in VOZES:
        cand = [i for i in ix_voz[v] if idx.chunks[i].chunk_ix == 0]
        teste.extend(rng.choice(cand, size=min(N_POR_VOZ, len(cand)),
                                replace=False).tolist())
    fora = set(teste)
    treino = {v: [i for i in ix_voz[v] if i not in fora] for v in VOZES}

    textos_pt = [idx.chunks[i].text for i in pt]
    print("codificações:", flush=True)
    passagens = _cache("pass_text", lambda: enc.encode_passages(textos_pt))

    qs_perg = enc.encode_queries([p["q"] for p in perguntas])
    qs_poem = enc.encode_queries([idx.chunks[i].text for i in teste])
    esp_q = [Voice(p["voz"]) for p in perguntas]
    esp_p = [idx.chunks[i].voice for i in teste]

    saida: dict = {}

    # --- coerência interna, com e sem o nome ------------------------------
    print("\n=== coerência interna: o nome inflacionava-a? ===")
    print("voz        n     com nome   sem nome    ao centro (sem nome)")
    centro = _norm(passagens.mean(axis=0))
    coer = {}
    for v in VOZES:
        com = float(np.linalg.norm(idx.vectores[treino[v]].mean(axis=0)))
        bloco = passagens[[pos[i] for i in treino[v]]]
        media = bloco.mean(axis=0)
        sem = float(np.linalg.norm(media))
        ao = float(_norm(media) @ centro)
        coer[v.value] = {"n": len(treino[v]), "com_nome": round(com, 4),
                         "sem_nome": round(sem, 4), "ao_centro": round(ao, 4)}
        print(f"{v.value:10s} {len(treino[v]):4d}   {com:8.4f}   {sem:8.4f}"
              f"   {ao:8.4f}")
    saida["coerencia"] = coer

    # --- confusão nas duas variantes que importam -------------------------
    variantes = {"original": None, "sem_nome": passagens}
    saida["confusao"] = {}
    for nome, fonte in variantes.items():
        cent = _norm(np.vstack([
            (idx.vectores[treino[v]] if fonte is None
             else fonte[[pos[i] for i in treino[v]]]).mean(axis=0)
            for v in VOZES]))
        for conj, qs, esp in (("perguntas", qs_perg, esp_q),
                              ("poemas", qs_poem, esp_p)):
            prev = [VOZES[int(np.argmax(cent @ q))] for q in qs]
            pares = list(zip(esp, prev))
            certos = sum(1 for a, b in pares if a is b)
            erros_para: dict[str, int] = {}
            for a, b in pares:
                if a is not b:
                    erros_para[b.value] = erros_para.get(b.value, 0) + 1
            saida["confusao"][f"{nome}_{conj}"] = {
                "exactidao": round(certos / len(pares), 3),
                "erros_para": erros_para,
                "por_voz": {v.value: round(
                    sum(1 for a, b in pares if a is v and b is v)
                    / sum(1 for a, _ in pares if a is v), 2) for v in VOZES}}
            print(f"\n--- {nome} · {conj}: {certos}/{len(pares)} = "
                  f"{certos/len(pares):.0%}   erros->{erros_para}")
            print(matriz(pares))

    with open("docs/fase-4/08b-confusao-remedida.json", "w",
              encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=1)
    print("\nescrito: docs/fase-4/08b-confusao-remedida.json")


if __name__ == "__main__":
    main()
