#!/usr/bin/env python
"""Fase 5W / A5 — o desfecho **contínuo**, e é ele que diz o tamanho.

**Posterior e declarado.** O §3 do protocolo pré-registou um desfecho
**binário** — «o poema rima» — e isso é a resolução errada, que é a lição da
[5D](../FASE-5D-RELATORIO.md) a repetir-se.

## Porque o binário subestima

Num poema de doze versos há 66 pares de versos. **Um** par que coincida por
acaso põe o binário em `True`. Logo o binário mistura «rima sistematicamente»
com «rimou uma vez sem querer», e foi isso que a [5V](../FASE-5V-RELATORIO.md)
mediu quando deu 0,7769 ao poeta e 0,2167 ao gerado.

O desfecho certo é a **densidade**: de todos os pares de versos do poema,
quantos partilham a chave de rima (excluindo os de palavra igual).

    densidade = pares que rimam / pares possíveis

É o mesmo instrumento, com a informação que o limiar deitava fora — e não
precisa de mais amostras para a ter.

Escreve `04-densidade.json`.
"""
from __future__ import annotations

import json
import os
import random
import statistics as st
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(RAIZ, "docs", "fase-5v"))

from analisar import _pares, chave_letra                     # noqa: E402
from src.corpus.models import Lang, Voice                    # noqa: E402
from src.corpus.parse import parse_corpus                     # noqa: E402

SEMENTE = 20261008
N_REAMOSTRAS = 4000
BRACOS = ("C", "R", "X")


def densidade(texto: str) -> float | None:
    """Fracção dos pares de versos que partilham a chave de rima."""
    ps = _pares(texto, chave_letra)
    n = len(ps)
    if n < 2:
        return None
    total = n * (n - 1) // 2
    rimam = sum(1 for i in range(n) for j in range(i + 1, n)
                if ps[i][0] == ps[j][0] and ps[i][1] != ps[j][1])
    return rimam / total


def ic(a: list[float], b: list[float]) -> list[float]:
    rng = random.Random(SEMENTE)
    ds = []
    for _ in range(N_REAMOSTRAS):
        ma = st.mean(a[rng.randrange(len(a))] for _ in a)
        mb = st.mean(b[rng.randrange(len(b))] for _ in b)
        ds.append(ma - mb)
    ds.sort()
    return [round(ds[int(0.025 * len(ds))], 5),
            round(ds[int(0.975 * len(ds)) - 1], 5)]


def main() -> None:
    poemas = [p for p in parse_corpus(os.path.join(RAIZ, "data/pessoa_poems"))
              if p.language is Lang.PT and p.voice is Voice.ORTONIMO]
    real = [x for x in map(densidade, [p.body for p in poemas])
            if x is not None]
    cru = [json.loads(l) for l in
           open(os.path.join(AQUI, "01-cru.jsonl"), encoding="utf-8")
           if l.strip()]
    arm = {b: [x for x in map(densidade, [d["texto_cru"] for d in cru
                                          if d["braco"] == b])
               if x is not None] for b in BRACOS}

    m_real = st.mean(real)
    out = {"_meta": {
        "analise": "POSTERIOR e declarada",
        "porque": "o §3 pre-registou um desfecho BINARIO, que e a resolucao "
                  "errada: num poema de 12 versos ha 66 pares e UM acerto por "
                  "acaso poe o binario em True",
        "desfecho": "pares que rimam / pares possiveis, chave-letra, pares de "
                    "palavra igual excluidos",
        "semente": SEMENTE},
        "real_ortonimo": {"n": len(real), "densidade": round(m_real, 5)},
        "por_braco": {b: {"n": len(v), "densidade": round(st.mean(v), 5),
                          "razao_ao_poeta": round(m_real / st.mean(v), 1)
                          if st.mean(v) else None,
                          "distancia_ao_poeta": round(abs(st.mean(v) - m_real),
                                                      5)}
                      for b, v in arm.items()},
        "contrastes": {
            "R_menos_C": {"dif": round(st.mean(arm["R"]) - st.mean(arm["C"]), 5),
                          "ic95": ic(arm["R"], arm["C"])},
            "X_menos_C": {"dif": round(st.mean(arm["X"]) - st.mean(arm["C"]), 5),
                          "ic95": ic(arm["X"], arm["C"])},
            "X_menos_R": {"dif": round(st.mean(arm["X"]) - st.mean(arm["R"]), 5),
                          "ic95": ic(arm["X"], arm["R"])}},
        "leitura": "o poeta rima cerca de 1 par em 10; os tres bracos cerca de "
                   "1 em 100. O fosso e de uma ordem de grandeza e NENHUM "
                   "braco o mexeu. O binario da 5V media presenca; isto mede "
                   "densidade, e e a densidade que separa sistematico de "
                   "acidental"}
    for k, v in out["contrastes"].items():
        v["exclui_zero"] = v["ic95"][0] > 0 or v["ic95"][1] < 0
    with open(os.path.join(AQUI, "04-densidade.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print(f"ortónimo REAL  densidade {m_real:.5f}   (n={len(real)})")
    for b in BRACOS:
        d = out["por_braco"][b]
        print(f"  braço {b}   {d['densidade']:.5f}   "
              f"{d['razao_ao_poeta']:>5.1f}× abaixo do poeta   (n={d['n']})")
    print()
    for k, v in out["contrastes"].items():
        print(f"  {k:12s} {v['dif']:+.5f}  IC95 {v['ic95']}  "
              f"{'EXCLUI ZERO' if v['exclui_zero'] else 'contém zero'}")
    print(f"\n{out['leitura']}")
    print(f"\n-> {os.path.join(AQUI, '04-densidade.json')}")


if __name__ == "__main__":
    main()
