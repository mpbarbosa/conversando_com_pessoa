#!/usr/bin/env python
"""Fase 5D / Passo B1–B2 — a folha dos 60 itens, às cegas.

Protocolo em [`../FASE-5D.md`](../FASE-5D.md), commitado **antes** de este
ficheiro produzir folha nenhuma.

Três grupos, uma escala, uma folha:

- **R** 20 poemas reais de Caeiro, dos que **nunca** foram recuperados para as
  perguntas da Fase 5B (a exclusão é a mesma da 5C, pela mesma razão);
- **O** 20 poemas reais do ortónimo em português;
- **G** 20 amostras geradas da Fase 5B, 10 de cada braço.

Todos com 6–25 versos, que é o intervalo das 60 amostras geradas: o FVV é uma
fracção, mas um texto longo tem mais oportunidades de volta, e deixar os grupos
divergirem em comprimento meteria um confundidor onde o V5 procura outro.

## Porque é que os versos vão numerados

O §2.2 do protocolo exige que cada contador registre **os índices dos versos** a
que atribuiu volta. Sem numeração na folha, os índices não são comparáveis entre
contadores, e é a numeração que torna a contagem auditável contra o texto.
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

#: §3 do protocolo.
SEMENTE = 3
N_POR_GRUPO = 20
VERSOS_MIN, VERSOS_MAX = 6, 25

CABECALHO_R1 = """# Fase 5D / Passo C1 — folha de contagem, às cegas

Contar, por poema, **a fracção de versos com volta**, pelas definições do
[`../FASE-5D.md`](../FASE-5D.md) §2.1 — commitadas antes de existir esta folha.

Registar, por item, **os índices dos versos** com volta e o tipo (A–D).
**Não abrir `01-chave.json`.**

"""

CABECALHO_R2 = """# Folha de contagem

{n} poemas em português, numerados verso a verso.

Por cada poema, identificar **quais os versos que atribuem sentido**, segundo as
quatro definições abaixo, e registar os índices desses versos.

"""

#: As quatro definições, verbatim do §2.1 do protocolo. É o único conteúdo
#: normativo que R2 recebe, e vai igual para as duas folhas.
DEFINICOES = """## Um verso tem **volta** se fizer pelo menos uma destas quatro coisas

| | tipo | o verso… |
|---|---|---|
| **A** | significado oculto | diz ou sugere que a coisa significa algo além de si: «sentido em cada pedra», «nas entrelinhas», «segredos dos montes» |
| **B** | metafísica ou símbolo | afirma sobre o ser, a verdade, a essência, o mistério, o nada, o destino: «a realidade segue as suas leis», «o não-ser» |
| **C** | moral | prescreve, aconselha, tira lição: «e assim deve ser», «ensina-me a sonhar» |
| **D** | personificação ou espelho | atribui a uma coisa acto mental, vontade ou sentimento, ou usa a natureza como espelho de sentimento: «a montanha sorri», «o riacho esquece a fonte», «praia desolada» |

## As quatro regras de contagem

1. A unidade é o **verso**. Um verso com três voltas conta **uma vez**.
2. Uma volta **negada não conta**: «não lhes atribuo sentido», «não busco na
   natureza uma moral oculta». Negar a atribuição não é atribuir.
3. Uma volta que a **frase inicial** já traga conta igual. O verso é do poema.
4. Verbos convencionais de som — «o vento sussurra», «a onda murmura» — contam
   como **D** só se atribuírem **intenção, destinatário ou sentimento**:
   «sussurra segredos» conta, «sussurra entre as folhas» não.

---

"""


def versos(texto: str) -> list[str]:
    return [l for l in texto.splitlines() if l.strip()]


def main() -> None:
    destino_r2 = sys.argv[1] if len(sys.argv) > 1 else None

    meta, chunks = load()
    poemas: dict[str, object] = {}
    for c in chunks:
        poemas.setdefault(c.poem_id, c)
    voz = lambda p: getattr(p.voice, "value", str(p.voice))
    lng = lambda p: getattr(p.language, "value", str(p.language))

    chave5b = json.load(open(os.path.join(AQUI, "..", "fase-5b",
                                          "01-chave.json")))["chave"]
    contaminados: set[str] = set()
    for d in chave5b:
        contaminados.update(d["recuperados"])

    def elegivel(p) -> bool:
        return VERSOS_MIN <= len(versos(p.text)) <= VERSOS_MAX

    cae = sorted((p for p in poemas.values()
                  if voz(p) == "caeiro" and elegivel(p)
                  and p.poem_id not in contaminados), key=lambda p: p.poem_id)
    orto = sorted((p for p in poemas.values()
                   if voz(p) == "ortonimo" and lng(p) == "pt" and elegivel(p)),
                  key=lambda p: p.poem_id)
    print(f"elegíveis: Caeiro limpos {len(cae)} · ortónimo PT {len(orto)}")

    rng = random.Random(SEMENTE)
    sel_r = rng.sample(cae, N_POR_GRUPO)
    sel_o = rng.sample(orto, N_POR_GRUPO)
    ger_c = [d for d in chave5b if d["braco"] == "C"]
    ger_p = [d for d in chave5b if d["braco"] == "P"]
    sel_g = rng.sample(ger_c, N_POR_GRUPO // 2) + rng.sample(ger_p, N_POR_GRUPO // 2)

    itens = (
        [{"grupo": "R", "origem": p.poem_id, "texto": p.text} for p in sel_r]
        + [{"grupo": "O", "origem": p.poem_id, "texto": p.text} for p in sel_o]
        + [{"grupo": "G", "origem": d["id"], "texto": d["texto"],
            "braco_5b": d["braco"], "pergunta_5b": d["pergunta_id"]}
           for d in sel_g])
    assert len(itens) == 3 * N_POR_GRUPO

    # §6.2: nunca três do mesmo grupo seguidos, e nunca duas geradas da mesma
    # pergunta adjacentes.
    def ok(ordem: list[int]) -> bool:
        for j in range(len(ordem) - 2):
            g = [itens[ordem[j + k]]["grupo"] for k in range(3)]
            if g[0] == g[1] == g[2]:
                return False
        for j in range(len(ordem) - 1):
            a, b = itens[ordem[j]], itens[ordem[j + 1]]
            if (a["grupo"] == b["grupo"] == "G"
                    and a.get("pergunta_5b") == b.get("pergunta_5b")):
                return False
        return True

    ordem = list(range(len(itens)))
    for tentativa in range(1, 100001):
        rng.shuffle(ordem)
        if ok(ordem):
            break
    else:
        raise AssertionError("não consegui embaralhar com as restrições do §6.2")
    print(f"embaralhado em {tentativa} tentativa(s)")

    ids = [f"V{n:02d}" for n in range(1, len(ordem) + 1)]
    chave = [dict(id=sid, **itens[j]) for sid, j in zip(ids, ordem)]

    with open(os.path.join(AQUI, "01-chave.json"), "w") as f:
        json.dump({"_meta": {
            "aviso": "NÃO ABRIR antes de 02-contagens.json e "
                     "02-contagens-r2.json estarem commitados.",
            "protocolo": "docs/FASE-5D.md §6",
        }, "chave": chave}, f, ensure_ascii=False, indent=1)

    def corpo(cab: str) -> str:
        out = [cab, DEFINICOES]
        for sid, j in zip(ids, ordem):
            vs = versos(itens[j]["texto"])
            out.append(f"## {sid}  ·  {len(vs)} versos\n")
            out.append("```")
            out += [f"{k:2d}  {v}" for k, v in enumerate(vs, 1)]
            out.append("```\n")
            out.append("voltas: versos=[] tipos=[]\n")
            out.append("---\n")
        return "\n".join(out)

    with open(os.path.join(AQUI, "01-itens.md"), "w") as f:
        f.write(corpo(CABECALHO_R1))

    if destino_r2:
        texto = corpo(CABECALHO_R2.format(n=len(itens)))
        with open(destino_r2, "w") as f:
            f.write(texto)
        # o enquadramento é o que eu escrevo; os poemas são o material, e
        # verificar o material seria censurar o que se está a medir — a 5B
        # aprendeu isso com «braço forte» e «abraço frio».
        enquadramento = CABECALHO_R2.format(n=len(itens)) + DEFINICOES
        # Fronteira de palavra, e não substring: na primeira corrida isto
        # reprovou por «real» dentro de «realidade», que é texto das definições
        # pré-registadas e não fuga de desenho. A 5B aprendeu a mesma lição com
        # «braço» dentro de «abraço».
        for proibida in ("fase 5", "fase-5", "grupo", "grupos", "caeiro",
                         "ortónimo", "heterónimo", "gerado", "gerados",
                         "gerada", "geradas", "autêntico", "autêntica",
                         "real", "reais", "hipótese", "portão", "protocolo",
                         "braço", "braços"):
            assert not re.search(rf"(?<!\w){re.escape(proibida)}(?!\w)",
                                 enquadramento, re.IGNORECASE), \
                f"o enquadramento de R2 contém «{proibida}»"
        print(f"folha de R2 em {destino_r2} — enquadramento verificado")

    n = {g: sum(1 for i in itens if i["grupo"] == g) for g in "ROG"}
    print(f"{len(itens)} itens: R={n['R']} O={n['O']} G={n['G']}. A chave está fechada.")


if __name__ == "__main__":
    main()
