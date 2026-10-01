"""Guarda lexical: palavras que o modelo inventou.

## Por que duas autoridades, e não uma

Medido em 2026-10-01, com os dois dicionários de português europeu instalados:

| | |
|---|---|
| defeitos que o `aspell` apanha | **10 de 13** |
| vocabulário real de Pessoa que o `aspell` **rejeita** | **593 tipos (7,1%)** |

O `hunspell-pt-pt` de 2025 tem 44 257 entradas e **nenhuma forma pré-acordo de
1990**. Nem ele nem o `aspell` conhecem `acção`, `nocturno`, `abstracto`,
`eléctrico`, `reflectem` — que são as formas **correctas** para este corpus. Ambos
aceitam `ação`, `noturno`, `refletem`, que aqui seriam erradas.

Não é lacuna dos pacotes: é a norma de 2026, que é a norma errada para um corpus
de 1915. Um dicionário sozinho sinalizaria 593 palavras legítimas de Pessoa.

Daí as **duas condições**: uma palavra é suspeita se o dicionário a desconhecer
**e** ela não existir no corpus.

- o **corpus** é a autoridade sobre o que Pessoa escrevia (`acção`, `inda`,
  `cousas`, `dlôn`, `Lídia` estão lá)
- o **dicionário** é a autoridade sobre o que é português moderno

A intersecção das duas ignorâncias é o espaço das palavras inventadas.

## O que apanha, e o que não

Dos 13 defeitos medidos em 28 respostas, apanha **10**: `poniente`
(castelhanismo de *poente*), `río`, `tus`, `veo`, `brevítil`, `naufragios`,
`invisiveis`, `numo`, `dispers`, `cutuca`.

Escapam três — `caiem`, `risada`, `perpetua` — porque o dicionário os aceita
como formas válidas noutros contextos. Para esses continua a servir a lista
enumerada de `voices.INTERDICOES`, que passa a complemento e não a mecanismo
principal.

## Duas limitações estruturais, medidas

**Flexões ausentes do corpus dão falsos positivos.** O corpus tem 216 mil
palavras e não cobre todas as formas das palavras que contém: `reflecte` está
lá, `reflectem` não. `reflectem` é português europeu pré-acordo correcto,
ausente por acaso, e o dicionário moderno rejeita-o — logo é sinalizado
indevidamente. Com 16 085 tipos de referência, cada flexão em falta é um falso
positivo potencial. É o preço de usar o corpus como autoridade ortográfica, e
não há correcção barata: um lematizador português resolveria parte, mas
introduziria os seus próprios erros sobre grafia de 1915.

**Quatro palavras inglesas no vocabulário «português»:** `and` (10x), `the`
(9x), `that`, `this` — vindas do `poem_135`, a *Ode Marítima*, que tem versos em
inglês a meio e está classificada como PT porque a maioria o é. Significa que
estas quatro não seriam sinalizadas numa resposta portuguesa. O caso de uma
resposta inteira noutra língua é coberto por `guard.fracao_pt`; palavras
isoladas passam.

## Reporta, não rejeita

Uma palavra inventada não estraga um poema, e rejeitar custa ~28 s de nova
geração. Ao contrário dos brasileirismos, que têm substituição conhecida e são
corrigidos, aqui não há correcção possível — logo avisa-se.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from functools import lru_cache

from .corpus.models import Lang

#: Dicionário do aspell por língua. O `pt_PT` é pós-acordo de 1990 — ver as
#: limitações abaixo. O `en` cobre o inglês de Pessoa pior do que parece: ele
#: escreve «giveth», «storiless», «aught», que o dicionário moderno desconhece
#: — e é por isso que o vocabulário do corpus é a segunda autoridade também
#: aqui, não só em português.
DICIONARIOS: dict[Lang, str] = {Lang.PT: "pt_PT", Lang.EN: "en"}

DICIONARIO = "pt_PT"      # compatibilidade
TIMEOUT_S = 10

#: Palavras com menos letras que isto são ruído: elisões, interjeições.
MIN_LETRAS = 3

_RE_PALAVRA = re.compile(r"[a-zà-ÿA-ZÀ-Ÿ]+")


@dataclass(frozen=True)
class Suspeita:
    palavra: str
    verso: str


@lru_cache(maxsize=4)
def aspell_disponivel(idioma: Lang = Lang.PT) -> bool:
    dic = DICIONARIOS.get(idioma)
    if dic is None:
        return False
    try:
        r = subprocess.run(["aspell", "-d", dic, "list"],
                           input="teste", capture_output=True, text=True,
                           timeout=TIMEOUT_S)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.SubprocessError):
        return False


def desconhecidas_do_dicionario(palavras: set[str],
                                idioma: Lang = Lang.PT) -> set[str]:
    """Palavras que o `aspell` não reconhece. Uma chamada em lote: 3,2 ms.

    Devolve conjunto vazio se o `aspell` não estiver disponível — e nesse caso
    a guarda fica **inerte**, em vez de sinalizar tudo o que não está no corpus
    (o corpus sozinho tem 87% de falsos positivos).
    """
    if not palavras or not aspell_disponivel(idioma):
        return set()
    try:
        r = subprocess.run(["aspell", "-d", DICIONARIOS[idioma], "list"],
                           input="\n".join(sorted(palavras)),
                           capture_output=True, text=True, timeout=TIMEOUT_S)
    except subprocess.SubprocessError:
        return set()
    return {p.strip().lower() for p in r.stdout.split() if p.strip()}


@lru_cache(maxsize=4)
def vocabulario_do_corpus(idioma: Lang = Lang.PT) -> frozenset[str]:
    """Tipos de palavra dos chunks **portugueses** do corpus.

    Só português **porque a referência é para avaliar respostas em português**,
    não porque o inglês seja ruído: Pessoa escreveu obra em inglês (os *35
    Sonnets*, as *Inscriptions*) e Alexander Search escrevia em inglês. Uma
    guarda para respostas inglesas precisaria do vocabulário inglês do corpus e
    do dicionário `en`, que o aspell tem.

    Na primeira tentativa desta medição misturei os dois e as palavras mais
    «rejeitadas» pelo dicionário português eram `the`, `and` e `that`.
    """
    from .corpus.build import load
    try:
        _, chunks = load()
    except OSError:
        return frozenset()
    v: set[str] = set()
    for c in chunks:
        if c.language is idioma:
            v.update(p.lower() for p in _RE_PALAVRA.findall(c.text))
    return frozenset(v)


def suspeitas(texto: str, vocabulario: frozenset[str] | None = None,
              idioma: Lang = Lang.PT) -> tuple[Suspeita, ...]:
    """Palavras que nem o corpus nem o dicionário da língua conhecem."""
    vocab = (vocabulario if vocabulario is not None
             else vocabulario_do_corpus(idioma))

    candidatas: dict[str, str] = {}      # palavra -> verso onde aparece
    for linha in texto.split("\n"):
        for p in _RE_PALAVRA.findall(linha):
            baixa = p.lower()
            if len(baixa) < MIN_LETRAS or baixa in vocab:
                continue
            candidatas.setdefault(baixa, linha.strip())

    if not candidatas:
        return ()
    fora = desconhecidas_do_dicionario(set(candidatas), idioma)
    return tuple(Suspeita(p, candidatas[p]) for p in sorted(fora))
