#!/usr/bin/env python
"""Correcção à Fase 4 — os centróides levavam o nome do heterónimo à cabeça.

## O defeito

O `index.py:61` constrói o índice sobre `Chunk.indexed_text`, que por desenho
leva **«Autor — Título» à cabeça** (`chunk.py:23`):

    indexed_text: 'Fernando Pessoa — Quarto: AS ILHAS AFORTUNADAS\\n\\nQue voz vem...'
    text        : 'Que voz vem...'

O Passo A1c usou `idx.vectores` para os centróides e `encode_queries(c.text)`
para as consultas. O centróide tem portanto uma componente ao longo do **nome**
que nenhuma consulta de verso puro pode igualar: o sinal discriminativo
disponível à consulta fica diluído, e a exactidão sai **subestimada**.

Foi encontrado por outra sessão a portar o desenho para a Fase 5, e confirmado
no código antes de ser registado.

## São dois defeitos empilhados, não um

O segundo já estava declarado por mim no `bench_roteador_b.py` — a assimetria
`query:`/`passage:` do e5 — sem que eu o ligasse ao A1c. Corrigir só o nome
mantém a assimetria, logo um número só confunde as duas causas. Daí três:

| variante | centróides | consultas | isola |
|---|---|---|---|
| `original` | `encode_passages(indexed_text)` = `idx.vectores` | `encode_queries(text)` | o que foi publicado |
| `sem_nome` | `encode_passages(text)` | `encode_queries(text)` | o efeito do nome |
| `sem_nome_nem_assimetria` | `encode_queries(text)` | `encode_queries(text)` | o efeito dos dois |

## O que esta correcção pode e não pode mudar

A **decisão** da Fase 4 — roteador por LLM — não depende disto: o 7B fez 72% e
todas as variantes de embedding partilham o handicap, logo a ordenação entre
elas mantém-se. O que está sob correcção é a **afirmação** «o espaço do e5 não
separa estas vozes», que se apoiou nos 42–46% sobre poemas reais.

Mede as duas evidências dessa afirmação: as 40 perguntas rotuladas (A1) e os 80
poemas reais retirados do índice (A1c), com o mesmo conjunto de teste e a mesma
semente nas três variantes, para os números serem comparáveis entre si.
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

PERGUNTAS = "docs/fase-1/08-perguntas.json"
VOZES = (Voice.CAEIRO, Voice.CAMPOS, Voice.REIS, Voice.ORTONIMO)
N_POR_VOZ = 20
SEMENTE = 4          # a mesma do A1c, para o conjunto de teste ser o mesmo


def _norm(a: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(a, axis=-1, keepdims=True)
    return a / np.where(n == 0, 1.0, n)


def main() -> None:
    meta, chunks = load()
    enc = Encoder()
    idx = Index.load(chunks, enc, meta["assinatura"])
    if idx is None:
        sys.exit("índice recusado")

    perguntas = json.load(open(PERGUNTAS, encoding="utf-8"))["perguntas"]
    pt = [i for i, c in enumerate(idx.chunks) if c.language is Lang.PT]
    ix_voz = {v: [i for i in pt if idx.chunks[i].voice is v] for v in VOZES}

    # --- conjunto de teste: o mesmo do A1c -------------------------------
    rng = np.random.default_rng(SEMENTE)
    teste: list[int] = []
    for v in VOZES:
        cand = [i for i in ix_voz[v] if idx.chunks[i].chunk_ix == 0]
        teste.extend(rng.choice(cand, size=min(N_POR_VOZ, len(cand)),
                                replace=False).tolist())
    fora = set(teste)
    treino = {v: [i for i in ix_voz[v] if i not in fora] for v in VOZES}
    print(f"{len(teste)} poemas de teste · "
          f"{sum(len(x) for x in treino.values())} de treino", flush=True)

    # --- consultas, iguais nas três variantes ----------------------------
    qs_perguntas = enc.encode_queries([p["q"] for p in perguntas])
    qs_poemas = enc.encode_queries([idx.chunks[i].text for i in teste])
    esperadas_q = [Voice(p["voz"]) for p in perguntas]
    esperadas_p = [idx.chunks[i].voice for i in teste]

    # --- as duas re-codificações do corpus, ~6 min cada ------------------
    textos_pt = [idx.chunks[i].text for i in pt]
    pos = {i: k for k, i in enumerate(pt)}

    print("a re-encodar o corpus como PASSAGEM sobre c.text (~6 min)...",
          flush=True)
    t0 = time.perf_counter()
    passagens_text = enc.encode_passages(textos_pt)
    print(f"  {time.perf_counter()-t0:.0f} s", flush=True)

    print("a re-encodar o corpus como CONSULTA sobre c.text (~6 min)...",
          flush=True)
    t0 = time.perf_counter()
    consultas_text = enc.encode_queries(textos_pt)
    print(f"  {time.perf_counter()-t0:.0f} s", flush=True)

    def centroides(fonte: np.ndarray | None) -> np.ndarray:
        """`None` usa `idx.vectores` (o publicado); senão indexa por `pos`."""
        blocos = []
        for v in VOZES:
            if fonte is None:
                blocos.append(idx.vectores[treino[v]].mean(axis=0))
            else:
                blocos.append(fonte[[pos[i] for i in treino[v]]].mean(axis=0))
        return _norm(np.vstack(blocos))

    variantes = {
        "original": None,
        "sem_nome": passagens_text,
        "sem_nome_nem_assimetria": consultas_text,
    }

    saida: dict = {"_meta": {
        "n_perguntas": len(perguntas), "n_poemas": len(teste),
        "semente": SEMENTE,
        "defeito": "idx.vectores = encode_passages(indexed_text), que leva "
                   "«Autor — Título» à cabeça; as consultas são verso puro",
    }}

    print(f"\n{'variante':26s} {'perguntas':>10s} {'poemas':>8s}"
          f" {'probe perg.':>12s} {'probe poem.':>12s}")
    from sklearn.linear_model import LogisticRegression
    for nome, fonte in variantes.items():
        cent = centroides(fonte)
        ac_q = sum(1 for e, q in zip(esperadas_q, qs_perguntas)
                   if VOZES[int(np.argmax(cent @ q))] is e) / len(esperadas_q)
        ac_p = sum(1 for e, q in zip(esperadas_p, qs_poemas)
                   if VOZES[int(np.argmax(cent @ q))] is e) / len(esperadas_p)

        # o probe partilhava o mesmo defeito; é grátis agora que há codificações
        base = idx.vectores if fonte is None else fonte
        X = np.vstack([base[treino[v]] if fonte is None
                       else base[[pos[i] for i in treino[v]]] for v in VOZES])
        y = np.array([k for k, v in enumerate(VOZES) for _ in treino[v]])
        clf = LogisticRegression(max_iter=2000,
                                 class_weight="balanced").fit(X, y)
        pq = sum(1 for e, p in zip(esperadas_q, clf.predict(qs_perguntas))
                 if VOZES[int(p)] is e) / len(esperadas_q)
        pp = sum(1 for e, p in zip(esperadas_p, clf.predict(qs_poemas))
                 if VOZES[int(p)] is e) / len(esperadas_p)

        # confusão sobre poemas, para ver se o colapso no Caeiro sobrevive
        prev = [VOZES[int(np.argmax(cent @ q))] for q in qs_poemas]
        conta: dict[str, int] = {}
        for e, p in zip(esperadas_p, prev):
            if e is not p:
                conta[p.value] = conta.get(p.value, 0) + 1

        saida[nome] = {
            "centroide_perguntas": round(ac_q, 3),
            "centroide_poemas": round(ac_p, 3),
            "probe_perguntas": round(pq, 3),
            "probe_poemas": round(pp, 3),
            "erros_por_voz_prevista_poemas": conta,
        }
        print(f"{nome:26s} {ac_q:9.0%} {ac_p:7.0%} {pq:11.0%} {pp:11.0%}"
              f"   erros->{conta}")

    with open("docs/fase-4/08-centroides-remedidos.json", "w",
              encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=1)
    print("\nescrito: docs/fase-4/08-centroides-remedidos.json")


if __name__ == "__main__":
    main()
