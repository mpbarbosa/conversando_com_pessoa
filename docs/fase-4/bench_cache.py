#!/usr/bin/env python
"""Passo A4b — o roteador e o gerador disputam o mesmo cache de KV?

Observado a correr o CLI em `/auto`: o roteador custou **20,0 s**, não os 1,2 s
medidos no Passo A2. A causa é óbvia depois de vista — no A2 descartei uma
chamada de aquecimento, logo medi o caso **quente**, e a primeira chamada paga o
prefill a frio dos 331 tokens do `SYSTEM` do roteador.

Mas a pergunta grave é outra. A Fase 0 resolveu os 13,63 s de prefill da persona
pondo-a no `system`, que é prefixo estável e fica em cache — «13,63 s -> 0,91 s
da 2.ª pergunta». O roteador tem um `system` **diferente**. Se o Ollama guarda um
prefixo por slot, alternar roteador e gerador invalida o cache de cada um, e o
custo do `/auto` não é +1,2 s por pergunta: é **+1,2 s mais a persona a voltar a
custar 20 s, em todas as perguntas**.

Isto decide se o `/auto` fica ligável. Mede-se alternando e lendo o
`prompt_eval_duration` que o Ollama devolve.
"""
from __future__ import annotations

import json
import sys

import requests

sys.path.insert(0, ".")
sys.path.insert(0, "docs/fase-4")

from src.corpus.models import Lang, Voice
from src.roteador import MAX_TOKENS, SYSTEM as SYS_ROTEADOR, TEMPERATURA
from src.voices import persona

URL = "http://127.0.0.1:11434/api/chat"
MODELO = "qwen2.5:7b-instruct-q4_K_M"
SYS_PERSONA = persona(Voice.CAMPOS, Lang.PT).system_prompt()

PERGUNTAS = ["o ruído em volta dá-me vertigem",
             "estou cansado de ser tanta coisa",
             "queria partir para longe"]


def chamar(system: str, user: str, max_tokens: int, temp: float) -> dict:
    corpo = {"model": MODELO, "stream": False, "keep_alive": "30m",
             "messages": [{"role": "system", "content": system},
                          {"role": "user", "content": user}],
             "options": {"num_thread": 10, "num_predict": max_tokens,
                         "temperature": temp, "top_p": 1.0 if temp == 0 else 0.9}}
    d = requests.post(URL, json=corpo, timeout=1800).json()
    return {"prefill_s": round(d.get("prompt_eval_duration", 0) / 1e9, 2),
            "prefill_tok": d.get("prompt_eval_count", 0),
            "decode_s": round(d.get("eval_duration", 0) / 1e9, 2)}


def main() -> None:
    saida: dict = {"sys_roteador_tok": None, "sys_persona_tok": None}

    print("A — só o gerador, três perguntas seguidas (o que o CLI faz hoje)")
    a = []
    for q in PERGUNTAS:
        r = chamar(SYS_PERSONA, q, 60, 0.9)
        a.append(r)
        print(f"   prefill {r['prefill_s']:6.2f} s ({r['prefill_tok']} tok)")
    saida["so_gerador"] = a

    print("\nB — alternado: roteador, gerador, roteador, gerador, ...")
    b = []
    for q in PERGUNTAS:
        rr = chamar(SYS_ROTEADOR, q, MAX_TOKENS, TEMPERATURA)
        rg = chamar(SYS_PERSONA, q, 60, 0.9)
        b.append({"roteador": rr, "gerador": rg})
        print(f"   roteador prefill {rr['prefill_s']:6.2f} s "
              f"({rr['prefill_tok']} tok)   |   "
              f"gerador prefill {rg['prefill_s']:6.2f} s ({rg['prefill_tok']} tok)")
    saida["alternado"] = b

    print("\n=== o que isto custa por pergunta, do 2.º turno em diante ===")
    gerador_so = a[-1]["prefill_s"]
    gerador_alt = b[-1]["gerador"]["prefill_s"]
    roteador_alt = b[-1]["roteador"]["prefill_s"]
    print(f"  prefill do gerador sozinho ....... {gerador_so:6.2f} s")
    print(f"  prefill do gerador alternado ..... {gerador_alt:6.2f} s")
    print(f"  prefill do roteador alternado .... {roteador_alt:6.2f} s")
    print(f"  custo real do /auto por pergunta . "
          f"{roteador_alt + (gerador_alt - gerador_so):+6.2f} s")
    saida["resumo"] = {
        "gerador_sozinho_s": gerador_so, "gerador_alternado_s": gerador_alt,
        "roteador_alternado_s": roteador_alt,
        "custo_auto_s": round(roteador_alt + (gerador_alt - gerador_so), 2)}

    with open("docs/fase-4/04-cache.json", "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=1)
    print("\nescrito: docs/fase-4/04-cache.json")


if __name__ == "__main__":
    main()
