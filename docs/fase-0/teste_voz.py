"""Fase 0 / Passo 5 - amostras de voz SEM RAG, gravadas cruas."""
import datetime, json, sys
import requests

URL = "http://127.0.0.1:11434/api/generate"
PROMPTS = json.load(open("docs/fase-0/prompts-voz.json"))
MODELS = [
    "qwen2.5:3b-instruct-q4_K_M",
    "qwen2.5:7b-instruct-q4_K_M",
    "llama3.1:8b-instruct-q4_K_M",
]
BEST_THREADS = int(sys.argv[1]) if len(sys.argv) > 1 else 8
N_AMOSTRAS = 2

out = ["# Fase 0 - teste de voz (sem RAG)\n",
       f"\nGerado em {datetime.datetime.now().isoformat(timespec='seconds')}  \n",
       f"threads={BEST_THREADS}, temperature=0.9, top_p=0.9, num_predict=300\n",
       "\n> Saidas **cruas**, sem edicao nem seleccao. Avaliar pela rubrica de FASE-0.md §5.3.\n",
       "\n> Sem RAG: o objectivo e isolar a competencia poetica do modelo.\n"]

for model in MODELS:
    out.append(f"\n---\n\n## {model}\n")
    for key, prompt in PROMPTS.items():
        out.append(f"\n### {key}\n")
        for i in range(N_AMOSTRAS):
            try:
                r = requests.post(URL, json={
                    "model": model, "prompt": prompt, "stream": False,
                    "keep_alive": "10m",
                    "options": {"num_thread": BEST_THREADS, "num_predict": 300,
                                "temperature": 0.9, "top_p": 0.9, "seed": 1000 + i},
                }, timeout=3600)
                r.raise_for_status()
                d = r.json()
                secs = d.get("total_duration", 0) / 1e9
                txt = d.get("response", "").strip()
            except Exception as e:
                secs, txt = 0, f"[ERRO: {type(e).__name__}: {e}]"
            out.append(f"\n**amostra {i+1}** ({secs:.0f}s)\n\n")
            out.append("```\n" + txt + "\n```\n")
            print(f"{model} {key} #{i+1} - {secs:.0f}s", flush=True)

open("docs/fase-0/05-teste-voz.md", "w", encoding="utf-8").writelines(out)
print("escrito docs/fase-0/05-teste-voz.md")
