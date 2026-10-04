#!/usr/bin/env python
"""Fase 5B / Passo B2 — a folha neutra que R2 recebe.

Protocolo em [`../FASE-5B.md`](../FASE-5B.md) §6.1. R2 é cego ao **desenho** e
não só à condição: não sabe que há dois braços, nem qual é a hipótese, nem que
existe um tratamento.

A folha de R1 (`01-amostras.md`) não serve para isso. Diz «Fase 5B» no título e
remete para `../FASE-5.md`, logo um avaliador que seguisse a referência
encontrava o protocolo, a hipótese e os portões. Este ficheiro escreve a mesma
folha — **as mesmas âncoras, as mesmas amostras, a mesma ordem** — sem nome de
fase e sem ligação nenhuma, para um sítio fora do repositório.

O que muda entre as duas folhas é só o enquadramento. As âncoras vão daqui
verbatim, e a ordem é a do embaralhamento, logo R1 e R2 pontuam exactamente o
mesmo material.
"""
from __future__ import annotations

import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

#: As âncoras do Caeiro, verbatim da Fase 5 §5.1–5.3. É o único conteúdo
#: normativo que R2 recebe.
CABECALHO = """# Folha de julgamento

{n} poemas em português, cada um escrito na voz de **Alberto Caeiro**,
heterónimo de Fernando Pessoa, a responder à frase que o encabeça.

Pontuar **três** critérios por poema, cada um **0, 1 ou 2**, pelas âncoras
abaixo. As âncoras são a definição operativa: pontuar por elas e não por
impressão geral.

## 3a — poética da voz

| 2 | 1 | 0 |
|---|---|---|
| vê e não interpreta; nenhuma metafísica, símbolo, moral, nem natureza como espelho de sentimento | sensorial na maior parte, com **uma** volta simbólica ou moral | filosofa, interpreta, atribui significado oculto, personifica |

## 3b — forma da voz

| 2 | 1 | 0 |
|---|---|---|
| verso livre, linhas curtas, sem rima, pouca imagem, 10–20 versos | livre mas com imagem decorativa, ou fora do intervalo | rimado, ou prosa com enters, ou longo e ornamentado |

Um poema **truncado** — cortado a meio de uma palavra ou de um verso — leva
**0 em 3b**, e é pontuado normalmente nos outros dois critérios.

## 4 — responde à frase

**2** responde ao que a frase põe, na voz · **1** toca o tema mas responde a
outra coisa, ou responde em geral · **0** divaga.

---

"""


def main() -> None:
    destino = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "folha-r2.md")
    am = json.load(open(os.path.join(AQUI, "01-amostras.json")))["amostras"]

    linhas = [CABECALHO.format(n=len(am))]
    enquadramento = [CABECALHO.format(n=len(am))]
    for s in am:
        andaime = [f"## {s['id']}", "", f"> {s['pergunta']}", "",
                   "```", s["texto"], "```", "", "3a=_ 3b=_ 4=_", "", "---", ""]
        linhas += andaime
        # O **enquadramento** é o que eu escrevo; a pergunta e o poema são o
        # material que os dois avaliadores vêem por igual. A verificação abaixo
        # corre só no enquadramento, e a razão está no comentário dela.
        enquadramento += [andaime[0], andaime[8]]
    with open(destino, "w") as f:
        f.write("\n".join(linhas))

    # Nada que **eu** escreva no ficheiro pode nomear a fase, o desenho ou a
    # hipótese. A verificação exclui os poemas e as perguntas de propósito: na
    # primeira corrida reprovou três amostras por «braço forte», «braços
    # estendidos» e «abraço frio», que são conteúdo e não fuga de desenho.
    # Verificar o material seria censurar o que se está a medir.
    alvo = "\n".join(enquadramento)
    for proibida in ("Fase 5", "FASE-5", "fase-5", "braço", "braco", "condição",
                     "controlo", "hipótese", "portão", "interdiç", "persona",
                     "protocolo", "CONTROLO", "ablação", "tratamento"):
        assert proibida.lower() not in alvo.lower(), \
            f"o enquadramento da folha de R2 contém «{proibida}»"
    print(f"{len(am)} amostras em {destino}")
    print("verificado: o enquadramento não nomeia fase, desenho nem hipótese.")


if __name__ == "__main__":
    main()
