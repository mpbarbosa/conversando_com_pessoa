#!/usr/bin/env python
"""Fase 5 / Instrumento II — identificabilidade da voz, por dois juízes mecânicos.

O desenho deste instrumento **não é meu**: veio de uma sessão paralela que
mediu a mesma pergunta aberta por outro caminho (`docs/FASE-VOZ.md`, não
commitado), e o utilizador decidiu juntar os dois. O que se preserva dela é o
que ela trouxe de melhor, e que o Instrumento I não tinha:

1. **O grupo de controlo de poemas reais.** Uma exactidão sobre poemas gerados
   não se interpreta sozinha. Se um juiz identificar o Caeiro gerado em 60% dos
   casos, isso é bom ou mau? Depende de quantas vezes identifica o Caeiro
   **verdadeiro** — e a Fase 4 A1c mediu o centróide sobre poemas reais a
   **42–46%**. Sem controlo, 45% sobre gerados seria chamado falhanço quando é
   «o instrumento não vê diferença». O que se reporta é a **diferença**.
2. **Juízes mecânicos.** Não julgo nada à mão aqui, logo o viés de avaliador
   único que o §6 do protocolo declara para o Instrumento I **não existe** neste.

O que a fusão acrescenta ao desenho original: os juízes correm sobre as **duas
condições** da ablação, e não só sobre o pipeline completo. A identificabilidade
fica assim emparelhada com e sem contexto, e dá um teste **mecânico** da mesma
hipótese H que o Instrumento I testa à mão. A concordância entre os dois é a
leitura robusta; a discordância deixa a rubrica à mão em suspeita.

## Duas armadilhas, e como são evitadas (do desenho original)

**O centróide tem de excluir os poemas de controlo.** Um poema real está no
índice: incluí-lo no centróide da sua própria voz é pedir ao juiz que reconheça
o que já viu.

**E os grupos têm de enfrentar o MESMO juiz.** Os centróides calculam-se **uma
vez**, sem os poemas de controlo, e usam-se nos três grupos. Excluir os reais só
quando se julgam reais daria instrumentos diferentes a grupos diferentes, e a
diferença entre eles deixaria de significar nada.

## Três confundidores, declarados

**Os vectores do índice levam «Autor — Título» à cabeça** (`Chunk.indexed_text`),
logo os centróides carregam o nome do heterónimo. Os três grupos são julgados
como **verso puro** contra esses centróides, logo o confundidor deprime o
**nível** dos três por igual e deixa a **diferença** — que é o que se reporta —
interpretável.

**E o defeito foi entretanto quantificado: vale 23 pontos.** A remedição da Fase
4 mediu o mesmo classificador com centróides construídos de `c.text` em vez de
`indexed_text` e obteve 64-69% em poemas, contra os 42-46% publicados. Isso
esvazia a razão pela qual este módulo usava `idx.vectores`: era
«comparabilidade com os 42-46% da Fase 4», e esse número é agora conhecido como
artefacto.

Logo correm-se **duas variantes de centróide**, e reportam-se as duas:

| variante | centróides | porquê |
|---|---|---|
| `com_nome` | `idx.vectores` = `encode_passages(indexed_text)` | é o que estava pré-registado, e o que foi pré-registado não se apaga |
| `sem_nome` | `encode_passages(c.text)` | é o instrumento a funcionar, 23 pontos mais forte, e é onde há potência |

A emenda não toca nos portões G5-G7, que são sobre **diferenças** entre grupos e
não sobre o nível: um juiz mais forte mede a mesma diferença com menos ruído.

**O juiz LLM pode ter memorizado os reais** do pré-treino. Isso infla os reais,
logo **alarga** a diferença real-vs-gerado: o defeito agrava a conclusão em vez
de a inventar. É o argumento §2.1 do desenho original, e mantém-se.

**E as descrições de voz do juiz LLM são quase as personas do gerador** — o que
empurra no sentido oposto: um poema gerado foi escrito *para* casar com essa
descrição, logo o juiz favorece os gerados e **encurta** a diferença. Os dois
confundidores do juiz LLM têm sinais contrários e não se somam; é mais uma razão
para a leitura robusta ser a concordância com o centróide, que não tem nenhum
dos dois.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time

import numpy as np
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.corpus.build import load
from src.corpus.models import Lang, Voice
from src.retrieval.encoder import Encoder
from src.retrieval.index import Index

AQUI = os.path.dirname(os.path.abspath(__file__))

#: A re-codificação do corpus não é artefacto de fase: são 6,4 MB de float32
#: deriváveis em 6 min. Fica fora do repositório.
CACHE_DIR = os.environ.get(
    "FASE5_CACHE", os.path.join(tempfile.gettempdir(), "fase5-cache"))

VOZES = (Voice.CAEIRO, Voice.CAMPOS, Voice.REIS, Voice.ORTONIMO)

#: 10 por voz = 40 controlos, para igualar as 40 amostras geradas e dar n=10 a
#: cada comparação por voz. O desenho original usava 6.
POR_VOZ_CONTROLO = 10
SEMENTE = 7

URL = "http://127.0.0.1:11434/api/chat"
MODELO = "qwen2.5:7b-instruct-q4_K_M"

#: Verbatim do desenho original. As descrições são as medidas na Fase 4; o que
#: muda é a **tarefa** — classificar um poema, não escolher quem responde a uma
#: pergunta. Os 72% do roteador da Fase 4 **não transferem**, e é o controlo de
#: reais que calibra este prompt.
SYSTEM_JUIZ = """És um especialista em Fernando Pessoa. Dado um poema, dizes
qual das quatro vozes o escreveu.

CAEIRO — vê as coisas como são e recusa dar-lhes sentido oculto. Verso livre,
linhas curtas, linguagem seca. Natureza, rebanhos, paisagem. Não há metafísica.

CAMPOS — versículo longo, acumulativo, exclamativo. Enumerações e anáfora.
Cidade, máquinas, viagens. Euforia e náusea, cansaço de ser tanta coisa.

REIS — ode breve, estrofes curtas e regulares, dicção alta e latinizante, com
inversões. Estóico. A medida, o gozo breve, as flores que murcham. Lídia, Neera,
Cloe.

ORTONIMO (Fernando Pessoa ele mesmo) — metro regular e rima, quadras ou
quintilhas, dicção simples e musical. O mistério, o fingir, não saber quem é.

Responde com UMA palavra: caeiro, campos, reis ou ortonimo. Nada mais."""


def _norm(a):
    n = np.linalg.norm(a, axis=-1, keepdims=True)
    return a / np.where(n == 0, 1.0, n)


def julgar_llm(texto: str) -> Voice | None:
    corpo = {"model": MODELO, "stream": False, "keep_alive": "30m",
             "messages": [{"role": "system", "content": SYSTEM_JUIZ},
                          {"role": "user", "content": texto}],
             "options": {"num_thread": 10, "num_predict": 8,
                         "temperature": 0.0, "top_p": 1.0}}
    bruto = requests.post(URL, json=corpo, timeout=600).json()
    t = bruto["message"]["content"].strip().lower()
    for v in VOZES:
        if v.value in t:
            return v
    return Voice.ORTONIMO if "pessoa" in t else None


def matriz(pares: list[tuple[Voice, Voice | None]]) -> str:
    cab = "esperada\\prevista".ljust(20) + "".join(v.value.ljust(11) for v in VOZES)
    linhas = [cab]
    for e in VOZES:
        cel = []
        for p in VOZES:
            n = sum(1 for a, b in pares if a is e and b is p)
            cel.append((str(n) if n else "·").ljust(11))
        linhas.append(e.value.ljust(20) + "".join(cel))
    return "\n".join(linhas)


def resumo(nome: str, pares: list[tuple[Voice, Voice | None]]) -> dict:
    certos = sum(1 for e, p in pares if e is p)
    pv = {v.value: f"{sum(1 for e, p in pares if e is v and p is v)}/"
                   f"{sum(1 for e, _ in pares if e is v)}" for v in VOZES}
    print(f"\n--- {nome}: {certos}/{len(pares)} = {certos/len(pares):.0%}   {pv}")
    print(matriz(pares))
    return {"exactidao": round(certos / len(pares), 3), "certos": certos,
            "n": len(pares), "por_voz": pv}


def main() -> None:
    chave = json.load(open(os.path.join(AQUI, "01-chave.json"),
                           encoding="utf-8"))["chave"]
    ger = {"A": [d for d in chave if d["condicao"] == "A"],
           "B": [d for d in chave if d["condicao"] == "B"]}
    assert len(ger["A"]) == len(ger["B"]) == 20, "esperava 20 por condição"

    meta, chunks = load()
    enc = Encoder()
    idx = Index.load(chunks, enc, meta["assinatura"])
    assert idx is not None, "índice ausente ou desactualizado"

    # --- controlo de poemas reais ---------------------------------------
    # Fora: tudo o que entrou no prompt de alguma geração. Só `usados` está
    # registado na chave; os recuperados que não couberam no orçamento nunca
    # chegaram ao modelo, logo não partilham texto com nenhuma resposta.
    no_contexto = {pid for d in chave for pid in d["usados"]}
    rng = np.random.default_rng(SEMENTE)
    reais: list[dict] = []
    ix_controlo: set[int] = set()
    for v in VOZES:
        cand = [i for i, c in enumerate(idx.chunks)
                if c.voice is v and c.language is Lang.PT and c.chunk_ix == 0
                and c.poem_id not in no_contexto
                and 120 <= len(c.text) <= 900]
        escolhidos = rng.choice(cand, size=POR_VOZ_CONTROLO, replace=False).tolist()
        for i in escolhidos:
            ix_controlo.add(i)
            reais.append({"id": f"R{len(reais)+1:02d}", "voz": v.value,
                          "poem_id": idx.chunks[i].poem_id,
                          "texto": idx.chunks[i].text})
    print(f"controlo: {len(reais)} poemas reais · "
          f"{len(no_contexto)} ids excluídos por terem entrado no prompt")

    # --- centróides, UMA vez por variante, sem os poemas de controlo ----
    pt = [i for i, c in enumerate(idx.chunks) if c.language is Lang.PT]
    treino = {v: [i for i in pt if idx.chunks[i].voice is v
                  and i not in ix_controlo] for v in VOZES}

    # `encode_passages(c.text)` sobre o corpus PT custa ~6 min, logo fica em
    # cache fora do repositório: 6,4 MB de float32 derivaveis nao sao artefacto.
    cache = os.path.join(CACHE_DIR, "passagens-text-pt.npy")
    if os.path.exists(cache):
        passagens = np.load(cache)
        print(f"re-codificação lida da cache {passagens.shape}", flush=True)
    else:
        print(f"a re-encodar {len(pt)} chunks como passagem sobre c.text "
              f"(~6 min, uma vez)...", flush=True)
        t0 = time.perf_counter()
        passagens = enc.encode_passages([idx.chunks[i].text for i in pt])
        print(f"  {time.perf_counter()-t0:.0f} s", flush=True)
        os.makedirs(CACHE_DIR, exist_ok=True)
        np.save(cache, passagens)
    pos = {i: k for k, i in enumerate(pt)}

    def centroides(fonte) -> np.ndarray:
        # `None` usa `idx.vectores`; senão indexa a re-codificação por `pos`.
        return _norm(np.vstack([
            (idx.vectores[treino[v]] if fonte is None
             else fonte[[pos[i] for i in treino[v]]]).mean(axis=0)
            for v in VOZES]))

    CENTROIDES = {"com_nome": centroides(None),
                  "sem_nome": centroides(passagens)}

    def julgar_centroide(textos: list[str], cent: np.ndarray) -> list[Voice]:
        qs = enc.encode_queries(textos)
        return [VOZES[int(np.argmax(cent @ q))] for q in qs]

    grupos = {
        "A_com_contexto": ([Voice(d["voz"]) for d in ger["A"]],
                           [d["texto"] for d in ger["A"]]),
        "B_sem_contexto": ([Voice(d["voz"]) for d in ger["B"]],
                           [d["texto"] for d in ger["B"]]),
        "real": ([Voice(r["voz"]) for r in reais], [r["texto"] for r in reais]),
    }

    saida: dict = {"_meta": {
        "protocolo": "docs/FASE-5.md §Instrumento II",
        "desenho": "de uma sessão paralela; fusão decidida pelo utilizador",
        "n_controlo_por_voz": POR_VOZ_CONTROLO, "semente": SEMENTE,
    }, "controlo": reais}
    previsoes: dict[str, list] = {}

    for var, cent in CENTROIDES.items():
        print(f"\n=== juiz: centróide `{var}` (não memoriza) ===")
        for nome, (esperadas, textos) in grupos.items():
            prev = julgar_centroide(textos, cent)
            previsoes[f"centroide_{var}_{nome}"] = [p.value for p in prev]
            saida[f"centroide_{var}_{nome}"] = resumo(
                f"centróide {var} · {nome}", list(zip(esperadas, prev)))

    print("\n=== juiz: qwen2.5:7b (forte; dois confundidores de sinal contrário) ===")
    for nome, (esperadas, textos) in grupos.items():
        prev = [julgar_llm(t) for t in textos]
        previsoes[f"llm_{nome}"] = [p.value if p else None for p in prev]
        saida[f"llm_{nome}"] = resumo(f"LLM · {nome}", list(zip(esperadas, prev)))

    saida["previsoes"] = previsoes

    # --- as diferenças, que são a resposta -------------------------------
    print("\n=== diferenças por juiz ===")
    JUIZES = ("centroide_com_nome", "centroide_sem_nome", "llm")
    for juiz in JUIZES:
        a = saida[f"{juiz}_A_com_contexto"]["exactidao"]
        b = saida[f"{juiz}_B_sem_contexto"]["exactidao"]
        r = saida[f"{juiz}_real"]["exactidao"]
        saida[f"diferencas_{juiz}"] = {
            "A_menos_real": round(a - r, 3), "B_menos_real": round(b - r, 3),
            "A_menos_B": round(a - b, 3)}
        print(f"  {juiz:20s} A {a:.0%} · B {b:.0%} · real {r:.0%}   "
              f"A−real {a-r:+.0%}  B−real {b-r:+.0%}  A−B {a-b:+.0%}")

    # --- o teste emparelhado, por pergunta -------------------------------
    # As 20 perguntas são as mesmas nas duas condições, logo a identificação é
    # emparelhada: contam-se os pares discordantes, que é o que a hipótese H
    # prevê desequilibrados a favor de B.
    print("\n=== pares discordantes, por juiz (H prevê B>A) ===")
    for juiz in JUIZES:
        pa = previsoes[f"{juiz}_A_com_contexto"]
        pb = previsoes[f"{juiz}_B_sem_contexto"]
        so_a = so_b = 0
        for d_a, d_b, x, y in zip(ger["A"], ger["B"], pa, pb):
            assert d_a["pergunta_id"] == d_b["pergunta_id"], "pares desalinhados"
            ca, cb = (x == d_a["voz"]), (y == d_b["voz"])
            so_a += ca and not cb
            so_b += cb and not ca
        saida[f"discordantes_{juiz}"] = {"so_A_acerta": so_a, "so_B_acerta": so_b,
                                         "concordantes": 20 - so_a - so_b}
        print(f"  {juiz:20s} só A acerta {so_a} · só B acerta {so_b} · "
              f"concordam {20-so_a-so_b}")

    with open(os.path.join(AQUI, "04-identificacao.json"), "w",
              encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=1)
    print("\nescrito: docs/fase-5/04-identificacao.json")


if __name__ == "__main__":
    main()
