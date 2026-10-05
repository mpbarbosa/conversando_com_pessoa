#!/usr/bin/env python
"""Fase 5I / Passo A3 — as 60 amostras dos dois braços de forma.

Protocolo em [`../FASE-5I.md`](../FASE-5I.md), commitado **antes** de este
ficheiro produzir qualquer amostra.

Gerador: **`llama3.1:8b`** nos dois braços — é o modelo cuja forma se corrige.
**A** usa a `forma` de serviço; **B** usa a reforçada de `personas_5i.py`. A
`poetica` é byte a byte igual, e é o activo que a Fase 5H mediu valer +0,700.

A persona entra por *monkeypatch* de `src.pipeline.persona`; `src/voices.py`
não se toca.

----

O harness é o da Fase 5H com o braço a mudar de **modelo** para **persona**. O
docstring de lá segue, porque a asserção de prompt que ele descreve continua a
correr — aqui a comparar os dois braços de forma, cujo `user` tem de ser igual
e cujo `system` tem de diferir **só** na cláusula de forma:

Fase 5H / Passo A2–A3 — as 60 amostras dos dois modelos.

Protocolo em [`../FASE-5H.md`](../FASE-5H.md), commitado **antes** de este
ficheiro produzir qualquer amostra.

**Q**: `qwen2.5:7b-instruct-q4_K_M`, o de serviço.
**L**: `llama3.1:8b-instruct-q4_K_M`, a alternativa.

Mesma persona (a de serviço), mesmo prompt, mesmas opções, mesma semente. **Só o
modelo muda.**

## A asserção que mata o confundidor

Se o orçamento de prompt fosse contado com o tokenizador do **gerador**, cada
modelo caberia um número diferente de poemas e isto mediria modelo + contexto.
Não é o caso — `src/tokens.py` diz que o contador do `Pipeline` é o do **encoder
e5** —, mas este harness não confia: para cada par recompõe o prompt com
`montar` e compara `system` e `user` **byte a byte** entre os dois braços. Se
diferirem, aborta.

## Porque gera em blocos e não alternado

Alternar modelo a cada amostra forçaria 60 recargas no Ollama, e o
`keep_alive=30m` existe para as evitar. O emparelhamento é por
`(pergunta, repetição)` com semente igual nos dois braços, logo a ordem de
geração não entra em nenhuma comparação (§3.3 do protocolo).
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
from src.voices import persona as persona_servico
sys.path.insert(0, AQUI)
from personas_5i import BRACOS

PERGUNTAS_JSON = os.path.join(AQUI, "..", "fase-1", "08-perguntas.json")

#: §3.2 do protocolo.
SEMENTE_BASE = 20261007
N_REPETICOES = 3
PISO_DICIONARIO = 0.50

#: §3 do protocolo. A ordem é a de geração: blocos por modelo.
MODELO = "llama3.1:8b-instruct-q4_K_M"


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
               for braco in BRACOS
               for i, p in enumerate(perguntas)
               for r in range(N_REPETICOES)]
    print(f"{len(perguntas)} perguntas × {len(BRACOS)} braços × "
          f"{N_REPETICOES} repetições = {len(celulas)} amostras\n", flush=True)

    meta, chunks = load()
    enc = Encoder()
    idx = Index.load(chunks, enc, meta["assinatura"])
    assert idx is not None, "índice ausente: correr build primeiro"
    gen = GeradorComSemente(modelo=MODELO)
    n_tokens = contador()
    pipe = Pipeline(idx, enc, gen, n_tokens, reranker=padrao())

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
        alvo = BRACOS[braco]
        gen.semente = SEMENTE_BASE + 100 * r + i

        # --- a asserção do §3.1, antes de gerar -------------------------
        recuperados = pipe.recuperar(p["q"], Voice.CAEIRO, Lang.PT)[0]
        pr = montar(p["q"], recuperados, alvo, n_tokens)
        # O `user` tem de ser igual entre braços (o contexto não muda), e o
        # `system` tem de diferir **só** na cláusula de forma.
        if p["id"] in prompts:
            user_a, sys_a = prompts[p["id"]]
            assert pr.user == user_a, f"{p['id']}: o user difere entre braços"
            assert (sys_a.replace(BRACOS["A"].forma, "\x00") ==
                    pr.system.replace(BRACOS[braco].forma, "\x00")), (
                f"{p['id']}: o system difere fora da cláusula de forma")
        else:
            prompts[p["id"]] = (pr.user, pr.system)

        def _persona(voz, idioma=Lang.PT, _alvo=alvo):
            if voz is Voice.CAEIRO and idioma is Lang.PT:
                return _alvo
            return persona_servico(voz, idioma)

        import src.pipeline as pipeline_mod
        pipeline_mod.persona = _persona
        try:
            t0 = time.perf_counter()
            turno = pipe.responder(p["q"], Voice.CAEIRO, Lang.PT)
            seg = time.perf_counter() - t0
        finally:
            pipeline_mod.persona = persona_servico

        anotar({"pergunta_id": p["id"], "pergunta": p["q"], "voz": "caeiro",
                "braco": braco, "modelo": MODELO, "repeticao": r,
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
    print(f"\n{len(cru)} amostras. `user` igual e `system` igual fora da "
          f"forma, verificado em {len(prompts)} perguntas.", flush=True)
    print("Correr agora folha.py para escrever a folha e fechar a chave.")


if __name__ == "__main__":
    main()
