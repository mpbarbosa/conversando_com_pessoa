"""Fase 3 / Passo 1 - latencia real dos rerankers em CPU.

Substitui as estimativas derivadas de FASE-3.md §1 (~19s para 568M sobre 20
candidatos), que extrapolavam o custo por token de um bi-encoder.

Independente do conjunto dourado e do indice: so precisa de pares
pergunta/texto, construidos do corpus.

Portao: so passam as configuracoes com latencia <= 6s. Acima disso o total
ultrapassa 50s (28s prefill + 16s decode medidos na Fase 0) e a fase nao e
viavel mesmo que a qualidade melhore.
"""
import json, os, statistics as st, time, subprocess, sys

# O Python poe o directorio do script no sys.path, nao o cwd.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from sentence_transformers import CrossEncoder
from transformers import AutoTokenizer

from src.corpus.parse import parse_corpus

RERANKERS = [
    ("cross-encoder/mmarco-mMiniLMv2-L12-H384-v1", "~120M"),
    ("BAAI/bge-reranker-base", "278M"),
    ("BAAI/bge-reranker-v2-m3", "568M"),
]
N_CANDIDATOS = [4, 8, 20]
TRUNCAGENS = [120, 256, None]
REPS = 5
PORTAO_S = 6.0

def temp():
    try:
        o = subprocess.run(["sensors"], capture_output=True, text=True, timeout=5).stdout
        for l in o.splitlines():
            if "Package id 0" in l:
                return float(l.split("+")[1].split("°")[0])
    except Exception:
        pass
    return float("nan")

# --- material: perguntas do conjunto de fumo + poemas reais como candidatos ---
smoke = json.load(open("docs/fase-0/smoke-set.json"))
perguntas = [s["q"] for s in smoke]
poemas = [p for p in parse_corpus() if p.language.value == "pt" and p.n_words >= 20]
tok_e5 = AutoTokenizer.from_pretrained("intfloat/multilingual-e5-base")

def truncar(texto, n_tok):
    if n_tok is None:
        return texto
    ids = tok_e5(texto, add_special_tokens=False).input_ids
    if len(ids) <= n_tok:
        return texto
    return tok_e5.decode(ids[:n_tok], skip_special_tokens=True)

resultados = []
for nome, tamanho in RERANKERS:
    print(f"\n{'='*74}\n>>> {nome}  ({tamanho})", flush=True)
    t0 = time.perf_counter()
    try:
        ce = CrossEncoder(nome, max_length=512)
    except Exception as e:
        print(f"    FALHOU: {type(e).__name__}: {e}", flush=True)
        resultados.append({"modelo": nome, "erro": f"{type(e).__name__}: {e}"[:200]})
        continue
    print(f"    load: {time.perf_counter()-t0:.1f}s", flush=True)

    for n_cand in N_CANDIDATOS:
        for trunc in TRUNCAGENS:
            # pares distintos a cada repeticao: nunca medir a mesma entrada 2x
            lotes = []
            for r in range(REPS + 1):          # +1 = aquecimento
                q = perguntas[r % len(perguntas)]
                base = (r * n_cand) % (len(poemas) - n_cand)
                lotes.append([(q, truncar(poemas[base + i].body, trunc))
                              for i in range(n_cand)])
            n_tok_medio = st.mean(
                len(tok_e5(d, add_special_tokens=False).input_ids)
                for _, d in lotes[0])

            ce.predict(lotes[0], show_progress_bar=False)   # aquecimento
            tempos = []
            for lote in lotes[1:]:
                t0 = time.perf_counter()
                ce.predict(lote, show_progress_bar=False)
                tempos.append(time.perf_counter() - t0)

            mediana = st.median(tempos)
            passa = mediana <= PORTAO_S
            etiqueta = "trunc=sem" if trunc is None else f"trunc={trunc}"
            print(f"    n={n_cand:2d} {etiqueta:10s} "
                  f"({n_tok_medio:5.0f} tok/doc): {mediana:6.2f}s  "
                  f"[{min(tempos):.2f}-{max(tempos):.2f}]  "
                  f"{'PASSA' if passa else 'reprova'}  pkg={temp():.0f}C", flush=True)
            resultados.append({
                "modelo": nome, "params": tamanho, "n_candidatos": n_cand,
                "truncagem": trunc, "tokens_por_doc": round(n_tok_medio),
                "latencia_mediana_s": round(mediana, 2),
                "latencia_min_s": round(min(tempos), 2),
                "latencia_max_s": round(max(tempos), 2),
                "passa_portao": passa, "temp_c": temp(),
            })
            json.dump(resultados, open("docs/fase-3/01-latencia.json", "w"),
                      ensure_ascii=False, indent=1)
    del ce

print(f"\n\n{'='*74}\n=== CONFIGURACOES QUE PASSAM O PORTAO ({PORTAO_S}s) ===")
viaveis = [r for r in resultados if r.get("passa_portao")]
if not viaveis:
    print("NENHUMA. A Fase 3 nao e viavel neste hardware.")
else:
    print(f"{'modelo':46s} {'n':>3s} {'trunc':>6s} {'lat':>7s} {'total previsto':>15s}")
    for r in sorted(viaveis, key=lambda x: x["latencia_mediana_s"]):
        t = "sem" if r["truncagem"] is None else str(r["truncagem"])
        print(f"{r['modelo'].split('/')[-1][:45]:46s} {r['n_candidatos']:3d} {t:>6s} "
              f"{r['latencia_mediana_s']:6.2f}s {44+r['latencia_mediana_s']:14.1f}s")
