#!/usr/bin/env python
"""Fase 5B — os dois braços da persona do Caeiro.

Protocolo em [`../FASE-5B.md`](../FASE-5B.md) §4, commitado **antes** de este
ficheiro produzir qualquer amostra.

**C** é a persona de serviço, importada de `src.voices` e nunca copiada à mão —
se alguém mudar `src/voices.py`, este módulo passa a medir o que lá estiver, e é
isso que se quer.

**P** é a mesma persona com **só** o campo `poetica` substituído. `forma`,
`REGRAS_LINGUA`, `REGRAS_NAO_COPIAR` e `REGRAS_SAIDA` ficam byte a byte iguais —
ver o §3.1 do protocolo para as três razões, das quais a mais importante é que
`REGRAS_NAO_COPIAR` é uma interdição **com carga útil medida**: na Fase 1 levou
a mediana de versos copiados de 82% para 0%.

## Porque é que `src/voices.py` não se toca

A variante só entra no serviço se o portão G1 disparar. Até lá, o que corre no
harness é um `dataclasses.replace` em memória, e o `Pipeline` recebe-a por
*monkeypatch* de `src.pipeline.persona` — `responder` chama `voices.persona`
directamente, logo não há injecção por parâmetro.
"""
from __future__ import annotations

import dataclasses
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.corpus.models import Lang, Voice
from src.voices import PERSONAS, Persona

#: O braço de controlo: a persona de serviço, tal e qual.
CAEIRO_C: Persona = PERSONAS[(Voice.CAEIRO, Lang.PT)]

#: A cláusula poética afirmativa. Produzida pela regra do §4.1 do protocolo, e
#: o mapa cláusula-a-cláusula está no §4.3. A regra, resumida: cada oração da
#: versão de serviço tem uma correspondente com o **mesmo referente**, zero
#: partículas negativas, comprimento dentro de ±20%, e nenhum conteúdo poético
#: novo — nenhuma imagem, nenhum exemplo, nenhum nome.
#:
#: A cláusula 5 («Recusas a metafísica, a simbologia e a moral») é a que mostra
#: o mecanismo em teste: a variante **não nomeia** os referentes. O §2.1 do
#: protocolo declara que polaridade e nomeação ficam fundidas de propósito, e
#: que este desenho não as separa.
POETICA_P = """Vês as coisas como elas são, e o que elas são está todo à vista. Uma
árvore é uma árvore; um poente é um poente, e é isso que ele é. Vês o que vês, e
o ver basta-te. Ficas na superfície das coisas, que é onde elas estão inteiras. A
natureza está ali por sua conta, e continua igual quando passas."""

#: O braço positivo.
CAEIRO_P: Persona = dataclasses.replace(CAEIRO_C, poetica=POETICA_P)

#: Os dois braços, pela letra com que aparecem no protocolo e na chave.
BRACOS: dict[str, Persona] = {"C": CAEIRO_C, "P": CAEIRO_P}

#: §4.1 regra 2. Fronteira de palavra, sem distinção de maiúsculas.
PARTICULAS_NEGATIVAS = (
    "não", "nunca", "nem", "sem", "nada",
    "recusas", "recusa", "proíbes", "evitas", "jamais", "sequer",
)

#: §7.1, Instrumento II. Os referentes que a persona **C** nomeia, com
#: variantes morfológicas. A lista vem da tabela do §4.3 — logo do
#: **tratamento**, nunca das amostras. É por isso que não tem portão: P não
#: contém estas palavras por construção, e um eco de vocabulário do prompt
#: produziria o resultado esperado sem nenhuma diferença de poética.
REFERENTES_NOMEADOS = (
    "significado", "significados", "sentido", "sentidos",
    "oculto", "oculta", "ocultos", "ocultas",
    "metafísica", "metafísico", "símbolo", "símbolos", "simbologia",
    "simbólico", "moral", "morais",
    "espelho", "espelhos", "tristeza", "tristezas",
)
