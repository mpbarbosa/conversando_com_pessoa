"""Um gerador bloqueante visto de dentro do laço de eventos.

## O problema, em números medidos

`Pipeline.responder_em_fluxo` é um gerador **síncrono**: faz um produto
matriz-vector em `numpy` (2290 × 768, 5,57 ms medidos na Fase 3) e depois lê um
`requests.post(stream=True)` que leva **~30 s** a terminar, dos quais **19 s**
são silêncio de prefill (Fase 1 Passo 5).

Posto directamente num `async def`, esse laço `for` não devolve o controlo ao
laço de eventos entre fragmentos. Consequência: o `GET /api/estado` fica em fila
atrás da geração — e o `/api/estado` é **o único canal** que a interface tem
para dizer «estou viva» nesses 19 s (§4.1–4.2 do [plano](../../docs/FASE-6.md)).
É isso que o portão **I4** mede: durante uma geração, o estado responde em menos
de 100 ms, em 10 de 10 tentativas.

## A decisão: uma thread de trabalho e uma fila

O gerador corre em `asyncio.to_thread` e os itens atravessam para o laço por uma
`asyncio.Queue`, que **não é segura entre threads** — daí cada entrega passar
por `loop.call_soon_threadsafe`. É o padrão inteiro, e cabe nesta página.

A fila é **sem limite**, de propósito. Com limite, a thread teria de esperar que
o consumidor a lesse, e `Queue.put` bloqueante numa thread de trabalho é um
`await` escondido no sítio errado. Sem limite, o custo é a memória dos
fragmentos ainda não lidos — para uma resposta de ~220 tokens, nada.

## A excepção viaja na fila, e isso é deliberado

Se o gerador levantar, o erro entra na fila **na posição em que ocorreu**: os
fragmentos emitidos antes da falha chegam ao cliente antes dela. O contrário —
guardar o erro à parte e levantá-lo no fim — trocava a ordem dos eventos e
mentia sobre quando a geração parou.

## Cancelar: `asyncio.to_thread` não se cancela, logo avisa-se o gerador

Se o consumidor desistir — e no navegador desistir é um `AbortController` —, a
thread não se interrompe: continua até o gerador terminar, porque o Ollama
continua a decodificar até ao `num_predict`. É o §2.3 do plano, e confirmou-se.

O que **não** se confirmou é o resto da previsão («o trinco fica retido»). Com
`starlette` 1.7.0 e `uvicorn` 0.54.0 o `CancelledError` cai dentro do
`await fila.get()` abaixo, o `finally` corre de imediato, e o `await tarefa`
levanta `CancelledError` à entrada porque o âmbito do `anyio` já está cancelado:
**não espera nada**. Medido, com o trinco livre em 1 ms. Logo a thread órfã não
tranca a porta — passa a competir pelo Ollama com a pergunta seguinte, que é a
mentira do §2.4 provocada pela própria interface.

Por isso o `finally` não se contenta com esperar: **avisa**. O `ao_desistir`
corre antes do `await`, é síncrono, e nunca bloqueia (ver `cancelar.py`, onde a
diferença entre `shutdown` e `close` está medida). Fechada a resposta do
`requests`, o leitor acorda em ~1 ms, a thread morre com `ChunkedEncodingError`
e o Ollama deixa de decodificar. Portão **I5**.

O `await tarefa` fica, porque continua a valer no caminho em que o consumidor
sai sem cancelamento do laço — um `break` ou uma excepção no corpo do `async
for`: aí espera-se de facto pela thread, e uma thread a escrever numa fila que
ninguém lê é uma fuga.
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable, Iterator
from typing import Any

#: Sentinela de fim. Um objecto próprio, e não `None`: `None` é um valor que um
#: gerador pode legitimamente emitir, e confundi-los truncava o fluxo em
#: silêncio.
_FIM = object()


async def em_fluxo(fabrica: Callable[[], Iterator[Any]],
                   ao_desistir: Callable[[], Any] | None = None,
                   ) -> AsyncIterator[Any]:
    """Corre `fabrica()` numa thread e emite o que ela emitir, item a item.

    Recebe uma **fábrica** e não um iterador já criado porque criar o gerador é
    de graça mas o primeiro `next` não é: é lá que a recuperação e o `montar`
    acontecem. A fábrica garante que nada do gerador corre no laço de eventos.

    `ao_desistir` é chamado — **síncrono, no laço** — se o consumidor sair antes
    de a thread acabar. É o único sítio do servidor onde se sabe que o cliente
    desistiu, e é a diferença entre abortar o `fetch` e parar o Ollama (§2.3).
    Tem de ser barato: ver o `cancelar.py`.
    """
    laco = asyncio.get_running_loop()
    fila: asyncio.Queue = asyncio.Queue()

    def trabalhar() -> None:
        """Na thread. Nunca levanta: a excepção vai na fila, em ordem."""
        try:
            for item in fabrica():
                laco.call_soon_threadsafe(fila.put_nowait, item)
        except BaseException as e:  # viaja na fila para o consumidor
            laco.call_soon_threadsafe(fila.put_nowait, e)
        finally:
            laco.call_soon_threadsafe(fila.put_nowait, _FIM)

    tarefa = asyncio.create_task(asyncio.to_thread(trabalhar))
    try:
        while True:
            item = await fila.get()
            if item is _FIM:
                return
            if isinstance(item, BaseException):
                raise item
            yield item
    finally:
        # `tarefa.done()` é o que distingue «o gerador acabou» de «o consumidor
        # desistiu»: só no segundo caso há o que cancelar. Avisar primeiro e
        # esperar depois é deliberado — invertido, o `await` levantava
        # `CancelledError` (o âmbito do `anyio` já está cancelado) e o aviso
        # nunca chegava a sair.
        if not tarefa.done() and ao_desistir is not None:
            ao_desistir()
        await tarefa
