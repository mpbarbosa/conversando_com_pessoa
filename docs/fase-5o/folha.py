#!/usr/bin/env python
"""Fase 5O / A1 — a folha e a chave: o braço L da 5H com os 24 reais da 5F.

Protocolo em [`../FASE-5O.md`](../FASE-5O.md) §2.1.

**Porque é que a folha mistura duas fases.** Eu já pontuei o braço **Q** da 5H
(na 5N, às cegas, commitado). Pontuar o **L** sozinho seria saber que é o braço
que a 5H diz ser melhor. Misturá-lo com itens que nunca li — os 24 poemas
**reais** de Caeiro do grupo R da 5F — devolve a cegueira, e de passagem dá a
régua de nível do passo 26.

Os poemas reais **não têm pergunta**; os gerados têm. Mostrar a pergunta só em
metade dos itens seria entregar o grupo. Logo **a folha não mostra pergunta
nenhuma** — e a âncora de 3a′ não precisa dela: julga se o poema acaba na coisa,
não se responde ao que foi perguntado (isso é o critério 4, que esta fase não
pontua).
"""
from __future__ import annotations

import json
import os
import random

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))

SEMENTE_CEGA = 23

ANCORA = """## A escala — 3a′, poética da voz

| 2 | 1 | 0 |
|---|---|---|
| o poema **acaba na coisa**: ou fica no visível de ponta a ponta, ou argumenta e o argumento **fecha a porta** — conclui que a coisa é só o que é | o poema fecha a porta mas deixa **uma** aberta: fica de pé uma afirmação de profundidade, de alma, de destino, ou uma lição que manda buscar além | o poema **acaba além da coisa**: mistério, alma, destino, verdade oculta, moral que manda buscar, ou a natureza a sentir pelo poeta |

As seis regras dos casos difíceis, da [Fase 5F](../FASE-5F.md) §2.1:

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

Regra de aplicação, da 5H: **1 é «fecha a porta mas deixa UMA aberta», logo duas
ou mais levam 0.**

Pontuar pela escala e não por impressão geral. Não há distribuição-alvo e não há
resposta certa.

---

"""

CAB = """# Fase 5O / Passo B1 — folha de julgamento, às cegas

Pontuar **3a′** (poética), 0–2, com a âncora abaixo — a da
[Fase 5F](../FASE-5F.md) §2, **inalterada**.

**Não há perguntas** nesta folha, de propósito: ver o docstring de `folha.py`.
**Não abrir `01-chave.json`.**

"""


def main() -> None:
    l5h = [json.loads(x) for x in
           open(os.path.join(RAIZ, "docs/fase-5h/01-cru.jsonl"),
                encoding="utf-8") if x.strip()]
    gerados = [{"grupo": "L", "origem": f'{d["pergunta_id"]}r{d["repeticao"]}',
                "texto": d["texto"]}
               for d in l5h if d["braco"] == "L"]
    assert len(gerados) == 30, len(gerados)

    f5f = json.load(open(os.path.join(RAIZ, "docs/fase-5f/01-chave.json"),
                         encoding="utf-8"))["chave"]
    reais = [{"grupo": "R", "origem": c["origem"], "texto": c["texto"],
              "id_5f": c["id"]}
             for c in f5f if c["grupo"] == "R"]
    assert len(reais) == 24, len(reais)

    itens = gerados + reais
    itens.sort(key=lambda d: (d["grupo"], d["origem"]))

    rng = random.Random(SEMENTE_CEGA)
    ordem = list(range(len(itens)))
    for tentativa in range(1, 100001):
        rng.shuffle(ordem)
        # Nenhum par adjacente do MESMO grupo mais de 3 vezes a seguir, para a
        # folha nao ter blocos obvios de um grupo so.
        seq = [itens[j]["grupo"] for j in ordem]
        if not any(len(set(seq[k:k + 4])) == 1 for k in range(len(seq) - 3)):
            break
    else:
        raise AssertionError("não consegui embaralhar sem blocos de 4")
    print(f"embaralhado em {tentativa} tentativa(s)")

    ids = [f"O{n:02d}" for n in range(1, len(ordem) + 1)]
    seguro = [{"id": s, "texto": itens[j]["texto"]}
              for s, j in zip(ids, ordem)]
    assert not any(k in s for s in seguro
                   for k in ("grupo", "origem", "id_5f"))

    with open(os.path.join(AQUI, "01-amostras.json"), "w",
              encoding="utf-8") as f:
        json.dump({"_meta": {"protocolo": "docs/FASE-5O.md §2.1",
                             "aviso": "sem o grupo nem a origem, de propósito."},
                   "amostras": seguro}, f, ensure_ascii=False, indent=1)
    with open(os.path.join(AQUI, "01-chave.json"), "w", encoding="utf-8") as f:
        json.dump({"_meta": {"aviso": "NÃO ABRIR antes de as pontuações "
                                      "estarem commitadas.",
                             "protocolo": "docs/FASE-5O.md §2.1"},
                   "chave": [dict(id=s, **itens[j])
                             for s, j in zip(ids, ordem)]},
                  f, ensure_ascii=False, indent=1)

    out = [CAB, ANCORA]
    for s in seguro:
        out += [f"## {s['id']}", "", "```", s["texto"], "```", "",
                "3a=_", "", "---", ""]
    with open(os.path.join(AQUI, "01-itens.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"{len(seguro)} itens em 01-itens.md. A chave está fechada.")


if __name__ == "__main__":
    main()
