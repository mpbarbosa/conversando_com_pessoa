#!/usr/bin/env python
"""Passo A1c — a hipótese do registo, e o teste que a separa do tema.

O A1b refutou a minha explicação. As quatro vozes têm coerência interna **igual**
(0,934–0,939), logo o colapso no Caeiro não vem de dispersão da classe. E um
classificador **supervisionado** com pesos equilibrados colapsa no Caeiro do
mesmo modo (20 de 23 erros), o que exclui «é a média que é má».

Hipótese nova: o colapso não é sobre tema, é sobre **registo**. As 40 perguntas
são prosa chã, declarativa, de frase curta — «pensar estraga o que se está a
ver». Esse é o registo do Caeiro. Campos é versículo longo e exclamativo; Reis é
inversão latinizante; o ortónimo é metro e rima. O encoder mede superfície — é o
§2 do plano, «similaridade semântica é o objectivo errado para recuperar poesia»
— e a superfície de uma pergunta em prosa chã é a do poeta mais chão.

**O teste que separa as duas explicações:** usar **poemas** como consulta, em vez
de perguntas. Se a mesma rota acerta a voz de um poema que não está no índice,
então o embedding sabe distinguir as vozes, e o que falha é a travessia do
registo de pergunta para o registo de verso. Se falhar também com poemas, as
vozes não são separáveis neste espaço, e o problema é outro.

O conjunto de teste são poemas **retirados do índice**: os centróides e o probe
são calculados sem eles, senão media-se memorização.
"""
from __future__ import annotations

import json
import sys

import numpy as np

sys.path.insert(0, ".")

from src.corpus.build import load
from src.corpus.models import Lang, Voice
from src.retrieval.encoder import Encoder
from src.retrieval.index import Index

PERGUNTAS = "docs/fase-1/08-perguntas.json"
VOZES = (Voice.CAEIRO, Voice.CAMPOS, Voice.REIS, Voice.ORTONIMO)
N_POR_VOZ = 20
SEMENTE = 4


def _norm(a: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(a, axis=-1, keepdims=True)
    return a / np.where(n == 0, 1.0, n)


def main() -> None:
    meta, chunks = load()
    enc = Encoder()
    idx = Index.load(chunks, enc, meta["assinatura"])
    if idx is None:
        sys.exit("índice recusado pelo manifesto")

    perguntas = json.load(open(PERGUNTAS, encoding="utf-8"))["perguntas"]
    qvs = enc.encode_queries([p["q"] for p in perguntas])
    saida: dict = {}

    pt = [i for i, c in enumerate(idx.chunks) if c.language is Lang.PT]
    ix_voz = {v: [i for i in pt if idx.chunks[i].voice is v] for v in VOZES}

    # --- 1. o viés, em números crus ---------------------------------------
    print("=== similaridade média de uma pergunta aos chunks de cada voz ===")
    print("esperada  " + "".join(f"{v.value:>11s}" for v in VOZES) + "   vencedora média")
    linhas = {}
    for esperada in VOZES:
        qs = np.vstack([q for p, q in zip(perguntas, qvs)
                        if Voice(p["voz"]) is esperada])
        medias = {v: float((qs @ idx.vectores[ix_voz[v]].T).mean()) for v in VOZES}
        linhas[esperada.value] = {k.value: round(x, 4) for k, x in medias.items()}
        venc = max(medias, key=medias.get)
        print(f"{esperada.value:10s}" + "".join(f"{medias[v]:11.4f}" for v in VOZES)
              + f"   {venc.value}")
    saida["sim_media_por_voz"] = linhas

    # --- 2. poemas como consulta, fora do índice ---------------------------
    rng = np.random.default_rng(SEMENTE)
    teste: list[int] = []
    for v in VOZES:
        cand = [i for i in ix_voz[v] if idx.chunks[i].chunk_ix == 0]
        teste.extend(rng.choice(cand, size=min(N_POR_VOZ, len(cand)),
                                replace=False).tolist())
    fora = set(teste)
    treino_voz = {v: [i for i in ix_voz[v] if i not in fora] for v in VOZES}

    # Reencodar o verso como CONSULTA: o índice tem-no com prefixo `passage: `,
    # e usá-lo tal qual seria comparar passagem com passagem, o que não é o que
    # o roteador faz em serviço.
    textos = [idx.chunks[i].text for i in teste]
    pvs = enc.encode_queries(textos)
    esperadas_p = [idx.chunks[i].voice for i in teste]

    cent = _norm(np.vstack([idx.vectores[treino_voz[v]].mean(axis=0) for v in VOZES]))
    from sklearn.linear_model import LogisticRegression
    X = np.vstack([idx.vectores[treino_voz[v]] for v in VOZES])
    y = np.array([i for i, v in enumerate(VOZES) for _ in treino_voz[v]])
    clf = LogisticRegression(max_iter=2000, class_weight="balanced").fit(X, y)

    def avaliar(nome: str, previstas: list[Voice], esperadas: list[Voice]) -> None:
        certos = sum(1 for e, p in zip(esperadas, previstas) if e is p)
        pv = {v.value: round(
            sum(1 for e, p in zip(esperadas, previstas) if e is v and p is v)
            / max(1, sum(1 for e in esperadas if e is v)), 2) for v in VOZES}
        saida.setdefault("variantes", {})[nome] = {
            "exactidao": round(certos / len(previstas), 3),
            "certos": certos, "n": len(previstas), "por_voz": pv}
        print(f"{nome:28s} {certos:3d}/{len(previstas):3d} = "
              f"{certos/len(previstas):4.0%}   {pv}")

    print("\n=== poemas como consulta (fora do índice) vs. perguntas ===")
    avaliar("poema -> centróide", [VOZES[int(np.argmax(cent @ q))] for q in pvs],
            esperadas_p)
    avaliar("poema -> probe", [VOZES[int(i)] for i in clf.predict(pvs)], esperadas_p)
    esperadas_q = [Voice(p["voz"]) for p in perguntas]
    cent_todo = _norm(np.vstack([idx.vectores[ix_voz[v]].mean(axis=0) for v in VOZES]))
    avaliar("pergunta -> centróide", [VOZES[int(np.argmax(cent_todo @ q))] for q in qvs],
            esperadas_q)

    with open("docs/fase-4/01c-registo.json", "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=1)
    print("\nescrito: docs/fase-4/01c-registo.json")


if __name__ == "__main__":
    main()
