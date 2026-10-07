#!/usr/bin/env python
"""Fase 5N / A3 — a folha e a chave: 30 do braço T com 30 do braço Q da 5H.

Protocolo em [`../FASE-5N.md`](../FASE-5N.md) §2.3.

Três diferenças ao `fase-5h/folha.py`, todas deliberadas:

1. **Junta duas fases.** Os 30 itens do braço **T** (`qwen2.5:3b`, gerados aqui)
   com os 30 do braço **Q** (`qwen2.5:7b`) de `fase-5h/01-cru.jsonl`. Não se
   regera o Q.
2. **A âncora de 3b é a NOVA.** A [5L](../FASE-5L.md) retirou-lhe a cláusula de
   comprimento em 2026-10-06. A folha da 5H levava a antiga, com «10–20 versos»;
   pôr a antiga aqui seria pontuar com um instrumento retirado.
3. **O `n_versos` sai da folha.** A folha da 5H mostrava-o, e com a âncora nova
   ele não serve para nada **e** correlaciona com o braço — um modelo de 3,1B não
   escreve o mesmo comprimento que um de 7,6B. Mostrá-lo era dar uma pista do
   braço a troco de nada. O `truncada` fica, porque a âncora nova ainda o usa.
"""
from __future__ import annotations

import json
import os
import random

AQUI = os.path.dirname(os.path.abspath(__file__))
CRU_5H = os.path.join(AQUI, "..", "fase-5h", "01-cru.jsonl")

SEMENTE_CEGA = 17

ANCORAS = """## As escalas

**3a′ — poética da voz**

| 2 | 1 | 0 |
|---|---|---|
| o poema **acaba na coisa**: ou fica no visível de ponta a ponta, ou argumenta e o argumento **fecha a porta** — conclui que a coisa é só o que é | o poema fecha a porta mas deixa **uma** aberta: fica de pé uma afirmação de profundidade, de alma, de destino, ou uma lição que manda buscar além | o poema **acaba além da coisa**: mistério, alma, destino, verdade oculta, moral que manda buscar, ou a natureza a sentir pelo poeta |

As seis regras dos casos difíceis:

1. **Filosofar não é falta.** Um poema inteiramente argumentativo pode levar 2
   se o argumento terminar na coisa.
2. **A tautologia deflacionária é a assinatura, não um defeito.** «As coisas são
   só o que são», «a borboleta é apenas borboleta» contam **para** o 2.
3. **Atribuição negada não conta como atribuição.** «Não lhes atribuo
   significado oculto» não abre porta nenhuma.
4. **Atribuição posta e depois retirada conta como fechada.**
5. **Personificação posta e mantida abre a porta.** «A montanha sorri», «o
   riacho esquece a fonte» levam 0, salvo retracção pela regra 4.
6. **Moral: a direcção decide.** Mandar **aceitar o que é** fecha a porta;
   mandar **buscar além** abre-a.

**3b — forma da voz** *(âncora NOVA, da [Fase 5L](../FASE-5L.md): sem contagem
de versos)*

| 2 | 1 | 0 |
|---|---|---|
| verso livre, linhas curtas, sem rima, pouca imagem | livre mas com imagem decorativa | rimado, ou prosa com enters, ou ornamentado |

Um poema **truncado** — cortado a meio, sem fechar — leva **0 em 3b** e é
pontuado normalmente em 3a′. **Não há intervalo de comprimento**: um poema de
quatro versos e um de quarenta podem levar os dois 2, se a forma for a da voz.

Pontuar pelas escalas acima e não por impressão geral. Não há distribuição-alvo
e não há resposta certa.

---

"""

CAB = """# Fase 5N / Passo B1 — folha de julgamento, às cegas

Pontuar **3a′** (poética) e **3b** (forma), 0–2, com as âncoras abaixo: a de 3a′
é a da [Fase 5F](../FASE-5F.md) §2, **inalterada**; a de 3b é a **nova**, da
[Fase 5L](../FASE-5L.md), sem contagem de versos.

A ordem é embaralhada e duas amostras da mesma pergunta não são adjacentes.
**Não abrir `01-chave.json`.**

"""


def main() -> None:
    with open(os.path.join(AQUI, "01-cru.jsonl"), encoding="utf-8") as f:
        t = [json.loads(l) for l in f if l.strip()]
    assert len(t) == 30, f"braço T tem {len(t)} amostras, esperava 30"
    with open(CRU_5H, encoding="utf-8") as f:
        q = [json.loads(l) for l in f if l.strip() and
             json.loads(l)["braco"] == "Q"]
    assert len(q) == 30, f"braço Q tem {len(q)} amostras, esperava 30"

    cru = t + q
    # ordem fixa antes de embaralhar, para a corrida ser reproduzível
    cru.sort(key=lambda d: (d["braco"], d["pergunta_id"], d["repeticao"]))

    rng = random.Random(SEMENTE_CEGA)
    ordem = list(range(len(cru)))
    for tentativa in range(1, 100001):
        rng.shuffle(ordem)
        if all(cru[ordem[j]]["pergunta_id"] != cru[ordem[j + 1]]["pergunta_id"]
               for j in range(len(ordem) - 1)):
            break
    else:
        raise AssertionError("não consegui embaralhar sem pares adjacentes")
    print(f"embaralhado em {tentativa} tentativa(s)")

    ids = [f"N{n:02d}" for n in range(1, len(ordem) + 1)]
    seguro = []
    for sid, j in zip(ids, ordem):
        d = cru[j]
        # Sem `braco`, sem `modelo` e sem `n_versos` — ver o docstring.
        seguro.append({"id": sid, "pergunta": d["pergunta"],
                       "texto": d["texto"], "truncada": d["truncada"]})
    assert not any(k in s for s in seguro
                   for k in ("braco", "modelo", "n_versos"))

    with open(os.path.join(AQUI, "01-amostras.json"), "w",
              encoding="utf-8") as f:
        json.dump({"_meta": {"protocolo": "docs/FASE-5N.md §2.3",
                             "aviso": "sem o braço, o modelo nem o n_versos, "
                                      "de propósito."},
                   "amostras": seguro}, f, ensure_ascii=False, indent=1)
    with open(os.path.join(AQUI, "01-chave.json"), "w", encoding="utf-8") as f:
        json.dump({"_meta": {"aviso": "NÃO ABRIR antes de as pontuações "
                                      "estarem commitadas.",
                             "protocolo": "docs/FASE-5N.md §2.3"},
                   "chave": [dict(id=s, **cru[j]) for s, j in zip(ids, ordem)]},
                  f, ensure_ascii=False, indent=1)

    out = [CAB, ANCORAS]
    for s in seguro:
        out += [f"## {s['id']}", "", f"> {s['pergunta']}", "",
                "```", s["texto"], "```", "", "3a=_ 3b=_", "", "---", ""]
    with open(os.path.join(AQUI, "01-itens.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"{len(seguro)} itens em 01-itens.md. A chave está fechada.")


if __name__ == "__main__":
    main()
