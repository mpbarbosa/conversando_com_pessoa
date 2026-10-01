"""Fase 0 / Passo 4 - prefill e decode por modelo x threads x tamanho de prompt.

BUG CORRIGIDO EM EXECUCAO: o llama.cpp reaproveita o KV cache do prompt entre
repeticoes identicas (visto no log do servidor: "cached n_tokens = 1803" e
"need to evaluate at least 1 token"), logo as repeticoes 2+ mediam a
reavaliacao de UM token em vez do prefill completo.

Em producao o contexto RAG muda a cada pergunta, portanto o prefill que
interessa medir e o prefill A FRIO. Correccao: prefixo variavel no INICIO do
prompt -- o cache e por prefixo, logo alterar os primeiros tokens invalida-o
por completo.
"""
import json, statistics, sys, time
import requests

URL = "http://127.0.0.1:11434/api/generate"
PROMPTS = json.load(open("docs/fase-0/prompts-bench.json"))

MODELS = [
    "qwen2.5:3b-instruct-q4_K_M",
    "qwen2.5:7b-instruct-q4_K_M",
    "llama3.1:8b-instruct-q4_K_M",
]
THREADS = [4, 6, 8, 10]      # nunca 14: exclui os LP-E de 2100 MHz
SIZES = ["500", "1500", "3000"]
NUM_PREDICT = 200
REPS = 2       # reduzido de 3: cada corrida e agora a frio, logo mais lenta
COOLDOWN = 90  # aumentado de 60: pkg subiu de 55 para 81 C na 1a configuracao

def temp():
    try:
        import subprocess
        o = subprocess.run(["sensors"], capture_output=True, text=True, timeout=5).stdout
        for l in o.splitlines():
            if "Package id 0" in l:
                return l.split("+")[1].split("°")[0]
    except Exception:
        pass
    return "?"

_nonce = [0]

def run(model, prompt, threads):
    # Prefixo variavel: impede o reaproveitamento do KV cache entre corridas.
    # Sem isto so a 1a corrida mede prefill real (ver docstring do modulo).
    _nonce[0] += 1
    prompt = f"[{_nonce[0]:04d}]\n{prompt}"
    r = requests.post(URL, json={
        "model": model, "prompt": prompt, "stream": False, "keep_alive": "10m",
        "options": {"num_thread": threads, "num_predict": NUM_PREDICT,
                    "temperature": 0.8, "top_p": 0.9, "seed": 42},
    }, timeout=3600)
    r.raise_for_status()
    d = r.json()
    pe_n, pe_t = d.get("prompt_eval_count", 0), d.get("prompt_eval_duration", 1) or 1
    ev_n, ev_t = d.get("eval_count", 0), d.get("eval_duration", 1) or 1
    return {"prefill_tokens": pe_n, "prefill_s": pe_t / 1e9,
            "prefill_tps": pe_n / (pe_t / 1e9),
            "decode_tokens": ev_n, "decode_s": ev_t / 1e9,
            "decode_tps": ev_n / (ev_t / 1e9),
            "total_s": d.get("total_duration", 0) / 1e9,
            "response": d.get("response", "")}

SWEEP_MODEL = "qwen2.5:7b-instruct-q4_K_M"
SWEEP_SIZE = "1500"

def medir(model, threads, size, cfg, total_cfg):
    prompt = PROMPTS[size]
    print(f"\n[{cfg}/{total_cfg}] {model} | threads={threads} | prompt={size} "
          f"| pkg={temp()}C", flush=True)
    try:
        run(model, prompt, threads)                 # aquecimento
        reps = [run(model, prompt, threads) for _ in range(REPS)]
    except Exception as e:
        print(f"    ERRO: {type(e).__name__}: {e}", flush=True)
        return {"model": model, "threads": threads, "prompt_size": size,
                "erro": str(e)[:200]}
    for i, m in enumerate(reps):
        print(f"    rep{i+1}: prefill {m['prefill_tps']:6.1f} tok/s "
              f"({m['prefill_s']:5.1f}s, {m['prefill_tokens']} tok) | "
              f"decode {m['decode_tps']:5.1f} tok/s "
              f"({m['decode_tokens']} tok) | total {m['total_s']:6.1f}s", flush=True)
    pre = [r["prefill_tps"] for r in reps]
    dec = [r["decode_tps"] for r in reps]
    drift = all(pre[i] > pre[i+1] for i in range(len(pre)-1))
    return {
        "model": model, "threads": threads, "prompt_size": size,
        "prefill_tokens_real": reps[0]["prefill_tokens"],
        "prefill_tps_median": round(statistics.median(pre), 1),
        "decode_tps_median": round(statistics.median(dec), 1),
        "prefill_s_median": round(statistics.median(r["prefill_s"] for r in reps), 1),
        "total_s_median": round(statistics.median(r["total_s"] for r in reps), 1),
        "throttling_suspeito": drift,
        "temp_pkg_c": temp(),
        "amostra_resposta": reps[-1]["response"][:400],
    }

results = []
total_cfg = len(THREADS) + len(MODELS) * len(SIZES)
cfg = 0

print(f"\n########## ETAPA 1: varredura de threads ({SWEEP_MODEL} @ {SWEEP_SIZE}) ##########",
      flush=True)
for threads in THREADS:
    cfg += 1
    r = medir(SWEEP_MODEL, threads, SWEEP_SIZE, cfg, total_cfg)
    r["etapa"] = "varredura_threads"
    results.append(r)
    json.dump(results, open("docs/fase-0/04-bench-geracao.json", "w"),
              ensure_ascii=False, indent=1)
    time.sleep(COOLDOWN)

validos = [r for r in results if "erro" not in r]
if not validos:
    print("ERRO: nenhuma configuracao valida na varredura", flush=True)
    sys.exit(1)
BEST = max(validos, key=lambda r: r["prefill_tps_median"])["threads"]
print(f"\n>>> melhor contagem de threads: {BEST} "
      f"(por prefill tok/s)", flush=True)

print(f"\n########## ETAPA 2: grelha modelo x tamanho @ threads={BEST} ##########",
      flush=True)
for model in MODELS:
    for size in SIZES:
        if model == SWEEP_MODEL and size == SWEEP_SIZE:
            pass  # remedir para consistencia da grelha
        cfg += 1
        r = medir(model, BEST, size, cfg, total_cfg)
        r["etapa"] = "grelha"
        results.append(r)
        json.dump(results, open("docs/fase-0/04-bench-geracao.json", "w"),
                  ensure_ascii=False, indent=1)
        time.sleep(COOLDOWN)

print("\n=== RESUMO (mediana de 3) ===", flush=True)
print(f"{'modelo':30s} {'thr':>4s} {'prompt':>7s} {'prefill':>10s} {'decode':>9s} {'total':>8s}")
for r in results:
    if "erro" in r:
        print(f"{r['model']:30s} {r['threads']:4d} {r['prompt_size']:>7s}   ERRO")
        continue
    flag = "  !throttle" if r["throttling_suspeito"] else ""
    print(f"{r['model']:30s} {r['threads']:4d} {r['prompt_size']:>7s} "
          f"{r['prefill_tps_median']:8.1f}/s {r['decode_tps_median']:7.1f}/s "
          f"{r['total_s_median']:7.1f}s{flag}")
