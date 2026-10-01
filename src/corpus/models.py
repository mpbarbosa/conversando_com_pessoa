"""Modelo de domínio do corpus.

Fronteira do sistema: tudo a jusante consome `Poem`/`Chunk`, nunca os `.txt`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Voice(StrEnum):
    """As vozes de Pessoa. Distribuição medida nos 2083 ficheiros."""

    ORTONIMO = "ortonimo"   # 1298
    CAMPOS = "campos"       #  323 (+1 com mojibake)
    REIS = "reis"           #  252
    CAEIRO = "caeiro"       #  120
    SEARCH = "search"       #   52
    SOARES = "soares"       #    6
    OUTRO = "outro"         #   ~15 pré-heterónimos e semi-heterónimos


class Lang(StrEnum):
    PT = "pt"
    EN = "en"
    INDETERMINADO = "?"


#: As quatro vozes com corpus suficiente para persona própria na Fase 1.
VOZES_PRINCIPAIS = (Voice.ORTONIMO, Voice.CAMPOS, Voice.REIS, Voice.CAEIRO)


@dataclass(frozen=True)
class Poem:
    id: str                      # "poem_135"
    author: str                  # nome canónico, já normalizado
    voice: Voice
    title: str                   # da linha "Titulo:"
    body: str                    # corpo limpo: sem cabeçalho nem título repetido
    language: Lang
    stanzas: tuple[str, ...]
    n_words: int
    duplicate_of: str | None = None   # id do representante do grupo

    @property
    def is_duplicate(self) -> bool:
        return self.duplicate_of is not None


@dataclass(frozen=True)
class Chunk:
    """Unidade de indexação. Para 96% dos poemas é o poema inteiro."""

    poem_id: str
    chunk_ix: int                # 0 quando o poema cabe inteiro
    text: str                    # o que vai no PROMPT (verso puro)
    indexed_text: str            # o que vai no ÍNDICE (com autor e título)
    voice: Voice
    language: Lang
    n_words: int
