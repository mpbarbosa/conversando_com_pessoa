"""Orquestração: recuperar -> montar -> gerar -> guardar -> repetir se preciso.

## Por que há repetição, e por que é rara

Medido em 24 respostas reais (ver `docs/fase-1/07-RELATORIO-PLAGIO.md`):

| | sem a regra preventiva | com a regra no `system` |
|---|---|---|
| mediana de versos copiados | **82%** | **0%** |
| respostas acima de 20% | 16/24 (67%) | 3/24 (12%) |

A regra preventiva (`REGRAS_NAO_COPIAR` em `voices.py`) faz quase todo o
trabalho, e custa zero por pergunta porque vive no prefixo em cache. A repetição
com reforço é rede de segurança: dispara em ~21% dos casos e corrigiu 3 de 3.

Custo médio esperado: 1,21 gerações, ou ~34 s.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterator, Sequence

from .corpus.models import Chunk, Lang, Voice
from .generation.base import Generator, Resposta
from .generation.prompt import montar
from .guard import Veredicto, verificar
from .plagio import REFORCO, REFORCO_EN, Analise, analisar
from .retrieval.encoder import Encoder
from .retrieval.index import Index
from .voices import persona

TOP_K = 6
MAX_TENTATIVAS = 2


@dataclass(frozen=True)
class Turno:
    pergunta: str
    voz: Voice
    idioma: Lang
    recuperados: tuple[Chunk, ...]
    usados: tuple[Chunk, ...]
    resposta: Resposta
    veredicto: Veredicto
    plagio: Analise
    tentativas: int
    recuperacao_ms: float

    @property
    def texto(self) -> str:
        return self.veredicto.texto

    @property
    def aprovado(self) -> bool:
        return bool(self.veredicto) and not self.plagio.plagiou

    def fontes(self) -> str:
        return ", ".join(f"{c.poem_id}" for c in self.usados)


class Pipeline:
    def __init__(self, index: Index, encoder: Encoder, gerador: Generator,
                 n_tokens: Callable[[str], int], top_k: int = TOP_K):
        self.index = index
        self.encoder = encoder
        self.gerador = gerador
        self.n_tokens = n_tokens
        self.top_k = top_k

    def recuperar(self, pergunta: str, voz: Voice,
                  idioma: Lang = Lang.PT) -> tuple[list[Chunk], float]:
        import time
        t0 = time.perf_counter()
        qv = self.encoder.encode_queries([pergunta])[0]
        res = self.index.search(qv, top_k=self.top_k, voz=voz, idioma=idioma)
        return [c for c, _ in res], (time.perf_counter() - t0) * 1000

    def responder(self, pergunta: str, voz: Voice, idioma: Lang = Lang.PT,
                  max_tentativas: int = MAX_TENTATIVAS) -> Turno:
        recuperados, ms = self.recuperar(pergunta, voz, idioma)
        p = montar(pergunta, recuperados, persona(voz, idioma), self.n_tokens)

        user = p.user
        for tentativa in range(1, max_tentativas + 1):
            r = self.gerador.gerar(p.system, user)
            v = verificar(r.texto, pergunta=pergunta, idioma=idioma)
            a = analisar(v.texto, p.chunks_usados)
            if not a.plagiou or tentativa == max_tentativas:
                return Turno(pergunta, voz, idioma, tuple(recuperados),
                             p.chunks_usados, r, v, a, tentativa, ms)
            # Reforço corrective: refere-se a uma tentativa concreta, logo não
            # pode viver no prefixo em cache como a regra preventiva.
            user = p.user + (REFORCO if idioma is Lang.PT else REFORCO_EN)
        raise AssertionError("inalcançável")

    def responder_em_fluxo(self, pergunta: str, voz: Voice,
                           idioma: Lang = Lang.PT,
                           max_tentativas: int = MAX_TENTATIVAS
                           ) -> Iterator[str | Turno]:
        """Como `responder`, mas emite fragmentos à medida que chegam.

        Emite `str` para cada fragmento e um `Turno` no fim de **cada**
        tentativa. Se o `Turno` não estiver aprovado e houver tentativas, segue-
        se outra ronda de fragmentos — o utilizador vê a primeira tentativa a
        aparecer e depois a ser substituída, o que é mais honesto que esconder
        os ~28 s que a repetição custa.
        """
        import time
        recuperados, ms = self.recuperar(pergunta, voz, idioma)
        p = montar(pergunta, recuperados, persona(voz, idioma), self.n_tokens)

        user = p.user
        for tentativa in range(1, max_tentativas + 1):
            partes: list[str] = []
            resposta: Resposta | None = None
            for item in self.gerador.gerar_em_fluxo(p.system, user):
                if isinstance(item, str):
                    partes.append(item)
                    yield item
                else:
                    resposta = item
            assert resposta is not None
            v = verificar(resposta.texto, pergunta=pergunta, idioma=idioma)
            a = analisar(v.texto, p.chunks_usados)
            turno = Turno(pergunta, voz, idioma, tuple(recuperados),
                          p.chunks_usados, resposta, v, a, tentativa, ms)
            yield turno
            if turno.aprovado or tentativa == max_tentativas:
                return
            user = p.user + REFORCO
