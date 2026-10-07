"""Fase 5N / A1 — as 30 amostras do `qwen2.5:3b`.

Protocolo em [`../FASE-5N.md`](../FASE-5N.md), commitado **antes** de este
ficheiro produzir qualquer amostra.

**T**: `qwen2.5:3b-instruct-q4_K_M`, o que nunca foi medido.

Deste harness mudou **só o modelo e o nome do braço**. É literalmente o
`fase-5h/gerar_amostras.py` com um braço em vez de dois: mesmas 10 perguntas do
banco dourado, mesmas 3 repetições, **mesmas sementes** (`20261006 + 100·r + i`),
mesmas opções, mesmo cálculo dos automáticos. Isso é o que torna o
emparelhamento com o braço Q da 5H exacto e seed-a-seed.

O braço **Q** (`qwen2.5:7b`) **não se regera**: está em `fase-5h/01-cru.jsonl`,
produzido por este mesmo código.

## A asserção do prompt

A da 5H comparava o prompt entre os dois braços para matar o confundidor do
orçamento de contexto. Aqui há um braço só, logo a comparação **entre** braços
não existe neste ficheiro — faz-se na análise, contra o prompt que a 5H gravou.
O que fica é a asserção de que o prompt é **igual entre repetições** da mesma
pergunta, que é o invariante que este harness pode verificar sozinho.
"""
from __future__ import annotations

import json
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(AQUI, "..", "..")))

from src.corpus.build import load
from src.corpus.models import Lang, Voice
from src.generation.ollama import OllamaGenerator
from src.generation.prompt import montar
from src.guard import (_fracao_reconhecida, brasileirismos, e_verso,
                       fracao_lingua, lingua_errada)
from src.pipeline import Pipeline
from src.plagio import analisar
from src.retrieval.encoder import Encoder
from src.retrieval.index import Index
from src.retrieval.rerank import padrao
from src.tokens import contador
from src.voices import persona

PERGUNTAS_JSON = os.path.join(AQUI, "..", "fase-1", "08-perguntas.json")

#: §3.2 do protocolo.
SEMENTE_BASE = 20261006
N_REPETICOES = 3
PISO_DICIONARIO = 0.50

#: §3 do protocolo. A ordem é a de geração: blocos por modelo.
MODELOS = {"T": "qwen2.5:3b-instruct-q4_K_M"}


class GeradorComSemente(OllamaGenerator):
    """`OllamaGenerator` com `seed`. Igual ao das fases 5B e 5G."""

    semente: int | None = None

    def _opcoes(self, max_tokens: int, temperatura: float | None = None) -> dict:
        o = super()._opcoes(max_tokens, temperatura)
        if self.semente is not None:
            o["seed"] = self.semente
        return o


def perguntas_caeiro() -> list[dict]:
    todas = json.load(open(PERGUNTAS_JSON))["perguntas"]
    sel = [p for p in todas if p["voz"] == Voice.CAEIRO.value]
    assert len(sel) == 10, f"esperava 10 perguntas de Caeiro, tenho {len(sel)}"
    return sel


def automaticas(texto_cru: str, texto_limpo: str, contexto) -> dict:
    """Critérios 1, 2 e 5, com a regra corrigida da Fase 5B."""
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
    perguntas = perguntas_caeiro()
    celulas = [(braco, i, p, r)
               for braco in MODELOS
               for i, p in enumerate(perguntas)
               for r in range(N_REPETICOES)]
    print(f"{len(perguntas)} perguntas × {len(MODELOS)} modelos × "
          f"{N_REPETICOES} repetições = {len(celulas)} amostras\n", flush=True)

    meta, chunks = load()
    enc = Encoder()
    idx = Index.load(chunks, enc, meta["assinatura"])
    assert idx is not None, "índice ausente: correr build primeiro"
    gen = GeradorComSemente()
    n_tokens = contador()
    pipe = Pipeline(idx, enc, gen, n_tokens, reranker=padrao())
    per = persona(Voice.CAEIRO, Lang.PT)

    diario = os.path.join(AQUI, "01-cru.jsonl")
    cru: list[dict] = []
    if os.path.exists(diario):
        with open(diario) as f:
            cru = [json.loads(l) for l in f if l.strip()]
        feitas = {(d["braco"], d["pergunta_id"], d["repeticao"]) for d in cru}
        print(f"retomado: {len(cru)} amostras no diário", flush=True)
    else:
        feitas = set()

    def anotar(d: dict) -> None:
        cru.append(d)
        with open(diario, "a") as f:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    #: §3.1 — o prompt por (pergunta, repetição), para comparar entre braços.
    prompts: dict[str, tuple[str, str]] = {}

    for braco, i, p, r in celulas:
        if (braco, p["id"], r) in feitas:
            print(f"{braco} {p['id']} r{r}  (no diário)", flush=True)
            continue
        gen.modelo = MODELOS[braco]
        gen.semente = SEMENTE_BASE + 100 * r + i

        # --- a asserção do §3.1, antes de gerar -------------------------
        recuperados = pipe.recuperar(p["q"], Voice.CAEIRO, Lang.PT)[0]
        pr = montar(p["q"], recuperados, per, n_tokens)
        if p["id"] in prompts:
            assert prompts[p["id"]] == (pr.system, pr.user), (
                f"{p['id']}: o prompt difere entre repetições, o que não "
                f"devia ser possível — a corrida aborta")
        else:
            prompts[p["id"]] = (pr.system, pr.user)

        t0 = time.perf_counter()
        turno = pipe.responder(p["q"], Voice.CAEIRO, Lang.PT)
        seg = time.perf_counter() - t0

        anotar({"pergunta_id": p["id"], "pergunta": p["q"], "voz": "caeiro",
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
        print(f"{braco} {p['id']} r{r}  {seg:5.1f}s  t={turno.tentativas}  "
              f"{len(turno.texto.splitlines())} linhas", flush=True)

    assert len(cru) == len(celulas), f"{len(cru)} amostras, esperava {len(celulas)}"
    print(f"\n{len(cru)} amostras. Prompt verificado estável entre "
          f"repetições em {len(prompts)} perguntas.", flush=True)
    print("Correr agora folha.py para escrever a folha e fechar a chave.")


if __name__ == "__main__":
    main()
