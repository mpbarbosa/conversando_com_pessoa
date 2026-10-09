#!/usr/bin/env python
"""Fase 5X / emenda — porque o §1 do relatório estava errado, e o que o substitui.

**Esta análise é posterior ao relatório e contradiz-lhe duas afirmações.**
Corre sobre os dados já comprometidos da 5W e da 5X; não gera nada.

## O que eu afirmei

> «A mesma configuração, medida duas vezes, varia tanto como o efeito que eu
> queria ver»: densidade de rima **0,00951** na 5W contra **0,00615** na 5X, e
> daí «o chão de ruído de uma célula de 20 amostras é um factor de 1,5».

## Porque é falso

**Não era a mesma configuração.** Entre as duas fases eu mudei o tokenizador do
orçamento — `contador()` (e5) na 5W, `contador(GERADOR)` (qwen) na 5X —, e o e5
subconta 17%. Consequência medida aqui: **18 das 20 células receberam prompts
diferentes**, com 4 chunks onde a 5X encaixou 3.

**E não há ruído de corrida nenhum.** Nas **2** células em que o prompt
coincidiu, o texto gerado é **idêntico byte a byte**. O modelo é determinista
dado prompt, semente e opções — logo o remédio que eu prescrevi («correr a
configuração de controlo duas vezes») devolveria resultados **idênticos** e não
mediria nada.

## O que se descobriu em vez disso, e é pior

**A repetição re-recupera.** Quando a guarda rejeita e o `responder` repete, o
contexto é trocado. Logo um braço que repetiu tem prompt diferente de um que não
repetiu — e **todas** as células com prompt divergente dentro de uma fase são
células em que os braços repetiram números diferentes de vezes: 3 de 20 na 5X,
2 de 20 na 5W, sem excepção.

Isto não é um confundidor a declarar: é um **mediador**. O tratamento pode causar
a repetição, que troca o contexto, que muda o desfecho.

Escreve `03-emenda.json`.
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
sys.path.insert(0, os.path.join(RAIZ, "docs", "fase-5v"))
sys.path.insert(0, os.path.join(RAIZ, "docs", "fase-5w"))

from densidade import densidade                              # noqa: E402

SEMENTE = 20261009


def ic(a: list[float], b: list[float]) -> list[float]:
    rng = random.Random(SEMENTE)
    ds = []
    for _ in range(4000):
        ma = st.mean(a[rng.randrange(len(a))] for _ in a)
        mb = st.mean(b[rng.randrange(len(b))] for _ in b)
        ds.append(ma - mb)
    ds.sort()
    return [round(ds[100], 5), round(ds[3899], 5)]


def carregar(fase: str) -> dict:
    d = [json.loads(ln) for ln in
         open(os.path.join(RAIZ, f"docs/fase-{fase}/01-cru.jsonl"),
              encoding="utf-8") if ln.strip()]
    cel: dict = {}
    for r in d:
        cel.setdefault((r["pergunta_id"], r["repeticao"]), {})[r["braco"]] = r
    return cel


def main() -> None:
    w, x = carregar("5w"), carregar("5x")

    # ---- 1. nao era a mesma configuracao ------------------------------- #
    ks = sorted(set(w) & set(x))
    pares = [(k, w[k]["C"], x[k]["B"]) for k in ks]
    iguais = [k for k, a, b in pares if a["usados"] == b["usados"]]
    texto_igual = [k for k in iguais
                   if w[k]["C"]["texto_cru"] == x[k]["B"]["texto_cru"]]
    chunks = {f"{len(a['usados'])}->{len(b['usados'])}": 0 for _, a, b in pares}
    for _, a, b in pares:
        chunks[f"{len(a['usados'])}->{len(b['usados'])}"] += 1

    p1 = {"celulas": len(pares),
          "prompt_identico": len(iguais),
          "prompt_diferente": len(pares) - len(iguais),
          "texto_identico_quando_o_prompt_coincide":
              f"{len(texto_igual)}/{len(iguais)}",
          "chunks_5w_para_5x": chunks,
          "tokens_system_5w": sorted({w[k]["C"]["tokens_system"] for k in ks}),
          "tokens_system_5x": sorted({x[k]["B"]["tokens_system"] for k in ks}),
          "leitura": "mudei o tokenizador do orcamento entre as fases; 18/20 "
                     "prompts diferem. E o modelo e determinista: onde o prompt "
                     "coincidiu o texto e identico byte a byte"}

    # ---- 2. a repeticao re-recupera ------------------------------------ #
    p2 = {}
    for nome, cel in (("5W", w), ("5X", x)):
        div = []
        for k, v in cel.items():
            if len({tuple(v[b]["usados"]) for b in v}) > 1:
                div.append({"celula": list(k),
                            "tentativas": {b: v[b]["tentativas"] for b in v}})
        p2[nome] = {
            "celulas": len(cel),
            "prompt_divergente_entre_bracos": len(div),
            "todas_com_tentativas_desiguais": all(
                len({t for t in d["tentativas"].values()}) > 1 for d in div),
            "detalhe": div}

    # ---- 3. os portoes da 5X nas celulas limpas ------------------------ #
    limpas = [k for k, v in x.items()
              if len({tuple(v[b]["usados"]) for b in v}) == 1]
    p3 = {"celulas_limpas": len(limpas), "de": len(x)}
    for nome, conj in (("todas_20", sorted(x)), ("limpas_17", sorted(limpas))):
        den = {b: [d for d in (densidade(x[k][b]["texto_cru"]) for k in conj)
                   if d is not None] for b in "BPT"}
        bloco = {b: round(st.mean(v), 5) for b, v in den.items()}
        for b in "PT":
            bloco[f"{b}_menos_B"] = {
                "diferenca": round(st.mean(den[b]) - st.mean(den["B"]), 5),
                "razao": round(st.mean(den[b]) / st.mean(den["B"]), 2),
                "ic95": ic(den[b], den["B"])}
            bloco[f"{b}_menos_B"]["exclui_zero"] = (
                bloco[f"{b}_menos_B"]["ic95"][0] > 0
                or bloco[f"{b}_menos_B"]["ic95"][1] < 0)
        p3[nome] = bloco

    out = {"_meta": {
        "o_que_e": "emenda POSTERIOR ao FASE-5X-RELATORIO.md, que contradiz "
                   "duas afirmacoes suas",
        "afirmacao_1_retirada": "«a mesma configuracao medida duas vezes varia "
                                "1,54x» e «o chao de ruido de uma celula de 20 "
                                "amostras e um factor de 1,5»",
        "afirmacao_2_nao_robusta": "«a temperatura vai para o lado errado "
                                   "(-36%)»: nas celulas limpas inverte-se",
        "semente": SEMENTE},
        "1_nao_era_a_mesma_configuracao": p1,
        "2_a_repeticao_re_recupera": p2,
        "3_portoes_nas_celulas_limpas": p3}
    with open(os.path.join(AQUI, "03-emenda.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print("=== 1. não era a mesma configuração ===")
    print(f"  prompts diferentes: {p1['prompt_diferente']}/{p1['celulas']}")
    print(f"  chunks 5W->5X: {p1['chunks_5w_para_5x']}")
    print(f"  texto idêntico quando o prompt coincide: "
          f"{p1['texto_identico_quando_o_prompt_coincide']}  <- determinista")
    print("\n=== 2. a repetição re-recupera ===")
    for nome, b in p2.items():
        print(f"  {nome}: {b['prompt_divergente_entre_bracos']}/{b['celulas']} "
              f"células com prompt divergente; todas com tentativas "
              f"desiguais: {b['todas_com_tentativas_desiguais']}")
    print("\n=== 3. os portões nas células limpas ===")
    for nome in ("todas_20", "limpas_17"):
        b = p3[nome]
        print(f"  {nome}:  B={b['B']:.5f}  P={b['P']:.5f}  T={b['T']:.5f}")
        for arm in "PT":
            r = b[f"{arm}_menos_B"]
            print(f"     {arm}-B {r['diferenca']:+.5f}  {r['razao']}×  "
                  f"IC {r['ic95']}  "
                  f"{'EXCLUI ZERO' if r['exclui_zero'] else 'contém zero'}")
    print(f"\n-> {os.path.join(AQUI, '03-emenda.json')}")


if __name__ == "__main__":
    main()
