"""Domínio → JSON. Uma função por tipo, e num ficheiro só.

## Porque não há modelos `pydantic`

`Turno`, `Tentativa`, `Resposta`, `Veredicto`, `Analise`, `Chunk` e `Persona`
são `@dataclass(frozen=True)` e são a fronteira do sistema. Declará-los outra
vez em `pydantic` criava **duas definições da mesma coisa**, e a segunda
derivaria da primeira em silêncio no dia em que um campo mudasse — que é o modo
de falha que o manifesto do índice existe para impedir: «um índice velho
carregado por engano não dá erro: dá respostas erradas»
(`src/retrieval/index.py`).

Em vez disso, este ficheiro. O formato do fio lê-se de uma vez, e o
`OMITIDOS` abaixo é a declaração do que **deliberadamente** não vai — comparada
com `dataclasses.fields()` por `tests/test_serial.py`, que falha quando o
domínio ganha um campo que ninguém decidiu.

## Duas decisões que não são de formato

**O corpo dos poemas não vai ao fio.** `Chunk.text` e `Chunk.indexed_text` são
verso de Pessoa, e `VersoCopiado.origem` é um verso real do contexto. Uma
resposta leva 6 chunks; serializá-los por inteiro mandava seis poemas ao
navegador em cada pergunta, quando o que a interface mostra são **fichas com
ids** (§4.7 do plano) e o corpo só a pedido, pelo `GET /api/poema/{id}` do
passo 9. A omissão é a opção segura, e é a **omissão por omissão**: quem quiser
o corpo tem de o ir pedir a um sítio que diz que o está a servir.

**Os campos derivados vão ao fio, calculados aqui.** `aprovado`, `plagiou`,
`decidiu`, `total_s` e `decode_tps` são propriedades do domínio e podiam ser
recalculadas em JavaScript a partir dos campos crus. **Não devem.** `aprovado` é
«veredicto limpo, sem plágio e não truncado» — uma regra que a Fase 5R corrigiu
e que decide se o pipeline repete. Recalculá-la no cliente era pôr uma segunda
política de decisão no navegador, e o §0 do plano existe para isso não acontecer.

## O que este ficheiro não faz

**Não arredonda.** `recuperacao_ms` vai como veio. Arredondar aqui era tomar
uma decisão de apresentação na camada errada; o CLI formata com `:.1f` no
rodapé e a interface faz o mesmo. E há motivo para não sugerir precisão que não
existe — o `CONTROLO.md` §5 registou *throttling* térmico até 101 °C, «latências
com precisão menor que as casas decimais sugerem» —, mas o sítio de o resolver é
quem mostra, não quem transporta.
"""
from __future__ import annotations

from typing import Any

from ..corpus.models import Chunk, Lang, Poem, Voice
from ..generation.base import Resposta
from ..guard import Veredicto
from ..lexico import Suspeita
from ..pipeline import Tentativa, Turno
from ..plagio import Analise, VersoCopiado
from ..roteador import Proposta
from ..voices import Persona

#: Por tipo, os campos que **deliberadamente** não vão ao fio, com o motivo.
#:
#: `tests/test_serial.py` compara isto com `dataclasses.fields()`: um campo novo
#: no domínio que não esteja serializado nem aqui declarado **falha o teste**. É
#: o portão do passo 2, e é a razão de esta tabela existir em vez de um
#: comentário.
OMITIDOS: dict[type, dict[str, str]] = {
    Chunk: {
        "text": "corpo de poema — não vai ao fio; ver o cabeçalho e §3.3",
        "indexed_text": "idem, e ainda com autor e título à cabeça",
    },
    VersoCopiado: {
        "origem": "é um verso real do contexto, logo corpo de poema",
    },
    Poem: {
        "stanzas": "derivável de `body`, e duplicava-o no fio",
    },
    Tentativa: {
        "usados": "as fontes de uma tentativa vão no `Turno`, não repetidas aqui",
    },
    Turno: {
        "recuperados": "vão como `fontes`, com `papel`, junto dos `usados`",
        "usados": "idem",
    },
    Persona: {
        "poetica": "é o texto do `system` prompt; a interface mostra o nome",
        "forma": "idem",
    },
}


def voz(v: Voice) -> str:
    return v.value


def idioma(ling: Lang) -> str:
    return ling.value


def chunk(c: Chunk) -> dict[str, Any]:
    """Referência a um chunk, **sem o corpo**. Ver o cabeçalho."""
    return {
        "poem_id": c.poem_id,
        "chunk_ix": c.chunk_ix,
        "voz": voz(c.voice),
        "idioma": idioma(c.language),
        "n_palavras": c.n_words,
    }


def fonte(c: Chunk, papel: str) -> dict[str, Any]:
    """Um chunk no papel que teve neste turno: `recuperado` ou `usado`.

    A distinção é informativa e não é redundante: `montar` corta o contexto
    quando o orçamento de tokens acaba, logo há poemas que a recuperação trouxe
    e que nunca entraram no prompt.
    """
    return chunk(c) | {"papel": papel}


def poema(p: Poem) -> dict[str, Any]:
    """O poema **com** corpo. Só o `GET /api/poema/{id}` do passo 9 chama isto.

    Está neste ficheiro para que o formato do fio viva todo num sítio, mas é o
    único serializador que leva verso de Pessoa — e o portão **I7** é o que
    mantém a rota que o usa fechada a `127.0.0.1`.
    """
    return {
        "id": p.id,
        "autor": p.author,
        "voz": voz(p.voice),
        "titulo": p.title,
        "corpo": p.body,
        "idioma": idioma(p.language),
        "n_palavras": p.n_words,
        "duplicado_de": p.duplicate_of,
    }


def resposta(r: Resposta) -> dict[str, Any]:
    return {
        "texto": r.texto,
        "prefill_s": r.prefill_s,
        "decode_s": r.decode_s,
        "prefill_tokens": r.prefill_tokens,
        "decode_tokens": r.decode_tokens,
        "truncada": r.truncada,
        # Derivados: ver o cabeçalho.
        "total_s": r.total_s,
        "decode_tps": r.decode_tps,
    }


def veredicto(v: Veredicto) -> dict[str, Any]:
    """O veredicto da guarda.

    `suspeitas` e `gramatica` são canais próprios e **não reprovam** o turno,
    por medição (ver `guard.py`). Vão ao fio porque o rodapé mostra-os: as
    palavras que nem o corpus nem o dicionário conhecem, e as construções que a
    persona proíbe.
    """
    return {
        "ok": v.ok,
        "motivos": list(v.motivos),
        "texto": v.texto,
        "suspeitas": [suspeita(s) for s in v.suspeitas],
        "gramatica": list(v.gramatica),
    }


def suspeita(x: Suspeita) -> dict[str, Any]:
    """Palavra que nem o corpus nem o dicionário conhecem, e o verso dela.

    O `verso` vai ao fio — é texto **gerado**, não verso de Pessoa, e já está no
    ecrã. É o que permite marcar a palavra em contexto em vez de a listar solta,
    que é o que o terminal tinha de fazer.
    """
    return {"palavra": x.palavra, "verso": x.verso}


def verso_copiado(x: VersoCopiado) -> dict[str, Any]:
    """O verso **gerado** que copiou, e de que poema. Sem o verso original."""
    return {
        "verso": x.verso,
        "similaridade": x.similaridade,
        "poema": x.poema,
    }


def analise(a: Analise) -> dict[str, Any]:
    return {
        "fracao_copiada": a.fracao_copiada,
        "n_versos": a.n_versos,
        "copiados": [verso_copiado(x) for x in a.copiados],
        "max_similaridade": a.max_similaridade,
        "plagiou": a.plagiou,
        "resumo": a.resumo(),
    }


def tentativa(t: Tentativa) -> dict[str, Any]:
    """Uma tentativa, como ela **foi** antes de o sistema a corrigir.

    Vai ao fio inteira porque a interface mostra a tentativa rejeitada no lugar,
    recolhida e com o motivo (§4.4 do plano), em vez de a substituir. E porque a
    [Fase 5Y](../../docs/FASE-5Y-RELATORIO.md) mostrou o que custa guardar só a
    última.
    """
    return {
        "n": t.n,
        "texto": t.texto,
        "resposta": resposta(t.resposta),
        "veredicto": veredicto(t.veredicto),
        "plagio": analise(t.plagio),
    }


def turno(t: Turno) -> dict[str, Any]:
    return {
        "pergunta": t.pergunta,
        "voz": voz(t.voz),
        "idioma": idioma(t.idioma),
        "texto": t.texto,
        "aprovado": t.aprovado,
        "tentativas": t.tentativas,
        "recuperacao_ms": t.recuperacao_ms,
        "rerank_ms": t.rerank_ms,
        "resposta": resposta(t.resposta),
        "veredicto": veredicto(t.veredicto),
        "plagio": analise(t.plagio),
        "fontes": ([fonte(c, "usado") for c in t.usados]
                   + [fonte(c, "recuperado") for c in t.recuperados
                      if c not in t.usados]),
        "historico": [tentativa(x) for x in t.historico],
    }


def proposta(p: Proposta) -> dict[str, Any]:
    """O que o roteador propôs.

    `voz: None` é um estado legítimo — «não sei» — e vai ao fio como tal, com
    `decidiu: false`. A interface responde mantendo a voz corrente, porque
    inventar uma era pior.
    """
    return {
        "voz": voz(p.voz) if p.voz is not None else None,
        "bruto": p.bruto,
        "segundos": p.segundos,
        "decidiu": p.decidiu,
    }


def persona(p: Persona) -> dict[str, Any]:
    """A persona, para o `/api/vozes` — sem o texto do `system` prompt."""
    return {
        "voz": voz(p.voz),
        "nome": p.nome,
        "idioma": idioma(p.idioma),
    }
