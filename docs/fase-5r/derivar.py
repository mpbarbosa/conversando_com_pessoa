#!/usr/bin/env python
"""Fase 5R / A1-B2 — deriva o detector do corpus e valida-o em dados retidos.

Protocolo: `../FASE-5R.md` §2-4.

Três classes, por transformação mecânica do vocabulário:
  **A** consoante muda reduzida (`objecto` -> `objeto`)
  **B** acento omitido         (`silêncio` -> `silencio`)
  **C** acento substituído     (`ténue` -> `tênue`)

Regra de marcação (§2): marca-se a variante `v` da canónica `c` se
`freq(c) >= 2 e freq(v) == 0`, ou `freq(c) >= 20 e freq(v) <= 1` — a segunda
cláusula tolera **uma** gralha da transcrição, medida em `silencio` (1 contra 93).

**A validação é retida (§3):** derivar do corpus e medir falsos positivos no
corpus é circular. Deriva-se da metade A e mede-se na metade B.

Escreve `01-derivacao.json` e, se os portões passarem, `data/ortografia-corpus.json`.
"""
from __future__ import annotations

import collections
import json
import os
import random
import re
import sys
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)

from src.corpus.models import Lang                        # noqa: E402
from src.corpus.parse import parse_corpus                 # noqa: E402

SEMENTE = 20261007
#: §2 — a regra de marcacao.
MIN_CANON_ABSOLUTO = 2
MIN_CANON_TOLERANTE = 20
MAX_VARIANTE_TOLERADA = 1
#: §4 R1
LIMIAR_FALSOS_POSITIVOS = 0.01
#: §4 R2
LIMIAR_RECALL = 0.50

_PALAVRA = re.compile(r"[a-zà-ÿ]+")
#: §2 classe A
_RE_MUDA = re.compile(r"[cp](?=[tç])")
#: §2 classe C — pares de diacriticos trocaveis na mesma vogal
_TROCA = {"á": "â", "â": "á", "é": "ê", "ê": "é", "ó": "ô", "ô": "ó"}


def palavras(texto: str) -> list[str]:
    return _PALAVRA.findall(texto.lower())


def sem_acento(w: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", w)
                   if not unicodedata.combining(c))


def variantes(w: str) -> list[tuple[str, str]]:
    """[(variante, classe)] geradas a partir de uma forma canonica."""
    out = []
    r = _RE_MUDA.sub("", w)
    if r != w:
        out.append((r, "A"))
    s = sem_acento(w)
    if s != w:
        out.append((s, "B"))
    for i, ch in enumerate(w):
        if ch in _TROCA:
            out.append((w[:i] + _TROCA[ch] + w[i + 1:], "C"))
    return out


def deriva(vocab: collections.Counter) -> dict[str, dict]:
    """variante -> {canonica, classe, freq_canonica, freq_variante}."""
    marcadas: dict[str, dict] = {}
    for w, n in vocab.items():
        for v, cls in variantes(w):
            nv = vocab.get(v, 0)
            ok = ((n >= MIN_CANON_ABSOLUTO and nv == 0)
                  or (n >= MIN_CANON_TOLERANTE and nv <= MAX_VARIANTE_TOLERADA))
            if not ok:
                continue
            # Se duas canonicas gerassem a mesma variante, fica a mais frequente.
            if v not in marcadas or marcadas[v]["freq_canonica"] < n:
                marcadas[v] = {"canonica": w, "classe": cls,
                               "freq_canonica": n, "freq_variante": nv}
    return marcadas


def marca(texto: str, lista: dict) -> list[str]:
    return sorted({w for w in palavras(texto) if w in lista})


def main() -> None:
    poemas = [p for p in parse_corpus(os.path.join(RAIZ, "data/pessoa_poems"))
              if p.language is Lang.PT]
    print(f"{len(poemas)} poemas em pt (de 2083)")

    def vocab_de(ps) -> collections.Counter:
        c = collections.Counter()
        for p in ps:
            c.update(palavras(p.body))
        return c

    # ---------------- B1: falsos positivos, em dados retidos ------------ #
    ordem = sorted(poemas, key=lambda p: p.id)
    random.Random(SEMENTE).shuffle(ordem)
    meio = len(ordem) // 2
    metA, metB = ordem[:meio], ordem[meio:]
    lista_A = deriva(vocab_de(metA))
    fp = [(p.id, marca(p.body, lista_A)) for p in metB]
    fp = [(i, m) for i, m in fp if m]
    r1 = {"n_variantes_derivadas_de_A": len(lista_A),
          "n_poemas_em_B": len(metB),
          "poemas_de_B_marcados": len(fp),
          "fraccao": round(len(fp) / len(metB), 5),
          "limiar": LIMIAR_FALSOS_POSITIVOS,
          "exemplos": [{"poema": i, "formas": m} for i, m in fp[:12]],
          "dispara": len(fp) / len(metB) < LIMIAR_FALSOS_POSITIVOS}

    # ---------------- a lista final, do corpus pt inteiro --------------- #
    vocab = vocab_de(poemas)
    lista = deriva(vocab)
    por_classe = collections.Counter(d["classe"] for d in lista.values())

    # ---------------- B2: recall nos 48 itens gerados da 5Q ------------- #
    cru5q = {c["id"]: c for c in
             json.load(open(os.path.join(RAIZ, "docs/fase-5q/01-chave.json"),
                            encoding="utf-8"))["chave"]}
    juizos = json.load(open(os.path.join(RAIZ, "docs/fase-5q/02-juizos.json"),
                            encoding="utf-8"))["juizos"]
    # os itens cuja razao cita defeito ORTOGRAFICO (classes A/B/C), §4 R2
    _ORTO = re.compile(r"grafia brasileir|sem acento|acento errado|brasileir",
                       re.I)
    gerados = [(sid, c) for sid, c in cru5q.items() if c["grupo"] != "R"]
    alvo = [sid for sid, _ in gerados if _ORTO.search(juizos[sid]["razao"])]
    apanhados_alvo = [sid for sid in alvo
                      if marca(cru5q[sid]["texto"], lista)]
    apanhados_todos = [sid for sid, c in gerados if marca(c["texto"], lista)]
    reais_marcados = [sid for sid, c in cru5q.items()
                      if c["grupo"] == "R" and marca(c["texto"], lista)]
    r2 = {"n_gerados": len(gerados),
          "n_alvo_ortografico": len(alvo),
          "apanhados_do_alvo": len(apanhados_alvo),
          "recall_no_alvo": (round(len(apanhados_alvo) / len(alvo), 4)
                             if alvo else None),
          "limiar": LIMIAR_RECALL,
          "apanhados_de_todos_os_gerados": len(apanhados_todos),
          "reais_da_5Q_marcados": len(reais_marcados),
          "detalhe": [{"id": sid, "voz": cru5q[sid]["voz"],
                       "modelo": cru5q[sid]["modelo"],
                       "formas": marca(cru5q[sid]["texto"], lista)}
                      for sid in apanhados_todos],
          "dispara": bool(alvo) and len(apanhados_alvo) / len(alvo) >= LIMIAR_RECALL}

    r4 = {"dispara": not r2["dispara"] and len(lista) < 50,
          "leitura": "a via mecanica nao da; declarar a limitacao e nao cair "
                     "na lista a mao"}

    out = {"_meta": {"protocolo": "docs/FASE-5R.md §2-4", "semente": SEMENTE,
                     "regra": f"freq(c)>={MIN_CANON_ABSOLUTO} e freq(v)==0, ou "
                              f"freq(c)>={MIN_CANON_TOLERANTE} e "
                              f"freq(v)<={MAX_VARIANTE_TOLERADA}",
                     "so_pt": True, "n_poemas_pt": len(poemas),
                     "n_formas_no_vocabulario": len(vocab)},
           "lista_final": {"n": len(lista), "por_classe": dict(por_classe)},
           "R1": r1, "R2": r2, "R4": r4}
    with open(os.path.join(AQUI, "01-derivacao.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print(f"\nlista final (corpus pt inteiro): {len(lista)} variantes  "
          f"{dict(por_classe)}")
    print("\n=== R1 — falsos positivos em dados retidos ===")
    print(f"  derivado da metade A ({len(lista_A)} variantes), corrido na "
          f"metade B ({len(metB)} poemas)")
    print(f"  poemas de B marcados: {len(fp)} = {r1['fraccao']:.3%}  "
          f"(limiar {LIMIAR_FALSOS_POSITIVOS:.0%})")
    for e in r1["exemplos"][:8]:
        print(f"    {e['poema']:12s} {e['formas']}")
    print(f"  R1 {'DISPARA' if r1['dispara'] else 'nao dispara'}")

    print("\n=== R2 — recall nos 48 itens gerados da 5Q ===")
    print(f"  alvo (razão cita defeito ortográfico): {len(alvo)} itens")
    print(f"  apanhados do alvo: {len(apanhados_alvo)} "
          f"({r2['recall_no_alvo']:.0%} se houver alvo)")
    print(f"  apanhados de todos os 48 gerados: {len(apanhados_todos)}")
    print(f"  poemas REAIS da 5Q marcados: {len(reais_marcados)} de 24")
    for d in r2["detalhe"][:10]:
        print(f"    {d['id']}  {d['voz']:9s} {d['modelo']:12s} {d['formas']}")
    print(f"  R2 {'DISPARA' if r2['dispara'] else 'nao dispara'}")

    if r1["dispara"] and r2["dispara"]:
        destino = os.path.join(RAIZ, "data", "ortografia-corpus.json")
        with open(destino, "w", encoding="utf-8") as f:
            json.dump({"_meta": {
                "porque_existe": "variantes ortograficas que o corpus NAO usa, "
                                 "derivadas dele por transformacao mecanica. "
                                 "Ver docs/FASE-5R.md §2.",
                "nao_sao_brasileirismos": "`objeto` e `eletrico` sao grafia "
                                          "europeia correcta desde 1990; o "
                                          "corpus e Pessoa pre-1990. Isto mede "
                                          "distancia a ortografia DO CORPUS.",
                "regra": out["_meta"]["regra"],
                "falsos_positivos_retidos": r1["fraccao"],
                "n": len(lista)},
                "variantes": {v: d["canonica"] for v, d in sorted(lista.items())}},
                f, ensure_ascii=False, indent=1)
        print(f"\n-> {destino}  ({len(lista)} variantes)")
    else:
        print("\nportões não passam: nada escrito em data/")
    print(f"-> {os.path.join(AQUI, '01-derivacao.json')}")


if __name__ == "__main__":
    main()
