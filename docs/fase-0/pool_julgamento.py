"""Fase 0 - correccao metodologica: pooling de relevancia estilo TREC.

O conjunto de fumo nomeia 1 poema esperado por pergunta. O corpus tem forte
redundancia tematica (Pessoa escreveu centenas de quadras sobre os mesmos
temas), logo exact-match subestima gravemente os encoders.

Solucao: agrupar os top-K de TODOS os modelos, deduplicar, e emitir uma folha
de julgamento com o texto de cada candidato. O julgamento e feito sobre o
conteudo, sem saber que modelo propos o candidato -> nao enviesa para nenhum.
"""
import json, os, sys
from collections import OrderedDict

TOPK = int(sys.argv[1]) if len(sys.argv) > 1 else 5

bench = json.load(open("docs/fase-0/06-bench-encoders.json"))
smoke = json.load(open("docs/fase-0/smoke-set.json"))

def texto(pid):
    p = f"data/pessoa_poems/{pid}.txt"
    if not os.path.exists(p):
        return "[inexistente]"
    linhas = open(p, encoding="utf-8").read().strip().split("\n")
    autor = linhas[0].strip()
    corpo = [l for l in linhas[1:] if l.strip() and not l.startswith("Titulo:")]
    return autor, "\n".join(corpo[:10])

# pool: pergunta -> candidatos (ordem estavel, sem repetir), anonimo quanto a modelo
pool = OrderedDict()
for s in smoke:
    pool[s["q"]] = OrderedDict()

for m in bench:
    if "erro" in m:
        continue
    for d in m["detalhe"]:
        q = next((s["q"] for s in smoke if s["q"].startswith(d["q"][:50])), None)
        if q is None:
            continue
        for pid in d["top3"][:TOPK]:
            pool[q].setdefault(pid, 0)
            pool[q][pid] += 1

# o esperado original entra tambem, para ser julgado em pe de igualdade
for s in smoke:
    for pid in s["esperado"]:
        pool[s["q"]].setdefault(pid, 0)

out = ["# Fase 0 - folha de julgamento agrupado (pooling)\n",
       f"\nTop-{TOPK} de cada encoder, deduplicado. Ordem alfabetica por id para\n",
       "nao revelar o ranking de nenhum modelo.\n",
       "\nPara cada candidato, marcar na coluna `apto`:\n",
       "- `2` = responde bem a pergunta (seria uma boa base para o chatbot)\n",
       "- `1` = tematicamente adjacente, aproveitavel\n",
       "- `0` = nao serve\n"]

total = 0
for s in smoke:
    q = s["q"]
    cands = sorted(pool[q].keys())
    total += len(cands)
    out.append(f"\n\n---\n\n## {s['voz']} | {q}\n")
    out.append(f"\n*(esperado originalmente: {', '.join(s['esperado'])})*\n")
    for pid in cands:
        autor, corpo = texto(pid)
        out.append(f"\n### {pid} — {autor}  ·  apto: `_`\n\n```\n{corpo}\n```\n")

open("docs/fase-0/06b-folha-julgamento.md", "w", encoding="utf-8").writelines(out)
print(f"{len(smoke)} perguntas, {total} candidatos ({total/len(smoke):.1f} por pergunta)")
print("escrito docs/fase-0/06b-folha-julgamento.md")
