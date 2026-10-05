#!/usr/bin/env python
"""Fase 5I — os dois braços da cláusula de **forma** do Caeiro.

Protocolo em [`../FASE-5I.md`](../FASE-5I.md) §3.

**A** é a `forma` de serviço, importada de `src.voices` e nunca copiada à mão.
**B** é a mesma com o requisito de comprimento **reforçado** — e nada mais.

## O que esta fase não muda, e é o ponto

A `poetica` fica **byte a byte igual**. Foi ela que a Fase 5H mediu valer +0,700
no llama3.1, e é o activo que esta fase não pode gastar. Também ficam iguais
`REGRAS_LINGUA`, `REGRAS_NAO_COPIAR` e `REGRAS_SAIDA`.

## Porque é que o lado reforçado não acrescenta o pedido, e sim insiste nele

A `forma` de serviço **já diz** «Entre dez e vinte versos». A Fase 5H mediu que o
llama3.1 a ignora: 21 das 30 amostras abaixo de dez versos, contra 25 das 30 do
qwen dentro do intervalo. O que falta não é o pedido — é ele pegar.
"""
from __future__ import annotations

import dataclasses
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.corpus.models import Lang, Voice
from src.voices import PERSONAS, Persona

#: O braço de controlo: a persona de serviço, tal e qual.
CAEIRO_A: Persona = PERSONAS[(Voice.CAEIRO, Lang.PT)]

#: A cláusula de forma reforçada. Regra de reescrita no §3.1 do protocolo:
#: todas as orações da versão de serviço são preservadas, o requisito de
#: comprimento passa para **primeira** posição e ganha uma instrução de
#: contagem, e **nenhum conteúdo poético novo** entra.
FORMA_B = """O poema tem de ter **entre dez e vinte versos** — conta-os antes de
terminares, e não entregues menos de dez. Verso livre, linhas curtas, sem rima.
Linguagem simples, quase seca. Poucas imagens, e nenhuma decorativa."""

#: O braço reforçado.
CAEIRO_B: Persona = dataclasses.replace(CAEIRO_A, forma=FORMA_B)

BRACOS: dict[str, Persona] = {"A": CAEIRO_A, "B": CAEIRO_B}

#: §3.1 regra 1. As orações da `forma` de serviço que têm de sobreviver
#: literalmente no braço B.
ORACOES_PRESERVADAS = (
    "Verso livre, linhas curtas, sem rima.",
    "Linguagem simples, quase",          # a quebra de linha difere; ver verificar
    "seca.",
    "Poucas imagens, e nenhuma decorativa.",
)
