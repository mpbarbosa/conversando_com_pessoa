#!/usr/bin/env python
"""Fase 5X / A1–A2 — as 60 amostras dos três braços de descodificação.

Protocolo em [`../FASE-5X.md`](../FASE-5X.md), commitado **antes** de este
ficheiro produzir qualquer amostra.

**B** produção · **P** `repeat_penalty = 1.0` · **T** `temperature = 0.5`

Adaptado de `fase-5w/gerar_amostras.py`. A diferença é só onde se mexe: ali era
o campo `forma` da persona, aqui é o dicionário de `_opcoes` — por subclasse,
sem tocar em `src/`.

O `repeat_last_n` **não** é definido em braço nenhum (§3.2): fica a omissão do
Ollama, 64, que é o que define a janela da hipótese.

Escreve `01-cru.jsonl`.
"""
from __future__ import annotations

import json
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(AQUI, "..", "..")))

from src.corpus.build import load                            # noqa: E402
from src.corpus.models import Lang, Voice                     # noqa: E402
from src.generation.ollama import (MODELO, REPEAT_PENALTY,     # noqa: E402
                                   TEMPERATURE, TOP_P,
                                   OllamaGenerator)
from src.generation.prompt import montar                      # noqa: E402
from src.retrieval.encoder import Encoder                     # noqa: E402
from src.retrieval.index import Index                          # noqa: E402
from src.retrieval.rerank import padrao                       # noqa: E402
from src.tokens import GERADOR, contador                      # noqa: E402
from src.voices import persona                                # noqa: E402
from src import pipeline as _pipeline                         # noqa: E402

PERGUNTAS_JSON = os.path.join(AQUI, "..", "fase-1", "08-perguntas.json")
SEMENTE_BASE = 20261007
N_REPETICOES = 2
VOZ = Voice.ORTONIMO

#: §2 — so o que muda. O que nao esta aqui fica como em producao.
BRACOS: dict[str, dict] = {
    "B": {},                                   # producao
    "P": {"repeat_penalty": 1.0},              # a hipotese do §1
    "T": {"temperature": 0.5},                 # o outro lado do passo 17
}


class GeradorAfinado(OllamaGenerator):
    """`OllamaGenerator` com `seed` e com as opções do braço por cima.

    O `_opcoes` da base monta o dicionário de produção; aqui acrescenta-se a
    semente e sobrepõem-se **apenas** as chaves do braço. Assim o braço B é
    produção por construção, e não por eu ter reescrito os valores.
    """

    semente: int | None = None
    sobreposicao: dict | None = None

    def _opcoes(self, max_tokens: int,
                temperatura: float | None = None) -> dict:
        o = super()._opcoes(max_tokens, temperatura)
        if self.semente is not None:
            o["seed"] = self.semente
        if self.sobreposicao:
            o.update(self.sobreposicao)
        return o


def main() -> None:
    # ---- §A1: o braco B e producao, e os outros diferem SO no declarado --- #
    g = GeradorAfinado()
    base = g._opcoes(220)
    assert base["repeat_penalty"] == REPEAT_PENALTY == 1.1, base
    assert base["temperature"] == TEMPERATURE == 0.9, base
    assert base["top_p"] == TOP_P == 0.9, base
    assert "repeat_last_n" not in base, "o §3.2 diz que fica na omissão"
    for b, sob in BRACOS.items():
        g.sobreposicao = sob
        o = g._opcoes(220)
        difere = {k for k in o if o[k] != base.get(k)}
        assert difere == set(sob), f"{b}: difere em {difere}, esperava {set(sob)}"
        print(f"  {b}: repeat_penalty={o['repeat_penalty']} "
              f"temperature={o['temperature']} top_p={o['top_p']}"
              f"{'   <- produção' if not sob else ''}")
    g.sobreposicao = None
    print("A1 verificado: cada braço difere de produção só no que declara\n",
          flush=True)

    todas = json.load(open(PERGUNTAS_JSON, encoding="utf-8"))["perguntas"]
    perguntas = [p for p in todas if p["voz"] == VOZ.value]
    assert len(perguntas) == 10, len(perguntas)

    # §2 — INTERCALADOS: (pergunta, repeticao) por fora, braco por dentro.
    celulas = [(i, p, r, b)
               for i, p in enumerate(perguntas)
               for r in range(N_REPETICOES)
               for b in BRACOS]
    print(f"10 perguntas × {N_REPETICOES} repetições × {len(BRACOS)} braços "
          f"= {len(celulas)} amostras · braços intercalados")
    print(f"modelo: {MODELO}\n", flush=True)

    meta, chunks = load()
    enc = Encoder()
    idx = Index.load(chunks, enc, meta["assinatura"])
    assert idx is not None, "índice ausente: correr build primeiro"
    # §30 do CONTROLO: o tokenizador do **gerador**, nao o do encoder.
    n_tokens = contador(GERADOR)
    pipe = _pipeline.Pipeline(idx, enc, g, n_tokens, reranker=padrao())
    p_ortonimo = persona(VOZ, Lang.PT)

    diario = os.path.join(AQUI, "01-cru.jsonl")
    cru: list[dict] = []
    if os.path.exists(diario):
        with open(diario, encoding="utf-8") as f:
            cru = [json.loads(ln) for ln in f if ln.strip()]
        feitas = {(d["braco"], d["pergunta_id"], d["repeticao"]) for d in cru}
        print(f"retomado: {len(cru)} amostras no diário", flush=True)
    else:
        feitas = set()

    t0_total = time.perf_counter()
    for i, p, r, b in celulas:
        if (b, p["id"], r) in feitas:
            continue
        g.semente = SEMENTE_BASE + 100 * r + i
        g.sobreposicao = BRACOS[b]

        recuperados = pipe.recuperar(p["q"], VOZ, Lang.PT)[0]
        pr = montar(p["q"], recuperados, p_ortonimo, n_tokens)

        t0 = time.perf_counter()
        turno = pipe.responder(p["q"], VOZ, Lang.PT)
        seg = time.perf_counter() - t0

        d = {"pergunta_id": p["id"], "pergunta": p["q"], "voz": VOZ.value,
             "braco": b, "opcoes": g._opcoes(220), "modelo": MODELO,
             "repeticao": r, "semente": g.semente,
             "tokens_system": pr.tokens_system, "tokens_user": pr.tokens_user,
             "texto_cru": turno.resposta.texto,
             "texto_limpo": turno.texto,
             "truncada": turno.resposta.truncada,
             "tentativas": turno.tentativas,
             "motivos_guarda": list(turno.veredicto.motivos),
             "gramatica_guarda": list(turno.veredicto.gramatica),
             "suspeitas": [s.palavra for s in turno.veredicto.suspeitas],
             "usados": [c.poem_id for c in turno.usados],
             "decode_tokens": turno.resposta.decode_tokens,
             "segundos": round(seg, 1)}
        cru.append(d)
        with open(diario, "a", encoding="utf-8") as f:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
        print(f"[{len(cru):2d}/{len(celulas)}] {b} {p['id']:4s} r{r}  "
              f"{seg:5.1f}s", flush=True)

    print(f"\n{(time.perf_counter()-t0_total)/60:.0f} min  ->  {diario}  "
          f"({len(cru)} amostras)")


if __name__ == "__main__":
    main()
