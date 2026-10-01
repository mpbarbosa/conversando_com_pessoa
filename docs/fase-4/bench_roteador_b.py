#!/usr/bin/env python
"""Passo A1b — diagnóstico do colapso, e duas variantes que ele sugere.

O A1 deu 45% ao centróide, e **17 dos seus 22 erros apontam para o Caeiro** — a
voz com menos chunks (127 contra 1250 do ortónimo). A tabela de riscos da
`FASE-4.md` previa o colapso na classe *maior*; aconteceu o inverso.

A hipótese: o que faz um centróide útil não é o tamanho da classe, é a
**coerência interna**. A média de 127 vectores parecidos aponta para onde eles
apontam; a média de 1250 vectores dispersos aponta para o centro do corpus e
deixa de discriminar. Mede-se pela norma da média **antes** de renormalizar: 1,0
seria uma classe de vectores idênticos, 0,0 uma classe uniformemente dispersa.

Daí as duas variantes:

- **centrado**: subtrair a média global de todo o corpus antes de comparar. É a
  correcção padrão para anisotropia de embeddings — se todos os vectores
  partilham uma direcção comum, essa direcção não discrimina nada e domina o
  cosseno.
- **probe**: regressão logística sobre os vectores dos chunks. Mesmo custo em
  inferência que o centróide (uma matriz 4x768), e aprende a direcção que
  separa, em vez de assumir que é a média.

A ressalva do probe é a assimetria do e5: treina-se em vectores `passage:` e
aplica-se a vectores `query:`. É desvio de distribuição, e se o probe falhar é
o primeiro suspeito.
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
    esperadas = [Voice(p["voz"]) for p in perguntas]

    mpt = np.fromiter((c.language is Lang.PT for c in idx.chunks),
                      bool, len(idx.chunks))
    por_voz = {v: np.fromiter((c.voice is v and c.language is Lang.PT
                               for c in idx.chunks), bool, len(idx.chunks))
               for v in VOZES}

    saida: dict = {}

    # --- diagnóstico: coerência interna de cada voz ------------------------
    print("=== coerência interna (norma da média antes de renormalizar) ===")
    print("voz        n chunks   coerência   sim. média ao centro do corpus")
    centro = _norm(idx.vectores[mpt].mean(axis=0))
    coer = {}
    for v in VOZES:
        bloco = idx.vectores[por_voz[v]]
        media = bloco.mean(axis=0)
        c = float(np.linalg.norm(media))
        ao_centro = float(_norm(media) @ centro)
        coer[v.value] = {"n": int(por_voz[v].sum()), "coerencia": round(c, 4),
                         "sim_ao_centro": round(ao_centro, 4)}
        print(f"{v.value:10s} {por_voz[v].sum():8d}   {c:9.4f}   {ao_centro:9.4f}")
    saida["coerencia"] = coer

    # --- variantes ---------------------------------------------------------
    resultados: dict[str, dict] = {}

    def registar(nome: str, previstas: list[Voice]) -> None:
        certos = sum(1 for e, p in zip(esperadas, previstas) if e is p)
        pv = {v.value: round(
            sum(1 for e, p in zip(esperadas, previstas) if e is v and p is v)
            / sum(1 for e in esperadas if e is v), 2) for v in VOZES}
        erros = [{"id": perguntas[i]["id"], "q": perguntas[i]["q"],
                  "esperada": esperadas[i].value, "prevista": previstas[i].value}
                 for i in range(len(previstas)) if esperadas[i] is not previstas[i]]
        resultados[nome] = {"exactidao": round(certos / len(previstas), 3),
                            "certos": certos, "n": len(previstas),
                            "por_voz": pv, "erros": erros}
        print(f"\n=== {nome} ===")
        print(f"exactidão: {certos}/{len(previstas)} = {certos/len(previstas):.0%}")
        print(f"por voz: {pv}")
        conta: dict[str, int] = {}
        for e in erros:
            conta[e["prevista"]] = conta.get(e["prevista"], 0) + 1
        print(f"erros por voz prevista: {conta}")

    # centróide centrado
    media_global = idx.vectores[mpt].mean(axis=0)
    cent_c = _norm(np.vstack([_norm(idx.vectores[por_voz[v]] - media_global).mean(axis=0)
                              for v in VOZES]))
    qc = _norm(qvs - media_global)
    registar("centrado", [VOZES[int(np.argmax(cent_c @ q))] for q in qc])

    # probe linear
    from sklearn.linear_model import LogisticRegression
    X, y = [], []
    for i, v in enumerate(VOZES):
        X.append(idx.vectores[por_voz[v]])
        y.extend([i] * int(por_voz[v].sum()))
    X = np.vstack(X)
    clf = LogisticRegression(max_iter=2000, class_weight="balanced", C=1.0)
    clf.fit(X, np.array(y))
    registar("probe", [VOZES[int(i)] for i in clf.predict(qvs)])

    # probe sobre vectores centrados
    clf_c = LogisticRegression(max_iter=2000, class_weight="balanced", C=1.0)
    clf_c.fit(_norm(X - media_global), np.array(y))
    registar("probe+centrado", [VOZES[int(i)] for i in clf_c.predict(qc)])

    saida["variantes"] = resultados
    with open("docs/fase-4/01b-roteador.json", "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=1)
    print("\nescrito: docs/fase-4/01b-roteador.json")


if __name__ == "__main__":
    main()
