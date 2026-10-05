#!/usr/bin/env python
"""Fase 5E / Passo B1–B2 — a folha dos 60 itens frescos, às cegas.

Protocolo em [`../FASE-5E.md`](../FASE-5E.md), commitado **antes** de este
ficheiro produzir folha nenhuma.

Itens **novos**: nenhum dos 60 da Fase 5D entra aqui. A razão está no §3 do
protocolo — eu abri a chave da 5D, logo estou desinibido para aqueles itens e
não posso ser avaliador deles.

## Duas coisas que esta folha faz e a da 5D não fazia

1. **Remove as linhas de numeral romano** («XXXV», «VII»). Nos poemas reais
   aparecem e nas amostras geradas nunca, logo são uma pista de que o item é
   autêntico — fuga de cegueira. A remoção está declarada no §6 do protocolo,
   antes de a folha existir.
2. **Verifica o enquadramento de R2 por fronteira de palavra.** A verificação por
   substring reprovou duas vezes: na 5B por «braço» dentro de «abraço», na 5D
   por «real» dentro de «realidade».
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

SEMENTE = 7
N_POR_GRUPO = 20
VERSOS_MIN, VERSOS_MAX = 6, 25

#: Numeral romano sozinho numa linha. Os poemas de Caeiro do corpus trazem-nos.
ROMANO = re.compile(r"^\s*[IVXLC]{1,7}\s*$")

#: A âncora de 3a do Caeiro, **verbatim** da Fase 5 §5.1. É o único conteúdo
#: normativo, e vai igual para as duas folhas.
ANCORA = """## A escala

Cada poema leva **0**, **1** ou **2**:

| 2 | 1 | 0 |
|---|---|---|
| vê e não interpreta; nenhuma metafísica, símbolo, moral, nem natureza como espelho de sentimento | sensorial na maior parte, com **uma** volta simbólica ou moral | filosofa, interpreta, atribui significado oculto, personifica |

Pontuar por esta escala e não por impressão geral: a escala é a definição
operativa. Não há distribuição-alvo e não há resposta certa — se a maior parte
dos poemas merecer 0, dá 0 à maior parte; se merecer 2, dá 2.

---

"""

CAB_R1 = """# Fase 5E / Passo C1 — folha de pontuação, às cegas

Pontuar com a âncora de 3a da [Fase 5](../FASE-5.md) §5.1, reproduzida abaixo.
Registar uma razão curta por item. **Não abrir `01-chave.json`.**

"""

CAB_R2 = """# Folha de pontuação

{n} poemas em português, cada um escrito na voz de Alberto Caeiro, heterónimo de
Fernando Pessoa — ou a tentar essa voz.

"""


def versos_limpos(texto: str) -> list[str]:
    return [l for l in texto.splitlines()
            if l.strip() and not ROMANO.match(l)]


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
    usados_5d = {d["origem"] for d in json.load(
        open(os.path.join(AQUI, "..", "fase-5d", "01-chave.json")))["chave"]}

    def elegivel(p) -> bool:
        return VERSOS_MIN <= len(versos_limpos(p.text)) <= VERSOS_MAX

    cae = sorted((p for p in poemas.values()
                  if voz(p) == "caeiro" and elegivel(p)
                  and p.poem_id not in contaminados
                  and p.poem_id not in usados_5d), key=lambda p: p.poem_id)
    orto = sorted((p for p in poemas.values()
                   if voz(p) == "ortonimo" and lng(p) == "pt" and elegivel(p)
                   and p.poem_id not in usados_5d), key=lambda p: p.poem_id)
    ger = [d for d in c5b if d["id"] not in usados_5d]
    print(f"frescos: Caeiro {len(cae)} · ortónimo {len(orto)} · geradas {len(ger)}")
    assert len(cae) >= N_POR_GRUPO and len(ger) >= N_POR_GRUPO

    rng = random.Random(SEMENTE)
    itens = (
        [{"grupo": "R", "origem": p.poem_id,
          "texto": "\n".join(versos_limpos(p.text))}
         for p in rng.sample(cae, N_POR_GRUPO)]
        + [{"grupo": "O", "origem": p.poem_id,
            "texto": "\n".join(versos_limpos(p.text))}
           for p in rng.sample(orto, N_POR_GRUPO)]
        + [{"grupo": "G", "origem": d["id"],
            "texto": "\n".join(versos_limpos(d["texto"])),
            "braco_5b": d["braco"], "pergunta_5b": d["pergunta_id"]}
           for d in rng.sample(ger, N_POR_GRUPO)])

    for i in itens:
        assert not any(ROMANO.match(l) for l in i["texto"].splitlines()), i["origem"]

    ordem = list(range(len(itens)))
    for tentativa in range(1, 100001):
        rng.shuffle(ordem)
        if all(not (itens[ordem[j]]["grupo"] == itens[ordem[j + 1]]["grupo"]
                    == itens[ordem[j + 2]]["grupo"])
               for j in range(len(ordem) - 2)):
            break
    else:
        raise AssertionError("não consegui embaralhar com a restrição do §5.2")
    print(f"embaralhado em {tentativa} tentativa(s)")

    ids = [f"W{n:02d}" for n in range(1, len(ordem) + 1)]
    with open(os.path.join(AQUI, "01-chave.json"), "w") as f:
        json.dump({"_meta": {
            "aviso": "NÃO ABRIR antes de 02-pontuacoes.json e "
                     "02-pontuacoes-r2.json estarem commitados.",
            "protocolo": "docs/FASE-5E.md §5",
            "numerais_romanos": "removidos dos textos (§6 do protocolo)",
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
        enquadramento = CAB_R2.format(n=len(itens)) + ANCORA
        for proibida in ("fase 5", "fase-5", "grupo", "grupos", "gerado",
                         "gerados", "gerada", "geradas", "autêntico",
                         "autêntica", "real", "reais", "hipótese", "portão",
                         "protocolo", "braço", "braços", "âncora", "rubrica"):
            assert not re.search(rf"(?<!\w){re.escape(proibida)}(?!\w)",
                                 enquadramento, re.IGNORECASE), \
                f"o enquadramento de R2 contém «{proibida}»"
        print(f"folha de R2 em {destino_r2} — enquadramento verificado")

    n = {g: sum(1 for i in itens if i["grupo"] == g) for g in "ROG"}
    print(f"{len(itens)} itens: R={n['R']} O={n['O']} G={n['G']}. A chave está fechada.")


if __name__ == "__main__":
    main()
