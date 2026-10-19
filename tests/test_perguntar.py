"""Os portões I1 e I4 da Fase 6: paridade da API, e o laço que não bloqueia.

**I1 — a API não decide nada.** 20 perguntas fixas, gerador determinista, e o
`Turno` que sai do `POST /api/perguntar` comparado **campo a campo** com o do
laço escrito à mão (`src/pipeline.py`) e com o do grafo (`src/grafo.py`). É o
`tests/test_grafo.py` com um terceiro braço, e existe pela mesma razão: se a
interface divergir, os números medidos nas Fases 0 a 5Y deixam de descrever o
caminho que o utilizador corre. A Fase 5Y mediu o que custa descobrir isso
tarde — de 7% a 40% das células contaminadas, fase a fase.

**I4 — o laço não bloqueia.** Durante uma geração, `GET /api/estado` responde
em menos de 100 ms, em 10 de 10 tentativas. O `/api/estado` é o único canal que
a interface tem para dizer «estou viva» nos 19 s de prefill (§4.1 do plano), e
um `responder_em_fluxo` posto directamente num `async def` calava-o.

⚠️ **O instrumento tem um modo de falha silencioso, e foi observado.** O
`TestClient` só faz fluxo quando é usado **como gestor de contexto**: sem `with`
cria um portal por pedido e consome o corpo inteiro antes de devolver a
resposta. O primeiro rascunho deste ficheiro media I4 contra uma geração **já
acabada** e passava vazio. Daí o `_cliente` abaixo, e daí o portão verificar o
trinco durante a medição: é a diferença entre medir e parecer medir, e o
`CONTROLO.md` §4 já lista defeitos nos próprios instrumentos desta casa.

⚠️ **A comparação é sobre o `Turno` publicado, e não sobre o serializado.** Desde
o passo 2 do [plano do serviço público](../docs/PRODUCAO.md) o fio passa pela
`src/web/retencao.py` — portão **I7′** —, e o CLI e o grafo não passam, porque
não publicam nada. O `_publicado` abaixo aplica a mesma retenção aos três
braços; a sua docstring diz porque é que isso não afrouxa o I1.

⚠️ **Uma divergência conhecida, e que não é desta fase:** o grafo não preenche
`Turno.historico` (`src/grafo.py:209`), que é o campo que a Fase 5Y criou. Logo
o braço do grafo compara-se em todos os campos **menos** esse, e isso está
escrito aqui em vez de escondido numa comparação selectiva sem motivo.
"""
from __future__ import annotations

import ast
import contextlib
import functools
import hashlib
import inspect
import json
import textwrap
import threading
import time

import pytest
from fastapi.testclient import TestClient

from src.corpus.build import load
from src.corpus.models import Lang, Voice
from src.generation.base import Resposta
from src.generation.ollama import MODELO
from src.grafo import PipelineGrafo
from src.pipeline import Turno
from src.web import serial
from src.web.app import Servico, criar_app
from src.web.retencao import linhas_de_corpo, redigir

from .test_pipeline import GeradorFalso, _pipeline

# --- duplos ----------------------------------------------------------------- #

#: Versos neutros, sem nada do corpus, para o gerador determinista compor.
VERSOS = (
    "Não sei o que é saber, e sei que escrevo.",
    "A tarde cai como quem não tem pressa.",
    "Penso em nada e o nada pensa em mim.",
    "Há uma janela aberta para dentro.",
    "O que passou não passa de passar.",
    "Digo o que vejo e vejo o que digo.",
    "Entre a palavra e a coisa cabe o mundo.",
    "Fico quieto e o resto move-se por mim.",
)


class GeradorDeterminista:
    """Mesmo prompt, mesmo texto — e textos diferentes para prompts diferentes.

    O `GeradorFalso` do `test_pipeline.py` devolve **o mesmo** poema a qualquer
    pergunta que não lhe mostre o poema a copiar, e com ele as 20 perguntas do
    portão I1 eram 20 cópias de uma. Este deriva o texto do prompt por `md5`,
    que é determinista entre processos — o `hash()` não é, e dois braços num
    `pytest` diferente deixavam de se poder comparar.

    Expõe também `disponivel`/`modelo_instalado` porque o portão **I4** consulta
    o `/api/estado` durante uma geração, e esse caminho pergunta-lhos.
    """

    def __init__(self, atraso_s: float = 0.0, n_fragmentos: int = 4):
        self.atraso_s = atraso_s
        self.n_fragmentos = n_fragmentos
        self.prompts: list[str] = []
        self.modelo = MODELO
        self.url_base = "http://127.0.0.1:11434"
        self.nome = MODELO

    def disponivel(self) -> bool:
        return True

    def modelo_instalado(self) -> bool:
        return True

    def _texto(self, user: str) -> str:
        self.prompts.append(user)
        d = hashlib.md5(user.encode("utf-8")).digest()
        return "\n".join(VERSOS[(d[i] + i) % len(VERSOS)] for i in range(5))

    def gerar(self, system: str, user: str, **kw) -> Resposta:
        return Resposta(texto=self._texto(user), prefill_s=0.1, decode_s=0.1,
                        prefill_tokens=10, decode_tokens=10)

    def gerar_em_fluxo(self, system: str, user: str, **kw):
        """Parte o texto em pedaços, e **bloqueia** entre eles se lho pedirem.

        O bloqueio é `time.sleep` de propósito: é o que o
        `requests.post(stream=True)` do `OllamaGenerator` faz ao laço de
        eventos se ninguém o puser numa thread, e é isso que o portão I4 mede.
        """
        r = self.gerar(system, user)
        passo = max(1, len(r.texto) // self.n_fragmentos)
        for i in range(0, len(r.texto), passo):
            if self.atraso_s:
                time.sleep(self.atraso_s)
            yield r.texto[i:i + passo]
        yield r


class GeradorComPreambulo(GeradorDeterminista):
    """Começa pelo preâmbulo e pelo eco da pergunta, como foi observado.

    As duas linhas são reais: «Aqui está um poema novo, seguindo as
    instruções:» apareceu à pergunta «qual é o futuro de portugal?», e o eco
    apareceu à «o que vês quando olhas para uma árvore?». Vêm em linhas
    separadas porque é assim que escapavam a uma retenção de uma linha só.
    """

    def __init__(self, pergunta: str, **kw):
        super().__init__(**kw)
        self.pergunta = pergunta

    def _texto(self, user: str) -> str:
        eco = self.pergunta.rstrip("?").strip().capitalize()
        return ("Aqui está um poema novo, seguindo as instruções:\n"
                f"{eco}\n" + super()._texto(user))


# --- andaime ---------------------------------------------------------------- #

PERGUNTAS = (
    "o que é a natureza?",
    "o que vês quando olhas para uma árvore?",
    "qual é o futuro de portugal?",
    "porque é que escreves?",
    "o que é o tédio?",
    "tens medo da morte?",
    "o que é um poente?",
    "para que serve a filosofia?",
    "o que é ser-se português?",
    "gostas de pessoas?",
    "o que fazes de manhã?",
    "o que é a saudade?",
    "acreditas em deus?",
    "o que é o amor?",
    "vale a pena viver?",
    "o que é uma cidade?",
    "o que pensas do progresso?",
    "o que é a solidão?",
    "porque é que o mar é triste?",
    "o que é a verdade?",
)


@pytest.fixture(scope="module")
def chunks_caeiro():
    _, cs = load()
    return [c for c in cs if c.voice is Voice.CAEIRO][:8]


def _servico(pipeline) -> Servico:
    """Um `Servico` com o pipeline **já feito**: nada se carrega nos testes.

    O `_pipeline` do `test_pipeline.py` constrói por `__new__` e não define
    `reranker`; o `/api/estado` lê-o, logo põe-se aqui o que o construtor real
    põe. É andaime do duplo, não comportamento do servidor.
    """
    pipeline.reranker = None
    return Servico(gerador=pipeline.gerador, pipeline=pipeline)


@contextlib.contextmanager
def _cliente(servico: Servico):
    """Um `TestClient`, para tudo **menos** medir concorrência. Ver `_servidor`."""
    with TestClient(criar_app(servico)) as c:
        yield c


@contextlib.contextmanager
def _servidor(servico: Servico):
    """Um uvicorn de verdade, numa thread — porque o `TestClient` não faz fluxo.

    ⚠️ **Isto não é preferência, é o instrumento.** O transporte do `TestClient`
    corre a aplicação até ao fim dentro do portal e só depois devolve a resposta
    (`starlette/testclient.py`: `portal.call(self.app, ...)` e o corpo num
    `io.BytesIO`). O `stream()` dele itera sobre um corpo **já completo**: a
    geração acaba antes da primeira linha chegar.

    Consequência, observada ao escrever este ficheiro: o portão I4 media o
    `/api/estado` contra um servidor **parado** e passava com tempos de 1 ms.
    Um portão que não pode falhar não é um portão — e o `CONTROLO.md` §4 já
    guarda a lição de um instrumento desta casa a reportar 25 625 tok/s.

    Logo os dois testes que dependem de haver uma geração **a correr** falam com
    um servidor a sério, por sockets, como o navegador vai falar.
    """
    import socket

    import httpx
    import uvicorn

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        porta = s.getsockname()[1]

    servidor = uvicorn.Server(uvicorn.Config(
        criar_app(servico), host="127.0.0.1", port=porta, log_level="warning"))
    thread = threading.Thread(target=servidor.run, daemon=True)
    thread.start()
    try:
        limite = time.monotonic() + 10
        while not servidor.started:
            assert time.monotonic() < limite, "o uvicorn não arrancou"
            time.sleep(0.01)
        with httpx.Client(base_url=f"http://127.0.0.1:{porta}",
                          timeout=30.0) as c:
            yield c
    finally:
        servidor.should_exit = True
        thread.join(timeout=10)


def _eventos(pipeline, pergunta: str, voz: Voice = Voice.CAEIRO,
             idioma: Lang = Lang.PT, **opcoes) -> list[dict]:
    """Corre o fluxo até ao fim e devolve os eventos, já desserializados."""
    corpo = {"pergunta": pergunta, "voz": voz.value, "idioma": idioma.value,
             **opcoes}
    with _cliente(_servico(pipeline)) as cliente, \
            cliente.stream("POST", "/api/perguntar", json=corpo) as r:
        assert r.status_code == 200, r.read()
        assert r.headers["content-type"].startswith("application/x-ndjson")
        return [json.loads(ln) for ln in r.iter_lines() if ln.strip()]


def _do_tipo(eventos: list[dict], tipo: str) -> list[dict]:
    return [e for e in eventos if e["tipo"] == tipo]


def _turno_da_api(pipeline, pergunta: str, voz: Voice = Voice.CAEIRO) -> dict:
    """O `turno` do último evento desse tipo: o que a API diz ser a resposta."""
    turnos = _do_tipo(_eventos(pipeline, pergunta, voz), "turno")
    assert turnos, "o fluxo acabou sem nenhum turno"
    return turnos[-1]["turno"]


@functools.cache
def _corpo_retido() -> frozenset[str]:
    """As linhas que a retenção do portão **I7′** não deixa sair pelo fio."""
    _, chunks = load()
    return linhas_de_corpo(chunks)


def _publicado(t: Turno) -> dict:
    """O `Turno` **como a API o publica**: serializado e com a retenção do I7′.

    O portão I1 compara o que o utilizador recebe, e desde o passo 2 do
    [plano do serviço público](../docs/PRODUCAO.md) o que ele recebe passa pela
    `src/web/retencao.py`: um verso de Pessoa à letra não vai ao fio, nem na
    tentativa rejeitada que o §4.4 manda mostrar.

    **Isto não afrouxa o I1, e a distinção é a que o portão afirma.** O `Turno`
    que os três braços produzem continua a ser idêntico campo a campo — a
    interface não decide nada. O que difere é a **publicação**, e o CLI e o
    grafo não têm publicação: correm nesta máquina, para quem já tem o corpus no
    disco. Comparar sem esta função era exigir que a API publicasse o corpus
    para o portão passar. E a função aplica-se **aos dois lados**, logo uma API
    que retivesse mais do que isto continuava a divergir e a falhar.
    """
    return redigir(serial.turno(t), _corpo_retido())[0]


def _turno_do_cli(pipeline, pergunta: str, voz: Voice = Voice.CAEIRO) -> Turno:
    """O caminho do CLI: `responder_em_fluxo`, e o último `Turno` que emite."""
    ultimo = None
    for item in pipeline.responder_em_fluxo(pergunta, voz, Lang.PT):
        if not isinstance(item, str):
            ultimo = item
    assert ultimo is not None
    return ultimo


def _tres_pipelines(chunks, gerador):
    """Três pipelines com geradores **independentes** mas equivalentes.

    Independentes porque os duplos acumulam os prompts que viram; partilhar a
    instância fazia o segundo braço ver o histórico do primeiro — é a mesma
    razão que o `_par` do `test_grafo.py` já documenta.
    """
    return tuple(_pipeline(chunks, gerador()) for _ in range(3))


# --- I1: paridade campo a campo -------------------------------------------- #

def test_i1_a_api_da_o_mesmo_turno_que_o_cli_nas_20_perguntas(chunks_caeiro):
    """O portão. 20 perguntas, e o dicionário do fio igual em **todos** os campos.

    A comparação é sobre `serial.turno(...)` e não sobre os objectos porque é
    isso que o utilizador recebe: um campo que o serializador perdesse passava
    ao lado de uma comparação de `Turno`s.
    """
    for pergunta in PERGUNTAS:
        api, cli, _ = _tres_pipelines(chunks_caeiro, GeradorDeterminista)
        assert _turno_da_api(api, pergunta) == _publicado(
            _turno_do_cli(cli, pergunta)), f"divergiu em «{pergunta}»"


def test_i1_as_20_perguntas_nao_dao_a_mesma_resposta(chunks_caeiro):
    """O portão I1 só vale se as 20 perguntas forem 20 casos.

    Com o `GeradorFalso` eram 20 cópias de uma, porque ele não olha para a
    pergunta. Este teste é o que impede o portão de voltar a ser vazio sem
    ninguém notar.
    """
    textos = set()
    for pergunta in PERGUNTAS:
        api, *_ = _tres_pipelines(chunks_caeiro, GeradorDeterminista)
        textos.add(_turno_da_api(api, pergunta)["texto"])
    assert len(textos) >= 15, f"só {len(textos)} respostas distintas em 20"


def test_i1_a_api_da_o_mesmo_que_o_grafo_nas_20_perguntas(chunks_caeiro):
    """O terceiro braço, em todos os campos menos o `historico`.

    O grafo não preenche `Turno.historico` (`src/grafo.py:209`) — divergência
    anterior a esta fase, declarada no cabeçalho deste ficheiro. Tudo o resto
    tem de bater, incluindo `fontes`, `recuperacao_ms` e os tempos da resposta.
    """
    for pergunta in PERGUNTAS:
        api, _, grf = _tres_pipelines(chunks_caeiro, GeradorDeterminista)
        da_api = _turno_da_api(api, pergunta)
        do_grafo = _publicado(PipelineGrafo.de(grf).responder(
            pergunta, Voice.CAEIRO, Lang.PT))
        del da_api["historico"], do_grafo["historico"]
        assert da_api == do_grafo, f"divergiu em «{pergunta}»"


def test_i1_a_paridade_vale_no_ciclo_de_repeticao(chunks_caeiro):
    """O caso que vale: com plágio na 1.ª tentativa, os três repetem igual.

    É o mesmo argumento do `test_grafo.py`: o ciclo é onde um consumidor
    descuidado quebrava, e o `_repetir_sem` é política medida — tirar do
    contexto o poema de que o modelo copiou resolveu um caso real de duas
    rejeições em ~80 s.
    """
    alvo = chunks_caeiro[0]
    api, cli, grf = _tres_pipelines(chunks_caeiro,
                                    lambda: GeradorFalso(alvo.text))
    do_cli = _turno_do_cli(cli, "o que é a natureza?")
    assert do_cli.tentativas == 2, "o duplo devia ter forçado uma repetição"

    da_api = _turno_da_api(api, "o que é a natureza?")
    assert da_api == _publicado(do_cli)

    # E a retenção do I7′ **morde neste caso**, que é o que impede o
    # `_publicado` de ser um `serial.turno` com mais passos: aqui a tentativa
    # rejeitada é uma cópia à letra do `poem_1005`, e o texto dela sai do fio.
    assert (serial.turno(do_cli)["historico"][0]["texto"]
            != _publicado(do_cli)["historico"][0]["texto"]), (
        "a retenção não tirou nada: o portão deixou de cobrir a redacção")

    do_grafo = _publicado(PipelineGrafo.de(grf).responder(
        "o que é a natureza?", Voice.CAEIRO, Lang.PT))
    copia = dict(da_api)
    del copia["historico"], do_grafo["historico"]
    assert copia == do_grafo


def test_i1_a_tentativa_rejeitada_vai_ao_fio_e_nao_e_substituida(chunks_caeiro):
    """§4.4: a tentativa rejeitada fica à vista, e o fluxo tem de a dar.

    São **dois** eventos `turno` — um por tentativa —, e o primeiro vem com o
    plágio que o reprovou. Sem isto, a interface não tinha como explicar porque
    é que o utilizador esperou 58 s em vez de 30.
    """
    alvo = chunks_caeiro[0]
    api, *_ = _tres_pipelines(chunks_caeiro, lambda: GeradorFalso(alvo.text))
    turnos = _do_tipo(_eventos(api, "o que é a natureza?"), "turno")

    assert len(turnos) == 2
    assert turnos[0]["turno"]["aprovado"] is False
    assert turnos[0]["turno"]["plagio"]["plagiou"] is True
    assert turnos[1]["turno"]["aprovado"] is True
    assert turnos[1]["turno"]["tentativas"] == 2


def test_i1_a_api_constroi_o_pipeline_com_os_mesmos_parametros_do_cli():
    """A única duplicação do passo 4, e o que a torna aceitável.

    `Servico.garantir_pipeline` repete o `_arrancar` do `cli.py` porque o
    `_arrancar` mistura construção com mensagens no terminal, e extraí-lo
    obrigava a mexer no `cli.py`, que esta fase declarou não tocar (§6). O
    risco é divergirem os parâmetros — um `top_k` diferente aqui produzia
    respostas que **nenhuma medição deste repositório descreve**, e o portão I1
    não o apanhava porque injecta o pipeline já feito.

    Logo: as duas chamadas a `Pipeline(...)` têm de ter o mesmo número de
    argumentos posicionais e **nenhum** por nome. Qualquer `top_k=`,
    `reranker=` ou `n_rerank=` num dos lados falha isto. E as duas têm de
    orçamentar com o contador do **gerador**: o qwen conta ~17% mais tokens em
    português, e usar o do encoder subestimava até 46%.
    """
    from src.cli import _arrancar

    def chamada(f) -> tuple[int, list[str | None]]:
        fonte = textwrap.dedent(inspect.getsource(f))
        for no in ast.walk(ast.parse(fonte)):
            if isinstance(no, ast.Call) and getattr(no.func, "id", "") == "Pipeline":
                return len(no.args), [k.arg for k in no.keywords]
        raise AssertionError(f"não há chamada a Pipeline em {f.__qualname__}")

    assert chamada(_arrancar) == chamada(Servico.garantir_pipeline) == (4, [])
    for f in (_arrancar, Servico.garantir_pipeline):
        assert "contador(GERADOR)" in inspect.getsource(f), (
            f"{f.__qualname__} deixou de orçamentar com o contador do gerador")


# --- I2: nada aparece que a guarda remova ---------------------------------- #

def test_i2_o_preambulo_e_o_eco_nao_chegam_ao_fio(chunks_caeiro):
    """O portão I2 sobre o fluxo da API, com as duas linhas observadas.

    Nenhum fragmento antes da 1.ª linha que sobreviva à `limpar_inicio` — e a
    prova de que o que sai é o que a guarda julgou é o texto montado dos
    fragmentos conter o `veredicto.texto`.
    """
    pergunta = "o que vês quando olhas para uma árvore?"
    pipeline = _pipeline(chunks_caeiro, GeradorComPreambulo(pergunta))
    eventos = _eventos(pipeline, pergunta)
    fragmentos = "".join(e["texto"] for e in _do_tipo(eventos, "fragmento"))

    assert fragmentos, "não saiu fragmento nenhum"
    assert "Aqui está um poema novo" not in fragmentos
    assert "O que vês quando olhas para uma árvore" not in fragmentos
    assert _do_tipo(eventos, "turno")[-1]["turno"]["texto"] in fragmentos


def test_i2_a_retencao_usa_a_funcao_do_cli_e_nao_uma_copia(monkeypatch,
                                                           chunks_caeiro):
    """O que o portão I2 realmente afirma: **uma** política de apresentação.

    Troca-se a `limpar_inicio` por um sabotador no módulo onde o `app.py` a
    importou. Se o fluxo sair intacto, há uma segunda implementação em algum
    sítio — e é essa a divergência silenciosa que o passo 1 extraiu a função
    para impedir. Um guarda que não se consegue quebrar não estava a guardar.
    """
    import src.web.app as mod

    monkeypatch.setattr(mod, "limpar_inicio",
                        lambda acumulado, pergunta: ("SABOTADO\n", False))
    pipeline = _pipeline(chunks_caeiro, GeradorDeterminista())
    fragmentos = "".join(
        e["texto"] for e in _do_tipo(
            _eventos(pipeline, "o que é a natureza?"), "fragmento"))
    assert "SABOTADO" in fragmentos, (
        "o fluxo não passa pela `limpar_inicio` do `apresentacao.py`")


# --- I4: o laço não bloqueia ----------------------------------------------- #

def test_i4_o_estado_responde_durante_uma_geracao(chunks_caeiro):
    """O portão I4: 10 de 10 consultas em menos de 100 ms, **a gerar**.

    O gerador bloqueia com `time.sleep` entre fragmentos, que é o que o
    `requests.post(stream=True)` faz ao laço de eventos. Sem o
    `src/web/fluxo.py` — o gerador posto directamente no `async def` — estas
    consultas ficavam em fila atrás da geração inteira.

    O `trinco.locked()` no meio da medição é o que impede este teste de passar
    vazio: só está tomado enquanto a geração corre, logo prova que havia o que
    bloquear. Ver a ressalva do cabeçalho.
    """
    pipeline = _pipeline(chunks_caeiro,
                         GeradorDeterminista(atraso_s=0.12, n_fragmentos=20))
    servico = _servico(pipeline)
    corpo = {"pergunta": "o que é a natureza?", "voz": "caeiro"}

    with _servidor(servico) as cliente, \
            cliente.stream("POST", "/api/perguntar", json=corpo) as r:
        assert r.status_code == 200
        linhas = r.iter_lines()
        next(linhas)                      # espera o 1.º evento: já está a gerar
        tempos = []
        for _ in range(10):
            assert servico.trinco.locked(), "a geração acabou a meio da medição"
            t0 = time.perf_counter()
            assert cliente.get("/api/estado").status_code == 200
            tempos.append((time.perf_counter() - t0) * 1000)
        restantes = sum(1 for ln in linhas if ln.strip())

    assert restantes, "a geração tinha acabado: o teste não mediu nada"
    assert all(t < 100 for t in tempos), (
        f"o laço bloqueou: {[round(t, 1) for t in tempos]} ms")


# --- §2.2: uma geração de cada vez ---------------------------------------- #

def test_a_segunda_geracao_concorrente_recebe_409_com_a_espera(chunks_caeiro):
    """O trinco, e a verdade do hardware em vez de uma fila escondida.

    Duas gerações em paralelo não dão duas respostas em 30 s: dão duas em 70 s,
    com `prefill_s` e `decode_s` a mentir porque vêm do Ollama, que não sabe
    que estavam a competir.
    """
    pipeline = _pipeline(chunks_caeiro,
                         GeradorDeterminista(atraso_s=0.1, n_fragmentos=20))
    corpo = {"pergunta": "o que é a natureza?", "voz": "caeiro"}

    with _servidor(_servico(pipeline)) as cliente, \
            cliente.stream("POST", "/api/perguntar", json=corpo) as r:
        assert r.status_code == 200
        linhas = r.iter_lines()
        next(linhas)
        segunda = cliente.post("/api/perguntar", json=corpo)
        assert segunda.status_code == 409
        d = segunda.json()["detail"]
        assert d["erro"] == "ocupado"
        assert 0 < d["espera_estimada_s"] <= 34.0
        for _ in linhas:
            pass


def test_o_trinco_fica_livre_depois_de_cada_geracao(chunks_caeiro):
    """Duas perguntas em série passam as duas. Sem isto, a 1.ª fechava a porta."""
    pipeline = _pipeline(chunks_caeiro, GeradorDeterminista())
    corpo = {"pergunta": "o que é a natureza?", "voz": "caeiro"}

    with _cliente(_servico(pipeline)) as cliente:
        for _ in range(2):
            with cliente.stream("POST", "/api/perguntar", json=corpo) as r:
                assert r.status_code == 200
                assert any(json.loads(ln)["tipo"] == "turno"
                           for ln in r.iter_lines() if ln.strip())


def test_uma_falha_na_geracao_liberta_o_trinco_e_vai_ao_fio(chunks_caeiro):
    """O `try/finally` do §3: uma falha não pode ficar com o trinco retido.

    E o erro vai ao fio como evento, porque quando a geração falha o `200` já
    foi enviado: um fluxo que morre calado é indistinguível de um que acabou.
    """
    class GeradorQueFalha(GeradorDeterminista):
        def gerar_em_fluxo(self, system, user, **kw):
            yield "um verso antes de rebentar\n"
            raise RuntimeError("o Ollama desligou-se a meio")

    pipeline = _pipeline(chunks_caeiro, GeradorQueFalha())
    corpo = {"pergunta": "o que é a natureza?", "voz": "caeiro"}

    with _cliente(_servico(pipeline)) as cliente:
        with cliente.stream("POST", "/api/perguntar", json=corpo) as r:
            eventos = [json.loads(ln) for ln in r.iter_lines() if ln.strip()]
        erros = _do_tipo(eventos, "erro")
        assert erros and "desligou-se" in erros[0]["mensagem"]
        assert eventos.index(erros[0]) == len(eventos) - 1, (
            "o erro vem na posição em que ocorreu, depois do que já saiu")

        # E a porta ficou aberta: a pergunta seguinte não recebe 409.
        assert cliente.post("/api/perguntar", json=corpo).status_code != 409


# --- §4.6: o impossível recusa-se, não se corrige ------------------------- #

@pytest.mark.parametrize("corpo,campo", [
    ({"pergunta": "o quê?", "voz": "search", "idioma": "pt"}, "idioma"),
    ({"pergunta": "o quê?", "voz": "caeiro", "idioma": "en"}, "idioma"),
    ({"pergunta": "o quê?", "voz": "ortonimo", "idioma": "en", "auto": True},
     "auto"),
])
def test_a_combinacao_impossivel_e_recusada_e_nao_corrigida(chunks_caeiro,
                                                            corpo, campo):
    """O CLI corrige em silêncio com uma nota; a API recusa (§4.6).

    Corrigir a escolha de alguém **depois** de ele a fazer é pior que lha negar
    antes, e o `/api/vozes` já publica os limites (`idiomas`, `idioma_unico`,
    `roteavel`) para a página poder desactivar o impossível à partida.

    Os três casos são os três do CLI: Search em português (tem 1 poema em
    português entre 52), Caeiro em inglês (não tem persona em inglês) e o
    roteador fora do português (só foi medido lá).
    """
    pipeline = _pipeline(chunks_caeiro, GeradorDeterminista())
    with _cliente(_servico(pipeline)) as cliente:
        r = cliente.post("/api/perguntar", json=corpo)
    assert r.status_code == 422
    assert r.json()["detail"]["campo"] == campo
    assert pipeline.gerador.prompts == [], "o pipeline foi tocado"


def test_a_combinacao_possivel_passa(chunks_caeiro):
    """O contraponto: sem ele, uma recusa a tudo passava os testes acima."""
    pipeline = _pipeline(chunks_caeiro, GeradorDeterminista())
    eventos = _eventos(pipeline, "what is nature?", Voice.SEARCH, Lang.EN)
    assert _do_tipo(eventos, "turno")[-1]["turno"]["idioma"] == "en"


def test_uma_voz_que_nao_existe_nao_chega_ao_pipeline(chunks_caeiro):
    """O `Pedido` é a fronteira: `422` sem nada ser construído nem gerado."""
    pipeline = _pipeline(chunks_caeiro, GeradorDeterminista())
    with _cliente(_servico(pipeline)) as cliente:
        r = cliente.post("/api/perguntar",
                         json={"pergunta": "o quê?", "voz": "shakespeare"})
    assert r.status_code == 422
    assert pipeline.gerador.prompts == [], "o pipeline foi tocado"


def test_uma_pergunta_vazia_e_recusada(chunks_caeiro):
    pipeline = _pipeline(chunks_caeiro, GeradorDeterminista())
    with _cliente(_servico(pipeline)) as cliente:
        assert cliente.post("/api/perguntar",
                            json={"pergunta": ""}).status_code == 422


# --- as opções: rerank e auto --------------------------------------------- #

def test_o_rerank_pedido_chega_ao_pipeline_e_sai_no_turno(chunks_caeiro):
    """A opção liga o reranker **no pipeline**, e não uma reordenação própria.

    O duplo substitui o `recuperar`, logo o que este teste fixa é que o
    `rerank: true` do corpo acaba no `pipeline.reranker` — a decisão de
    reordenar continua a ser do `Pipeline.recuperar`, que é o que o §0 exige.
    """
    class RerankerFalso:
        def rerank(self, consulta, candidatos, top_k):
            return [(c, 1.0) for c in reversed(list(candidatos))][:top_k]

    pipeline = _pipeline(chunks_caeiro, GeradorDeterminista())
    servico = _servico(pipeline)
    servico._reranker = RerankerFalso()
    corpo = {"pergunta": "o que é a natureza?", "voz": "caeiro"}

    with _cliente(servico) as cliente:
        with cliente.stream("POST", "/api/perguntar",
                            json=corpo | {"rerank": True}) as r:
            assert r.status_code == 200
            list(r.iter_lines())
        assert pipeline.reranker is servico._reranker

        with cliente.stream("POST", "/api/perguntar", json=corpo) as r:
            list(r.iter_lines())
        assert pipeline.reranker is None, "um pedido sem rerank deixou-o ligado"
        assert servico._reranker is not None, (
            "desligar não pode significar recarregar 568M na próxima vez")


def test_o_auto_emite_a_proposta_antes_dos_fragmentos(chunks_caeiro,
                                                      monkeypatch):
    """§4.5: a proposta aparece **antes** de gerar, para custar uma tecla.

    A geração arranca logo — não se paga latência por uma caixa de diálogo —,
    e é por isso que o evento tem de vir primeiro: é o que deixa o cliente
    abortar durante os 19 s de prefill em vez de esperar pela resposta errada.
    """
    import src.roteador as rot
    from src.roteador import Proposta

    monkeypatch.setattr(rot, "rotear",
                        lambda p, g: Proposta(Voice.CAMPOS, "campos", 0.5))
    pipeline = _pipeline(chunks_caeiro, GeradorDeterminista())
    eventos = _eventos(pipeline, "o que é a natureza?", auto=True)

    assert eventos[0]["tipo"] == "proposta"
    assert eventos[0]["proposta"]["voz"] == "campos"
    assert eventos[0]["proposta"]["decidiu"] is True
    assert eventos[0]["voz"] == "campos"
    assert _do_tipo(eventos, "turno")[-1]["turno"]["voz"] == "campos"


def test_o_roteador_sem_opiniao_mantem_a_voz_pedida(chunks_caeiro, monkeypatch):
    """`Proposta.voz is None` é «não sei», e inventar uma era pior."""
    import src.roteador as rot
    from src.roteador import Proposta

    monkeypatch.setattr(rot, "rotear", lambda p, g: Proposta(None, "", 0.4))
    pipeline = _pipeline(chunks_caeiro, GeradorDeterminista())
    eventos = _eventos(pipeline, "o que é a natureza?", auto=True)

    assert eventos[0]["proposta"]["decidiu"] is False
    assert eventos[0]["voz"] == "caeiro"
    assert _do_tipo(eventos, "turno")[-1]["turno"]["voz"] == "caeiro"


def test_o_auto_marca_o_roteador_como_aquecido(chunks_caeiro, monkeypatch):
    """Uma chamada põe os 331 tokens do `SYSTEM` em cache: o estado diz-no.

    Antes, o `/api/estado` dizia «frio: a 1.ª proposta custa ~20 s» para sempre
    — e isso deixava de ser verdade depois da primeira pergunta em `auto`.
    """
    import src.roteador as rot
    from src.roteador import Proposta

    monkeypatch.setattr(rot, "rotear",
                        lambda p, g: Proposta(Voice.CAEIRO, "caeiro", 0.5))
    pipeline = _pipeline(chunks_caeiro, GeradorDeterminista())

    with _cliente(_servico(pipeline)) as cliente:
        def comp(nome):
            corpo = cliente.get("/api/estado").json()
            return next(c for c in corpo["componentes"] if c["nome"] == nome)

        assert comp("roteador")["pronto"] is False
        with cliente.stream("POST", "/api/perguntar",
                            json={"pergunta": "o que é a natureza?",
                                  "voz": "caeiro", "auto": True}) as r:
            list(r.iter_lines())
        assert comp("roteador")["pronto"] is True


def test_a_primeira_pergunta_constroi_o_pipeline_uma_vez_so(chunks_caeiro):
    """§4.2: «carrega na 1.ª pergunta», e **só** na primeira.

    O `/api/estado` reporta o encoder como não carregado até haver pipeline, e
    isso tem de deixar de ser verdade depois da primeira pergunta — senão a
    interface mente ao contrário, dizendo que ainda falta pagar o que já pagou.
    """
    pipeline = _pipeline(chunks_caeiro, GeradorDeterminista())
    pipeline.reranker = None
    servico = Servico(gerador=pipeline.gerador)
    chamadas = []

    def garantir():
        chamadas.append(1)
        servico.pipeline = pipeline
        return pipeline

    servico.garantir_pipeline = garantir
    corpo = {"pergunta": "o que é a natureza?", "voz": "caeiro"}

    with _cliente(servico) as cliente:
        def encoder_pronto():
            corpo_estado = cliente.get("/api/estado").json()
            return next(c for c in corpo_estado["componentes"]
                        if c["nome"] == "encoder")["pronto"]

        assert encoder_pronto() is False
        for _ in range(2):
            with cliente.stream("POST", "/api/perguntar", json=corpo) as r:
                list(r.iter_lines())
        assert encoder_pronto() is True
    assert len(chamadas) == 2, "o manipulador tem de o pedir sempre (é de graça)"


def test_garantir_pipeline_devolve_o_mesmo_objecto_a_segunda_vez(chunks_caeiro):
    """O que torna «pedir sempre» de graça: a segunda chamada não constrói nada."""
    pipeline = _pipeline(chunks_caeiro, GeradorDeterminista())
    servico = Servico(gerador=pipeline.gerador, pipeline=pipeline)
    assert servico.garantir_pipeline() is pipeline
    assert servico.garantir_pipeline() is pipeline


# --- o formato do fio ------------------------------------------------------ #

def test_o_corpo_e_ndjson_e_cada_linha_e_um_json_valido(chunks_caeiro):
    """Uma linha, um evento. Ver §1.3: é isto, e não SSE nem um JSON gigante."""
    pipeline = _pipeline(chunks_caeiro, GeradorDeterminista(n_fragmentos=6))
    with _cliente(_servico(pipeline)) as cliente, \
            cliente.stream("POST", "/api/perguntar",
                           json={"pergunta": "o que é a natureza?",
                                 "voz": "caeiro"}) as r:
        bruto = r.read().decode("utf-8")

    linhas = [ln for ln in bruto.split("\n") if ln]
    assert len(linhas) > 2, "não houve fluxo: saiu tudo numa linha"
    tipos = [json.loads(ln)["tipo"] for ln in linhas]
    assert tipos[-1] == "turno"
    assert set(tipos) <= {"fragmento", "turno", "proposta", "erro"}
    assert bruto.endswith("\n"), "a última linha também é uma linha"


def test_o_fio_nao_leva_corpos_de_poemas(chunks_caeiro):
    """§3.3, sobre o fluxo inteiro e não só sobre o `serial.turno`.

    As fontes vão como ids, e não como corpo.

    ⚠️ **Este teste é o antepassado fraco do portão I7′**, e fica porque mede o
    caminho aprovado em detalhe. Vê a **primeira** linha de cada chunk do
    contexto, com um gerador que não plagia — e foi por isso que não viu nada
    quando a tentativa plagiada começou a levar 6 versos ao fio. O varrimento
    completo, sobre todas as rotas e todas as linhas do corpus, está em
    `tests/test_i7.py`.
    """
    pipeline = _pipeline(chunks_caeiro, GeradorDeterminista())
    with _cliente(_servico(pipeline)) as cliente, \
            cliente.stream("POST", "/api/perguntar",
                           json={"pergunta": "o que é a natureza?",
                                 "voz": "caeiro"}) as r:
        bruto = r.read().decode("utf-8")

    for c in chunks_caeiro:
        primeiro = next(ln for ln in c.text.split("\n") if ln.strip())
        assert primeiro not in bruto, f"o corpo do {c.poem_id} foi ao fio"
