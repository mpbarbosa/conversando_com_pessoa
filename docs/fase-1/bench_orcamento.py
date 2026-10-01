"""Fase 1 / Passo 5 - orcamento de prompt: prefill a frio e a quente.

A primeira tentativa desta medicao foi invalida, por dois erros registados:

1. **Uma unica medicao por configuracao**, depois de ter observado variancia de
   6x por throttling termico nesta maquina. Resultado: o caso de 5 poemas deu
   prefill 4.5x menor que o de 3 poemas com mais 83 tokens -- impossivel.

2. **A separacao frio/quente nao separava nada.** Variei so o texto da pergunta,
   que fica no inicio da mensagem do utilizador; o prefixo de sistema continua
   em cache nas duas chamadas, logo ambas mediam o regime quente.

Correccoes aqui:

- 3 repeticoes, mediana, pausa de 60s entre configuracoes, temperatura registada
- **frio** forcado com um nonce no INICIO do prompt de sistema. A posicao e
  critica: no fim nao invalida nada, porque o cache e por prefixo
- **quente** com aquecimento explicito do sistema simples antes de medir
- perguntas distintas em cada repeticao, para a parte variavel nunca ser cache
- tokens gerados reportados, para o decode ser comparavel
"""
import os, statistics as st, subprocess, sys, time, uuid

import requests
from transformers import AutoTokenizer

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.corpus.build import load
from src.corpus.models import Voice
from src.voices import persona

URL = "http://127.0.0.1:11434/api/chat"
MODELO = "qwen2.5:7b-instruct-q4_K_M"
N_POEMAS = [1, 3, 5]
REPS = 3
PAUSA = 60
NUM_PREDICT = 150

PERGUNTAS = [
    "O que é a saudade?", "O que é o tempo?", "O que é o mar?",
    "O que é a memória?", "O que é a noite?", "O que é o silêncio?",
]

tq = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
SISTEMA = persona(Voice.CAEIRO).system_prompt()
_, chunks = load()
CAEIRO = [c for c in chunks if c.voice is Voice.CAEIRO][:40]


def temp():
    try:
        o = subprocess.run(["sensors"], capture_output=True, text=True, timeout=5).stdout
        for l in o.splitlines():
            if "Package id 0" in l:
                return float(l.split("+")[1].split("°")[0])
    except Exception:
        pass
    return float("nan")


def n_tok(t: str) -> int:
    return len(tq(t, add_special_tokens=False).input_ids)


def monta_user(n_poemas: int, pergunta: str) -> str:
    ctx = "\n\n---\n\n".join(c.text for c in CAEIRO[:n_poemas])
    return (f"Pergunta: {pergunta}\n\nPoemas teus, para terdes presente o "
            f"registo:\n\n{ctx}\n\nResponde só com o poema.")


def pedir(sistema: str, user: str) -> dict:
    d = requests.post(URL, json={
        "model": MODELO, "stream": False, "keep_alive": "20m",
        "messages": [{"role": "system", "content": sistema},
                     {"role": "user", "content": user}],
        "options": {"num_thread": 10, "num_predict": NUM_PREDICT,
                    "temperature": 0.9, "top_p": 0.9,
                    "repeat_penalty": 1.1, "seed": 11},
    }, timeout=1800).json()
    return {
        "prefill_tok": d.get("prompt_eval_count", 0),
        "prefill_s": d.get("prompt_eval_duration", 1) / 1e9,
        "decode_tok": d.get("eval_count", 0),
        "decode_s": d.get("eval_duration", 1) / 1e9,
        "total_s": d.get("total_duration", 0) / 1e9,
    }


print(f"persona (Caeiro): {n_tok(SISTEMA)} tokens")
print(f"modelo: {MODELO}, threads=10, num_predict={NUM_PREDICT}\n")

resultados = []
for n in N_POEMAS:
    user_exemplo = monta_user(n, PERGUNTAS[0])
    tok_user = n_tok(user_exemplo)
    print(f"{'='*72}\n>>> {n} poema(s) de contexto: user={tok_user} tok, "
          f"total≈{n_tok(SISTEMA)+tok_user} tok  | pkg={temp():.0f}C", flush=True)

    # --- FRIO: nonce no sistema invalida o prefixo em cada corrida ---
    frios = []
    for r in range(REPS):
        # O nonce vai no INICIO. Na primeira tentativa estava no fim, e o cache
        # e por PREFIXO: os 313 tokens da persona continuavam a ser prefixo
        # valido, logo o "frio" media quase o mesmo que o quente (8-13s contra
        # 10.9s). Terceira vez nesta sessao que o cache de prefixo quebra um
        # desenho de medicao meu.
        sis = f"<!-- {uuid.uuid4().hex} -->\n\n{SISTEMA}"
        m = pedir(sis, monta_user(n, PERGUNTAS[r % len(PERGUNTAS)]))
        frios.append(m)
        print(f"    frio  rep{r+1}: prefill {m['prefill_s']:6.2f}s "
              f"({m['prefill_tok']:4d} tok) | decode {m['decode_s']:5.1f}s "
              f"({m['decode_tok']:3d} tok)", flush=True)

    time.sleep(10)

    # --- QUENTE: aquecer o sistema simples, depois medir com users novos ---
    pedir(SISTEMA, monta_user(n, "aquecimento"))
    quentes = []
    for r in range(REPS):
        m = pedir(SISTEMA, monta_user(n, PERGUNTAS[(r + 3) % len(PERGUNTAS)]))
        quentes.append(m)
        print(f"    quente rep{r+1}: prefill {m['prefill_s']:6.2f}s "
              f"({m['prefill_tok']:4d} tok) | decode {m['decode_s']:5.1f}s "
              f"({m['decode_tok']:3d} tok)", flush=True)

    def med(xs, k):
        return st.median(x[k] for x in xs)

    linha = {
        "n_poemas": n, "tok_user": tok_user, "tok_total": n_tok(SISTEMA) + tok_user,
        "frio_prefill_s": round(med(frios, "prefill_s"), 2),
        "quente_prefill_s": round(med(quentes, "prefill_s"), 2),
        "decode_s": round(med(quentes, "decode_s"), 1),
        "decode_tok": int(med(quentes, "decode_tok")),
        "decode_tps": round(med(quentes, "decode_tok") / med(quentes, "decode_s"), 1),
        "total_frio_s": round(med(frios, "prefill_s") + med(frios, "decode_s"), 1),
        "total_quente_s": round(med(quentes, "prefill_s") + med(quentes, "decode_s"), 1),
        "temp_c": temp(),
        "frio_min_max": [round(min(x["prefill_s"] for x in frios), 2),
                         round(max(x["prefill_s"] for x in frios), 2)],
        "quente_min_max": [round(min(x["prefill_s"] for x in quentes), 2),
                           round(max(x["prefill_s"] for x in quentes), 2)],
    }
    resultados.append(linha)
    import json
    json.dump(resultados, open("docs/fase-1/05-orcamento.json", "w"),
              ensure_ascii=False, indent=1)
    print(f"    -> frio {linha['frio_prefill_s']}s  quente {linha['quente_prefill_s']}s  "
          f"decode {linha['decode_s']}s ({linha['decode_tps']} tok/s)", flush=True)
    if n != N_POEMAS[-1]:
        print(f"    (pausa de {PAUSA}s)", flush=True)
        time.sleep(PAUSA)

print(f"\n\n{'='*72}\n=== RESUMO (mediana de {REPS}) ===")
print(f"{'poemas':>6s} {'user':>5s} {'total':>6s} | {'prefill frio':>13s} "
      f"{'prefill quente':>15s} | {'decode':>8s} | {'1a pergunta':>12s} {'seguintes':>10s}")
for x in resultados:
    print(f"{x['n_poemas']:6d} {x['tok_user']:5d} {x['tok_total']:6d} | "
          f"{x['frio_prefill_s']:12.2f}s {x['quente_prefill_s']:14.2f}s | "
          f"{x['decode_s']:7.1f}s | {x['total_frio_s']:11.1f}s {x['total_quente_s']:9.1f}s")
print("\nIntervalos (min-max do prefill), para julgar a fiabilidade:")
for x in resultados:
    print(f"  {x['n_poemas']} poemas: frio {x['frio_min_max']}  quente {x['quente_min_max']}")
