#!/usr/bin/env python
"""Fase 5U / A1–A2 — as 120 amostras da ablação emparelhada.

Protocolo em [`../FASE-5U.md`](../FASE-5U.md), commitado **antes** de este
ficheiro produzir qualquer amostra.

**C** braço completo, o `system` como está em produção.
**A** braço ablado, o mesmo `system` **sem** `REGRAS_LINGUA[Lang.PT]`.

Adaptado de `fase-5m/gerar_amostras.py`. As mudanças:

- **o braço é a ablação e não o modelo.** O modelo é um só, o de serviço
  (`llama3.1:8b`, desde a 5S);
- **a ablação faz-se substituindo o `persona` que o `src.pipeline` importa**
  (§2 do protocolo), e não mexendo em `src/`. O `Pipeline.responder` chama
  `persona(voz, idioma)` do seu próprio espaço de nomes, logo trocar esse nome
  troca a persona sem tocar em mais nada;
- **a asserção do §A2 é ao contrário da da 5M**: ali exigia-se que o `system`
  fosse igual entre braços; aqui exige-se que difira **exactamente** no bloco.

Mesmo esquema de sementes e mesmo diário retomável.

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

from src.corpus.build import load                          # noqa: E402
from src.corpus.models import Lang, Voice                  # noqa: E402
from src.generation.ollama import MODELO, OllamaGenerator   # noqa: E402
from src.generation.prompt import montar                   # noqa: E402
from src.retrieval.encoder import Encoder                  # noqa: E402
from src.retrieval.index import Index                       # noqa: E402
from src.retrieval.rerank import padrao                    # noqa: E402
from src.tokens import contador                            # noqa: E402
from src.voices import REGRAS_LINGUA, Persona, persona     # noqa: E402
from src import pipeline as _pipeline                      # noqa: E402

PERGUNTAS_JSON = os.path.join(AQUI, "..", "fase-1", "08-perguntas.json")

#: §2.2 — o mesmo esquema da 5M e da 5H.
SEMENTE_BASE = 20261007
N_REPETICOES = 2
#: §2 — as tres vozes que falham na 5Q.
VOZES = (Voice.CAMPOS, Voice.REIS, Voice.ORTONIMO)
BRACOS = ("C", "A")


class GeradorComSemente(OllamaGenerator):
    """`OllamaGenerator` com `seed`. Igual ao das fases 5B, 5G, 5H e 5M."""

    semente: int | None = None

    def _opcoes(self, max_tokens: int, temperatura: float | None = None) -> dict:
        o = super()._opcoes(max_tokens, temperatura)
        if self.semente is not None:
            o["seed"] = self.semente
        return o


class PersonaSemLingua(Persona):
    """A persona sem o bloco de língua, e **só** sem ele.

    Reproduz o `system_prompt()` do original omitindo `REGRAS_LINGUA`. Não
    reescreve mais nada: a abertura, a poética, a forma, o `REGRAS_NAO_COPIAR` e
    o `REGRAS_SAIDA` ficam como estão, na mesma ordem e com os mesmos
    separadores.
    """

    def system_prompt(self) -> str:
        from src.voices import REGRAS_NAO_COPIAR, REGRAS_SAIDA
        abertura = "És" if self.idioma is Lang.PT else "You are"
        return (f"{abertura} {self.nome}.\n\n{self.poetica}\n\n{self.forma}"
                f"\n\n{REGRAS_NAO_COPIAR[self.idioma]}"
                f"\n\n{REGRAS_SAIDA[self.idioma]}")


def ablada(p: Persona) -> PersonaSemLingua:
    return PersonaSemLingua(**{f.name: getattr(p, f.name)
                               for f in dataclasses.fields(p)})


def perguntas_de(voz: Voice) -> list[dict]:
    todas = json.load(open(PERGUNTAS_JSON, encoding="utf-8"))["perguntas"]
    sel = [p for p in todas if p["voz"] == voz.value]
    assert len(sel) == 10, f"esperava 10 perguntas de {voz.value}, tenho {len(sel)}"
    return sel


def main() -> None:
    perguntas = {v: perguntas_de(v) for v in VOZES}
    completas = {v: persona(v, Lang.PT) for v in VOZES}
    abladas = {v: ablada(completas[v]) for v in VOZES}

    # ---- §A2: o `system` difere EXACTAMENTE no bloco de lingua --------- #
    bloco = REGRAS_LINGUA[Lang.PT]
    for v in VOZES:
        sc, sa = completas[v].system_prompt(), abladas[v].system_prompt()
        assert bloco in sc, f"{v.value}: o bloco nao esta no braco C"
        assert bloco not in sa, f"{v.value}: o bloco ficou no braco A"
        assert sc.replace(f"\n\n{bloco}", "") == sa, (
            f"{v.value}: os dois `system` diferem em mais do que o bloco")
    print(f"A2 verificado nas {len(VOZES)} vozes: o `system` difere "
          f"exactamente no bloco de língua ({len(bloco)} caracteres)\n",
          flush=True)

    celulas = [(braco, v, i, p, r)
               for braco in BRACOS
               for v in VOZES
               for i, p in enumerate(perguntas[v])
               for r in range(N_REPETICOES)]
    print(f"{len(VOZES)} vozes × {len(BRACOS)} braços × 10 perguntas × "
          f"{N_REPETICOES} repetições = {len(celulas)} amostras", flush=True)
    print(f"modelo único: {MODELO}\n", flush=True)

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
        feitas = {(d["braco"], d["voz"], d["pergunta_id"], d["repeticao"])
                  for d in cru}
        print(f"retomado: {len(cru)} amostras no diário", flush=True)
    else:
        feitas = set()

    def anotar(d: dict) -> None:
        cru.append(d)
        with open(diario, "a", encoding="utf-8") as f:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    t_inicio = time.perf_counter()
    original = _pipeline.persona
    try:
        for braco, voz, i, p, r in celulas:
            if (braco, voz.value, p["id"], r) in feitas:
                continue
            gen.semente = SEMENTE_BASE + 100 * r + i
            escolhidas = completas if braco == "C" else abladas
            # §2: a ablacao e aqui, e so aqui.
            _pipeline.persona = (lambda v, lang, _e=escolhidas: _e[v])

            recuperados = pipe.recuperar(p["q"], voz, Lang.PT)[0]
            pr = montar(p["q"], recuperados, escolhidas[voz], n_tokens)
            assert (bloco in pr.system) == (braco == "C"), (
                f"{braco}/{voz.value}/{p['id']}: o bloco está do lado errado")

            t0 = time.perf_counter()
            turno = pipe.responder(p["q"], voz, Lang.PT)
            seg = time.perf_counter() - t0

            anotar({"pergunta_id": p["id"], "pergunta": p["q"],
                    "voz": voz.value, "braco": braco, "modelo": MODELO,
                    "repeticao": r, "semente": gen.semente,
                    "tokens_system": pr.tokens_system,
                    # §2.1 — o CRU e o que se mede; o limpo vai so para o registo
                    "texto_cru": turno.resposta.texto,
                    "texto_limpo": turno.texto,
                    "truncada": turno.resposta.truncada,
                    "tentativas": turno.tentativas,
                    "motivos_guarda": list(turno.veredicto.motivos),
                    "gramatica_guarda": list(turno.veredicto.gramatica),
                    "usados": [c.poem_id for c in turno.usados],
                    "prefill_tokens": turno.resposta.prefill_tokens,
                    "decode_tokens": turno.resposta.decode_tokens,
                    "segundos": round(seg, 1)})
            feito = len(cru)
            resta = (len(celulas) - feito) * (
                (time.perf_counter() - t_inicio) / max(feito - len(feitas), 1))
            print(f"[{feito:3d}/{len(celulas)}] {braco} {voz.value:9s} "
                  f"{p['id']:4s} r{r}  {seg:5.1f}s  "
                  f"(~{resta/60:.0f} min)", flush=True)
    finally:
        _pipeline.persona = original

    print(f"\n-> {diario}  ({len(cru)} amostras)")


if __name__ == "__main__":
    main()
