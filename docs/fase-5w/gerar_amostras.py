#!/usr/bin/env python
"""Fase 5W / A1–A2 — as 60 amostras dos três braços.

Protocolo em [`../FASE-5W.md`](../FASE-5W.md), commitado **antes** de este
ficheiro produzir qualquer amostra.

**C** como está em produção · **R** directiva explícita · **X** directiva mais
exemplo.

Adaptado de `fase-5u/gerar_amostras.py`. As duas mudanças:

- **os braços são INTERCALADOS** (§2.2): o ciclo exterior é
  `(pergunta, repetição)` e o braço é o interior. Era o defeito nº 1 da 5U, onde
  o braço era o ciclo exterior e a latência ficou não interpretável;
- **muda-se o campo `forma`** da persona do ortónimo, e não o `REGRAS_LINGUA`.

A asserção do §A1 é que os três `forma` diferem **só** na parte da rima — o
resto, incluindo «Entre doze e vinte versos», é idêntico byte a byte.

Escreve `01-cru.jsonl`.
"""
from __future__ import annotations

import dataclasses
import json
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(AQUI, "..", "..")))

from src.corpus.build import load                           # noqa: E402
from src.corpus.models import Lang, Voice                   # noqa: E402
from src.generation.ollama import MODELO, OllamaGenerator    # noqa: E402
from src.generation.prompt import montar                    # noqa: E402
from src.retrieval.encoder import Encoder                   # noqa: E402
from src.retrieval.index import Index                        # noqa: E402
from src.retrieval.rerank import padrao                     # noqa: E402
from src.tokens import contador                             # noqa: E402
from src.voices import persona                              # noqa: E402
from src import pipeline as _pipeline                       # noqa: E402

PERGUNTAS_JSON = os.path.join(AQUI, "..", "fase-1", "08-perguntas.json")
SEMENTE_BASE = 20261007
N_REPETICOES = 2
VOZ = Voice.ORTONIMO

#: O que esta em producao, e o que os tres bracos partilham a seguir.
_RIMA_C = "Metro regular e rima."
#: §2 braco R — a directiva. O esquema vem do corpus (§1.1): entre as janelas
#: de quatro com algum esquema, a rima alternada e ~8x a emparelhada.
_RIMA_R = ("Metro regular e rima. Rima alternada: em cada quadra, o segundo "
           "verso rima com o quarto. A rima é obrigatória, não decorativa.")
#: §2 braco X — a directiva mais um exemplo esquematico. Nao e um poema de
#: Pessoa: e um molde de terminacoes, para nao dar material a copiar.
_RIMA_X = (_RIMA_R + " O molde das terminações é este: o 2.º e o 4.º verso "
           "fecham no mesmo som — «…cansada / …sol / …nada / …só» — e o 1.º e "
           "o 3.º podem ou não fechar entre si.")

#: O resto do campo `forma` do ortonimo, IDENTICO nos tres bracos (§2).
_RESTO = (" Quadras ou quintilhas. Dicção simples e\nmusical — a simplicidade "
          "é aparente, o pensamento não é. Entre doze e vinte\nversos.")
BRACOS = {"C": _RIMA_C, "R": _RIMA_R, "X": _RIMA_X}


class GeradorComSemente(OllamaGenerator):
    semente: int | None = None

    def _opcoes(self, max_tokens: int, temperatura: float | None = None) -> dict:
        o = super()._opcoes(max_tokens, temperatura)
        if self.semente is not None:
            o["seed"] = self.semente
        return o


def persona_com(forma: str):
    base = persona(VOZ, Lang.PT)
    campos = {f.name: getattr(base, f.name) for f in dataclasses.fields(base)}
    campos["forma"] = forma
    return type(base)(**campos)


def main() -> None:
    base = persona(VOZ, Lang.PT)
    # ---- §A1: o `forma` de producao e `_RIMA_C` + `_RESTO`? ------------- #
    esperado = _RIMA_C + _RESTO
    assert base.forma == esperado, (
        "o `forma` em producao mudou; o braco C deixaria de ser producao:\n"
        f"  producao: {base.forma!r}\n  esperado: {esperado!r}")

    personas = {b: persona_com(r + _RESTO) for b, r in BRACOS.items()}
    for b, p in personas.items():
        assert p.forma.endswith(_RESTO), b
        assert p.forma[:-len(_RESTO)] == BRACOS[b], b
    print("A1 verificado: os três `forma` diferem só na parte da rima; "
          f"o resto são {len(_RESTO)} caracteres idênticos")
    for b, p in personas.items():
        print(f"  {b}: {len(p.system_prompt())} caracteres de `system`")

    todas = json.load(open(PERGUNTAS_JSON, encoding="utf-8"))["perguntas"]
    perguntas = [p for p in todas if p["voz"] == VOZ.value]
    assert len(perguntas) == 10, len(perguntas)

    # §2.2 — INTERCALADOS: (pergunta, repeticao) por fora, braco por dentro.
    celulas = [(i, p, r, b)
               for i, p in enumerate(perguntas)
               for r in range(N_REPETICOES)
               for b in BRACOS]
    print(f"\n10 perguntas × {N_REPETICOES} repetições × {len(BRACOS)} braços "
          f"= {len(celulas)} amostras · braços intercalados")
    print(f"modelo: {MODELO}\n", flush=True)

    meta, chunks = load()
    enc = Encoder()
    idx = Index.load(chunks, enc, meta["assinatura"])
    assert idx is not None, "índice ausente: correr build primeiro"
    gen = GeradorComSemente()
    n_tokens = contador()
    pipe = _pipeline.Pipeline(idx, enc, gen, n_tokens, reranker=padrao())

    diario = os.path.join(AQUI, "01-cru.jsonl")
    cru: list[dict] = []
    if os.path.exists(diario):
        with open(diario, encoding="utf-8") as f:
            cru = [json.loads(l) for l in f if l.strip()]
        feitas = {(d["braco"], d["pergunta_id"], d["repeticao"]) for d in cru}
        print(f"retomado: {len(cru)} amostras no diário", flush=True)
    else:
        feitas = set()

    t0_total = time.perf_counter()
    original = _pipeline.persona
    try:
        for i, p, r, b in celulas:
            if (b, p["id"], r) in feitas:
                continue
            gen.semente = SEMENTE_BASE + 100 * r + i
            _pipeline.persona = (lambda v, lang, _p=personas[b]: _p)

            recuperados = pipe.recuperar(p["q"], VOZ, Lang.PT)[0]
            pr = montar(p["q"], recuperados, personas[b], n_tokens)
            assert BRACOS[b] in pr.system, f"{b}: o braço não está no `system`"

            t0 = time.perf_counter()
            turno = pipe.responder(p["q"], VOZ, Lang.PT)
            seg = time.perf_counter() - t0

            d = {"pergunta_id": p["id"], "pergunta": p["q"], "voz": VOZ.value,
                 "braco": b, "modelo": MODELO, "repeticao": r,
                 "semente": gen.semente, "tokens_system": pr.tokens_system,
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
            feito = len(cru)
            print(f"[{feito:2d}/{len(celulas)}] {b} {p['id']:4s} r{r}  "
                  f"{seg:5.1f}s", flush=True)
    finally:
        _pipeline.persona = original

    print(f"\n{(time.perf_counter()-t0_total)/60:.0f} min  ->  {diario}  "
          f"({len(cru)} amostras)")


if __name__ == "__main__":
    main()
