"""Correccoes 1 e 2 do relatorio da Fase 0.

1. repeat_penalty: nao estava definido, e o 8B degenerou em ciclo no prompt
   longo de Campos. Usado 1.1 (o default do llama.cpp).

   TENSAO DELIBERADA: o estilo de Alvaro de Campos E acumulativo e anaforico
   ("Olho pro lado da barra, olho pro Indefinido, / Olho e contenta-me ver").
   Penalizar repeticao combate o estilo-alvo. 1.1 e moderado de proposito;
   valores altos esterilizariam Campos. Registar se o ciclo volta.

2. Avaliacao as cegas: as amostras saem AGRUPADAS POR PROMPT (necessario para
   julgar "a voz pedida?" e "cumpre a forma?") mas EMBARALHADAS QUANTO AO
   MODELO, com ids opacos. A chave vai para ficheiro separado, a abrir so
   depois de pontuar.
"""
import datetime, json, random, sys
import requests

URL = "http://127.0.0.1:11434/api/generate"
PROMPTS = json.load(open("docs/fase-0/prompts-voz.json"))
MODELS = [
    "qwen2.5:3b-instruct-q4_K_M",
    "qwen2.5:7b-instruct-q4_K_M",
    "llama3.1:8b-instruct-q4_K_M",
]
THREADS = 10
N_AMOSTRAS = 2
SEMENTE_EMBARALHO = 20261001

amostras = {}   # prompt -> [ {modelo, n, texto, segundos} ]
for key, prompt in PROMPTS.items():
    amostras[key] = []
    for model in MODELS:
        for i in range(N_AMOSTRAS):
            try:
                r = requests.post(URL, json={
                    "model": model, "prompt": prompt, "stream": False,
                    "keep_alive": "10m",
                    "options": {"num_thread": THREADS, "num_predict": 300,
                                "temperature": 0.9, "top_p": 0.9,
                                "repeat_penalty": 1.1,          # <- correccao 1
                                "seed": 2000 + i},
                }, timeout=3600)
                r.raise_for_status()
                d = r.json()
                txt = d.get("response", "").strip()
                secs = d.get("total_duration", 0) / 1e9
            except Exception as e:
                txt, secs = f"[ERRO: {type(e).__name__}: {e}]", 0
            amostras[key].append({"modelo": model, "n": i + 1,
                                  "texto": txt, "segundos": secs})
            print(f"{model} {key} #{i+1} - {secs:.0f}s", flush=True)

rng = random.Random(SEMENTE_EMBARALHO)
chave, cego = {}, []
cego += ["# Fase 0 - teste de voz AS CEGAS (correccoes 1 e 2)\n",
         f"\nGerado em {datetime.datetime.now().isoformat(timespec='seconds')}  \n",
         f"threads={THREADS}, temperature=0.9, top_p=0.9, **repeat_penalty=1.1**, num_predict=300\n",
         "\n> Amostras agrupadas por prompt (preciso para julgar voz e forma),\n",
         "> **embaralhadas quanto ao modelo**. A chave esta em `05b-chave.json`,\n",
         "> a abrir so DEPOIS de pontuar.\n",
         "\n> Saidas cruas, sem edicao nem seleccao.\n"]

contador = 0
for key in PROMPTS:
    lote = amostras[key][:]
    rng.shuffle(lote)
    cego.append(f"\n\n---\n\n## prompt: {key}\n")
    for a in lote:
        contador += 1
        aid = f"A{contador:02d}"
        chave[aid] = {"modelo": a["modelo"], "prompt": key,
                      "amostra": a["n"], "segundos": round(a["segundos"], 1)}
        cego.append(f"\n### {aid}  ·  verso `_` PT-PT `_` voz `_` forma `_` poema `_`\n\n")
        cego.append("```\n" + a["texto"] + "\n```\n")

open("docs/fase-0/05b-teste-voz-cego.md", "w", encoding="utf-8").writelines(cego)
json.dump(chave, open("docs/fase-0/05b-chave.json", "w"), ensure_ascii=False, indent=1)
print(f"\nescrito 05b-teste-voz-cego.md ({contador} amostras) e 05b-chave.json")
