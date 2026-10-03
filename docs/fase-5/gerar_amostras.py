#!/usr/bin/env python
"""Fase 5 / Passo A2–A4 — as 40 amostras das duas condições, às cegas.

Protocolo em [`../FASE-5.md`](../FASE-5.md), commitado **antes** deste ficheiro
produzir qualquer amostra.

Condição **A**: `Pipeline.responder` completo — recuperação densa, reordenação
ligada, guardas, repetição por plágio. É o que o utilizador recebe.

Condição **B**: o mesmo `system` (byte a byte), a mesma pergunta, a mesma
semente, e a mensagem de utilizador **sem o bloco de poemas**. Nada mais muda.

## Porque é que B não passa pelo `montar`

`montar` emite sempre o cabeçalho «Poemas teus, para terdes presente o registo e
as imagens:», e sem poemas essa frase anuncia o que não está lá. Medir isso
seria medir um prompt defeituoso em vez da ausência de contexto, logo B monta a
mensagem com as mesmas duas peças que sobram — a pergunta e o rodapé — e as
constantes vêm de `src.generation.prompt`, não copiadas à mão.

## A semente

`OllamaGenerator._opcoes` não a aceita: no serviço, cada resposta é um sorteio
novo, e isso está certo para um chatbot. Para uma ablação emparelhada não está,
e a subclasse abaixo injecta-a. É o **único** desvio à configuração de serviço,
e está declarado no §3.1 do protocolo.

## O que fica num ficheiro que eu posso ler, e o que não

`01-amostras.md` tem id opaco, voz, pergunta e texto — nada mais, porque é o que
vou ler para pontuar. As métricas automáticas vão para `01-amostras.json`, e o
mapa `id -> (pergunta, condição)` para `01-chave.json`, que não se abre antes de
`02-pontuacoes.json` estar commitado.
"""
from __future__ import annotations

import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.corpus.build import load
from src.corpus.models import Lang, Voice
from src.generation.ollama import OllamaGenerator
from src.generation.prompt import _RODAPE
from src.guard import brasileirismos, e_verso, fracao_lingua, verificar
from src.pipeline import Pipeline
from src.plagio import analisar
from src.retrieval.encoder import Encoder
from src.retrieval.index import Index
from src.retrieval.rerank import padrao
from src.tokens import contador
from src.voices import persona

AQUI = os.path.dirname(os.path.abspath(__file__))
PERGUNTAS_JSON = os.path.join(AQUI, "..", "fase-1", "08-perguntas.json")
JULGAMENTOS_JSON = os.path.join(AQUI, "..", "fase-1", "08-julgamentos.json")

#: §3.1 do protocolo. A semente de cada pergunta é `SEMENTE_BASE + índice`, e é
#: a mesma nas duas condições.
SEMENTE_BASE = 20261003

#: §6 do protocolo. Embaralha as 40 amostras e garante que duas amostras da
#: mesma pergunta nunca ficam adjacentes — lê-las em sequência seria reconhecer
#: a condição.
SEMENTE_CEGA = 5

#: §5.1 do critério 2. O detector é lexical, de 14 palavras: zero
#: brasileirismos e fracção de língua acima do piso das guardas dá 2, um dá 1,
#: dois ou mais dá 0. Não apanha colocação proclítica, que a Fase 0 observou ser
#: sistemática neste modelo — está declarado no relatório.
PISO_LINGUA = 0.50


class GeradorComSemente(OllamaGenerator):
    """`OllamaGenerator` com `seed` nas opções. Ver o docstring do módulo."""

    semente: int | None = None

    def _opcoes(self, max_tokens: int, temperatura: float | None = None) -> dict:
        o = super()._opcoes(max_tokens, temperatura)
        if self.semente is not None:
            o["seed"] = self.semente
        return o


def perguntas_julgadas() -> list[dict]:
    """As 20 do gabarito fechado, na ordem do ficheiro. Cinco por voz."""
    todas = json.load(open(PERGUNTAS_JSON))["perguntas"]
    julgadas = {k for k in json.load(open(JULGAMENTOS_JSON)) if not k.startswith("_")}
    sel = [p for p in todas if p["id"] in julgadas]
    assert len(sel) == 20, f"esperava 20 perguntas julgadas, tenho {len(sel)}"
    por_voz: dict[str, int] = {}
    for p in sel:
        por_voz[p["voz"]] = por_voz.get(p["voz"], 0) + 1
    assert set(por_voz.values()) == {5}, f"não são 5 por voz: {por_voz}"
    return sel


def automaticas(texto_cru: str, texto_limpo: str, contexto) -> dict:
    """Critérios 1, 2 e 5 — os que não precisam de juízo."""
    br = brasileirismos(texto_cru)
    frac = fracao_lingua(texto_limpo, Lang.PT)
    a = analisar(texto_limpo, tuple(contexto))
    if len(br) == 0 and frac >= PISO_LINGUA:
        c2 = 2
    elif len(br) == 1 and frac >= PISO_LINGUA:
        c2 = 1
    else:
        c2 = 0
    return {
        "c1_verso": 2 if e_verso(texto_limpo) else 0,
        "c2_pt": c2,
        "c5_plagio": 0 if a.plagiou else 2,
        "brasileirismos": list(br),
        "fracao_lingua": round(frac, 3),
        "fracao_copiada": round(a.fracao_copiada, 3),
        "max_similaridade": round(a.max_similaridade, 3),
        "n_versos": a.n_versos,
    }


def main() -> None:
    perguntas = perguntas_julgadas()
    print(f"{len(perguntas)} perguntas, 2 condições = {2*len(perguntas)} amostras\n",
          flush=True)

    meta, chunks = load()
    enc = Encoder()
    idx = Index.load(chunks, enc, meta["assinatura"])
    assert idx is not None, "índice ausente ou desactualizado: correr build primeiro"
    gen = GeradorComSemente()
    pipe = Pipeline(idx, enc, gen, contador(), reranker=padrao())
    print(f"gerador {gen.nome} · reordenação ligada · top_k={pipe.top_k}\n", flush=True)

    # Persistência **incremental**, uma linha por amostra. Uma sessão paralela
    # perdeu 12 gerações por só serializar no fim; com 40 amostras e ~35 s cada
    # isso é meia hora a arriscar. O `.jsonl` é o diário de bordo, e os
    # ficheiros finais escrevem-se a partir dele.
    diario = os.path.join(AQUI, "01-cru.jsonl")
    cru: list[dict] = []
    if os.path.exists(diario):
        with open(diario) as f:
            cru = [json.loads(l) for l in f if l.strip()]
        feitas = {(d["pergunta_id"], d["condicao"]) for d in cru}
        print(f"retomado: {len(cru)} amostras já no diário", flush=True)
    else:
        feitas = set()

    def anotar(d: dict) -> None:
        cru.append(d)
        with open(diario, "a") as f:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    for i, p in enumerate(perguntas):
        voz = Voice(p["voz"])
        per = persona(voz, Lang.PT)
        gen.semente = SEMENTE_BASE + i
        recuperados = None

        # --- A: o pipeline completo -------------------------------------
        if (p["id"], "A") in feitas:
            print(f"{p['id']} A  (no diário)", flush=True)
        else:
            t0 = time.perf_counter()
            turno = pipe.responder(p["q"], voz, Lang.PT)
            sa = time.perf_counter() - t0
            recuperados = turno.recuperados
            anotar({
                "pergunta_id": p["id"], "voz": p["voz"], "pergunta": p["q"],
                "condicao": "A", "semente": gen.semente,
                "texto": turno.texto, "texto_cru": turno.resposta.texto,
                "truncada": turno.resposta.truncada,
                "tentativas": turno.tentativas,
                "motivos_guarda": list(turno.veredicto.motivos),
                "n_recuperados": len(recuperados),
                "n_usados": len(turno.usados),
                "usados": [c.poem_id for c in turno.usados],
                "segundos": round(sa, 1),
                **automaticas(turno.resposta.texto, turno.texto, recuperados),
            })
            print(f"{p['id']} A  {sa:5.1f}s  t={turno.tentativas}  "
                  f"{len(turno.texto.splitlines())} linhas", flush=True)

        # --- B: a mesma coisa sem o bloco de poemas ---------------------
        if (p["id"], "B") in feitas:
            print(f"{p['id']} B  (no diário)\n", flush=True)
            continue
        # O critério 5 de B compara contra os mesmos chunks de A (§5.4 do
        # protocolo), logo numa retoma é preciso recuperá-los de novo. A
        # recuperação é determinista, logo são os mesmos.
        if recuperados is None:
            recuperados = pipe.recuperar(p["q"], voz, Lang.PT)[0]
        user_b = f"Pergunta: {p['q']}" + _RODAPE
        t0 = time.perf_counter()
        r = gen.gerar(per.system_prompt(), user_b)
        sb = time.perf_counter() - t0
        v = verificar(r.texto, pergunta=p["q"], idioma=Lang.PT)
        anotar({
            "pergunta_id": p["id"], "voz": p["voz"], "pergunta": p["q"],
            "condicao": "B", "semente": gen.semente,
            "texto": v.texto, "texto_cru": r.texto,
            "truncada": r.truncada, "tentativas": 1,
            "motivos_guarda": list(v.motivos),
            "n_recuperados": len(recuperados), "n_usados": 0, "usados": [],
            "segundos": round(sb, 1),
            **automaticas(r.texto, v.texto, recuperados),
        })
        print(f"{p['id']} B  {sb:5.1f}s           "
              f"{len(v.texto.splitlines())} linhas\n", flush=True)

    # a ordem do diário é a de geração; o embaralhamento abaixo depende dela,
    # logo numa retoma ordena-se pelo conjunto fixo e não pela chegada.
    ordem_fixa = {(q["id"], c): n for n, (q, c) in enumerate(
        [(q, c) for q in perguntas for c in ("A", "B")])}
    cru.sort(key=lambda d: ordem_fixa[(d["pergunta_id"], d["condicao"])])
    assert len(cru) == 2 * len(perguntas), f"{len(cru)} amostras, esperava 40"

    # --- embaralhar, com pares nunca adjacentes -------------------------
    rng = random.Random(SEMENTE_CEGA)
    ordem = list(range(len(cru)))
    for tentativa in range(1, 1001):
        rng.shuffle(ordem)
        if all(cru[ordem[j]]["pergunta_id"] != cru[ordem[j+1]]["pergunta_id"]
               for j in range(len(ordem) - 1)):
            break
    else:
        raise AssertionError("não consegui embaralhar sem pares adjacentes")
    print(f"embaralhado em {tentativa} tentativa(s)", flush=True)

    ids = [f"A{n:02d}" for n in range(1, len(ordem) + 1)]

    # o que eu posso ler: nada que revele a condição
    seguro = []
    for sid, j in zip(ids, ordem):
        d = cru[j]
        seguro.append({
            "id": sid, "voz": d["voz"], "pergunta": d["pergunta"],
            "texto": d["texto"], "truncada": d["truncada"],
            "c1_verso": d["c1_verso"], "c2_pt": d["c2_pt"],
            "brasileirismos": d["brasileirismos"],
            "fracao_lingua": d["fracao_lingua"], "n_versos": d["n_versos"],
        })
    with open(os.path.join(AQUI, "01-amostras.json"), "w") as f:
        json.dump({"_meta": {
            "protocolo": "docs/FASE-5.md",
            "aviso": "sem a condição, de propósito. A chave está em 01-chave.json.",
        }, "amostras": seguro}, f, ensure_ascii=False, indent=1)

    # a chave, e tudo o que revela a condição
    with open(os.path.join(AQUI, "01-chave.json"), "w") as f:
        json.dump({"_meta": {
            "aviso": "NÃO ABRIR antes de 02-pontuacoes.json estar commitado.",
            "protocolo": "docs/FASE-5.md §6",
        }, "chave": [dict(id=sid, **cru[j]) for sid, j in zip(ids, ordem)]},
            f, ensure_ascii=False, indent=1)

    # a folha de julgamento, cega
    linhas = [
        "# Fase 5 / Passo B1 — folha de julgamento, às cegas",
        "",
        "Pontuar **3a (poética)**, **3b (forma)** e **4 (responde)**, 0–2, com as",
        "âncoras de [`../FASE-5.md`](../FASE-5.md) §5.1–5.3. Os critérios 1, 2 e 5",
        "são automáticos e não se pontuam aqui.",
        "",
        "A ordem é embaralhada e as duas amostras da mesma pergunta não são",
        "adjacentes. **Não abrir `01-chave.json`.**",
        "",
        "---",
        "",
    ]
    for s in seguro:
        linhas += [
            f"## {s['id']} · voz pedida: **{s['voz']}**",
            "",
            f"> {s['pergunta']}",
            "",
            "```",
            s["texto"],
            "```",
            "",
            "3a=_ 3b=_ 4=_",
            "",
            "---",
            "",
        ]
    with open(os.path.join(AQUI, "01-amostras.md"), "w") as f:
        f.write("\n".join(linhas))

    print(f"\n{len(seguro)} amostras escritas. A chave está fechada.", flush=True)


if __name__ == "__main__":
    main()
