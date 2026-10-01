"""Fase 0 / Passo 6 - custo operacional + teste de fumo de recuperacao."""
import gc, glob, json, os, sys, time
import numpy as np
from sentence_transformers import SentenceTransformer

CANDIDATOS = [
    ("PORTULAN/serafim-335m-portuguese-pt-sentence-encoder-ir", None),
    ("intfloat/multilingual-e5-base", "e5"),
    ("BAAI/bge-m3", None),
    ("paraphrase-multilingual-MiniLM-L12-v2", None),
    ("all-MiniLM-L6-v2", None),   # controlo negativo: ingles, deve reprovar
]

SMOKE = json.load(open("docs/fase-0/smoke-set.json"))

def rss_mb():
    for line in open("/proc/self/status"):
        if line.startswith("VmRSS:"):
            return int(line.split()[1]) / 1024
    return 0.0

ids, textos = [], []
for f in sorted(glob.glob("data/pessoa_poems/*.txt")):
    ids.append(os.path.basename(f)[:-4])
    textos.append(open(f, encoding="utf-8").read().strip())
print(f"corpus: {len(ids)} poemas", flush=True)

def prep(xs, kind, modo):
    if modo == "e5":   # sem os prefixos o e5 degrada em silencio
        p = "query: " if kind == "q" else "passage: "
        return [p + x for x in xs]
    return xs

relatorio = []
for nome, modo in CANDIDATOS:
    print(f"\n>>> {nome}", flush=True)
    base_rss = rss_mb()
    t0 = time.perf_counter()
    try:
        m = SentenceTransformer(nome)
    except Exception as e:
        print(f"    FALHOU ao carregar: {type(e).__name__}: {e}", flush=True)
        relatorio.append({"modelo": nome, "erro": f"{type(e).__name__}: {e}"[:300]})
        continue
    t_load = time.perf_counter() - t0
    dim = m.get_sentence_embedding_dimension()
    maxlen = getattr(m, "max_seq_length", None)

    t0 = time.perf_counter()
    emb = m.encode(prep(textos, "p", modo), convert_to_numpy=True,
                   batch_size=16, show_progress_bar=False)
    t_emb = time.perf_counter() - t0
    pico_rss = rss_mb()

    emb = np.asarray(emb, dtype="float32")
    emb /= np.linalg.norm(emb, axis=1, keepdims=True)

    qs = [s["q"] for s in SMOKE]
    qe = np.asarray(m.encode(prep(qs, "q", modo), convert_to_numpy=True), dtype="float32")
    qe /= np.linalg.norm(qe, axis=1, keepdims=True)

    ordem = np.argsort(-(qe @ emb.T), axis=1)
    r1 = r5 = r10 = 0
    detalhe = []
    for i, s in enumerate(SMOKE):
        esp = set(s["esperado"])
        top = [ids[j] for j in ordem[i][:10]]
        pos = next((k + 1 for k, t in enumerate(top) if t in esp), None)
        r1 += pos == 1
        r5 += bool(pos and pos <= 5)
        r10 += bool(pos and pos <= 10)
        detalhe.append({"voz": s["voz"], "q": s["q"][:55], "esperado": s["esperado"][0],
                        "posicao": pos, "top3": top[:3]})

    n = len(SMOKE)
    linha = {
        "modelo": nome, "dim": dim, "max_seq_length": maxlen,
        "load_s": round(t_load, 1),
        "embed_corpus_s": round(t_emb, 1),
        "poemas_por_s": round(len(textos) / t_emb, 1),
        "rss_pico_mb": round(pico_rss, 0),
        "rss_delta_mb": round(pico_rss - base_rss, 0),
        "indice_mb": round(emb.nbytes / 1e6, 1),
        "smoke_r1": r1, "smoke_r5": r5, "smoke_r10": r10, "smoke_n": n,
        "detalhe": detalhe,
    }
    relatorio.append(linha)
    print(f"    dim={dim} maxlen={maxlen} load={t_load:.1f}s embed={t_emb:.1f}s "
          f"({len(textos)/t_emb:.1f} poemas/s) rss={pico_rss:.0f}MB indice={emb.nbytes/1e6:.1f}MB",
          flush=True)
    print(f"    FUMO: R@1={r1}/{n}  R@5={r5}/{n}  R@10={r10}/{n}", flush=True)

    del m, emb, qe
    gc.collect()
    json.dump(relatorio, open("docs/fase-0/06-bench-encoders.json", "w"),
              ensure_ascii=False, indent=1)

print("\n=== RESUMO ===", flush=True)
print(f"{'modelo':56s} {'dim':>5s} {'p/s':>6s} {'idx MB':>7s} {'R@1':>5s} {'R@5':>5s} {'R@10':>5s}")
for r in relatorio:
    if "erro" in r:
        print(f"{r['modelo']:56s}  ERRO: {r['erro'][:40]}")
        continue
    print(f"{r['modelo']:56s} {r['dim']:5d} {r['poemas_por_s']:6.1f} "
          f"{r['indice_mb']:7.1f} {r['smoke_r1']:5d} {r['smoke_r5']:5d} {r['smoke_r10']:5d}")
