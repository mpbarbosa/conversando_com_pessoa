"""Parar o Ollama quando o cliente desiste. Passo 6 da Fase 6, portão **I5**.

## O problema, e a parte dele que o plano previu ao contrário

O §2.3 do [plano](../../docs/FASE-6.md) diz que abortar o `fetch` **não para o
Ollama**: ele continua a decodificar até ao `num_predict` (220), a gastar CPU que
a pergunta seguinte vai querer. Isso confirmou-se, e é o que este módulo
resolve.

O que o plano previu e **não** se confirmou nesta pilha é a consequência: «se não
parar, o trinco do §2.2 fica retido». Medido, com `starlette` 1.7.0 e `uvicorn`
0.54.0: o trinco fica **livre em 1 ms**. O `uvicorn` anuncia `spec_version`
`2.3`, logo o `StreamingResponse` corre o `stream_response` dentro de um grupo de
tarefas e cancela-o quando o `listen_for_disconnect` acorda; o `CancelledError`
cai dentro do `await fila.get()` do `fluxo.py`, o `finally` do gerador de eventos
corre de imediato e liberta o trinco. O `await tarefa` do `fluxo.py` — escrito
para não abandonar a thread — **também** levanta `CancelledError` à entrada,
porque o âmbito do `anyio` já está cancelado, e portanto não espera por nada.

A mentira é pior do que a prevista, não menor. O trinco diz «livre», a pergunta
seguinte é aceite com `200`, e corre **em competição com uma geração órfã** que
ninguém pode ver nem parar — exactamente o modo de falha que o §2.4 descreve
para um `gerar_amostras.py` a correr em paralelo, mas provocado pela própria
interface. E os `prefill_s`/`decode_s` do rodapé vêm do Ollama, que não sabe que
estava a competir.

## A decisão: acordar o leitor pelo socket, e não pelo `close()`

O `fluxo.py` chama `cancelar()` **no laço de eventos**, logo nada aqui pode
bloquear — o portão **I4** exige que o `/api/estado` responda em menos de 100 ms
durante uma geração, e um cancelamento que bloqueasse o laço fazia-o falhar no
pior momento.

Medido com um servidor que escreve uma linha a cada 2 s e um leitor bloqueado a
meio (`exp_close.py`, no bloco de notas desta sessão):

| o que se chama | quando o leitor acorda | quanto bloqueia quem chamou |
|---|---|---|
| só `r.close()` | **+1,002 s** (no fragmento seguinte) | **1,002 s** |
| `sock.shutdown(SHUT_RDWR)` e depois `r.close()` | +1 ms, com `ChunkedEncodingError` | 1 ms |

`r.close()` sozinho não acorda ninguém: põe `_fp` a `None` e o leitor só
descobre no `read` seguinte — e **a própria chamada** fica retida até lá. O
`shutdown` do socket é o que acorda um `recv` bloqueado, é instantâneo, e é
também o que diz ao Ollama que o cliente desapareceu.

⚠️ `r.raw._connection.sock` é interno do `urllib3` (2.8.0). É o preço de não
tocar no `src/generation/ollama.py`, que é o caminho que as Fases 0 a 5Y
mediram; o `_socket_de` abaixo falha em silêncio se a estrutura mudar, e o
`interromper` continua a fechar a resposta numa thread própria — mais lento, mas
não bloqueia o laço e não deixa de cancelar.

## Porque é uma subclasse, e não uma alteração ao gerador

`gerar_em_fluxo` consome o `requests.Response` dentro do seu próprio quadro: de
fora não há como lhe chegar. O sítio onde a resposta é visível é o `_post`, e é
esse que esta subclasse intercepta — uma atribuição sob trava, zero chamadas
HTTP acrescentadas, zero linhas mudadas no ficheiro medido. É a mesma decisão
que o §2.4 tomou para a sentinela: «pô-lo lá era o sítio arquitectonicamente
certo e a decisão errada».

## O que isto NÃO cancela, e é honesto dizê-lo

Só o fluxo. As três esperas que ficam de fora, por ordem de custo:

1. `garantir_pipeline` — corpus (~40 s) e índice (até ~6,4 min) na 1.ª pergunta.
   Corre em `asyncio.to_thread` e não fala com o Ollama: não há socket para
   fechar.
2. o roteador em `/auto` (~20 s a frio) — é `gerar`, **sem** fluxo. Com
   `stream=False` o `requests` já descarregou o corpo inteiro antes de o `_post`
   devolver, logo não existe nenhuma resposta aberta no momento em que o
   cancelamento chega. Cancelá-lo obrigava a mexer no caminho medido.
3. o reranker na 1.ª vez (~4,8 s), que é CPU local.

O botão da página diz «cancelar» e cancela o que pode. A interface não promete
mais do que isto — é a mesma regra do §4.1: um estado que avança com números,
nunca um indicador a rodar a fingir controlo.
"""
from __future__ import annotations

import contextlib
import socket
import threading

from ..generation.ollama import OllamaGenerator


def _socket_de(resposta) -> socket.socket | None:
    """O socket por baixo de um `requests.Response`, ou `None`.

    Três `getattr` em cadeia e uma verificação de tipo, porque isto é estrutura
    interna do `urllib3` e um `AttributeError` aqui tirava do ar uma geração
    por causa do cancelamento de outra.
    """
    bruto = getattr(resposta, "raw", None)
    ligacao = getattr(bruto, "_connection", None)
    meia = getattr(ligacao, "sock", None)
    return meia if isinstance(meia, socket.socket) else None


def _fechar_calado(resposta) -> None:
    """`r.close()` numa thread. Pode bloquear ~um intervalo entre fragmentos."""
    with contextlib.suppress(Exception):
        resposta.close()


def interromper(resposta) -> bool:
    """Acorda quem está bloqueado a ler `resposta` e diz ao Ollama que acabou.

    Devolve se o socket foi encontrado e fechado — isto é, se o leitor acorda
    **já**. A `False` o cancelamento ainda acontece, pela thread do
    `_fechar_calado`, mas só no fragmento seguinte.

    Nunca bloqueia: é chamada do laço de eventos.
    """
    meia = _socket_de(resposta)
    acordou = False
    if meia is not None:
        try:
            meia.shutdown(socket.SHUT_RDWR)
            acordou = True
        except OSError:
            # Já fechado, ou nunca ligado. Não é erro: é o estado que se queria.
            pass
    threading.Thread(target=_fechar_calado, args=(resposta,), daemon=True,
                     name="fechar-resposta-ollama").start()
    return acordou


class GeradorCancelavel(OllamaGenerator):
    """`OllamaGenerator` que se deixa interromper a meio de um fluxo.

    Acrescenta ao caminho medido **uma atribuição sob trava por pedido HTTP em
    fluxo**, e nada mais: nem um cabeçalho, nem uma opção, nem uma chamada.

    A trava é de threads (`threading.Lock`) e não do `asyncio`: o `_post` corre
    na thread de trabalho do `fluxo.py` e o `cancelar` corre no laço de eventos.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._trava = threading.Lock()
        #: A resposta em fluxo aberta agora, ou `None`.
        self._aberta = None
        #: Levantado pelo `cancelar`, baixado pelo `preparar`. Existe por causa
        #: da repetição: ~21% das respostas são rejeitadas e o pipeline chama
        #: `gerar_em_fluxo` outra vez. Um cancelamento que chegue entre as duas
        #: tentativas não tem resposta nenhuma para fechar — e sem esta marca a
        #: tentativa seguinte abria um fluxo novo que ninguém ia parar.
        self._desistido = False

    def _post(self, corpo: dict, fluxo: bool):
        r = super()._post(corpo, fluxo)
        if not fluxo:
            # `stream=False`: o corpo já veio todo e o socket já voltou à
            # reserva. Não há nada aberto para fechar, e guardá-lo era guardar
            # uma promessa falsa de que o roteador se cancela.
            return r
        with self._trava:
            self._aberta = r
            desistido = self._desistido
        if desistido:
            interromper(r)
        return r

    def preparar(self) -> None:
        """Desarma o cancelamento anterior. Chamado antes de cada geração.

        O trinco do §2.2 garante uma geração de cada vez, logo não há aqui
        nenhuma corrida com um fluxo vivo: quando isto corre, o anterior ou
        acabou ou foi cancelado.
        """
        with self._trava:
            self._aberta = None
            self._desistido = False

    def cancelar(self) -> bool:
        """Fecha o fluxo aberto. Devolve se havia um para fechar.

        `False` não é falha: é «o cliente desistiu enquanto se carregava o
        corpus», ou entre duas tentativas. Nesse caso fica a marca, e é o
        `_post` da tentativa seguinte que a cumpre.
        """
        with self._trava:
            r, self._aberta = self._aberta, None
            self._desistido = True
        if r is None:
            return False
        interromper(r)
        return True
