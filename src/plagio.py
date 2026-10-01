"""Guarda de plágio.

## Por que não n-gramas

O plano (§6.3 de PLANO-RAG-LOCAL.md) especificava «maior sobreposição de
n-gramas (n=8)». A primeira travessia completa do pipeline mostrou que isso não
serve. A saída foi:

    Nunca sei como se pode achar um poente triste.      <- 0,94 do contexto
    Só se for por não ser madrugada.                    <- 0,76
    Ambos existem; cada um seu caminho.                 <- 0,75

Três de oito versos eram cópia, e a sobreposição de 8-gramas era **2%**. A cópia
é por **paráfrase ao nível do verso** — troca uma palavra, encurta, reordena — e
n-gramas literais não a vêem.

É o mesmo problema que obrigou a trocar de métrica na deduplicação (Passo 2),
onde o Jaccard de 4-gramas dava 0,457 a duas versões do mesmo poema e 0,480 a
poemas distintos.

## A métrica

Fracção dos versos da **saída** que têm par próximo no contexto injectado.
Assimétrica de propósito: o que interessa é quanto da resposta é emprestado, não
quanto do contexto foi usado.
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from typing import Sequence

from .corpus.models import Chunk

#: Acima disto, dois versos são o mesmo verso.
#:
#: **Calibrado** sobre 24 respostas reais (ver `07-RELATORIO-PLAGIO.md`). Há uma
#: lacuna limpa na similaridade máxima por resposta:
#:
#:     respostas que copiam (5):  mediana 0,91   mínimo 0,79
#:     respostas limpas    (19):  mediana 0,55   máximo 0,70
#:
#: 0,72 cai nessa lacuna. Nenhuma resposta limpa é apanhada por engano.
LIMIAR_VERSO = 0.72

#: Fracção de versos copiados acima da qual a resposta é rejeitada.
#:
#: Nos dados de calibração, 0,0 e 0,10 dão o mesmo resultado (5 de 24), logo a
#: regra efectiva é **«qualquer verso copiado dispara uma repetição»**. Mantém-se
#: como fracção para permitir tolerância mais tarde, se se justificar.
#:
#: Taxa de repetição e custo médio medidos (28 s por geração):
#:
#:     0,10 -> 21% -> 33,8 s      0,20 -> 12% -> 31,5 s
#:     0,40 ->  8% -> 30,3 s
#:
#: Escolhido 0,10: os casos entre 0,10 e 0,20 são cópias literais de versos
#: distintivos («Se às vezes falo nela como num companheiro»), e 33,8 s continua
#: dentro do limite de 45 s. Ser estrito é barato aqui.
LIMIAR_FRACAO = 0.10

#: Versos com menos de 3 palavras são ignorados: «E mais nada.» coincide por
#: acidente e não é plágio.
MIN_PALAVRAS = 3

_RE_PONT = re.compile(r"[^\w\s]")
_RE_ESP = re.compile(r"\s+")


def _norm(t: str) -> str:
    return _RE_ESP.sub(" ", _RE_PONT.sub(" ", t.lower())).strip()


def _versos(texto: str) -> list[str]:
    return [l.strip() for l in texto.split("\n")
            if len(l.strip().split()) >= MIN_PALAVRAS]


@dataclass(frozen=True)
class VersoCopiado:
    verso: str
    similaridade: float
    origem: str          # verso do contexto a que corresponde
    poema: str           # id do poema de onde vem


@dataclass(frozen=True)
class Analise:
    fracao_copiada: float
    n_versos: int
    copiados: tuple[VersoCopiado, ...]
    max_similaridade: float

    @property
    def plagiou(self) -> bool:
        return self.fracao_copiada > LIMIAR_FRACAO

    def resumo(self) -> str:
        if not self.copiados:
            return "sem versos copiados"
        return (f"{len(self.copiados)}/{self.n_versos} versos copiados "
                f"({self.fracao_copiada:.0%}), máximo {self.max_similaridade:.2f}")


def analisar(saida: str, contexto: Sequence[Chunk],
             limiar_verso: float = LIMIAR_VERSO) -> Analise:
    versos_saida = _versos(saida)
    if not versos_saida:
        return Analise(0.0, 0, (), 0.0)

    # (verso normalizado, verso original, id do poema)
    fonte: list[tuple[str, str, str]] = []
    for c in contexto:
        for v in _versos(c.text):
            fonte.append((_norm(v), v, c.poem_id))
    if not fonte:
        return Analise(0.0, len(versos_saida), (), 0.0)

    normalizados = [f[0] for f in fonte]
    copiados: list[VersoCopiado] = []
    maximo = 0.0
    for v in versos_saida:
        vn = _norm(v)
        melhor, melhor_sim = None, 0.0
        for i, fn in enumerate(normalizados):
            s = difflib.SequenceMatcher(None, vn, fn).ratio()
            if s > melhor_sim:
                melhor_sim, melhor = s, i
        maximo = max(maximo, melhor_sim)
        if melhor_sim >= limiar_verso and melhor is not None:
            copiados.append(VersoCopiado(v, round(melhor_sim, 3),
                                         fonte[melhor][1], fonte[melhor][2]))

    return Analise(
        fracao_copiada=len(copiados) / len(versos_saida),
        n_versos=len(versos_saida),
        copiados=tuple(copiados),
        max_similaridade=round(maximo, 3),
    )


#: Reforço a juntar ao prompt quando a primeira tentativa plagiou.
#: Corretivo e não preventivo: refere-se a uma tentativa concreta, logo não pode
#: viver no prefixo em cache como a regra de `voices.REGRAS_NAO_COPIAR`.
REFORCO = """

ATENÇÃO: na tentativa anterior copiaste versos dos poemas que te foram dados.
Os poemas são para tu reconheceres o teu registo, não para repetires. Escreve um
poema **novo**: outras imagens, outras palavras, outro arranque. Não reutilizes
nenhum verso nem o reescrevas trocando uma palavra."""


REFORCO_EN = """

ATTENTION: in your previous attempt you copied lines from the poems you were
given. The poems are there for you to recognise your own register, not to
repeat. Write a **new** poem: other images, other words, another opening. Do not
reuse any line, nor rewrite one by changing a word."""
