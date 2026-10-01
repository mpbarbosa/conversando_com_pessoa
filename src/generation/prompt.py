"""Montagem do prompt, com orçamento de tokens.

## Duas camadas, por razão medida

O prompt divide-se em **sistema** (persona da voz) e **utilizador** (pergunta e
contexto). A divisão não é estética: medido na Fase 1 Passo 5, com `system`
fixo o llama.cpp reaproveita o cache de KV do prefixo, e os 313 tokens da
persona passam de **13,63 s a 0,91 s** da segunda pergunta em diante — 15x.

Isso inverte a aritmética do orçamento. O que se paga a cada pergunta é a
**parte variável**, não o total. Por isso o orçamento aqui é sobre a mensagem do
utilizador.

É o mesmo mecanismo que invalidou o benchmark da Fase 0, onde tive de o
neutralizar com um nonce para medir prefill honesto. Lá era um defeito de
medição; aqui é o que torna uma persona detalhada acessível.

## A pergunta vem antes do contexto

O tokenizador trunca pela direita. Com o contexto primeiro, um poema longo
empurra a pergunta fora do prompt e o modelo nunca a vê — era o defeito do
`main.py` original. Aqui a pergunta vem primeiro **e** o contexto é ajustado ao
orçamento, logo a truncagem nunca a alcança.

## Contar com o tokenizador certo

Medido: o qwen2.5 conta **17% mais tokens** que o e5 em português (mediana 1,166,
máximo 1,458). Orçamentar o prompt do gerador com o contador do encoder
subestimaria até 46%.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from ..corpus.models import Chunk
from ..voices import Persona

#: Orçamento da mensagem do utilizador (pergunta + contexto), em tokens do
#: gerador. A persona vive no `system` e é paga uma vez por voz.
#:
#: **300, derivado de medição** (ver docs/fase-1/05-RELATORIO-ORCAMENTO.md):
#: a quente o prefill corre a ~16 tok/s e o decode leva ~23 s, logo 300 tokens
#: dão ~18,8 s + 23 s = ~41,8 s, dentro do limite de 45 s fixado na Fase 0.
#: Medido: 168 tokens -> 33,7 s total; 448 tokens -> 53,7 s, fora do limite.
#:
#: Deixa ~243 tokens para contexto, ou 1 a 2 poemas (mediana de um chunk: 126
#: tokens do qwen). É orçamento e não contagem fixa de propósito: um poema curto
#: deixa espaço para um segundo, um longo ocupa tudo, e a latência não varia com
#: o que a recuperação trouxer.
ORCAMENTO_USER = 300

#: Margem para o enquadramento do chat (tags de turno, etc.).
RESERVA = 24

SEPARADOR = "\n\n---\n\n"


@dataclass(frozen=True)
class Prompt:
    system: str
    user: str
    chunks_usados: tuple[Chunk, ...]
    tokens_system: int
    tokens_user: int

    @property
    def tokens_variaveis(self) -> int:
        """O que se paga a cada pergunta, com o sistema em cache."""
        return self.tokens_user


def _cabecalho(pergunta: str, nome: str) -> str:
    return (f"Pergunta: {pergunta}\n\n"
            f"Poemas teus, para terdes presente o registo e as imagens:\n\n")


_RODAPE = "\n\nResponde só com o poema."


def montar(pergunta: str, chunks: Sequence[Chunk], persona: Persona,
           n_tokens: Callable[[str], int],
           orcamento: int = ORCAMENTO_USER,
           reserva: int = RESERVA) -> Prompt:
    """Monta o prompt, cabendo o contexto no que resta do orçamento.

    Os chunks entram pela ordem dada (a da recuperação) e param quando o
    orçamento acaba. Um chunk que não caiba inteiro **não é truncado**: é
    deixado de fora, porque meio poema não é contexto, é ruído.
    """
    system = persona.system_prompt()
    cabecalho = _cabecalho(pergunta, persona.nome)

    fixo = n_tokens(cabecalho) + n_tokens(_RODAPE) + reserva
    disponivel = orcamento - fixo

    usados: list[Chunk] = []
    custo_sep = n_tokens(SEPARADOR)
    for c in chunks:
        texto = c.text.strip()
        if not texto:
            continue
        custo = n_tokens(texto) + (custo_sep if usados else 0)
        if custo > disponivel:
            continue          # não cabe: salta, não trunca
        usados.append(c)
        disponivel -= custo

    corpo = SEPARADOR.join(c.text.strip() for c in usados)
    user = cabecalho + corpo + _RODAPE
    return Prompt(
        system=system, user=user, chunks_usados=tuple(usados),
        tokens_system=n_tokens(system), tokens_user=n_tokens(user),
    )
