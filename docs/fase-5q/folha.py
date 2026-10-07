#!/usr/bin/env python
"""Fase 5Q / A1 — a folha e a chave: 24 gerados e 8 reais por voz.

Protocolo em [`../FASE-5Q.md`](../FASE-5Q.md) §2.

Por voz: 8 do `qwen2.5:7b` e 8 do `llama3.1:8b` (a **mesma** pergunta e
repetição nos dois braços, vindos da 5M) e 8 **poemas reais** da voz.

**O comprimento não pode denunciar o real** (§2.2): os modelos produzem 4 a 24
versos e o corpus vai até 161, logo os reais são amostrados **só de 4 a 25
versos**, elegíveis, `pt`, e excluindo os que esta sessão imprimiu.

A folha etiqueta cada item com a **voz** — preciso dela para julgar, e não revela
a origem — e **não mostra pergunta**, porque os reais não têm e mostrá-la em dois
terços dos itens entregava o grupo.
"""
from __future__ import annotations

import json
import os
import random

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))

SEMENTE = 29
VOZES = ("campos", "reis", "ortonimo")
N_POR_CELULA = 8
VERSOS_REAIS = (4, 25)

#: §5.2 — poemas cujo texto esta sessao imprimiu, a excluir dos reais.
JA_LIDOS = {"poem_100", "poem_1008", "poem_1002", "poem_1487", "poem_1482",
            "poem_1456", "poem_3214", "poem_344", "poem_1485", "poem_2873"}

CAB = """# Fase 5Q / Passo B1 — folha de julgamento, às cegas

Cada item é **um poema**, de uma das três vozes, e a voz está indicada. Decidir,
por item, se é **Pessoa autêntico** ou **gerado por um modelo**:

| 1 | 2 | 3 | 4 |
|---|---|---|---|
| certamente **gerado** | provavelmente gerado | provavelmente **real** | certamente real |

Não há perguntas nesta folha, de propósito: os poemas reais não têm, e mostrá-las
só nos gerados entregava o grupo.

**Não abrir `01-chave.json`.**

---

"""


def main() -> None:
    cont = json.load(open(os.path.join(RAIZ, "docs/fase-5j/01-contagem.json"),
                          encoding="utf-8"))
    cru = [json.loads(l) for l in
           open(os.path.join(RAIZ, "docs/fase-5m/01-cru.jsonl"),
                encoding="utf-8") if l.strip()]
    rng = random.Random(SEMENTE)

    itens: list[dict] = []
    for voz in VOZES:
        # --- os gerados: 8 perguntas, uma repeticao cada, nos DOIS bracos --
        perguntas = sorted({r["pergunta_id"] for r in cru if r["voz"] == voz})
        assert len(perguntas) == 10, (voz, len(perguntas))
        escolhidas = sorted(rng.sample(perguntas, N_POR_CELULA))
        for q in escolhidas:
            rep = rng.choice([0, 1, 2])
            for braco, rotulo in (("Q", "qwen2.5:7b"), ("L", "llama3.1:8b")):
                m = [r for r in cru if r["voz"] == voz and r["braco"] == braco
                     and r["pergunta_id"] == q and r["repeticao"] == rep]
                assert len(m) == 1, (voz, braco, q, rep, len(m))
                itens.append({"grupo": braco, "modelo": rotulo, "voz": voz,
                              "origem": f"{q}r{rep}", "texto": m[0]["texto"]})

        # --- os reais: 8, na gama de comprimento dos modelos --------------
        lo, hi = VERSOS_REAIS
        pool = [p for p in cont["por_poema"][voz]
                if p["elegivel"] and p["lingua"] == "pt"
                and lo <= p["versos_min3"] <= hi and p["id"] not in JA_LIDOS]
        assert len(pool) >= N_POR_CELULA * 4, (voz, len(pool))
        for p in rng.sample(pool, N_POR_CELULA):
            caminho = os.path.join(RAIZ, "data/pessoa_poems", f'{p["id"]}.txt')
            import sys
            sys.path.insert(0, RAIZ)
            from src.corpus.parse import parse_poem
            itens.append({"grupo": "R", "modelo": "Pessoa", "voz": voz,
                          "origem": p["id"],
                          "texto": parse_poem(caminho).body})

    assert len(itens) == len(VOZES) * N_POR_CELULA * 3, len(itens)
    itens.sort(key=lambda d: (d["voz"], d["grupo"], d["origem"]))

    ordem = list(range(len(itens)))
    for tentativa in range(1, 100001):
        rng.shuffle(ordem)
        seq = [itens[j]["grupo"] for j in ordem]
        # nenhum bloco de 4 do mesmo grupo, e nenhum bloco de 5 da mesma voz
        vz = [itens[j]["voz"] for j in ordem]
        if (not any(len(set(seq[k:k + 4])) == 1 for k in range(len(seq) - 3))
                and not any(len(set(vz[k:k + 5])) == 1
                            for k in range(len(vz) - 4))):
            break
    else:
        raise AssertionError("não consegui embaralhar")
    print(f"embaralhado em {tentativa} tentativa(s)")

    ids = [f"Q{n:02d}" for n in range(1, len(ordem) + 1)]
    seguro = [{"id": s, "voz": itens[j]["voz"], "texto": itens[j]["texto"]}
              for s, j in zip(ids, ordem)]
    assert not any(k in s for s in seguro for k in ("grupo", "modelo", "origem"))

    with open(os.path.join(AQUI, "01-amostras.json"), "w",
              encoding="utf-8") as f:
        json.dump({"_meta": {"protocolo": "docs/FASE-5Q.md §2",
                             "aviso": "sem o grupo, o modelo nem a origem."},
                   "amostras": seguro}, f, ensure_ascii=False, indent=1)
    with open(os.path.join(AQUI, "01-chave.json"), "w", encoding="utf-8") as f:
        json.dump({"_meta": {"aviso": "NÃO ABRIR antes de as pontuações "
                                      "estarem commitadas.",
                             "protocolo": "docs/FASE-5Q.md §2.4",
                             "semente": SEMENTE},
                   "chave": [dict(id=s, **itens[j])
                             for s, j in zip(ids, ordem)]},
                  f, ensure_ascii=False, indent=1)

    out = [CAB]
    for s in seguro:
        out += [f"## {s['id']}  ·  voz: **{s['voz']}**", "", "```",
                s["texto"], "```", "", "real? _", "", "---", ""]
    with open(os.path.join(AQUI, "01-itens.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    import collections
    print(f"{len(seguro)} itens em 01-itens.md. A chave está fechada.")
    print("por voz x grupo:",
          dict(collections.Counter((i["voz"], i["grupo"]) for i in itens)))


if __name__ == "__main__":
    main()
