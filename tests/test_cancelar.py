"""O portão **I5** da Fase 6: cancelar cancela.

A afirmação pré-registada: «após `abort`, a pergunta seguinte arranca em menos
de 2 s e o trinco está livre; o Ollama não está a decodificar».

⚠️ **As duas primeiras cláusulas já passavam antes deste passo, e passavam
vazias.** Medido com `starlette` 1.7.0 e `uvicorn` 0.54.0: ao abortar, o
`CancelledError` cai dentro do `await fila.get()` do `src/web/fluxo.py`, o
`finally` do gerador de eventos corre de imediato e o trinco fica livre em
**1 ms** — com a geração a continuar na thread órfã até ao `num_predict`. O
plano previu o contrário («se não parar, o trinco fica retido», §2.3), e a
realidade é pior do que a previsão: a porta fica aberta, a pergunta seguinte é
aceite com `200`, e corre **em competição** com uma geração que ninguém vê.

Logo a cláusula que **morde** é a terceira. E para a medir é preciso perguntar
ao Ollama, não ao servidor: é o `_OllamaFalso` abaixo, um servidor HTTP que fala
o `/api/chat` em fluxo e **conta** quantos fragmentos escreveu e quando
descobriu que o cliente desapareceu. É a única testemunha que não é parte
interessada.

⚠️ **E tem de ser um `uvicorn` a sério.** O `TestClient` do `starlette` corre a
aplicação até ao fim dentro do portal e devolve o corpo num `io.BytesIO`: não há
«a meio» onde abortar. O `_servidor` do `tests/test_perguntar.py` é o mesmo
instrumento, pela mesma razão — ver a ressalva longa que lá está escrita.

**Verificado por mutação** (como o I4 e a paridade de eventos): sem o
`ao_desistir` no `src/web/fluxo.py`, `test_i5_...nao_esta_a_decodificar` falha
com o Ollama falso a escrever os 220 fragmentos até ao fim. As outras duas
cláusulas continuam a passar — que é precisamente o que esta nota existe para
registar.
"""
from __future__ import annotations

import contextlib
import json
import socket
import threading
import time

import pytest
import requests

from src.corpus.build import load
from src.corpus.models import Voice
from src.generation.base import ErroDeGeracao
from src.generation.ollama import OllamaGenerator
from src.web.app import Servico
from src.web.cancelar import GeradorCancelavel, _socket_de, interromper

from .test_perguntar import _servidor
from .test_pipeline import _pipeline

#: Quantos fragmentos o Ollama falso está disposto a escrever. É o
#: `NUM_PREDICT` real, para a geração órfã durar o que duraria a de verdade.
FRAGMENTOS = 220

#: Intervalo entre fragmentos. O real é ~0,19 s (5,3 tok/s medidos na Fase 6);
#: isto é 200× mais rápido para o teste não levar 42 s, e é o suficiente para o
#: leitor estar bloqueado num `recv` quando o cancelamento chega.
INTERVALO_S = 0.001

#: Verso em vez de palavras soltas: o `responder_em_fluxo` passa o texto pela
#: guarda e pelo detector de plágio, e lixo fazia a tentativa ser rejeitada e
#: começar outra — que é outra coisa a testar, não esta.
VERSO = "Nada sei de mim senão o que vejo\n"


@pytest.fixture(scope="module")
def chunks_caeiro():
    """Oito chunks de Caeiro, como nos outros três ficheiros que o fazem.

    Repetido em vez de partilhado porque é o que o `test_pipeline.py`, o
    `test_grafo.py` e o `test_perguntar.py` já fazem: são três linhas, e um
    `conftest.py` por três linhas acrescentava um sítio onde procurar.
    """
    _, cs = load()
    return [c for c in cs if c.voice is Voice.CAEIRO][:8]


class _OllamaFalso:
    """Um `/api/chat` em fluxo, por sockets, que se deixa medir.

    Não é um `monkeypatch` do `requests` de propósito: o que este teste exerce é
    **um socket a ser fechado por baixo de um leitor bloqueado**, e um duplo em
    memória não tem socket nenhum. Ver a tabela medida em `src/web/cancelar.py`.
    """

    def __init__(self, fragmentos: int = FRAGMENTOS,
                 intervalo_s: float = INTERVALO_S):
        self.fragmentos = fragmentos
        self.intervalo_s = intervalo_s
        #: Fragmentos efectivamente escritos no socket. É o número que diz se a
        #: geração parou: `escritos < fragmentos` é «parou a meio».
        self.escritos = 0
        #: Levantado quando um `sendall` falha, isto é, quando o Ollama falso
        #: descobre que o cliente desapareceu. É o «deixou de decodificar».
        self.desistiu = threading.Event()
        #: Levantado quando chegou ao fim sem ninguém o interromper.
        self.completou = threading.Event()
        self._escuta = socket.socket()
        self._escuta.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._escuta.bind(("127.0.0.1", 0))
        self.porta = self._escuta.getsockname()[1]
        self._escuta.listen(4)
        self._parar = False
        self._thread = threading.Thread(target=self._servir, daemon=True,
                                        name="ollama-falso")

    @property
    def url_base(self) -> str:
        return f"http://127.0.0.1:{self.porta}"

    def _servir(self) -> None:
        while not self._parar:
            try:
                con, _ = self._escuta.accept()
            except OSError:
                return
            threading.Thread(target=self._atender, args=(con,),
                             daemon=True).start()

    def _atender(self, con: socket.socket) -> None:
        with con:
            try:
                con.recv(65536)
                con.sendall(b"HTTP/1.1 200 OK\r\n"
                            b"Content-Type: application/x-ndjson\r\n"
                            b"Transfer-Encoding: chunked\r\n\r\n")
                for i in range(self.fragmentos):
                    ultimo = i == self.fragmentos - 1
                    self._enviar(con, self._linha(ultimo))
                    self.escritos = i + 1
                    if not ultimo:
                        time.sleep(self.intervalo_s)
                self._enviar(con, b"")
                self.completou.set()
            except OSError:
                # O cliente desapareceu. É isto que o portão mede: o Ollama
                # descobriu que não vale a pena continuar a decodificar.
                self.desistiu.set()

    @staticmethod
    def _enviar(con: socket.socket, corpo: bytes) -> None:
        con.sendall(b"%x\r\n" % len(corpo) + corpo + b"\r\n")

    def _linha(self, ultimo: bool) -> bytes:
        d: dict = {"message": {"role": "assistant", "content": VERSO},
                   "done": ultimo}
        if ultimo:
            d |= {"done_reason": "stop", "prompt_eval_duration": 10 ** 9,
                  "eval_duration": 10 ** 9, "prompt_eval_count": 600,
                  "eval_count": self.fragmentos}
        return json.dumps(d).encode("utf-8") + b"\n"

    def __enter__(self) -> _OllamaFalso:
        self._thread.start()
        return self

    def __exit__(self, *_) -> None:
        self._parar = True
        self._escuta.close()


@contextlib.contextmanager
def _montado(chunks, **kw):
    """Ollama falso + `Servico` com o `GeradorCancelavel` real + uvicorn.

    O gerador é o **verdadeiro**: é a classe que o `Servico` usa em produção, e
    um duplo aqui testava o duplo. O que se finge é só o Ollama.
    """
    with _OllamaFalso(**kw) as ollama:
        gerador = GeradorCancelavel(url_base=ollama.url_base)
        pipeline = _pipeline(chunks, gerador)
        pipeline.reranker = None
        servico = Servico(gerador=gerador, pipeline=pipeline)
        with _servidor(servico) as cliente:
            yield ollama, servico, cliente


CORPO = {"pergunta": "o que é a natureza?", "voz": Voice.CAEIRO.value}


def _abortar_a_meio(cliente) -> None:
    """Começa uma geração, espera pelo 1.º fragmento e fecha o socket.

    É o que o `AbortController` do `app.js` faz ao `fetch`: o navegador fecha a
    ligação, o `uvicorn` vê `http.disconnect` e o `starlette` cancela o
    `stream_response`.
    """
    with cliente.stream("POST", "/api/perguntar", json=CORPO) as r:
        assert r.status_code == 200, r.read()
        for linha in r.iter_lines():
            if linha.strip() and json.loads(linha)["tipo"] == "fragmento":
                return
        pytest.fail("a geração acabou antes de haver o que cancelar")


# --- I5, as três cláusulas ------------------------------------------------ #

def test_i5_depois_do_abort_o_ollama_nao_esta_a_decodificar(chunks_caeiro):
    """A cláusula que morde: a geração **parou**, medida no Ollama.

    `escritos` é quantos fragmentos o Ollama falso conseguiu pôr no socket.
    Sem cancelamento escreve os 220 e levanta o `completou`; com cancelamento
    para no primeiro `sendall` que falha e levanta o `desistiu`.
    """
    with _montado(chunks_caeiro) as (ollama, _servico, cliente):
        _abortar_a_meio(cliente)
        assert ollama.desistiu.wait(timeout=2.0), (
            f"o Ollama continuou a decodificar: {ollama.escritos} de "
            f"{ollama.fragmentos} fragmentos escritos, "
            f"completou={ollama.completou.is_set()}")
        assert not ollama.completou.is_set(), (
            "o Ollama chegou ao fim: o cancelamento não chegou a tempo")
        assert ollama.escritos < ollama.fragmentos


def test_i5_o_trinco_fica_livre_e_a_pergunta_seguinte_arranca_em_menos_de_2s(
        chunks_caeiro):
    """As outras duas cláusulas, e a nota de que já passavam. Ver o cabeçalho.

    Ficam aqui porque são o que o portão afirma, e porque **se** uma mudança no
    `starlette` voltar a reter o trinco no cancelamento, é este teste que avisa.
    """
    with _montado(chunks_caeiro) as (_ollama, servico, cliente):
        _abortar_a_meio(cliente)

        limite = time.monotonic() + 2.0
        while servico.trinco.locked() and time.monotonic() < limite:
            time.sleep(0.01)
        assert not servico.trinco.locked(), "o trinco ficou retido"

        t0 = time.monotonic()
        with cliente.stream("POST", "/api/perguntar", json=CORPO) as r:
            assert r.status_code == 200, (
                "a pergunta seguinte foi recusada: o trinco não estava livre")
            for linha in r.iter_lines():
                if linha.strip():
                    break
        arranque = time.monotonic() - t0
        assert arranque < 2.0, f"a pergunta seguinte levou {arranque:.2f} s"


def test_i5_o_fluxo_cancelado_nao_deixa_o_servidor_avariado(chunks_caeiro):
    """Depois de um cancelamento, uma geração inteira continua a funcionar.

    A marca `_desistido` do `GeradorCancelavel` existe para fechar a corrida
    entre duas tentativas; se ficasse levantada, a geração seguinte era
    cancelada à nascença e o fluxo saía vazio. Isto é o teste dessa reposição,
    e é por isso que corre **depois** de um abort e não isolado.
    """
    with _montado(chunks_caeiro, fragmentos=4) as (_o, _s, cliente):
        _abortar_a_meio(cliente)
        with cliente.stream("POST", "/api/perguntar", json=CORPO) as r:
            eventos = [json.loads(ln) for ln in r.iter_lines() if ln.strip()]
    tipos = [e["tipo"] for e in eventos]
    assert "turno" in tipos, f"a geração seguinte não acabou: {tipos}"
    assert tipos.count("fragmento") >= 1
    assert "erro" not in tipos, [e for e in eventos if e["tipo"] == "erro"]


# --- a asserção de não-regressão, ao nível da classe --------------------- #

def test_a_subclasse_nao_muda_o_pedido_que_vai_ao_ollama():
    """Zero alterações ao caminho que as Fases 0 a 5Y mediram.

    O `GeradorCancelavel` herda o `_corpo` e o `_opcoes` e só intercepta o
    `_post` para guardar a resposta. Se alguém lhe acrescentar um cabeçalho, uma
    opção ou um `num_ctx` «de passagem», os números das sete fases deixam de
    descrever o que o servidor corre — e este teste é o que o impede.

    É o §0 do plano aplicado à única classe desta fase que entra no caminho da
    geração: a interface não decide nada, e isto inclui não afinar o gerador.
    """
    base = OllamaGenerator()
    sub = GeradorCancelavel()
    assert (sub.modelo, sub.url_base, sub.num_thread, sub.timeout) == (
        base.modelo, base.url_base, base.num_thread, base.timeout)
    for fluxo in (True, False):
        for temperatura in (None, 0.0):
            assert sub._corpo("s", "u", 220, fluxo, temperatura) == \
                base._corpo("s", "u", 220, fluxo, temperatura), (
                    f"o corpo divergiu (fluxo={fluxo}, t={temperatura})")
    assert sub.janela_contexto == base.janela_contexto
    # E nenhum método do caminho de geração foi reescrito: só o `_post`.
    for nome in ("gerar", "gerar_em_fluxo", "_corpo", "_opcoes", "_resposta"):
        assert getattr(GeradorCancelavel, nome) is getattr(OllamaGenerator,
                                                           nome), (
            f"a subclasse reescreveu `{nome}`, que está no caminho medido")


# --- o mecanismo, por si ------------------------------------------------- #

def test_o_cancelamento_acorda_um_leitor_bloqueado_e_nao_bloqueia_quem_chama():
    """O `shutdown` do socket, e porque não basta o `r.close()`.

    Medido ao escrever o passo 6, com um servidor a escrever uma linha a cada
    2 s e um leitor a dormir a meio: `r.close()` sozinho só acorda o leitor no
    fragmento seguinte (**+1,002 s**) e **retém quem chamou** o mesmo tempo. O
    `cancelar` corre no laço de eventos, onde o portão I4 exige respostas em
    menos de 100 ms, logo bloquear um segundo não é uma opção.

    Este teste fixa as duas metades: o leitor acorda, e quem cancelou não
    esperou por ele.
    """
    with _OllamaFalso(fragmentos=50, intervalo_s=0.5) as ollama:
        gerador = GeradorCancelavel(url_base=ollama.url_base)
        acabou = threading.Event()

        def ler():
            try:
                for _ in gerador.gerar_em_fluxo("s", "u"):
                    pass
            except BaseException:
                pass
            acabou.set()

        threading.Thread(target=ler, daemon=True).start()
        limite = time.monotonic() + 5
        while gerador._aberta is None and time.monotonic() < limite:
            time.sleep(0.01)
        assert gerador._aberta is not None, "o fluxo não arrancou"
        time.sleep(0.2)                   # o leitor está a dormir num `recv`

        t0 = time.perf_counter()
        assert gerador.cancelar() is True
        chamada_ms = (time.perf_counter() - t0) * 1000

        assert acabou.wait(timeout=2.0), "o leitor não acordou"
        acordar_ms = (time.perf_counter() - t0) * 1000
        assert chamada_ms < 100, (
            f"o `cancelar` bloqueou o laço {chamada_ms:.0f} ms")
        # O intervalo entre fragmentos é 500 ms: acordar em menos de 250 ms só
        # acontece se o `recv` **bloqueado** foi interrompido. Sem o `shutdown`,
        # o leitor só descobre no fragmento seguinte, e isto mede-o.
        assert acordar_ms < 250, (
            f"o leitor só acordou no fragmento seguinte ({acordar_ms:.0f} ms): "
            f"o `shutdown` do socket não aconteceu")


def test_o_socket_do_requests_continua_a_ser_alcancavel():
    """`r.raw._connection.sock` é interno do `urllib3`, logo fixa-se aqui.

    Se uma versão nova do `urllib3` mudar a estrutura, o `_socket_de` devolve
    `None` em silêncio e o cancelamento passa a ser o lento — que é um portão a
    deixar de morder sem ninguém dar por isso. Este teste é o alarme.
    """
    with _OllamaFalso(fragmentos=50, intervalo_s=0.5) as ollama:
        gerador = GeradorCancelavel(url_base=ollama.url_base)
        fluxo = gerador.gerar_em_fluxo("s", "u")
        next(fluxo)                       # abre a resposta e lê o 1.º fragmento
        try:
            assert _socket_de(gerador._aberta) is not None, (
                "o socket deixou de ser alcançável: ver o cabeçalho do "
                "src/web/cancelar.py")
            assert interromper(gerador._aberta) is True
        finally:
            fluxo.close()


def test_um_pedido_sem_fluxo_nao_fica_guardado_como_cancelavel():
    """O roteador é `gerar`, sem fluxo, e não se cancela — e não finge que sim.

    Com `stream=False` o `requests` já descarregou o corpo antes de o `_post`
    devolver: não há resposta aberta. Guardá-la fazia o `cancelar` devolver
    `True` sem cancelar nada, que é a pior das três respostas possíveis.
    """
    with _OllamaFalso(fragmentos=1) as ollama:
        gerador = GeradorCancelavel(url_base=ollama.url_base)
        gerador.gerar("s", "u")
        assert gerador._aberta is None
        assert gerador.cancelar() is False


def test_cancelar_entre_duas_tentativas_apanha_a_tentativa_seguinte():
    """A corrida que a marca `_desistido` fecha.

    ~21% das respostas são rejeitadas e o pipeline chama `gerar_em_fluxo` outra
    vez. Um cancelamento que chegue entre as duas não tem resposta nenhuma para
    fechar — e sem a marca, a tentativa seguinte abria um fluxo que mais ninguém
    ia parar: o cliente já se tinha ido, e o `finally` do `fluxo.py` já tinha
    corrido.
    """
    with _OllamaFalso(fragmentos=50, intervalo_s=0.5) as ollama:
        gerador = GeradorCancelavel(url_base=ollama.url_base)
        assert gerador.cancelar() is False      # nada aberto: fica a marca
        fluxo = gerador.gerar_em_fluxo("s", "u")
        # Qual das duas depende de onde o `shutdown` apanha o leitor, e as duas
        # contam como «interrompida»: a meio do fluxo é `ChunkedEncodingError`
        # (uma `RequestException`); **antes** da 1.ª leitura — que é este caso,
        # porque o `_post` interrompe à nascença — o `iter_lines` acaba limpo e
        # sem a linha `done`, e o `gerar_em_fluxo` levanta `ErroDeGeracao`.
        # Nomeá-las é o que distingue isto de rebentar por outra razão.
        with pytest.raises((ErroDeGeracao, requests.exceptions.RequestException)):
            for _ in fluxo:
                pass
        assert ollama.desistiu.wait(timeout=2.0), (
            "a tentativa seguinte ao cancelamento ficou a decodificar")

        # E o `preparar` desarma: é o que o `POST /api/perguntar` chama depois
        # de tomar o trinco, e sem ele a pergunta seguinte nascia cancelada.
        gerador.preparar()
        assert gerador._desistido is False
