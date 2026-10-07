#!/usr/bin/env python
"""Fase 5M / A1–A2 — as 180 amostras das três vozes que faltavam.

Protocolo em [`../FASE-5M.md`](../FASE-5M.md), commitado **antes** de este
ficheiro produzir qualquer amostra.

**Q**: `qwen2.5:7b-instruct-q4_K_M`, o de serviço.
**L**: `llama3.1:8b-instruct-q4_K_M`, a alternativa.

Adaptado de `fase-5h/gerar_amostras.py`, que fez o Caeiro. As mudanças:

- **itera vozes** (campos, reis, ortonimo), cada uma com a sua persona de serviço
  e as suas 10 perguntas do banco dourado (`q11-q20`, `q21-q30`, `q31-q40`);
- a asserção byte a byte do prompt entre braços é por **`(voz, pergunta)`** e não
  só por pergunta;
- **o Caeiro não é regerado.** As 60 amostras da 5H usam exactamente as 10
  perguntas de Caeiro deste mesmo banco (verificado), logo reutilizam-se e a
  grelha fica 4×2 em pé de igualdade.

Mesmas opções, mesmo esquema de sementes, mesmo diário retomável. Só o modelo
muda entre braços; a voz muda entre células.
"""
from __future__ import annotations

import json
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(AQUI, "..", "..")))

from src.corpus.build import load                         # noqa: E402
from src.corpus.models import Lang, Voice                 # noqa: E402
from src.generation.ollama import OllamaGenerator         # noqa: E402
from src.generation.prompt import montar                  # noqa: E402
from src.guard import (_fracao_reconhecida, brasileirismos, e_verso,  # noqa
                       fracao_lingua, lingua_errada)
from src.pipeline import Pipeline                         # noqa: E402
from src.plagio import analisar                           # noqa: E402
from src.retrieval.encoder import Encoder                 # noqa: E402
from src.retrieval.index import Index                     # noqa: E402
from src.retrieval.rerank import padrao                   # noqa: E402
from src.tokens import contador                           # noqa: E402
from src.voices import persona                            # noqa: E402

PERGUNTAS_JSON = os.path.join(AQUI, "..", "fase-1", "08-perguntas.json")

#: §3.2 do protocolo.
SEMENTE_BASE = 20261007
N_REPETICOES = 3
PISO_DICIONARIO = 0.50

MODELOS = {"Q": "qwen2.5:7b-instruct-q4_K_M",
           "L": "llama3.1:8b-instruct-q4_K_M"}

#: §3.1 — as três vozes que a 5H não mediu. O Caeiro vem da 5H.
VOZES = (Voice.CAMPOS, Voice.REIS, Voice.ORTONIMO)


class GeradorComSemente(OllamaGenerator):
    """`OllamaGenerator` com `seed`. Igual ao das fases 5B, 5G e 5H."""

    semente: int | None = None

    def _opcoes(self, max_tokens: int, temperatura: float | None = None) -> dict:
        o = super()._opcoes(max_tokens, temperatura)
        if self.semente is not None:
            o["seed"] = self.semente
        return o


def perguntas_de(voz: Voice) -> list[dict]:
    todas = json.load(open(PERGUNTAS_JSON, encoding="utf-8"))["perguntas"]
    sel = [p for p in todas if p["voz"] == voz.value]
    assert len(sel) == 10, f"esperava 10 perguntas de {voz.value}, tenho {len(sel)}"
    return sel


def automaticas(texto_cru: str, texto_limpo: str, contexto) -> dict:
    """Critérios 1, 2 e 5, com a regra corrigida da Fase 5B. Igual à 5H."""
    br = brasileirismos(texto_cru)
    errada = lingua_errada(texto_limpo, Lang.PT)
    dic = _fracao_reconhecida(texto_limpo, Lang.PT)
    a = analisar(texto_limpo, tuple(contexto))
    if errada or len(br) >= 2 or (dic is not None and dic < PISO_DICIONARIO):
        c2 = 0
    elif len(br) == 1:
        c2 = 1
    else:
        c2 = 2
    return {"c1_verso": 2 if e_verso(texto_limpo) else 0, "c2_pt": c2,
            "c5_plagio": 0 if a.plagiou else 2,
            "brasileirismos": list(br), "lingua_errada": errada,
            "fracao_lingua": round(fracao_lingua(texto_limpo, Lang.PT), 3),
            "fracao_dicionario": None if dic is None else round(dic, 3),
            "fracao_copiada": round(a.fracao_copiada, 3),
            "max_similaridade": round(a.max_similaridade, 3),
            "n_versos": a.n_versos}


def main() -> None:
    perguntas = {v: perguntas_de(v) for v in VOZES}
    celulas = [(braco, v, i, p, r)
               for braco in MODELOS
               for v in VOZES
               for i, p in enumerate(perguntas[v])
               for r in range(N_REPETICOES)]
    print(f"{len(VOZES)} vozes × {len(MODELOS)} modelos × 10 perguntas × "
          f"{N_REPETICOES} repetições = {len(celulas)} amostras", flush=True)
    print("(o Caeiro vem da 5H e não é regerado)\n", flush=True)

    meta, chunks = load()
    enc = Encoder()
    idx = Index.load(chunks, enc, meta["assinatura"])
    assert idx is not None, "índice ausente: correr build primeiro"
    gen = GeradorComSemente()
    n_tokens = contador()
    pipe = Pipeline(idx, enc, gen, n_tokens, reranker=padrao())
    personas = {v: persona(v, Lang.PT) for v in VOZES}

    diario = os.path.join(AQUI, "01-cru.jsonl")
    cru: list[dict] = []
    if os.path.exists(diario):
        with open(diario, encoding="utf-8") as f:
            cru = [json.loads(l) for l in f if l.strip()]
        feitas = {(d["braco"], d["voz"], d["pergunta_id"], d["repeticao"])
                  for d in cru}
        print(f"retomado: {len(cru)} amostras no diário", flush=True)
    else:
        feitas = set()

    def anotar(d: dict) -> None:
        cru.append(d)
        with open(diario, "a", encoding="utf-8") as f:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    #: §3.2 — o prompt por (voz, pergunta), para comparar entre braços.
    prompts: dict[tuple[str, str], tuple[str, str]] = {}
    t_inicio = time.perf_counter()

    for braco, voz, i, p, r in celulas:
        if (braco, voz.value, p["id"], r) in feitas:
            continue
        gen.modelo = MODELOS[braco]
        gen.semente = SEMENTE_BASE + 100 * r + i

        # --- a asserção do §3.2, antes de gerar -------------------------
        recuperados = pipe.recuperar(p["q"], voz, Lang.PT)[0]
        pr = montar(p["q"], recuperados, personas[voz], n_tokens)
        chave = (voz.value, p["id"])
        if chave in prompts:
            assert prompts[chave] == (pr.system, pr.user), (
                f"{voz.value}/{p['id']}: o prompt difere entre braços — o "
                f"confundidor do §3.2 existe e a corrida aborta")
        else:
            prompts[chave] = (pr.system, pr.user)

        t0 = time.perf_counter()
        turno = pipe.responder(p["q"], voz, Lang.PT)
        seg = time.perf_counter() - t0

        anotar({"pergunta_id": p["id"], "pergunta": p["q"], "voz": voz.value,
                "braco": braco, "modelo": MODELOS[braco], "repeticao": r,
                "semente": gen.semente,
                "texto": turno.texto, "texto_cru": turno.resposta.texto,
                "truncada": turno.resposta.truncada,
                "tentativas": turno.tentativas,
                "motivos_guarda": list(turno.veredicto.motivos),
                "n_recuperados": len(turno.recuperados),
                "n_usados": len(turno.usados),
                "usados": [c.poem_id for c in turno.usados],
                "recuperados": [c.poem_id for c in turno.recuperados],
                "segundos": round(seg, 1),
                **automaticas(turno.resposta.texto, turno.texto,
                              turno.recuperados)})
        feito = len(cru)
        decorrido = time.perf_counter() - t_inicio
        resta = (len(celulas) - feito) * (decorrido / max(feito, 1)) / 60
        print(f"[{feito:3d}/{len(celulas)}] {braco} {voz.value[:4]} {p['id']} "
              f"r{r}  {seg:5.1f}s  t={turno.tentativas}  "
              f"{turno.resposta.n_versos if hasattr(turno.resposta, 'n_versos') else len(turno.texto.splitlines())} linhas"
              f"  ~{resta:.0f} min restantes", flush=True)

    assert len(cru) == len(celulas), \
        f"{len(cru)} amostras, esperava {len(celulas)}"
    print(f"\n{len(cru)} amostras. Prompts verificados iguais entre braços em "
          f"{len(prompts)} pares (voz, pergunta).", flush=True)


if __name__ == "__main__":
    main()
