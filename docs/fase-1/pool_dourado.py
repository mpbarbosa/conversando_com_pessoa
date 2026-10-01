"""Fase 1 / Passo 8 - pooling de candidatos para o conjunto dourado.

Metodo TREC: agrupa o top-k de **cada** recuperador, deduplica por grupo, e
ordena por id para nao revelar o ranking de nenhum. Julgar sobre o conteudo, sem
saber quem propos, e o que impede ajustar o gabarito ao vencedor.

Inclui BM25 de proposito: um gabarito construido so com candidatos do encoder
denso ficaria enviesado a favor dele, e a Fase 2 existe para comparar os dois.
"""
import json, os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.corpus.build import load
from src.corpus.models import Voice
from src.retrieval.encoder import Encoder
from src.retrieval.index import Index
from src.retrieval.lexical import IndiceLexical

TOP_K = 5

perguntas = json.load(open("docs/fase-1/08-perguntas.json"))["perguntas"]
meta, chunks = load()
reps = meta["representantes"]

enc = Encoder()
idx = Index.load(chunks, enc, meta["assinatura"])
assert idx is not None, "indice recusado"
lex = IndiceLexical(chunks)
print(f"{len(chunks)} chunks | {len(perguntas)} perguntas | top-{TOP_K} de cada", flush=True)

por_id = {c.poem_id: c for c in chunks}
pool = {}
for p in perguntas:
    voz = Voice(p["voz"])
    qv = enc.encode_queries([p["q"]])[0]
    densos = [c.poem_id for c, _ in idx.search(qv, top_k=TOP_K, voz=voz)]
    lexicais = [c.poem_id for c, _ in lex.search(p["q"], top_k=TOP_K, voz=voz)]
    # dedupe por grupo: dois membros do mesmo grupo sao o mesmo poema
    vistos, cands = set(), []
    for pid in densos + lexicais:
        rep = reps.get(pid, pid)
        if rep in vistos:
            continue
        vistos.add(rep)
        cands.append(pid)
    pool[p["id"]] = {"voz": p["voz"], "q": p["q"],
                     "candidatos": sorted(cands),      # ordem alfabetica: anonimiza
                     "n_densos": len(densos), "n_lexicais": len(lexicais),
                     "sobreposicao": len(set(densos) & set(lexicais))}
    print(f"  {p['id']} {p['voz']:9s} {len(cands):2d} candidatos "
          f"(sobreposição denso/BM25: {pool[p['id']]['sobreposicao']}/{TOP_K})", flush=True)

json.dump(pool, open("docs/fase-1/08-pool.json", "w"), ensure_ascii=False, indent=1)

# --- folha de julgamento ---
linhas = ["# Fase 1 / Passo 8 - folha de julgamento do conjunto dourado\n",
          f"\nTop-{TOP_K} do encoder denso **e** do BM25, deduplicado por grupo,\n",
          "ordenado por id para nao revelar o ranking de nenhum.\n",
          "\n## Escala\n",
          "\n- **2** = responde bem a pergunta; seria boa base para o chatbot\n",
          "- **1** = serviria **se nada melhor houvesse** (nao «tambem e sobre melancolia»)\n",
          "- **0** = nao serve\n",
          "\n> O aperto da nota 1 e deliberado: na Fase 0 fui permissivo e a metrica\n",
          "> saturou, com o controlo ingles a fazer 9/10.\n"]
total = 0
for qid, d in pool.items():
    total += len(d["candidatos"])
    linhas.append(f"\n\n---\n\n## {qid} · {d['voz']} · {d['q']}\n")
    for pid in d["candidatos"]:
        c = por_id.get(pid)
        if c is None:
            continue
        corpo = c.text if len(c.text) <= 420 else c.text[:420] + " […]"
        linhas.append(f"\n### {qid}/{pid} — nota: `_`\n\n```\n{corpo}\n```\n")
open("docs/fase-1/08-folha-julgamento.md", "w", encoding="utf-8").writelines(linhas)

sob = [d["sobreposicao"] for d in pool.values()]
print(f"\n{total} candidatos, {total/len(pool):.1f} por pergunta")
print(f"sobreposicao denso/BM25: mediana {sorted(sob)[len(sob)//2]}/{TOP_K}, "
      f"zero em {sum(1 for x in sob if x == 0)}/{len(sob)} perguntas")
print("escrito docs/fase-1/08-pool.json e 08-folha-julgamento.md")
