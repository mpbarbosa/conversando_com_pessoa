#!/usr/bin/env python
"""Fase 5L — as duas verificações da nota, reprodutíveis.

Existe porque a 5I publicou um número calculado **na sessão, sem script**, e a
definição não ficou registada em sítio nenhum — defeito que custou duas adendas
(ver `FASE-5J.md` §2.1). Os dois quadros do `FASE-5L.md` saem daqui.

1. **§2.1** — cada intervalo do 3b aplicado ao poeta real e aos dois braços da
   5H: algum braço é premiado **acima** do poeta? (invertibilidade)
2. **§2.2** — as pontuações históricas de 3b cruzadas com o intervalo da sua
   voz: a cláusula era vinculativa? quantas notas mudariam ao retirá-la?

Escreve `01-verificacao.json`.
"""
from __future__ import annotations

import collections
import glob
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)

from src.plagio import _versos                            # noqa: E402

#: Os intervalos da âncora **original** (Fase 5 §5.2, antes de 2026-10-06).
#: Reis era «<=12», logo o piso é 1. É esta a versão que se está a avaliar.
INTERVALOS = {"caeiro": (10, 20), "campos": (15, 30),
              "reis": (1, 12), "ortonimo": (12, 20)}


def dentro(n: int, iv: tuple[int, int]) -> bool:
    return iv[0] <= n <= iv[1]


def conformidade(xs, iv) -> float:
    return sum(1 for x in xs if dentro(x, iv)) / len(xs)


def invertibilidade() -> dict:
    """§2.1 — cada intervalo premeia algum braço acima do poeta?"""
    cont = json.load(open(os.path.join(RAIZ, "docs/fase-5j/01-contagem.json"),
                          encoding="utf-8"))
    reais = {v: [p["versos_min3"] for p in cont["por_poema"][v]
                 if p["elegivel"] and p["lingua"] == "pt"]
             for v in INTERVALOS}
    cru = [json.loads(l) for l in
           open(os.path.join(RAIZ, "docs/fase-5h/01-cru.jsonl"))]
    bracos = {"llama3.1": [r["n_versos"] for r in cru if r["braco"] == "L"],
              "qwen2.5": [r["n_versos"] for r in cru if r["braco"] == "Q"]}

    out = {}
    for voz, iv in INTERVALOS.items():
        c_real = conformidade(reais[voz], iv)
        cs = {k: conformidade(v, iv) for k, v in bracos.items()}
        acima = [k for k, c in cs.items() if c > c_real]
        out[voz] = {
            "intervalo": list(iv), "n_real": len(reais[voz]),
            "conformidade_real": round(c_real, 4),
            "conformidade_bracos": {k: round(c, 4) for k, c in cs.items()},
            "bracos_acima_do_poeta": acima,
            "invertivel": bool(acima),
        }
    out["_todos_invertiveis"] = all(
        out[v]["invertivel"] for v in INTERVALOS)
    return out


def compatibilidade() -> dict:
    """§2.2 — a cláusula era vinculativa? quantas notas mudariam?"""
    tab = collections.Counter()
    porfase: dict = {}
    for ch in sorted(glob.glob(os.path.join(RAIZ, "docs/fase-5*/01-chave.json"))):
        base = os.path.dirname(ch)
        pf = os.path.join(base, "02-pontuacoes.json")
        if not os.path.exists(pf):
            continue
        chave = json.load(open(ch, encoding="utf-8")).get("chave")
        if not isinstance(chave, list):
            continue
        pon = json.load(open(pf, encoding="utf-8"))["pontuacoes"]
        loc = collections.Counter()
        for it in chave:
            s = pon.get(it["id"])
            if not s or "c3b" not in s or "texto" not in it:
                continue
            iv = INTERVALOS.get(it.get("voz", "caeiro"), (10, 20))
            d = dentro(len(_versos(it["texto"])), iv)
            loc[(d, s["c3b"])] += 1
            tab[(d, s["c3b"])] += 1
        if loc:
            porfase[os.path.basename(base)] = {
                f"{'dentro' if d else 'fora'}_3b{c}": n
                for (d, c), n in sorted(loc.items())}

    fora = {c: tab[(False, c)] for c in (0, 1, 2)}
    dentro_ = {c: tab[(True, c)] for c in (0, 1, 2)}
    n_fora = sum(fora.values())
    n_tot = n_fora + sum(dentro_.values())
    return {
        "por_fase": porfase,
        "fora_do_intervalo": fora, "dentro_do_intervalo": dentro_,
        "n_total": n_tot, "n_fora": n_fora,
        "fora_com_tecto_em_1_ou_menos": fora[0] + fora[1],
        "fora_que_ainda_levaram_2": fora[2],
        "clausula_vinculativa":
            f"{fora[0] + fora[1]} de {n_fora} itens fora do intervalo "
            f"ficaram em <=1",
        "limite_superior_de_notas_que_mudariam": fora[1],
        "fraccao_que_poderia_mudar": round(fora[1] / n_tot, 4) if n_tot else None,
        "nota": "limite SUPERIOR: um item podia estar em 1 por razao "
                "qualitativa tambem, e isso so se sabe repontuando",
    }


def main() -> None:
    out = {"_meta": {
        "porque_existe": "a 5I publicou um numero calculado ad hoc e sem "
                         "script; ver FASE-5J.md §2.1",
        "nota": "docs/FASE-5L.md §2",
        "intervalos_avaliados": "a ancora ORIGINAL, Fase 5 §5.2 ate 2026-10-06",
        "definicao_verso": "plagio._versos (MIN_PALAVRAS=3)"},
        "invertibilidade": invertibilidade(),
        "compatibilidade": compatibilidade()}

    caminho = os.path.join(AQUI, "01-verificacao.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    inv = out["invertibilidade"]
    print("=== §2.1 — os intervalos são invertíveis? ===")
    print(f"{'intervalo de':12s} {'real':>6s} {'llama':>7s} {'qwen':>7s}   "
          f"inverte?")
    for voz in INTERVALOS:
        c = inv[voz]
        print(f"{voz:12s} {c['conformidade_real']:6.0%} "
              f"{c['conformidade_bracos']['llama3.1']:7.0%} "
              f"{c['conformidade_bracos']['qwen2.5']:7.0%}   "
              f"{('SIM: ' + ','.join(c['bracos_acima_do_poeta']))
                 if c['invertivel'] else 'nao'}")
    print(f"-> todos invertíveis: {inv['_todos_invertiveis']}")

    com = out["compatibilidade"]
    print("\n=== §2.2 — a cláusula era vinculativa? ===")
    print(f"{'':22s} 3b=0  3b=1  3b=2")
    print(f"{'fora do intervalo':22s} "
          + "  ".join(f"{com['fora_do_intervalo'][c]:4d}" for c in (0, 1, 2)))
    print(f"{'dentro do intervalo':22s} "
          + "  ".join(f"{com['dentro_do_intervalo'][c]:4d}" for c in (0, 1, 2)))
    print(f"-> {com['clausula_vinculativa']}")
    print(f"-> até {com['limite_superior_de_notas_que_mudariam']} de "
          f"{com['n_total']} notas mudariam "
          f"({com['fraccao_que_poderia_mudar']:.0%}), limite superior")
    print(f"\n-> {caminho}")


if __name__ == "__main__":
    main()
