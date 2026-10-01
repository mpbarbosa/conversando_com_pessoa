"""Normalização ortográfica para a busca lexical.

Tudo aqui foi construído **a partir do corpus**, não de memória, e é muito mais
pequeno do que a `FASE-2.md` antecipava. O que ficou de fora importa tanto como
o que ficou.

## O que entra

**Elisões** — 245 ocorrências em 80 formas, o mecanismo mais frequente.
`p'ra` (59) e `p’ra` (36) usam apóstrofos diferentes (U+0027 e U+2019), e o
tokenizador do BM25 reduzia ambos ao token **`ra`**, que é lixo. `prò` (2) e
`pra` (60) nunca casavam com `para`.

**Alternância `ou`/`oi`** — 13 pares, a variação real da época: `coisa`/`cousa`
(387/39), `ouro`/`oiro`, `ouço`/`oiço`, `loura`/`loira`, `papoila`/`papoula`.
67 ocorrências das formas raras.

## O que fica de fora, e porquê

**Todos os pares distinguidos por acento.** A `FASE-2.md` já dizia «sem remoção
de acentos — em português o acento distingue palavras», e o meu gerador de
candidatos usou «acento» como sinal de equivalência apesar disso. Propôs fundir
`para`/`pára`, `pais`/`país`, `bebe`/`bebé`, `faca`/`faça`, `sois`/`sóis`,
`dois`/`dóis`, `mares`/`marés`, `seria`/`séria` — **pares de palavras
diferentes**.

Dos 11 candidatos com razão de frequência extrema, 8 são palavras distintas ou
infinitivos com clítico (`esquecê-lo`, `deixá-lo`). Os 3 restantes — `duvida`,
`gloria`, `angustia` — são plausivelmente gralhas de transcrição, mas nos três
a forma sem acento **é também um verbo válido**. São 8 ocorrências em 229 mil
palavras: risco de correcção real por ganho nulo.

**`facto`/`fato`.** Em português europeu são palavras diferentes: um facto e um
fato.

**Lematização.** O Snowball reduz `cousa`→`cous` e `coisa`→`cois`: continua a
não casar, e destrói terminações que em verso carregam rima.
"""
from __future__ import annotations

import re

#: Apóstrofos que o corpus usa, todos normalizados para `'`.
_APOSTROFOS = "’ʼ´`"

#: Elisões, expandidas antes da remoção de pontuação. A ordem importa: as mais
#: longas primeiro, senão `p'` consome o `p'ra`.
_ELISOES: tuple[tuple[str, str], ...] = (
    (r"\bp'ra\b", "para"),        # 95 ocorrências nas duas grafias de apóstrofo
    (r"\bpra\b", "para"),         # 60
    (r"\bpr[òó]s\b", "para os"),  # 2
    (r"\bpr[òó]\b", "para o"),    # 8
    (r"\bp'l([oa]s?)\b", r"pel\1"),   # p'lo -> pelo, p'la -> pela (4)
    (r"\bd'", "de "),             # d'alma (22), d'além (5)
    (r"\bn'", "em "),             # n'alma (17)
    (r"\bm'", "me "),             # m'o digas
    (r"\bt'", "te "),
    (r"\bs'", "se "),
    (r"\bl'", "lhe "),
)

#: Alternância ou/oi, com a forma comum como canónica. Construída do corpus:
#: só pares em que **as duas formas existem** lá.
_OU_OI: tuple[tuple[str, str], ...] = (
    (r"\bcousas\b", "coisas"), (r"\bcousa\b", "coisa"),
    (r"\boiro\b", "ouro"),
    (r"\boiço\b", "ouço"), (r"\boiça\b", "ouça"),
    (r"\bloira\b", "loura"),
    (r"\bdoira\b", "doura"), (r"\bdoire\b", "doure"),
    (r"\bdoirado\b", "dourado"),
    (r"\btesoira\b", "tesoura"),
    (r"\baçoute\b", "açoite"),
    (r"\bpapoulas\b", "papoilas"), (r"\bpapoula\b", "papoila"),
)

_RE_ELISOES = tuple((re.compile(p, re.I), r) for p, r in _ELISOES)
_RE_OU_OI = tuple((re.compile(p, re.I), r) for p, r in _OU_OI)
_RE_ESPACOS = re.compile(r"\s+")


def normalizar(texto: str) -> str:
    """Aplica-se aos **dois** lados: documento e consulta."""
    t = texto.lower()
    for a in _APOSTROFOS:
        t = t.replace(a, "'")
    for rx, sub in _RE_ELISOES:
        t = rx.sub(sub, t)
    for rx, sub in _RE_OU_OI:
        t = rx.sub(sub, t)
    return _RE_ESPACOS.sub(" ", t).strip()
