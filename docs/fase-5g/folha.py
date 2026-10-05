#!/usr/bin/env python
"""Fase 5G / Passo A4 (correcção) — as folhas de julgamento, com a âncora certa.

O harness desta fase é o da Fase 5B com uma linha mudada (§3.1 do protocolo), e
isso trouxe um defeito: escreveu em `01-amostras.md` a **âncora antiga** de 3a e
o **critério 4**, que o §4 do protocolo desta fase substitui e remove.

As amostras e a chave não estão afectadas — dependem só da geração. Este ficheiro
reescreve as **folhas de julgamento** a partir de `01-amostras.json`, que é o
ficheiro sem o braço, e põe lá:

- a âncora **3a′** da [Fase 5F](../FASE-5F.md) §2, com as seis regras dos casos
  difíceis;
- a âncora de **3b** da [Fase 5](../FASE-5.md) §5.2, **inalterada**;
- **nada** sobre o critério 4.

Corrido antes de qualquer amostra ter sido lida por mim.
"""
from __future__ import annotations

import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

ANCORA_3A = """**3a′ — poética da voz**

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

**3b — forma da voz**

| 2 | 1 | 0 |
|---|---|---|
| verso livre, linhas curtas, sem rima, pouca imagem, 10–20 versos | livre mas com imagem decorativa, ou fora do intervalo | rimado, ou prosa com enters, ou longo e ornamentado |

Um poema **truncado** — cortado a meio — leva **0 em 3b** e é pontuado
normalmente em 3a′.

Pontuar pelas âncoras e não por impressão geral. Não há distribuição-alvo e não
há resposta certa.

---

"""

CAB_R1 = """# Fase 5G / Passo B1 — folha de julgamento, às cegas

Pontuar **3a′** (poética) e **3b** (forma), 0–2, com as âncoras abaixo: a de 3a′
é a recalibrada da [Fase 5F](../FASE-5F.md) §2, a de 3b é a da
[Fase 5](../FASE-5.md) §5.2, inalterada. O critério 4 **não** se pontua (§4 do
[protocolo](../FASE-5G.md)).

A ordem é embaralhada e duas amostras da mesma pergunta não são adjacentes.
**Não abrir `01-chave.json`.**

"""

CAB_R2 = """# Folha de julgamento

{n} poemas em português, cada um escrito na voz de Alberto Caeiro, heterónimo de
Fernando Pessoa, a responder à frase que o encabeça.

Pontuar **dois** critérios por poema, cada um **0, 1 ou 2**, pelas âncoras
abaixo.

"""


def main() -> None:
    destino_r2 = sys.argv[1] if len(sys.argv) > 1 else None
    am = json.load(open(os.path.join(AQUI, "01-amostras.json")))["amostras"]
    assert len(am) == 60, len(am)
    # o ficheiro sem o braço: a asserção torna isso verificado em vez de alegado
    assert not any("braco" in a or "condicao" in a for a in am)

    def corpo(cab: str) -> str:
        out = [cab, ANCORA_3A]
        for s in am:
            out += [f"## {s['id']}", "", f"> {s['pergunta']}", "",
                    "```", s["texto"], "```", "", "3a=_ 3b=_", "", "---", ""]
        return "\n".join(out)

    with open(os.path.join(AQUI, "01-itens.md"), "w") as f:
        f.write(corpo(CAB_R1))
    print(f"{len(am)} itens em 01-itens.md (R1)")

    if destino_r2:
        with open(destino_r2, "w") as f:
            f.write(corpo(CAB_R2.format(n=len(am))))
        enq = CAB_R2.format(n=len(am)) + ANCORA_3A
        for proibida in ("fase 5", "fase-5", "braço", "braços", "condição",
                         "controlo", "hipótese", "portão", "protocolo",
                         "interdição", "interdições", "persona", "ablação",
                         "tratamento", "âncora", "recalibrada", "antiga",
                         "nova", "rubrica"):
            assert not re.search(rf"(?<!\w){re.escape(proibida)}(?!\w)",
                                 enq, re.IGNORECASE), \
                f"o enquadramento de R2 contém «{proibida}»"
        print(f"folha de R2 em {destino_r2} — enquadramento verificado")


if __name__ == "__main__":
    main()
