#!/usr/bin/env python
"""Fase 5P — onde vive a discordância, e se a fronteira importa.

Protocolo: `../FASE-5P.md` §3. Não pontua nada: junta as pontuações que já
existem e corre os três portões.

Fontes:
  - os **24 poemas reais** com **três** leituras independentes: eu (5O),
    R1 e R2 (5F), todos com a âncora 3a′ da 5F §2 inalterada;
  - os itens **gerados** com a minha leitura: llama (5O) e qwen (5N).
"""
from __future__ import annotations

import collections
import json
import math
import os
import statistics as st

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))

#: §3 P3
TECTO_MAX = 0.85
#: §4.2 — abaixo disto o P1 e inconclusivo
PISO_NAO_UNANIMES = 5


def carrega_reais() -> dict[str, dict[str, int]]:
    """poem_id -> {avaliador: nota}, nos 24 reais retidos."""
    f5f = {c["id"]: c for c in
           json.load(open(os.path.join(RAIZ, "docs/fase-5f/01-chave.json"),
                          encoding="utf-8"))["chave"]}
    r1 = json.load(open(os.path.join(RAIZ, "docs/fase-5f/02-pontuacoes.json"),
                        encoding="utf-8"))["pontuacoes"]
    r2 = json.load(open(os.path.join(RAIZ,
                                     "docs/fase-5f/02-pontuacoes-r2.json"),
                        encoding="utf-8"))["pontuacoes"]
    out: dict[str, dict[str, int]] = {}
    for sid, c in f5f.items():
        if c["grupo"] != "R":
            continue
        d = {}
        if sid in r1 and "c3a" in r1[sid]:
            d["R1"] = r1[sid]["c3a"]
        if sid in r2 and "c3a" in r2[sid]:
            d["R2"] = r2[sid]["c3a"]
        out[c["origem"]] = d

    ch5o = {c["id"]: c for c in
            json.load(open(os.path.join(RAIZ, "docs/fase-5o/01-chave.json"),
                           encoding="utf-8"))["chave"]}
    p5o = json.load(open(os.path.join(RAIZ, "docs/fase-5o/02-pontuacoes.json"),
                         encoding="utf-8"))["pontuacoes"]
    for sid, s in p5o.items():
        c = ch5o[sid]
        if c["grupo"] == "R":
            out[c["origem"]]["R3"] = s["c3a"]
    return out


def carrega_gerados() -> dict[str, list[int]]:
    """braço -> notas minhas (um avaliador só)."""
    ch5o = {c["id"]: c for c in
            json.load(open(os.path.join(RAIZ, "docs/fase-5o/01-chave.json"),
                           encoding="utf-8"))["chave"]}
    p5o = json.load(open(os.path.join(RAIZ, "docs/fase-5o/02-pontuacoes.json"),
                         encoding="utf-8"))["pontuacoes"]
    llama = [s["c3a"] for sid, s in p5o.items() if ch5o[sid]["grupo"] == "L"]

    ch5n = {c["id"]: c for c in
            json.load(open(os.path.join(RAIZ, "docs/fase-5n/01-chave.json"),
                           encoding="utf-8"))["chave"]}
    p5n = json.load(open(os.path.join(RAIZ, "docs/fase-5n/03-pontuacoes.json"),
                         encoding="utf-8"))["pontuacoes"]
    qwen = [s["c3a"] for sid, s in p5n.items() if ch5n[sid]["braco"] == "Q"]
    qwen3b = [s["c3a"] for sid, s in p5n.items() if ch5n[sid]["braco"] == "T"]
    return {"llama3.1": llama, "qwen2.5_7b": qwen, "qwen2.5_3b": qwen3b}


def onde_discordam(reais, avaliadores) -> dict:
    """§3 P1 — entre os nao unanimes, a divisao e 1-vs-2 ou 0-vs-1?"""
    nao_unanimes, por_tipo = [], collections.Counter()
    for pid, d in sorted(reais.items()):
        notas = [d[a] for a in avaliadores if a in d]
        if len(notas) < len(avaliadores) or len(set(notas)) == 1:
            continue
        lo, hi = min(notas), max(notas)
        tipo = ("1-vs-2" if (lo, hi) == (1, 2)
                else "0-vs-1" if (lo, hi) == (0, 1)
                else "0-vs-2" if (lo, hi) == (0, 2)
                else f"{lo}-vs-{hi}")
        por_tipo[tipo] += 1
        nao_unanimes.append({"poema": pid, "notas": {a: d[a] for a in
                                                     avaliadores if a in d},
                             "tipo": tipo})
    n = len(nao_unanimes)
    n12 = por_tipo["1-vs-2"]
    n01 = por_tipo["0-vs-1"]
    return {"avaliadores": list(avaliadores), "n_itens": len(reais),
            "n_nao_unanimes": n, "por_tipo": dict(por_tipo),
            "itens": nao_unanimes,
            "maioria_em_1_vs_2": n > 0 and n12 > n01,
            "inconclusivo_por_poucos": n < PISO_NAO_UNANIMES}


def main() -> None:
    reais = carrega_reais()
    gerados = carrega_gerados()
    assert len(reais) == 24, len(reais)

    # ---------------- P1 ------------------------------------------------ #
    p1_tres = onde_discordam(reais, ("R1", "R2", "R3"))
    p1_sem_r1 = onde_discordam(reais, ("R2", "R3"))
    p1 = {"com_os_tres": p1_tres, "sem_o_R1": p1_sem_r1,
          "dispara": p1_tres["maioria_em_1_vs_2"]
                     and not p1_tres["inconclusivo_por_poucos"],
          "efeito_de_nivel": (p1_tres["n_nao_unanimes"]
                              - p1_sem_r1["n_nao_unanimes"])}

    # ---------------- P2: subir todos os 1 a 2 -------------------------- #
    def sobe(xs):
        return [2 if x == 1 else x for x in xs]

    r3 = [reais[p]["R3"] for p in sorted(reais)]
    r3_s = sobe(r3)
    ll, ll_s = gerados["llama3.1"], sobe(gerados["llama3.1"])
    qw, qw_s = gerados["qwen2.5_7b"], sobe(gerados["qwen2.5_7b"])
    tb, tb_s = gerados["qwen2.5_3b"], sobe(gerados["qwen2.5_3b"])

    def binom(k, d):
        if d == 0:
            return 1.0
        return min(1.0, 2 * sum(math.comb(d, i)
                                for i in range(0, min(k, d - k) + 1)) / 2 ** d)

    def emparelhado(a, b):
        """a - b, emparelhado pela ordem (ja alinhada a montante)."""
        difs = [x - y for x, y in zip(a, b)]
        disc = [x for x in difs if x != 0]
        k = sum(1 for x in disc if x > 0)
        return {"delta": round(st.mean(difs), 4), "d": len(disc),
                "k_favor_a": k, "p": round(binom(k, len(disc)), 5)}

    # Alinhar llama e qwen por (pergunta, repeticao), como a 5O fez.
    ch5o = {c["id"]: c for c in
            json.load(open(os.path.join(RAIZ, "docs/fase-5o/01-chave.json"),
                           encoding="utf-8"))["chave"]}
    p5o = json.load(open(os.path.join(RAIZ, "docs/fase-5o/02-pontuacoes.json"),
                         encoding="utf-8"))["pontuacoes"]
    Lmap = {ch5o[s]["origem"]: v["c3a"] for s, v in p5o.items()
            if ch5o[s]["grupo"] == "L"}
    ch5n = {c["id"]: c for c in
            json.load(open(os.path.join(RAIZ, "docs/fase-5n/01-chave.json"),
                           encoding="utf-8"))["chave"]}
    p5n = json.load(open(os.path.join(RAIZ, "docs/fase-5n/03-pontuacoes.json"),
                         encoding="utf-8"))["pontuacoes"]
    Qmap = {f'{ch5n[s]["pergunta_id"]}r{ch5n[s]["repeticao"]}': v["c3a"]
            for s, v in p5n.items() if ch5n[s]["braco"] == "Q"}
    Tmap = {f'{ch5n[s]["pergunta_id"]}r{ch5n[s]["repeticao"]}': v["c3a"]
            for s, v in p5n.items() if ch5n[s]["braco"] == "T"}
    com_LQ = sorted(set(Lmap) & set(Qmap))
    com_QT = sorted(set(Qmap) & set(Tmap))

    o1_antes = emparelhado([Lmap[k] for k in com_LQ], [Qmap[k] for k in com_LQ])
    o1_depois = emparelhado([2 if Lmap[k] == 1 else Lmap[k] for k in com_LQ],
                            [2 if Qmap[k] == 1 else Qmap[k] for k in com_LQ])
    n1_antes = emparelhado([Qmap[k] for k in com_QT], [Tmap[k] for k in com_QT])
    n1_depois = emparelhado([2 if Qmap[k] == 1 else Qmap[k] for k in com_QT],
                            [2 if Tmap[k] == 1 else Tmap[k] for k in com_QT])

    def x1(xs):
        return {"mediana": st.median(xs),
                "fraccao_com_2": round(sum(1 for x in xs if x == 2) / len(xs), 4),
                "passa": st.median(xs) >= 1
                         and sum(1 for x in xs if x == 2) / len(xs) >= 0.30}

    portoes = {
        "X1_da_5F_nos_reais": {"antes": x1(r3), "depois": x1(r3_s)},
        "O1_da_5O_llama_vs_qwen": {"antes": o1_antes, "depois": o1_depois},
        "O3_da_5O_nivel_nos_reais": {
            "antes": round(st.mean(r3), 4), "depois": round(st.mean(r3_s), 4),
            "faixa": [1.30, 1.90],
            "passa_antes": 1.30 <= st.mean(r3) <= 1.90,
            "passa_depois": 1.30 <= st.mean(r3_s) <= 1.90},
        "N1_da_5N_qwen_vs_3b": {"antes": n1_antes, "depois": n1_depois},
    }
    invertidos = []
    if portoes["X1_da_5F_nos_reais"]["antes"]["passa"] != \
       portoes["X1_da_5F_nos_reais"]["depois"]["passa"]:
        invertidos.append("X1")
    if (o1_antes["p"] <= 0.05) != (o1_depois["p"] <= 0.05):
        invertidos.append("O1")
    if portoes["O3_da_5O_nivel_nos_reais"]["passa_antes"] != \
       portoes["O3_da_5O_nivel_nos_reais"]["passa_depois"]:
        invertidos.append("O3")
    if (n1_antes["p"] <= 0.05) != (n1_depois["p"] <= 0.05):
        invertidos.append("N1")
    p2 = {"portoes": portoes, "invertidos": invertidos,
          "dispara": bool(invertidos)}

    # ---------------- P3: a saturacao depois de afrouxar ---------------- #
    def tecto(xs):
        return round(sum(1 for x in xs if x == 2) / len(xs), 4)

    p3 = {"antes": {"reais": tecto(r3), "llama": tecto(ll), "qwen7b": tecto(qw),
                    "qwen3b": tecto(tb)},
          "depois": {"reais": tecto(r3_s), "llama": tecto(ll_s),
                     "qwen7b": tecto(qw_s), "qwen3b": tecto(tb_s)},
          "limiar": TECTO_MAX}
    p3["dispara"] = (p3["depois"]["reais"] < TECTO_MAX
                     and p3["depois"]["llama"] < TECTO_MAX)

    # ---------------- a prescricao do §3.1 ------------------------------ #
    if not p1["dispara"]:
        presc = ("retirar o passo 28 e reapontar a fronteira 0/1 (passo 12)"
                 if not p1_tres["inconclusivo_por_poucos"]
                 else "retirar o passo 28: P1 inconclusivo por poucos itens "
                      "nao unanimes (§4.2)")
    elif not p2["dispara"]:
        presc = ("retirar o passo 28: fronteira mal definida mas "
                 "INCONSEQUENTE, e a quebra de compatibilidade nao se paga")
    elif not p3["dispara"]:
        presc = ("nao afrouxar: a fronteira importa E afrouxar mata o tecto. "
                 "O caminho e uma escala com MAIS niveis")
    else:
        presc = "abrir uma fase de recalibracao, com validacao retida"

    out = {"_meta": {"protocolo": "docs/FASE-5P.md §3",
                     "nao_pontua_nada_de_novo": True,
                     "fontes": "5O (eu), 5F (R1 e R2), 5N (eu)"},
           "P1": p1, "P2": p2, "P3": p3, "prescricao": presc}
    with open(os.path.join(AQUI, "02-resultados.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print("=== P1 — onde vive a discordância (24 poemas reais) ===")
    for rot, bloco in (("os três (R1,R2,R3)", p1_tres),
                       ("sem o R1 (R2,R3)", p1_sem_r1)):
        print(f"  {rot:22s} não unânimes: {bloco['n_nao_unanimes']:2d}/24  "
              f"{bloco['por_tipo']}")
    print("  itens não unânimes com os três:")
    for it in p1_tres["itens"]:
        print(f"    {it['poema']:12s} {it['notas']}  {it['tipo']}")
    print(f"  efeito de nível (itens que o R1 sozinho torna discordantes): "
          f"{p1['efeito_de_nivel']}")
    print(f"  P1 {'DISPARA' if p1['dispara'] else 'nao dispara'}"
          + ("  (inconclusivo: menos de 5 não unânimes)"
             if p1_tres["inconclusivo_por_poucos"] else ""))

    print("\n=== P2 — subir todos os 1 a 2 inverte algum portão? ===")
    x = portoes["X1_da_5F_nos_reais"]
    print(f"  X1 (reais): mediana {x['antes']['mediana']}->"
          f"{x['depois']['mediana']}, com 2 {x['antes']['fraccao_com_2']:.0%}->"
          f"{x['depois']['fraccao_com_2']:.0%}  passa "
          f"{x['antes']['passa']}->{x['depois']['passa']}")
    print(f"  O1 (llama-qwen): Δ {o1_antes['delta']:+.3f}->"
          f"{o1_depois['delta']:+.3f}  p {o1_antes['p']:.4f}->"
          f"{o1_depois['p']:.4f}  d {o1_antes['d']}->{o1_depois['d']}")
    o3 = portoes["O3_da_5O_nivel_nos_reais"]
    print(f"  O3 (nível): {o3['antes']:.3f}->{o3['depois']:.3f}  passa "
          f"{o3['passa_antes']}->{o3['passa_depois']}")
    print(f"  N1 (qwen-3b): Δ {n1_antes['delta']:+.3f}->"
          f"{n1_depois['delta']:+.3f}  p {n1_antes['p']:.4f}->"
          f"{n1_depois['p']:.4f}")
    print(f"  invertidos: {invertidos or 'NENHUM'}   "
          f"P2 {'DISPARA' if p2['dispara'] else 'nao dispara'}")

    print("\n=== P3 — a saturação depois de afrouxar ===")
    print(f"  {'grupo':10s} {'antes':>7s} {'depois':>8s}")
    for g in ("reais", "llama", "qwen7b", "qwen3b"):
        print(f"  {g:10s} {p3['antes'][g]:7.0%} {p3['depois'][g]:8.0%}")
    print(f"  P3 {'DISPARA' if p3['dispara'] else 'nao dispara'} "
          f"(limiar {TECTO_MAX:.0%})")

    print(f"\n=== PRESCRIÇÃO (§3.1, escrita antes de medir) ===\n  {presc}")
    print(f"\n-> {os.path.join(AQUI, '02-resultados.json')}")


if __name__ == "__main__":
    main()
