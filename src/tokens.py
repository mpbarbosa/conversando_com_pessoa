"""Contagem de tokens com o tokenizador real.

Dois tokenizadores importam neste projecto e **não** são intercambiáveis:

- o do **encoder** (`e5`), que define o limite de chunk (maxlen=512)
- o do **gerador** (`qwen2.5`), que define o orçamento de prompt (500 tokens)

Medido no corpus: o e5 dá mediana de 1,469 tokens por palavra (a estimativa de
1,45 usada no planeamento estava certa).
"""
from __future__ import annotations

from functools import lru_cache
from typing import Callable

ENCODER = "intfloat/multilingual-e5-base"


@lru_cache(maxsize=4)
def _tokenizador(nome: str):
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(nome)


def contador(nome: str = ENCODER) -> Callable[[str], int]:
    """Devolve uma função que conta tokens, sem tokens especiais."""
    tok = _tokenizador(nome)

    def conta(texto: str) -> int:
        return len(tok(texto, add_special_tokens=False).input_ids)

    return conta
