"""Reordenação por cross-encoder.

## A decisão, e o que a sustenta

**`bge-reranker-v2-m3`, 8 candidatos, truncados a 120 tokens: +0,090 de nDCG@5
por 2,57 s.** Ligado por escolha (`--rerank`), não por omissão.

A Fase 3 mediu isto e não conseguiu decidir, porque o mesmo reranker dava
−0,048, +0,001 ou +0,074 conforme o gabarito — um poema não julgado conta 0, e
o pool crescia com cada sistema testado. A Fase 3B **fechou o pool**: julgados
os 142 candidatos que faltavam, o top-20 do denso está coberto por inteiro, e
nenhum documento que este reranker promova pode contar 0 por falta de
julgamento. Gabarito: 433 julgamentos, 125 de nota 2.

| | nDCG@5 | Δ | IC95% do Δ | sinais | latência |
|---|---|---|---|---|---|
| denso | 0,606 | — | — | — | — |
| **n=8 trunc120** | **0,696** | **+0,090** | [+0,005, +0,171] | **+16/−4** (p=0,012) | **2,57 s** |
| n=12 trunc120 | 0,710 | +0,103 | [+0,020, +0,185] | +15/−5 (p=0,041) | 3,71 s |
| n=20 trunc80 | 0,730 | +0,124 | [+0,027, +0,218] | +15/−5 (p=0,041) | 4,66 s |
| n=20 trunc120 | 0,733 | +0,127 | [+0,031, +0,221] | +14/−5 (p=0,064) | 8,43 s |
| oráculo@20 | 0,980 | +0,374 | — | — | — |

### Por que a mais barata, e não a melhor

**Nenhuma destas configurações se distingue das outras.** Emparelhado, `n=20
trunc80 − n=8 trunc120` dá +0,033 com IC95% [−0,017, +0,081] e 12/−5 no teste
de sinais (p=0,14). Escolher a de cima por mais 0,033 que a medição não
distingue de zero, pagando mais 2 s, seria o erro que a Fase 2 evitou ao
rejeitar +0,004 **por ser ruído a n=20**.

A n=8 é também a que tem o sinal mais forte (16 de 20 perguntas melhoram) e a
mais barata. Não há troca a fazer.

### O custo: 2,6 s por pergunta, e ~4,8 s na primeira

Os 2,57 s do banco são o caso **quente** — descartei uma chamada de aquecimento
e medi da 2.ª em diante. A correr o CLI: **4,8 s** na primeira reordenação, 2,7
e 2,5 s nas seguintes.

**Tentei eliminar o custo único com um aquecimento, e não funciona.** Em
isolamento funciona — aquecido, a 1.ª reordenação custa 2,56 s em vez de 4,77 s.
Mas o processo real tem o encoder e5 carregado antes, e aí o aquecimento deixa
de valer:

| | 1.ª reordenação | seguintes |
|---|---|---|
| isolado, sem aquecer | 4,77 s | 2,5 s |
| isolado, aquecido | **2,56 s** | 2,5 s |
| **com o e5 carregado antes, aquecido** | **4,56 s** | 2,5 s |
| no CLI (tem o e5 carregado) | 4,8 s | 2,5 s |

Duas tentativas minhas de explicar isto falharam — primeiro aqueci com um par
de duas palavras e atribuí a falha à forma do lote; depois aqueci com a forma
real, continuou a falhar, e atribuí-o a contenção com o Ollama. A terceira
medição mostra que é a presença do e5 em memória, e **nenhuma das duas
primeiras explicações era verdade**.

O aquecimento foi **removido**: custava ~4 s de arranque e não tirava os 2,3 s
da primeira pergunta. O custo único fica anunciado em vez de escondido.

### O que isto não é

Os +0,090 capturam **24% dos 0,374** que o oráculo@20 mostra estarem lá. O
limite inferior do IC95% é +0,005, logo a magnitude é incerta; o que está
estabelecido é o **sinal**, por 16 de 20 perguntas.

E o `apt@3` fica em 95%, como ficou em todas as medições desde a Fase 2 — este
reranker muda **qual** das respostas certas aparece primeiro, não **se** aparece.

## O que a Fase 3 Passo 1 mediu

| reranker | params | 3100 tokens | tokens/s |
|---|---|---|---|
| `mmarco-mMiniLMv2-L12-H384-v1` | ~120M | **1,83 s** | 1694 |
| `bge-reranker-base` | 278M | 5,89 s | 526 |
| `bge-reranker-v2-m3` | 568M | **34,59 s** | 90 |

19x entre o mais pequeno e o maior, com 4,7x de diferença em parâmetros: a razão
é a dimensão oculta (384 contra 1024) e o custo das camadas densas escalar com o
quadrado dela.

## A expectativa, calibrada pela Fase 2

A fusão híbrida falhou por um tecto medido: o denso leva 40 documentos de nota 2
no top-5 somado de 20 perguntas, a fusão leva 39 — **trocar respostas boas por
outras respostas boas não melhora o nDCG**, porque há mediana de 3 respostas
certas por pergunta e o top-5 só leva cinco.

O mesmo tecto aplica-se aqui. Reordenar vai mexer em **quais** respostas certas
aparecem, não em **quantas**.
"""
from __future__ import annotations

from typing import Sequence

from ..corpus.models import Chunk

MINILM = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
BGE_BASE = "BAAI/bge-reranker-base"
BGE_M3 = "BAAI/bge-reranker-v2-m3"

#: O `MINILM` era o padrão quando a latência parecia ser o constrangimento. É
#: mau em poesia portuguesa e está medido: +0,018, e dada «o que vês numa
#: árvore?» põe o poema das árvores em último. Fica como controlo negativo.
PADRAO = BGE_M3

#: Candidatos a reordenar. 8 é a escolha medida — ver o cabeçalho.
N_RERANK = 8

#: Truncar **melhora** a qualidade, não só a velocidade, e está reproduzido em
#: três truncagens e dois modelos: a n=20, 120 tokens dá +0,127 e 256 dá menos.
#: A abertura do chunk carrega o tema; a cauda acrescenta ruído ao cross-encoder.
TRUNCAR_TOKENS = 120


def padrao() -> "Reranker":
    """O reranker na configuração que a Fase 3B mediu e escolheu."""
    return Reranker(PADRAO, truncar_tokens=TRUNCAR_TOKENS)


class Reranker:
    def __init__(self, modelo: str = PADRAO, max_length: int = 512,
                 truncar_tokens: int | None = None):
        from sentence_transformers import CrossEncoder
        self._ce = CrossEncoder(modelo, max_length=max_length)
        self.modelo = modelo
        self.truncar_tokens = truncar_tokens
        self._tok = None

    def _truncar(self, texto: str) -> str:
        if self.truncar_tokens is None:
            return texto
        if self._tok is None:
            from ..tokens import _tokenizador, ENCODER
            self._tok = _tokenizador(ENCODER)
        ids = self._tok(texto, add_special_tokens=False).input_ids
        if len(ids) <= self.truncar_tokens:
            return texto
        return self._tok.decode(ids[:self.truncar_tokens], skip_special_tokens=True)

    def rerank(self, consulta: str, candidatos: Sequence[Chunk],
               top_k: int | None = None) -> list[tuple[Chunk, float]]:
        if not candidatos:
            return []
        pares = [(consulta, self._truncar(c.text)) for c in candidatos]
        pontos = self._ce.predict(pares, show_progress_bar=False)
        ordenados = sorted(zip(candidatos, (float(p) for p in pontos)),
                           key=lambda x: -x[1])
        return ordenados[:top_k] if top_k else ordenados
