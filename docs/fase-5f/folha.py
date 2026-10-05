#!/usr/bin/env python
"""Fase 5F / Passo B1–B2 — a folha dos 64 itens, com os 24 retidos.

Protocolo em [`../FASE-5F.md`](../FASE-5F.md), commitado **antes** de este
ficheiro produzir folha nenhuma.

O grupo **R** são os **24** poemas de Caeiro que nenhuma folha anterior usou e
que eu nunca li. São eles que carregam os portões; os 39 que eu li servem só
para escrever a âncora, e nenhum número sobre eles entra no relatório — é a
lição da Fase 5C, que viu a AUC do FAS cair de 0,869 in-sample para 0,544
retida.
"""
from __future__ import annotations

import json
import os
import random
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(AQUI, "..", "..")))

from src.corpus.build import load

SEMENTE = 11
N_CONTRASTE = 20
VERSOS_MIN, VERSOS_MAX = 6, 25
ROMANO = re.compile(r"^\s*[IVXLC]{1,7}\s*$")

#: A âncora **recalibrada**, verbatim do §2 do protocolo. É o único conteúdo
#: normativo, e vai igual para as duas folhas.
ANCORA = """## A escala

Cada poema leva **0**, **1** ou **2**:

| 2 | 1 | 0 |
|---|---|---|
| o poema **acaba na coisa**: ou fica no visível de ponta a ponta, ou argumenta e o argumento **fecha a porta** — conclui que a coisa é só o que é | o poema fecha a porta mas deixa **uma** aberta: fica de pé uma afirmação de profundidade, de alma, de destino, ou uma lição que manda buscar além | o poema **acaba além da coisa**: mistério, alma, destino, verdade oculta, moral que manda buscar, ou a natureza a sentir pelo poeta |

## Os casos difíceis, já decididos

1. **Filosofar não é falta.** Um poema inteiramente argumentativo pode levar 2
   se o argumento terminar na coisa. «Vi que não há Natureza… A Natureza é
   partes sem um todo» é um **2**.
2. **A tautologia deflacionária é a assinatura, não um defeito.** «As coisas são
   só o que são», «a borboleta é apenas borboleta» contam **para** o 2.
3. **Atribuição negada não conta como atribuição.** «Não lhes atribuo
   significado oculto» não abre porta nenhuma.
4. **Atribuição posta e depois retirada conta como fechada.** «Se às vezes digo
   que as flores sorriem… não é porque eu julgue que há sorrisos nas flores» é
   retracção, e o poema é candidato a 2.
5. **Personificação posta e mantida abre a porta.** «A montanha sorri», «o
   riacho esquece a fonte» levam 0, salvo retracção pela regra 4.
6. **Moral: a direcção decide.** Mandar **aceitar o que é** fecha a porta («e eu
   aceito, e nem agradeço» conta para 2); mandar **buscar além** abre-a
   («ensina-me a sonhar» é 0).

Pontuar por esta escala e não por impressão geral. Não há distribuição-alvo e
não há resposta certa.

---

"""

CAB_R1 = """# Fase 5F / Passo C1 — folha de pontuação, às cegas

Pontuar com a âncora **recalibrada** do §2 do [protocolo](../FASE-5F.md).
Registar uma razão curta por item. **Não abrir `01-chave.json`.**

"""

CAB_R2 = """# Folha de pontuação

{n} poemas em português, cada um escrito na voz de Alberto Caeiro, heterónimo de
Fernando Pessoa — ou a tentar essa voz.

"""


def versos_limpos(texto: str) -> list[str]:
    return [l for l in texto.splitlines() if l.strip() and not ROMANO.match(l)]


def main() -> None:
    destino_r2 = sys.argv[1] if len(sys.argv) > 1 else None
    meta, chunks = load()
    poemas: dict[str, object] = {}
    for c in chunks:
        poemas.setdefault(c.poem_id, c)
    voz = lambda p: getattr(p.voice, "value", str(p.voice))
    lng = lambda p: getattr(p.language, "value", str(p.language))

    c5b = json.load(open(os.path.join(AQUI, "..", "fase-5b",
                                      "01-chave.json")))["chave"]
    contaminados: set[str] = set()
    for d in c5b:
        contaminados.update(d["recuperados"])
    usados: set[str] = set()
    for fase in ("fase-5d", "fase-5e"):
        usados |= {d["origem"] for d in json.load(
            open(os.path.join(AQUI, "..", fase, "01-chave.json")))["chave"]}

    def elegivel(p) -> bool:
        return VERSOS_MIN <= len(versos_limpos(p.text)) <= VERSOS_MAX

    retidos = sorted((p for p in poemas.values()
                      if voz(p) == "caeiro" and elegivel(p)
                      and p.poem_id not in contaminados
                      and p.poem_id not in usados), key=lambda p: p.poem_id)
    orto = sorted((p for p in poemas.values()
                   if voz(p) == "ortonimo" and lng(p) == "pt" and elegivel(p)
                   and p.poem_id not in usados), key=lambda p: p.poem_id)
    ger = [d for d in c5b if d["id"] not in usados]
    print(f"retidos de Caeiro: {len(retidos)} · ortónimo frescos: {len(orto)} "
          f"· geradas por usar: {len(ger)}")
    assert len(retidos) == 24, f"esperava 24 retidos, tenho {len(retidos)}"
    assert len(ger) == N_CONTRASTE, f"esperava 20 geradas, tenho {len(ger)}"

    rng = random.Random(SEMENTE)
    itens = (
        [{"grupo": "R", "origem": p.poem_id,
          "texto": "\n".join(versos_limpos(p.text))} for p in retidos]
        + [{"grupo": "O", "origem": p.poem_id,
            "texto": "\n".join(versos_limpos(p.text))}
           for p in rng.sample(orto, N_CONTRASTE)]
        + [{"grupo": "G", "origem": d["id"],
            "texto": "\n".join(versos_limpos(d["texto"])),
            "braco_5b": d["braco"], "pergunta_5b": d["pergunta_id"]}
           for d in ger])

    ordem = list(range(len(itens)))
    for tentativa in range(1, 100001):
        rng.shuffle(ordem)
        if all(not (itens[ordem[j]]["grupo"] == itens[ordem[j + 1]]["grupo"]
                    == itens[ordem[j + 2]]["grupo"])
               for j in range(len(ordem) - 2)):
            break
    else:
        raise AssertionError("não consegui embaralhar com a restrição do §4")
    print(f"embaralhado em {tentativa} tentativa(s)")

    ids = [f"X{n:02d}" for n in range(1, len(ordem) + 1)]
    with open(os.path.join(AQUI, "01-chave.json"), "w") as f:
        json.dump({"_meta": {
            "aviso": "NÃO ABRIR antes de 02-pontuacoes.json e "
                     "02-pontuacoes-r2.json estarem commitados.",
            "protocolo": "docs/FASE-5F.md §4",
            "grupo_R": "os 24 retidos — nunca usados em folha anterior",
        }, "chave": [dict(id=s, **itens[j]) for s, j in zip(ids, ordem)]},
            f, ensure_ascii=False, indent=1)

    def corpo(cab: str) -> str:
        out = [cab, ANCORA]
        for sid, j in zip(ids, ordem):
            out += [f"## {sid}", "", "```", itens[j]["texto"], "```", "",
                    "3a=_", "", "---", ""]
        return "\n".join(out)

    with open(os.path.join(AQUI, "01-itens.md"), "w") as f:
        f.write(corpo(CAB_R1))

    if destino_r2:
        with open(destino_r2, "w") as f:
            f.write(corpo(CAB_R2.format(n=len(itens))))
        enq = CAB_R2.format(n=len(itens)) + ANCORA
        # Fronteira de palavra, nunca substring: a verificação por substring
        # reprovou na 5B por «braço» dentro de «abraço» e na 5D por «real»
        # dentro de «realidade». «recalibrada» e «antiga» entram porque esta
        # folha não pode revelar que houve uma âncora anterior.
        for proibida in ("fase 5", "fase-5", "grupo", "grupos", "gerado",
                         "gerados", "gerada", "geradas", "autêntico",
                         "autêntica", "real", "reais", "hipótese", "portão",
                         "protocolo", "braço", "braços", "âncora", "rubrica",
                         "recalibrada", "antiga", "nova", "retido", "retidos"):
            assert not re.search(rf"(?<!\w){re.escape(proibida)}(?!\w)",
                                 enq, re.IGNORECASE), \
                f"o enquadramento de R2 contém «{proibida}»"
        print(f"folha de R2 em {destino_r2} — enquadramento verificado")

    n = {g: sum(1 for i in itens if i["grupo"] == g) for g in "ROG"}
    print(f"{len(itens)} itens: R={n['R']} O={n['O']} G={n['G']}. A chave está fechada.")


if __name__ == "__main__":
    main()
