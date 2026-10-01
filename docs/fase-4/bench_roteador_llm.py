#!/usr/bin/env python
"""Passo A2 — roteador por chamada ao LLM, e a linha de base lexical.

O portão do A1 falhou: nenhuma variante de embedding passa dos 52,5%, e o A1c
mostrou que não é um problema de registo — poemas usados como consulta roteiam
tão mal como perguntas (42–46%). O espaço do e5 **não separa estas vozes**: toda
a tabela de similaridades vive entre 0,801 e 0,807.

Duas coisas se medem aqui:

- **lexical**: BM25 sobre os chunks, voz com maior pontuação somada no top-k.
  Custo zero, e testa se o que o denso não vê está nas palavras exactas —
  `Lídia` é de Reis, `máquinas` é de Campos, `rebanho` é de Caeiro.
- **llm**: uma chamada curta ao gerador. O LLM leu Pessoa no pré-treino e julga
  **tema e postura**, não superfície — que é exactamente o que falta ao encoder.

**`temperature=0`, não os 0,9 do gerador.** Um roteador tem de ser determinista:
a mesma pergunta não pode dar vozes diferentes em duas sessões. É uma decisão
distinta da do gerador, onde 0,9 foi medido às cegas na Fase 0.
"""
from __future__ import annotations

import json
import sys
import time

sys.path.insert(0, ".")

import requests

from src.corpus.build import load
from src.corpus.models import Lang, Voice

PERGUNTAS = "docs/fase-1/08-perguntas.json"
VOZES = (Voice.CAEIRO, Voice.CAMPOS, Voice.REIS, Voice.ORTONIMO)
URL = "http://127.0.0.1:11434/api/chat"

#: Descreve a **postura** de cada voz, não só o nome. A Fase 0 mediu que nomear
#: o heterónimo produz pastiche e descrever a postura produz a voz; o mesmo
#: princípio vale para o classificar.
SYSTEM = """És um especialista em Fernando Pessoa. Dada uma pergunta ou
sentimento de um leitor, dizes qual das quatro vozes lhe responderia melhor.

CAEIRO — vê as coisas como são e recusa dar-lhes sentido oculto. Natureza,
rebanhos, paisagem, o sol. Pensar estraga o ver. Não há metafísica nem símbolo.

CAMPOS — sente tudo em excesso e ao mesmo tempo. Cidade, máquinas, viagens,
multidões, tabacaria. Euforia e náusea, cansaço de ser tanta coisa, infância
perdida como ferida.

REIS — estóico e epicurista contido. Aceita o destino, aconselha a medida, o
gozo breve do presente, a flor que se colhe antes de murchar. Lídia, Neera,
Cloe. A morte encarada com calma clássica.

ORTONIMO (Fernando Pessoa ele mesmo) — não sabe quem é e sabe que finge. O
mistério, o sonho, a fingida dor, a distância entre pensar e ser, Portugal e o
mar como destino, a criança que foi e não reconhece.

Responde com UMA palavra: caeiro, campos, reis ou ortonimo. Nada mais."""


def rotear_llm(modelo: str, pergunta: str) -> tuple[Voice | None, dict]:
    corpo = {"model": modelo, "stream": False, "keep_alive": "30m",
             "messages": [{"role": "system", "content": SYSTEM},
                          {"role": "user", "content": pergunta}],
             "options": {"num_thread": 10, "num_predict": 8,
                         "temperature": 0.0, "top_p": 1.0}}
    t0 = time.perf_counter()
    d = requests.post(URL, json=corpo, timeout=600).json()
    parede = time.perf_counter() - t0
    bruto = d["message"]["content"].strip().lower()
    achada = next((v for v in VOZES if v.value in bruto), None)
    if achada is None and "pessoa" in bruto:
        achada = Voice.ORTONIMO
    return achada, {
        "bruto": bruto, "parede_s": round(parede, 2),
        "prefill_s": round(d.get("prompt_eval_duration", 0) / 1e9, 2),
        "decode_s": round(d.get("eval_duration", 0) / 1e9, 2),
        "prefill_tok": d.get("prompt_eval_count", 0),
    }


def main() -> None:
    perguntas = json.load(open(PERGUNTAS, encoding="utf-8"))["perguntas"]
    esperadas = [Voice(p["voz"]) for p in perguntas]
    saida: dict = {}

    def registar(nome: str, previstas, extra: dict | None = None) -> None:
        certos = sum(1 for e, p in zip(esperadas, previstas) if e is p)
        pv = {v.value: round(
            sum(1 for e, p in zip(esperadas, previstas) if e is v and p is v)
            / sum(1 for e in esperadas if e is v), 2) for v in VOZES}
        erros = [{"id": perguntas[i]["id"], "q": perguntas[i]["q"],
                  "esperada": esperadas[i].value,
                  "prevista": previstas[i].value if previstas[i] else None}
                 for i in range(len(previstas)) if esperadas[i] is not previstas[i]]
        saida[nome] = {"exactidao": round(certos / len(previstas), 3),
                       "certos": certos, "n": len(previstas), "por_voz": pv,
                       "erros": erros, **(extra or {})}
        print(f"{nome:22s} {certos:3d}/{len(previstas)} = {certos/len(previstas):4.0%}"
              f"   {pv}")

    # --- linha de base lexical --------------------------------------------
    meta, chunks = load()
    from src.retrieval.lexical import IndiceLexical
    lex = IndiceLexical(chunks)
    previstas = []
    for p in perguntas:
        pontos: dict[Voice, float] = {}
        for c, s in lex.search(p["q"], top_k=20, idioma=Lang.PT):
            if c.voice in VOZES:
                pontos[c.voice] = pontos.get(c.voice, 0.0) + s
        previstas.append(max(pontos, key=pontos.get) if pontos else Voice.ORTONIMO)
    print("=== linhas de base e roteador por LLM ===")
    registar("lexical@20", previstas)

    # --- roteadores por LLM ------------------------------------------------
    for modelo in ("qwen2.5:3b-instruct-q4_K_M", "qwen2.5:7b-instruct-q4_K_M"):
        rotear_llm(modelo, "aquecimento, para o modelo carregar")  # descartada
        previstas, tempos, brutos = [], [], []
        for p in perguntas:
            v, info = rotear_llm(modelo, p["q"])
            previstas.append(v)
            tempos.append(info)
            if v is None:
                brutos.append({"id": p["id"], "bruto": info["bruto"]})
        import statistics as st
        registar(f"llm {modelo.split(':')[1].split('-')[0]}", previstas, {
            "parede_mediana_s": round(st.median(t["parede_s"] for t in tempos), 2),
            "prefill_mediana_s": round(st.median(t["prefill_s"] for t in tempos), 2),
            "prefill_tok_mediana": st.median(t["prefill_tok"] for t in tempos),
            "sem_voz_reconhecida": brutos,
        })
        print(f"{'':22s} parede mediana "
              f"{st.median(t['parede_s'] for t in tempos):.2f} s · prefill "
              f"{st.median(t['prefill_s'] for t in tempos):.2f} s "
              f"({st.median(t['prefill_tok'] for t in tempos)} tok)")

    with open("docs/fase-4/02-roteador-llm.json", "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=1)
    print("\nescrito: docs/fase-4/02-roteador-llm.json")


if __name__ == "__main__":
    main()
