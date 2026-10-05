#!/usr/bin/env python
"""Fase 5I / Passo A4 — a folha e a chave, separadas do harness.

Protocolo em [`../FASE-5I.md`](../FASE-5I.md) §7.

**Esta fase separa a folha do harness de propósito.** Na Fase 5G o harness
herdado da 5B escreveu na folha a âncora **antiga** de 3a e o critério 4 — as
duas coisas que aquele protocolo substituía — e só não estragou a medição porque
foi apanhado antes de eu ler uma amostra. Aqui a folha é escrita por quem sabe
qual é a âncora.

Lê `01-cru.jsonl`, embaralha, escreve `01-chave.json` (fechada), `01-itens.md`
(R1) e, se lhe derem um caminho, a cópia neutra de R2.
"""
from __future__ import annotations

import json
import os
import random
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

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

**3b — forma da voz**

| 2 | 1 | 0 |
|---|---|---|
| verso livre, linhas curtas, sem rima, pouca imagem, 10–20 versos | livre mas com imagem decorativa, ou fora do intervalo | rimado, ou prosa com enters, ou longo e ornamentado |

Um poema **truncado** — cortado a meio — leva **0 em 3b** e é pontuado
normalmente em 3a′.

Pontuar pelas escalas acima e não por impressão geral. Não há distribuição-alvo e não
há resposta certa.

---

"""

CAB_R1 = """# Fase 5H / Passo B1 — folha de julgamento, às cegas

Pontuar **3a′** (poética) e **3b** (forma), 0–2, com as âncoras abaixo: a de 3a′
é a da [Fase 5F](../FASE-5F.md) §2, a de 3b a da [Fase 5](../FASE-5.md) §5.2.

A ordem é embaralhada e duas amostras da mesma pergunta não são adjacentes.
**Não abrir `01-chave.json`.**

"""

CAB_R2 = """# Folha de julgamento

{n} poemas em português, cada um escrito na voz de Alberto Caeiro, heterónimo de
Fernando Pessoa, a responder à frase que o encabeça.

Pontuar **dois** critérios por poema, cada um **0, 1 ou 2**, pelas escalas
abaixo. As escalas são a definição operativa: pontuar por elas e não por
impressão geral.

"""


def main() -> None:
    destino_r2 = sys.argv[1] if len(sys.argv) > 1 else None
    with open(os.path.join(AQUI, "01-cru.jsonl")) as f:
        cru = [json.loads(l) for l in f if l.strip()]
    assert len(cru) == 60, len(cru)

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

    ids = [f"I{n:02d}" for n in range(1, len(ordem) + 1)]
    seguro = []
    for sid, j in zip(ids, ordem):
        d = cru[j]
        seguro.append({"id": sid, "pergunta": d["pergunta"], "texto": d["texto"],
                       "truncada": d["truncada"], "c1_verso": d["c1_verso"],
                       "c2_pt": d["c2_pt"], "c5_plagio": d["c5_plagio"],
                       "n_versos": d["n_versos"]})
    # o ficheiro que eu posso ler: sem o braço e sem o modelo
    assert not any("braco" in s or "modelo" in s for s in seguro)
    with open(os.path.join(AQUI, "01-amostras.json"), "w") as f:
        json.dump({"_meta": {"protocolo": "docs/FASE-5I.md",
                             "aviso": "sem o braço nem o modelo, de propósito."},
                   "amostras": seguro}, f, ensure_ascii=False, indent=1)
    with open(os.path.join(AQUI, "01-chave.json"), "w") as f:
        json.dump({"_meta": {"aviso": "NÃO ABRIR antes de as duas pontuações "
                                      "estarem commitadas.",
                             "protocolo": "docs/FASE-5I.md §7"},
                   "chave": [dict(id=s, **cru[j]) for s, j in zip(ids, ordem)]},
                  f, ensure_ascii=False, indent=1)

    def corpo(cab: str) -> str:
        out = [cab, ANCORAS]
        for s in seguro:
            out += [f"## {s['id']}", "", f"> {s['pergunta']}", "",
                    "```", s["texto"], "```", "", "3a=_ 3b=_", "", "---", ""]
        return "\n".join(out)

    with open(os.path.join(AQUI, "01-itens.md"), "w") as f:
        f.write(corpo(CAB_R1))
    print(f"{len(seguro)} itens em 01-itens.md (R1). A chave está fechada.")

    if destino_r2:
        with open(destino_r2, "w") as f:
            f.write(corpo(CAB_R2.format(n=len(seguro))))
        # §7: só o CABEÇALHO que eu escrevo é verificado. As âncoras falam
        # necessariamente de «versos» e de «forma» — é o critério 3b — e
        # censurá-las seria censurar o que se está a medir. A 5B aprendeu a
        # mesma lição com «braço» dentro de «abraço».
        enq = CAB_R2.format(n=len(seguro))
        # §7: o enquadramento de R2 não pode revelar que há dois modelos.
        for proibida in ("fase 5", "fase-5", "braço", "braços", "modelo",
                         "modelos", "gerador", "qwen", "llama", "ollama",
                         "comprimento", "versos", "contagem", "reforço",
                         "reforçada", "forma",
                         "hipótese", "portão", "protocolo", "persona",
                         "ablação", "tratamento", "âncora", "âncoras",
                         "recalibrada", "antiga", "nova", "rubrica"):
            assert not re.search(rf"(?<!\w){re.escape(proibida)}(?!\w)",
                                 enq, re.IGNORECASE), \
                f"o enquadramento de R2 contém «{proibida}»"
        print(f"folha de R2 em {destino_r2} — enquadramento verificado")


if __name__ == "__main__":
    main()
