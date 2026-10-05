#!/usr/bin/env python
"""Fase 5G / Passo A3–A4 — as 60 amostras dos dois braços, às cegas.

**Este ficheiro é o da Fase 5B com uma linha mudada: `SEMENTE_BASE`.** O
desenho, os dois braços, as 10 perguntas, a configuração e as asserções são os
de lá, de propósito — o que a Fase 5G muda é a **régua** (a âncora 3a' da Fase
5F), e não o que se mede.

A semente base passa de `20261003` para `20261005` porque as amostras têm de
ser **novas**: eu li as 60 da 5B ao pontuá-las, e a âncora 3a' foi escrita
depois. Pontuá-las agora com um desfecho escolhido após eu as conhecer é a pesca
que a 5C e a 5E recusaram. Ver o §3.1 do protocolo.

As personas vêm de `fase-5b/personas_5b.py`, **inalteradas**.

----

O docstring original da Fase 5B segue, porque descreve o que este harness faz:

Fase 5B / Passo A3–A4 — as 60 amostras dos dois braços, às cegas.

Protocolo em [`../FASE-5G.md`](../FASE-5G.md), commitado **antes** de este
ficheiro produzir qualquer amostra.

**C** (controlo): `Pipeline.responder` completo com a persona de serviço.
**P** (positiva): o mesmo, com **só** a cláusula poética substituída.

10 perguntas de Caeiro × 2 braços × 3 repetições = **60 amostras**, **30 pares**.

## Porque é que os dois braços têm contexto

A Fase 5 absolveu o contexto por medição (4 pares contra 4, IC95% a conter 0),
logo mantê-lo ligado nos dois braços é manter um incómodo **constante**, e é o
que o utilizador recebe. `Pipeline.recuperar` depende da pergunta e da voz e
nunca do texto da persona, logo os dois braços vêem **os mesmos chunks**: o
emparelhamento é exacto nessa parte, e verifica-se por asserção abaixo.

## Como a persona entra

`Pipeline.responder` chama `voices.persona(voz, idioma)` directamente — não há
injecção por parâmetro. O harness faz *monkeypatch* de `src.pipeline.persona`, e
`src/voices.py` **não se toca**: a variante só entra no serviço se o portão G1
disparar.

## A semente, e o que ela não é

`OllamaGenerator._opcoes` não a aceita, e para um chatbot isso está certo. Aqui
a subclasse injecta-a. **Não é emparelhamento verdadeiro**: o `system` difere
entre braços, logo a sequência de tokens difere e a mesma semente não produz o
mesmo sorteio. Remove uma fonte de variância e torna a corrida reproduzível, e é
o único desvio à configuração de serviço (§3.2 do protocolo).

## O critério 2 usa o piso certo desde o início

A Fase 5 pôs `PISO_LINGUA=0,50` sobre `fracao_lingua`, que conta **stopwords**,
quando 0,50 é o `MIN_FRACAO_DICIONARIO` e o piso real das stopwords é **0,12**
em `lingua_errada`. Reprovou 38 de 40 amostras e teve de se corrigir a si mesma
em `fase-5/corrigir_c2.py`. Aqui a regra corrigida está no sítio à partida, e é
a mesma — logo os números são comparáveis.
"""
from __future__ import annotations

import json
import os
import random
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(AQUI, "..", "fase-5b"))
sys.path.insert(0, os.path.abspath(os.path.join(AQUI, "..", "..")))

import src.pipeline as pipeline_mod
from personas_5b import BRACOS
from src.corpus.build import load
from src.corpus.models import Lang, Voice
from src.generation.ollama import OllamaGenerator
from src.guard import (_fracao_reconhecida, brasileirismos, e_verso,
                       fracao_lingua, lingua_errada)
from src.plagio import analisar
from src.retrieval.encoder import Encoder
from src.retrieval.index import Index
from src.retrieval.rerank import padrao
from src.tokens import contador
from src.voices import persona as persona_servico

PERGUNTAS_JSON = os.path.join(AQUI, "..", "fase-1", "08-perguntas.json")

#: §3.2 do protocolo. A semente de cada célula é `SEMENTE_BASE + 100·r + i`, e
#: é a mesma nos dois braços.
SEMENTE_BASE = 20261005

#: §6.2 do protocolo. Embaralha as 60 amostras garantindo que duas amostras da
#: mesma pergunta nunca ficam adjacentes.
SEMENTE_CEGA = 5

#: §5 do protocolo.
N_REPETICOES = 3

#: O piso do dicionário, onde ele pertence (`guard.MIN_FRACAO_DICIONARIO`).
PISO_DICIONARIO = 0.50


class GeradorComSemente(OllamaGenerator):
    """`OllamaGenerator` com `seed` nas opções. Ver o docstring do módulo."""

    semente: int | None = None

    def _opcoes(self, max_tokens: int, temperatura: float | None = None) -> dict:
        o = super()._opcoes(max_tokens, temperatura)
        if self.semente is not None:
            o["seed"] = self.semente
        return o


def perguntas_caeiro() -> list[dict]:
    """As 10 de Caeiro do gabarito dourado, na ordem do ficheiro."""
    todas = json.load(open(PERGUNTAS_JSON))["perguntas"]
    sel = [p for p in todas if p["voz"] == Voice.CAEIRO.value]
    assert len(sel) == 10, f"esperava 10 perguntas de Caeiro, tenho {len(sel)}"
    return sel


def automaticas(texto_cru: str, texto_limpo: str, contexto) -> dict:
    """Critérios 1, 2 e 5 — os que não precisam de juízo.

    O critério 2 é a regra corrigida da Fase 5: `lingua_errada` (que já faz a
    cascata stopwords → língua rival → dicionário), `brasileirismos`, e o
    dicionário a 0,50 onde pertence.
    """
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
    return {
        "c1_verso": 2 if e_verso(texto_limpo) else 0,
        "c2_pt": c2,
        "c5_plagio": 0 if a.plagiou else 2,
        "brasileirismos": list(br),
        "lingua_errada": errada,
        "fracao_lingua": round(fracao_lingua(texto_limpo, Lang.PT), 3),
        "fracao_dicionario": None if dic is None else round(dic, 3),
        "fracao_copiada": round(a.fracao_copiada, 3),
        "max_similaridade": round(a.max_similaridade, 3),
        "n_versos": a.n_versos,
    }


def main() -> None:
    perguntas = perguntas_caeiro()
    celulas = [(i, p, braco, r)
               for i, p in enumerate(perguntas)
               for r in range(N_REPETICOES)
               for braco in ("C", "P")]
    print(f"{len(perguntas)} perguntas × 2 braços × {N_REPETICOES} repetições "
          f"= {len(celulas)} amostras\n", flush=True)

    meta, chunks = load()
    enc = Encoder()
    idx = Index.load(chunks, enc, meta["assinatura"])
    assert idx is not None, "índice ausente ou desactualizado: correr build primeiro"
    gen = GeradorComSemente()
    pipe = pipeline_mod.Pipeline(idx, enc, gen, contador(), reranker=padrao())
    print(f"gerador {gen.nome} · reordenação ligada · top_k={pipe.top_k}\n", flush=True)

    # Persistência **incremental**, uma linha por amostra. A sessão da Fase 4
    # perdeu 12 gerações por só serializar no fim; com 60 amostras e ~35 s cada
    # isso é mais de meia hora a arriscar.
    diario = os.path.join(AQUI, "01-cru.jsonl")
    cru: list[dict] = []
    if os.path.exists(diario):
        with open(diario) as f:
            cru = [json.loads(l) for l in f if l.strip()]
        feitas = {(d["pergunta_id"], d["braco"], d["repeticao"]) for d in cru}
        print(f"retomado: {len(cru)} amostras já no diário", flush=True)
    else:
        feitas = set()

    def anotar(d: dict) -> None:
        cru.append(d)
        with open(diario, "a") as f:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    # Os chunks recuperados por pergunta: iguais nos dois braços, e a asserção
    # abaixo é o que torna essa afirmação verificada em vez de alegada.
    recuperados_por_q: dict[str, list] = {}

    for i, p, braco, r in celulas:
        chave_celula = (p["id"], braco, r)
        if chave_celula in feitas:
            print(f"{p['id']} {braco} r{r}  (no diário)", flush=True)
            continue

        gen.semente = SEMENTE_BASE + 100 * r + i
        alvo = BRACOS[braco]

        # --- a persona do braço, por monkeypatch -------------------------
        def _persona(voz, idioma=Lang.PT, _alvo=alvo):
            if voz is Voice.CAEIRO and idioma is Lang.PT:
                return _alvo
            return persona_servico(voz, idioma)

        pipeline_mod.persona = _persona
        try:
            t0 = time.perf_counter()
            turno = pipe.responder(p["q"], Voice.CAEIRO, Lang.PT)
            seg = time.perf_counter() - t0
        finally:
            pipeline_mod.persona = persona_servico

        ids_rec = [c.poem_id for c in turno.recuperados]
        if p["id"] in recuperados_por_q:
            assert recuperados_por_q[p["id"]] == ids_rec, (
                f"{p['id']}: recuperação diferente entre braços/repetições — "
                f"o emparelhamento do §3 não se verifica")
        else:
            recuperados_por_q[p["id"]] = ids_rec

        # O `system` tem de conter a cláusula do braço e não a do outro: é a
        # verificação de que o monkeypatch pegou.
        sistema = alvo.system_prompt()
        assert alvo.poetica in sistema
        assert BRACOS["C" if braco == "P" else "P"].poetica not in sistema

        anotar({
            "pergunta_id": p["id"], "pergunta": p["q"], "voz": "caeiro",
            "braco": braco, "repeticao": r, "semente": gen.semente,
            "texto": turno.texto, "texto_cru": turno.resposta.texto,
            "truncada": turno.resposta.truncada,
            "tentativas": turno.tentativas,
            "motivos_guarda": list(turno.veredicto.motivos),
            "n_recuperados": len(turno.recuperados),
            "n_usados": len(turno.usados),
            "usados": [c.poem_id for c in turno.usados],
            "recuperados": ids_rec,
            "segundos": round(seg, 1),
            **automaticas(turno.resposta.texto, turno.texto, turno.recuperados),
        })
        print(f"{p['id']} {braco} r{r}  {seg:5.1f}s  t={turno.tentativas}  "
              f"{len(turno.texto.splitlines())} linhas", flush=True)

    # A ordem do diário é a de geração; o embaralhamento depende dela, logo
    # numa retoma ordena-se pelas células e não pela chegada.
    ordem_fixa = {(p["id"], b, r): n
                  for n, (_, p, b, r) in enumerate(celulas)}
    cru.sort(key=lambda d: ordem_fixa[(d["pergunta_id"], d["braco"], d["repeticao"])])
    assert len(cru) == len(celulas), f"{len(cru)} amostras, esperava {len(celulas)}"

    # --- embaralhar, sem duas da mesma pergunta adjacentes ---------------
    rng = random.Random(SEMENTE_CEGA)
    ordem = list(range(len(cru)))
    for tentativa in range(1, 100001):
        rng.shuffle(ordem)
        if all(cru[ordem[j]]["pergunta_id"] != cru[ordem[j + 1]]["pergunta_id"]
               for j in range(len(ordem) - 1)):
            break
    else:
        raise AssertionError("não consegui embaralhar sem pares adjacentes")
    print(f"\nembaralhado em {tentativa} tentativa(s)", flush=True)

    ids = [f"B{n:02d}" for n in range(1, len(ordem) + 1)]

    # o que os avaliadores podem ler: nada que revele o braço
    seguro = []
    for sid, j in zip(ids, ordem):
        d = cru[j]
        seguro.append({
            "id": sid, "voz": d["voz"], "pergunta": d["pergunta"],
            "texto": d["texto"], "truncada": d["truncada"],
            "c1_verso": d["c1_verso"], "c2_pt": d["c2_pt"],
            "c5_plagio": d["c5_plagio"],
            "brasileirismos": d["brasileirismos"],
            "lingua_errada": d["lingua_errada"],
            "fracao_lingua": d["fracao_lingua"],
            "fracao_dicionario": d["fracao_dicionario"],
            "n_versos": d["n_versos"],
        })
    with open(os.path.join(AQUI, "01-amostras.json"), "w") as f:
        json.dump({"_meta": {
            "protocolo": "docs/FASE-5B.md",
            "aviso": "sem o braço, de propósito. A chave está em 01-chave.json.",
        }, "amostras": seguro}, f, ensure_ascii=False, indent=1)

    with open(os.path.join(AQUI, "01-chave.json"), "w") as f:
        json.dump({"_meta": {
            "aviso": "NÃO ABRIR antes de 02-pontuacoes.json e "
                     "02-pontuacoes-r2.json estarem commitados.",
            "protocolo": "docs/FASE-5B.md §6.2",
        }, "chave": [dict(id=sid, **cru[j]) for sid, j in zip(ids, ordem)]},
            f, ensure_ascii=False, indent=1)

    # a folha de julgamento, cega. É a mesma folha para os dois avaliadores, e
    # **não diz que há braços** — ver o §6.1: R2 é cego ao desenho, não só à
    # condição, e uma folha que anunciasse o tratamento estragaria isso.
    linhas = [
        "# Fase 5B — folha de julgamento, às cegas",
        "",
        "60 poemas gerados na voz de **Alberto Caeiro**, cada um a responder à",
        "pergunta que o encabeça. Pontuar três critérios, **0, 1 ou 2**, com as",
        "âncoras de [`../FASE-5.md`](../FASE-5.md) §5.1–5.3, repetidas aqui:",
        "",
        "**3a — poética da voz**",
        "",
        "| 2 | 1 | 0 |",
        "|---|---|---|",
        "| vê e não interpreta; nenhuma metafísica, símbolo, moral, nem natureza"
        " como espelho de sentimento | sensorial na maior parte, com **uma**"
        " volta simbólica ou moral | filosofa, interpreta, atribui significado"
        " oculto, personifica |",
        "",
        "**3b — forma da voz**",
        "",
        "| 2 | 1 | 0 |",
        "|---|---|---|",
        "| verso livre, linhas curtas, sem rima, pouca imagem, 10–20 versos |"
        " livre mas com imagem decorativa, ou fora do intervalo | rimado, ou"
        " prosa com enters, ou longo e ornamentado |",
        "",
        "Uma amostra **truncada** (cortada a meio) leva **0 em 3b** e é"
        " pontuada normalmente nos outros critérios.",
        "",
        "**4 — responde à pergunta**",
        "",
        "**2** responde ao que foi perguntado, na voz · **1** toca o tema mas",
        "responde a outra coisa, ou responde em geral · **0** divaga.",
        "",
        "Os critérios 1 (é verso), 2 (português europeu) e 5 (não plagia) são",
        "automáticos e **não** se pontuam aqui.",
        "",
        "A ordem é embaralhada e duas amostras da mesma pergunta não são",
        "adjacentes. **Não abrir `01-chave.json`.**",
        "",
        "---",
        "",
    ]
    for s in seguro:
        linhas += [
            f"## {s['id']}",
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

    print(f"{len(seguro)} amostras escritas. A chave está fechada.", flush=True)


if __name__ == "__main__":
    main()
