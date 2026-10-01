#!/usr/bin/env python
"""Fase 3B / Passo 1 — fechar o pool no top-20 do denso.

A Fase 3 mediu o mesmo reranker contra três gabaritos e obteve −0,048, +0,001 e
+0,074. A causa é que **um poema não julgado conta 0**, e o pool crescia com cada
sistema testado.

Um reranker sobre o top-20 do denso só pode promover documentos desse top-20.
Julgando-o **por inteiro**, o pool deixa de depender de que sistemas se testam —
passa a ser definido pela recuperação, que não muda.

A folha sai **por id**, como a da Fase 1 Passo 8, para não revelar a posição no
ranking: saber que um candidato está em 18.º é saber que o denso o despromoveu,
e isso contamina o julgamento.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.avaliacao import Gabarito
from src.corpus.build import load
from src.corpus.models import Voice
from src.retrieval.encoder import Encoder
from src.retrieval.index import Index

PROFUNDIDADE = 20
LIMITE_TEXTO = 420


def main() -> None:
    meta, chunks = load()
    j = json.load(open("docs/fase-1/08-julgamentos.json", encoding="utf-8"))
    notas = {k: v for k, v in j.items() if not k.startswith("_")}
    reps = meta["representantes"]
    gab = Gabarito(notas=notas, representantes=reps)
    perguntas = json.load(open("docs/fase-1/08-perguntas.json",
                               encoding="utf-8"))["perguntas"]

    enc = Encoder()
    idx = Index.load(chunks, enc, meta["assinatura"])
    assert idx is not None, "índice recusado"
    por_id = {c.poem_id: c for c in chunks}

    def julgado(qid: str, poem_id: str) -> bool:
        rep = reps.get(poem_id, poem_id)
        jd = notas.get(qid, {})
        return (poem_id in jd or rep in jd
                or any(reps.get(pid, pid) == rep for pid in jd))

    pool, total_novos = {}, 0
    for p in perguntas:
        if not gab.tem(p["id"]):
            continue
        qv = enc.encode_queries([p["q"]])[0]
        res = idx.search(qv, top_k=PROFUNDIDADE, voz=Voice(p["voz"]))
        vistos, novos, ja = set(), [], []
        for c, _ in res:
            rep = reps.get(c.poem_id, c.poem_id)
            if rep in vistos:
                continue
            vistos.add(rep)
            (ja if julgado(p["id"], c.poem_id) else novos).append(c.poem_id)
        total_novos += len(novos)
        pool[p["id"]] = {"voz": p["voz"], "q": p["q"],
                         "unicos": len(vistos), "ja_julgados": len(ja),
                         "novos": sorted(novos)}
        print(f"  {p['id']} {p['voz']:9s} {len(vistos):2d} únicos · "
              f"{len(ja):2d} julgados · {len(novos):2d} novos", flush=True)

    json.dump(pool, open("docs/fase-3b/01-pool-fechado.json", "w",
                         encoding="utf-8"), ensure_ascii=False, indent=1)

    linhas = [
        "# Fase 3B / Passo 1 — folha de julgamento do pool fechado\n",
        f"\nOs **{total_novos}** candidatos do top-{PROFUNDIDADE} do denso que\n",
        "ainda não têm nota. Ordenados por id dentro de cada pergunta, para\n",
        "**não revelar a posição no ranking**: saber que um candidato está em\n",
        "18.º é saber que o denso o despromoveu.\n",
        "\n## Escala — a mesma da Fase 1 Passo 8\n",
        "\n- **2** = responde bem à pergunta; seria boa base para o chatbot\n",
        "- **1** = serviria **se nada melhor houvesse** (não «também é sobre melancolia»)\n",
        "- **0** = não serve\n",
        "\n> O aperto da nota 1 é deliberado: na Fase 0 fui permissivo e a métrica\n",
        "> saturou, com o controlo inglês a fazer 9/10.\n",
        "\n> **Por que isto é a fase toda:** a Fase 3 mediu o mesmo reranker contra\n",
        "> três gabaritos e deu −0,048, +0,001 e +0,074. Com o top-20 julgado por\n",
        "> inteiro, nenhum documento que um reranker promova pode contar 0 por\n",
        "> falta de julgamento, e o pool deixa de depender de quem o construiu.\n",
    ]
    for qid, d in pool.items():
        if not d["novos"]:
            continue
        linhas.append(f"\n\n---\n\n## {qid} · {d['voz']} · {d['q']}\n")
        for pid in d["novos"]:
            c = por_id.get(pid)
            if c is None:
                continue
            corpo = (c.text if len(c.text) <= LIMITE_TEXTO
                     else c.text[:LIMITE_TEXTO] + " […]")
            linhas.append(f"\n### {qid}/{pid} — nota: `_`\n\n```\n{corpo}\n```\n")
    with open("docs/fase-3b/01-folha-julgamento.md", "w", encoding="utf-8") as f:
        f.writelines(linhas)

    print(f"\n{total_novos} candidatos novos a julgar")
    print(f"gabarito actual: {sum(len(v) for v in notas.values())} julgamentos")
    print(f"depois de fechar: {sum(len(v) for v in notas.values()) + total_novos}")
    print("escrito docs/fase-3b/01-pool-fechado.json e 01-folha-julgamento.md")


if __name__ == "__main__":
    main()
