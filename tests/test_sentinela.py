"""O portão I8 da Fase 6: o servidor cede à medição.

**A afirmação.** Com o sentinela presente, `POST /api/perguntar` responde
**409** nomeando a fase e o PID, e `GET /api/estado` mostra-o como componente;
sem o ficheiro, gera normalmente. E a medição que o justifica: **com**
sentinela, os `segundos` de 10 gerações do servidor e de 10 de um script **não
se sobrepõem no tempo** — verificado por *timestamps*, não por intenção.

**E a asserção que o `PRODUCAO.md` §4 acrescentou**, antes de o passo 7 ser
escrito: **a fase escreve de um checkout e o servidor, no outro, vê-o.** Sem
ela, o I8 passava num processo com um directório só e não dizia nada sobre a
máquina real, onde o serviço público corre num segundo checkout e portanto há
**dois `data/`**. A especificação original do sentinela —
`data/.medicao-a-correr`, relativo — faz a fase escrever no seu e o servidor
verificar o outro: o ficheiro nunca é visto, o `/api/estado` diz que está tudo
bem, e o mecanismo que existe para tornar o túnel seguro fica **silenciosamente
desligado**. É o modo de falha do manifesto do índice outra vez, «não dá erro:
dá respostas erradas».

Dois testes abaixo são sobre isso e não sobre o mecanismo:
`test_i8_a_fase_de_um_checkout_e_vista_pelo_servidor_do_outro` é a asserção
nova, e `test_i8_com_o_caminho_relativo_da_especificacao_fica_invisivel`
demonstra, **a correr o código real**, que com o caminho da especificação
original a primeira falharia — e é por isso que ela existe.

⚠️ **Nenhum teste deste ficheiro toca no sentinela real desta máquina.** Todos
apontam a `PESSOABOT_SENTINELA` para um `tmp_path`: um teste que escrevesse em
`~/.local/state/pessoabot/` podia recusar perguntas a um servidor a correr ao
lado, ou apagar o sentinela de uma medição em curso — que é o dano que este
módulo existe para impedir.
"""
from __future__ import annotations

import contextlib
import json
import os
import subprocess
import threading
import time
import warnings
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.corpus.build import load
from src.corpus.models import Voice
from src.web import sentinela, tunel
from src.web.app import BLOQUEANTES, EXIGIDOS, criar_app
from src.web.tunel import TunelIndisponivel

from .test_perguntar import GeradorDeterminista, _servico, _servidor
from .test_pipeline import _pipeline

PERGUNTA = {"pergunta": "o que é a natureza?", "voz": "caeiro"}


@pytest.fixture(scope="module")
def chunks_caeiro():
    """Oito chunks de Caeiro, como nos outros quatro ficheiros que o fazem.

    Repetido em vez de partilhado pela razão que o `test_cancelar.py` escreve:
    são três linhas, e um `conftest.py` por três linhas acrescentava um sítio
    onde procurar.
    """
    _, cs = load()
    return [c for c in cs if c.voice is Voice.CAEIRO][:8]


@pytest.fixture
def alvo(tmp_path, monkeypatch) -> Path:
    """O sentinela desta corrida de testes, fora do estado real da máquina."""
    c = tmp_path / "estado" / ".medicao-a-correr"
    monkeypatch.setenv(sentinela.VARIAVEL, str(c))
    return c


@contextlib.contextmanager
def _cliente(pipeline):
    with TestClient(criar_app(_servico(pipeline))) as c:
        yield c


def _pipeline_rapido(chunks):
    return _pipeline(chunks, GeradorDeterminista())


# --- I8: o caminho, que é a correcção que vem do PRODUCAO.md §4 ------------ #

def test_i8_o_caminho_por_omissao_e_absoluto_e_fora_de_qualquer_checkout():
    """A guarda contra o regresso ao `data/.medicao-a-correr` da especificação.

    Se alguém voltar a pôr um caminho relativo por omissão, este teste cai —
    e cai **antes** de alguém descobrir na máquina que o mecanismo estava
    desligado. É a asserção mais barata deste ficheiro e a que cobre o defeito
    mais caro.
    """
    c = sentinela.CAMINHO_OMISSAO
    assert c.is_absolute(), f"caminho relativo: {c}"
    repo = Path(__file__).resolve().parent.parent
    assert repo not in c.resolve().parents, (
        f"{c} está dentro de um checkout: com dois checkouts há dois destes")
    assert c.name == ".medicao-a-correr"


def test_i8_a_variavel_de_ambiente_sobrepoe_o_caminho(tmp_path, monkeypatch):
    monkeypatch.setenv(sentinela.VARIAVEL, str(tmp_path / "x"))
    assert sentinela.caminho() == tmp_path / "x"
    monkeypatch.delenv(sentinela.VARIAVEL)
    assert sentinela.caminho() == sentinela.CAMINHO_OMISSAO


def test_i8_o_caminho_e_lido_a_cada_chamada_e_nao_na_importacao(tmp_path,
                                                                monkeypatch):
    """Uma constante fixada na importação tornava a variável inútil no uvicorn.

    O servidor é um processo de vida longa e o teste dos dois checkouts troca
    de ambiente a meio; se isto fosse lido uma vez, nenhum dos dois funcionava.
    """
    monkeypatch.setenv(sentinela.VARIAVEL, str(tmp_path / "a"))
    primeiro = sentinela.caminho()
    monkeypatch.setenv(sentinela.VARIAVEL, str(tmp_path / "b"))
    assert sentinela.caminho() != primeiro


def test_i8_a_fase_de_um_checkout_e_vista_pelo_servidor_do_outro(
        tmp_path, monkeypatch, chunks_caeiro):
    """**A asserção que o `PRODUCAO.md` §4 acrescentou ao portão.**

    Dois directórios de trabalho distintos, cada um com o seu `data/`, como os
    dois checkouts desta máquina: o de trabalho, onde as fases correm, e o do
    serviço, que só corre o `uvicorn`. A fase escreve do primeiro e o servidor,
    a correr do segundo, recusa.

    O que faz este teste significar algo é o `monkeypatch.chdir` entre as duas
    metades: sem ele, «dois checkouts» era uma frase e não uma condição.

    ✅ **Verificado por mutação**, que é o que o distingue de um teste que passa
    por acaso. Com o `caminho()` revertido para o `data/.medicao-a-correr` da
    especificação original, este teste falha — e falha no sítio exacto que o
    `PRODUCAO.md` §4 previu:

        assert m is not None and m.fase == "fase-5z"
        E   assert (None is not None)

    E repare-se **onde não falha**: a asserção anterior,
    `sentinela.caminho() == escrito`, passa com a mutação. Os dois lados
    concordam no caminho — `data/.medicao-a-correr` é igual a
    `data/.medicao-a-correr` — e apontam a ficheiros diferentes. É a forma mais
    pura do «não dá erro: dá respostas erradas» que se podia pedir.
    """
    trabalho, servico_ = tmp_path / "trabalho", tmp_path / "servico"
    for d in (trabalho, servico_):
        (d / "data").mkdir(parents=True)
    monkeypatch.setenv(sentinela.VARIAVEL,
                       str(tmp_path / "estado" / ".medicao-a-correr"))

    # A fase, no checkout de trabalho.
    monkeypatch.chdir(trabalho)
    with sentinela.medicao("fase-5z"):
        escrito = sentinela.caminho()
        assert escrito.exists()

        # O servidor, no checkout do serviço. Mesmo processo, outro `cwd` — é a
        # única parte desta máquina que um teste pode reproduzir honestamente.
        monkeypatch.chdir(servico_)
        assert sentinela.caminho() == escrito, (
            "os dois lados resolveram caminhos diferentes")
        m = sentinela.a_correr()
        assert m is not None and m.fase == "fase-5z"

        with _cliente(_pipeline_rapido(chunks_caeiro)) as cliente:
            r = cliente.post("/api/perguntar", json=PERGUNTA)
            assert r.status_code == 409, (
                "o servidor do segundo checkout não viu o sentinela do primeiro")
            assert r.json()["detail"]["fase"] == "fase-5z"

    # E o levantar da medição chega ao outro checkout da mesma maneira.
    assert sentinela.a_correr() is None


def test_i8_com_o_caminho_relativo_da_especificacao_fica_invisivel(
        tmp_path, monkeypatch, chunks_caeiro):
    """Porque é que o teste de cima existe: com `data/.medicao-a-correr`, falha.

    Isto corre o **código real** com o caminho que a Fase 6 §2.4 especificou, e
    mostra o que ele faz na máquina real: a fase escreve `trabalho/data/...`, o
    servidor procura `servico/data/...`, não encontra nada, e **gera**. Não dá
    erro nenhum — dá a resposta errada, que é a forma que custa caro.

    É a mutação do portão: com a correcção do `PRODUCAO.md` §4 o teste anterior
    passa, e sem ela passaria este. Os dois juntos são o que torna o I8 uma
    medição em vez de uma intenção.
    """
    trabalho, servico_ = tmp_path / "trabalho", tmp_path / "servico"
    for d in (trabalho, servico_):
        (d / "data").mkdir(parents=True)
    monkeypatch.delenv(sentinela.VARIAVEL, raising=False)
    monkeypatch.setattr(sentinela, "CAMINHO_OMISSAO",
                        Path("data") / ".medicao-a-correr")

    monkeypatch.chdir(trabalho)
    with sentinela.medicao("fase-5z"):
        assert (trabalho / "data" / ".medicao-a-correr").exists()

        monkeypatch.chdir(servico_)
        assert sentinela.a_correr() is None, (
            "este teste deixou de demonstrar coisa nenhuma: verifica o que "
            "mudou no `caminho()`")
        with _cliente(_pipeline_rapido(chunks_caeiro)) as cliente:
            r = cliente.post("/api/perguntar", json=PERGUNTA)
            # O mecanismo está desligado e **nada** o diz: 200, e o
            # `/api/estado` a declarar o sentinela pronto.
            assert r.status_code == 200
            assert cliente.get("/api/estado").json()["pode_perguntar"] is True


# --- I8: o 409, a fase e o PID -------------------------------------------- #

def test_i8_com_o_sentinela_o_perguntar_recusa_com_409(alvo, chunks_caeiro):
    """O portão, metade um: 409 **nomeando a fase e o PID**."""
    with sentinela.medicao("fase-5z-amostras") as m, \
            _cliente(_pipeline_rapido(chunks_caeiro)) as cliente:
        r = cliente.post("/api/perguntar", json=PERGUNTA)
        assert r.status_code == 409
        d = r.json()["detail"]
        assert d["erro"] == "medicao_a_correr"
        assert d["fase"] == "fase-5z-amostras"
        assert d["pid"] == m.pid == os.getpid()
        # A mensagem é para quem a lê no ecrã, e tem de dizer as duas coisas.
        assert "fase-5z-amostras" in d["mensagem"]
        assert str(m.pid) in d["mensagem"]


def test_i8_sem_o_sentinela_gera_normalmente(alvo, chunks_caeiro):
    """O portão, metade dois. Um guarda que recusa sempre não é um guarda."""
    assert not alvo.exists()
    with _cliente(_pipeline_rapido(chunks_caeiro)) as cliente, \
            cliente.stream("POST", "/api/perguntar", json=PERGUNTA) as r:
        assert r.status_code == 200
        assert any(json.loads(ln)["tipo"] == "turno"
                   for ln in r.iter_lines() if ln.strip())


def test_i8_o_sentinela_e_verificado_a_cada_pergunta_e_nao_no_arranque(
        alvo, chunks_caeiro):
    """§2.4: «antes de cada geração, não no arranque».

    Um servidor que verificasse no arranque não protegia nada: as fases duram
    horas e arrancam **depois** dele.
    """
    with _cliente(_pipeline_rapido(chunks_caeiro)) as cliente:
        assert cliente.post("/api/perguntar", json=PERGUNTA).status_code != 409
        with sentinela.medicao("fase-que-arrancou-depois"):
            assert cliente.post("/api/perguntar",
                                json=PERGUNTA).status_code == 409
        with cliente.stream("POST", "/api/perguntar", json=PERGUNTA) as r:
            assert r.status_code == 200


def test_i8_o_409_do_sentinela_nao_toma_o_trinco(alvo, chunks_caeiro):
    """Uma recusa não pode trancar a porta que já estava livre.

    Verificado porque o `409` do §2.2 é devolvido **depois** de um `locked()` e
    este é devolvido antes de qualquer `acquire()`: trocar a ordem das duas
    verificações deixava um trinco tomado por um pedido que nunca gerou.
    """
    servico = _servico(_pipeline_rapido(chunks_caeiro))
    with TestClient(criar_app(servico)) as cliente:
        with sentinela.medicao("fase-5z"):
            assert cliente.post("/api/perguntar",
                                json=PERGUNTA).status_code == 409
        assert not servico.trinco.locked()


# --- I8: o componente do /api/estado, e em qual dos dois booleanos entra -- #

def test_i8_o_estado_reporta_o_sentinela_como_componente(alvo, chunks_caeiro):
    with sentinela.medicao("fase-5z") as m, \
            _cliente(_pipeline_rapido(chunks_caeiro)) as cliente:
        cs = {c["nome"]: c for c in cliente.get("/api/estado").json()["componentes"]}
        assert "sentinela" in cs, "o §2.4 pede-o ao lado do ollama e do índice"
        assert cs["sentinela"]["pronto"] is False
        assert "fase-5z" in cs["sentinela"]["detalhe"]
        assert str(m.pid) in cs["sentinela"]["detalhe"]
        # O remédio nomeia o ficheiro **por caminho completo**: com dois
        # checkouts na mesma máquina, «apaga o sentinela» não diz onde.
        assert str(alvo) in cs["sentinela"]["remedio"]


def test_i8_o_sentinela_nao_e_uma_avaria_do_sistema_e_o_pronto_di_lo(
        alvo, chunks_caeiro):
    """A decisão do §4.2: o sentinela entra no `pode_perguntar`, não no `pronto`.

    O `pronto` responde «está tudo verificado?» — é uma afirmação sobre o
    **sistema**: Ollama de pé, modelo instalado, corpus e índice de confiança.
    Uma medição a correr não avaria nada disso; é uma **cedência**, e por três
    minutos ou por sete horas o sistema continua exactamente tão pronto como
    estava. Metê-la no `pronto` fazia a página acender uma cruz vermelha de
    avaria sobre uma decisão deliberada de quem corre a casa.

    O `pode_perguntar` responde «vale a pena carregar no botão?», e a essa a
    resposta é **não** — senão o utilizador escreve a pergunta e recebe um 409,
    que é a surpresa que o `pode_perguntar` nasceu para evitar (ver a docstring
    do `/api/estado`: a distinção vem de um defeito observado a correr).
    """
    assert "sentinela" not in EXIGIDOS
    assert "sentinela" in BLOQUEANTES
    with sentinela.medicao("fase-5z"), \
            _cliente(_pipeline_rapido(chunks_caeiro)) as cliente:
        corpo = cliente.get("/api/estado").json()
        assert corpo["pode_perguntar"] is False
        cs = {c["nome"]: c for c in corpo["componentes"]}
        # E não vai à página como requisito: a página desenha `✗` ao que é
        # exigido e não está pronto, e isto não é uma avaria.
        assert cs["sentinela"]["exigido"] is False
        assert cs["sentinela"]["bloqueante"] is True


def test_i8_a_leitura_do_sentinela_nao_poe_em_risco_o_portao_i4(alvo):
    """O I4 continua a valer, e isto acrescenta um `stat` ao caminho dele.

    O portão I4 dá 100 ms a **toda** a resposta do `/api/estado`, que já faz
    duas chamadas HTTP ao Ollama. Medido nesta máquina, 2000 leituras:
    **7,9 µs** sem ficheiro e **15,6 µs** com ele — 0,016 ms contra um
    orçamento de 100 ms, quatro ordens de grandeza abaixo. O I4 foi corrido
    cinco vezes depois desta peça entrar e passou 5 de 5.

    O limite abaixo é folgado de propósito: é uma rede contra alguém pôr uma
    chamada HTTP ou um `glob` aqui dentro, não uma medição fina — essa está no
    número acima, que esta casa prefere escrito a reconstituído.
    """
    for existe in (False, True):
        if existe:
            sentinela.escrever("fase-5z", alvo=alvo)
        t0 = time.perf_counter()
        for _ in range(200):
            sentinela.componente()
        ms = (time.perf_counter() - t0) * 1000
        assert ms < 100, f"200 leituras (ficheiro {existe}) custaram {ms:.0f} ms"


# --- o mecanismo: o ajudante, e o sentinela esquecido --------------------- #

def test_o_ajudante_escreve_e_apaga(alvo):
    assert sentinela.a_correr() is None
    with sentinela.medicao("fase-6-passo-7") as m:
        assert alvo.exists()
        lido = sentinela.a_correr()
        assert lido is not None
        assert (lido.fase, lido.pid) == (m.fase, m.pid)
    assert not alvo.exists()
    assert sentinela.a_correr() is None


def test_o_ajudante_apaga_mesmo_quando_a_fase_rebenta(alvo):
    """É isto que o torna mecanismo e não disciplina.

    Sem o `finally`, um `gerar_amostras.py` que levanta a meio deixava o
    servidor a recusar perguntas para sempre — e a culpa parecia do servidor.
    """
    with pytest.raises(RuntimeError), sentinela.medicao("fase-que-rebenta"):
        raise RuntimeError("o Ollama desligou-se a meio")
    assert not alvo.exists()


def test_o_ajudante_cria_o_directorio_que_falta(tmp_path, monkeypatch):
    """`~/.local/state/pessoabot/` não existe na primeira vez, e isso não é erro."""
    c = tmp_path / "nada" / "disto" / "existe" / ".medicao-a-correr"
    monkeypatch.setenv(sentinela.VARIAVEL, str(c))
    with sentinela.medicao("fase-5z"):
        assert c.exists()


def test_limpar_e_idempotente(alvo):
    assert sentinela.limpar() is False
    sentinela.escrever("fase-5z")
    assert sentinela.limpar() is True
    assert sentinela.limpar() is False


def test_um_sentinela_esquecido_diagnostica_se(alvo):
    """O PID existe para isto, e é o §2.4 que o pede por estas palavras.

    Um `kill -9` a uma fase deixa o ficheiro para trás. O servidor continua a
    recusar — o sentido é único, e ceder é a direcção segura —, mas a mensagem
    deixa de ser um mistério: diz que o processo já não existe e o que apagar.
    """
    # Um PID que não corre. O 2**22 está acima do `pid_max` desta máquina, e o
    # teste verifica-o em vez de o assumir.
    morto = 2 ** 22
    assert not sentinela._processo_vivo(morto)
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text(json.dumps({"fase": "fase-5z", "pid": morto,
                                "inicio": time.time()}), encoding="utf-8")

    m = sentinela.a_correr()
    assert m is not None and m.vivo is False, "continua a bloquear"
    c = sentinela.componente()
    assert c.pronto is False
    assert "já não existe" in c.detalhe and str(morto) in c.detalhe
    assert str(alvo) in c.remedio


def test_o_processo_desta_corrida_conta_se_como_vivo(alvo):
    assert sentinela._processo_vivo(os.getpid())
    with sentinela.medicao("fase-5z"):
        m = sentinela.a_correr()
        assert m is not None and m.vivo is True


@pytest.mark.parametrize("conteudo", ["", "isto não é json", "{}",
                                      '{"fase": "x"}', '{"pid": "nem isto"}'])
def test_um_sentinela_ilegivel_bloqueia_em_vez_de_ser_ignorado(alvo, conteudo):
    """A direcção segura, outra vez: lixo não é «não há medição».

    Tratar um ficheiro mal escrito como ausência era escolher a única saída que
    pode invalidar horas de dados, e pela razão errada — porque não se
    conseguiu ler um JSON de 80 bytes.
    """
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text(conteudo, encoding="utf-8")
    m = sentinela.a_correr()
    assert m is not None, f"ignorado: {conteudo!r}"
    assert sentinela.componente().pronto is False


# --- I8: a medição que o justifica, por timestamps ----------------------- #

def test_i8_as_geracoes_do_servidor_e_do_script_nao_se_sobrepoem(
        alvo, chunks_caeiro):
    """**A medição do portão**, e é por *timestamps* e não por intenção.

    10 «gerações» de um script de fase e 10 do servidor, a correr ao mesmo
    tempo contra o mesmo processo, e nenhum par de intervalos a intersectar-se.
    É esta sobreposição que torna o campo `segundos` do `01-cru.jsonl` de uma
    fase ininterpretável, e é o precedente dos 25 625 tok/s do `CONTROLO.md`
    §4 — um instrumento com uma variável que não controlava.

    O script é uma thread e não um processo: o que se mede é o **ficheiro**
    como canal entre quem gera, e uma thread lê e escreve o mesmo disco. O que
    um processo separado acrescentaria é a resolução de caminho, e isso é o
    teste dos dois checkouts.

    O servidor é um `uvicorn` a sério (`_servidor`), porque com o `TestClient`
    o fluxo acaba antes da primeira linha chegar — a ressalva está no cabeçalho
    do `test_perguntar.py`, e já fez um portão desta casa passar vazio.
    """
    pipeline = _pipeline(chunks_caeiro,
                         GeradorDeterminista(atraso_s=0.01, n_fragmentos=4))
    intervalos_script: list[tuple[float, float]] = []
    intervalos_servidor: list[tuple[float, float]] = []
    recusas = 0
    script_comecou = threading.Event()
    script_acabou = threading.Event()
    pode_largar = threading.Event()

    def o_script():
        """A fase: toma o sentinela e mede 10 gerações suas.

        O `pode_largar` no fim **não** é andaime a mais: sem ele, a fase
        largava o sentinela antes de avisar que acabou, e o POST que estava a
        voar nesse instante recebia 200. Não era sobreposição nenhuma — a fase
        já tinha terminado —, mas contava como uma, e a contagem é o que impede
        este teste de passar por não ter tentado. Fechar a janela no
        instrumento é mais honesto que relaxar a asserção.
        """
        try:
            with sentinela.medicao("portao-i8"):
                script_comecou.set()
                for _ in range(10):
                    t0 = time.monotonic()
                    time.sleep(0.03)      # o lugar do Ollama
                    intervalos_script.append((t0, time.monotonic()))
                script_acabou.set()
                pode_largar.wait(timeout=10)
        finally:
            script_acabou.set()

    thread = threading.Thread(target=o_script, daemon=True)
    with _servidor(_servico(pipeline)) as cliente:
        thread.start()
        # ⚠️ Esperar pelo ficheiro, e não pelo `thread.start()`. O primeiro
        # rascunho deste teste atirava o 1.º POST antes de o `medicao()` ter
        # escrito o sentinela, e esse 200 era uma sobreposição real: o servidor
        # gerou quando a fase já tinha arrancado. **A asserção apanhou-o** —
        # «o servidor gerou 11 vezes» —, e é o instrumento a funcionar e não um
        # incómodo a contornar. Fica escrito porque o `CONTROLO.md` §4 guarda a
        # lição de um portão desta casa que passava vazio.
        assert script_comecou.wait(timeout=5), "a fase não arrancou"
        # Enquanto a fase corre, o servidor não gera nada: conta-se cada recusa
        # para o teste não poder passar por não ter tentado.
        while not script_acabou.is_set():
            t0 = time.monotonic()
            r = cliente.post("/api/perguntar", json=PERGUNTA)
            if r.status_code == 409:
                recusas += 1
                continue
            # Qualquer 200 durante a fase é uma sobreposição, e o intervalo
            # vai para a lista para a asserção final a apanhar.
            with contextlib.closing(r):
                pass
            intervalos_servidor.append((t0, time.monotonic()))
        pode_largar.set()
        thread.join(timeout=10)
        assert sentinela.a_correr() is None, "a fase não largou o sentinela"

        # E depois da fase, as 10 do servidor: é o que mostra que o guarda
        # recusou por haver medição e não por estar avariado.
        for _ in range(10):
            t0 = time.monotonic()
            with cliente.stream("POST", "/api/perguntar", json=PERGUNTA) as r:
                assert r.status_code == 200
                for _ln in r.iter_lines():
                    pass
            intervalos_servidor.append((t0, time.monotonic()))

    assert len(intervalos_script) == 10
    assert len(intervalos_servidor) == 10, (
        f"o servidor gerou {len(intervalos_servidor)} vezes: as que passam de "
        f"10 aconteceram durante a fase")
    assert recusas >= 10, (
        f"só {recusas} recusas: o teste não exercitou o guarda o suficiente "
        f"para a não-sobreposição significar algo")
    for a0, a1 in intervalos_script:
        for b0, b1 in intervalos_servidor:
            assert a1 <= b0 or b1 <= a0, (
                f"sobreposição: fase [{a0:.3f}, {a1:.3f}] e servidor "
                f"[{b0:.3f}, {b1:.3f}]")


# --- D3: a ordem, que é a decisão do passo 5 do PRODUCAO.md --------------- #
#
# «Parar o túnel vem imediatamente depois do `escrever` e arrancá-lo
# imediatamente antes do `limpar`, por fora» — de modo que o ficheiro já exista
# quando o URL cai e ainda exista enquanto ele volta, e **nunca haja um
# instante com túnel de pé e medição a correr**. Invertê-la abre exactamente a
# janela que o mecanismo fecha.
#
# A ordem está verificada **por mutação**, e não só por os testes passarem:
# trocadas as duas chamadas em `src/web/sentinela.py` — `parar` antes do
# `escrever` e `arrancar` depois do `limpar` —, caem os **três** testes abaixo
# que falam da ordem (`..._cai_depois_de_o_sentinela_existir`,
# `..._volta_antes_de_o_sentinela_ser_apagado` e `..._nunca_ha_um_instante_...`)
# e nenhum outro. O `..._mesmo_quando_a_fase_rebenta` **não** cai, e é correcto
# que não caia: é sobre o `finally`, não sobre a ordem. A disciplina é a do
# passo 7 e está registada no `CONTROLO.md` §2.

class TunelDuplo:
    """Um túnel de mentira que **observa o ficheiro** em cada transição.

    Não basta registar a ordem das chamadas: o que o plano afirma é uma relação
    entre o túnel e o *sentinela*, logo o duplo olha para o ficheiro em cada
    transição. É a diferença entre verificar a sequência e verificar a
    propriedade.
    """

    nome = "duplo.service"

    def __init__(self, alvo: Path, *, falha_a_parar=None, falha_a_arrancar=None):
        self.alvo = alvo
        self.falha_a_parar = falha_a_parar
        self.falha_a_arrancar = falha_a_arrancar
        self.de_pe = True
        #: `(evento, o ficheiro existia?, o túnel estava de pé antes?)`
        self.registo: list[tuple[str, bool, bool]] = []

    def _anotar(self, evento: str) -> None:
        self.registo.append((evento, self.alvo.exists(), self.de_pe))

    def parar(self) -> None:
        self._anotar("parar")
        if self.falha_a_parar is not None:
            raise self.falha_a_parar
        self.de_pe = False

    def arrancar(self) -> None:
        self._anotar("arrancar")
        if self.falha_a_arrancar is not None:
            raise self.falha_a_arrancar
        self.de_pe = True

    def observar(self, evento: str) -> None:
        """Para o corpo da fase se anotar a si mesmo no mesmo registo."""
        self._anotar(evento)

    @property
    def eventos(self) -> list[str]:
        return [e for e, _, _ in self.registo]


def test_d3_o_tunel_cai_depois_de_o_sentinela_existir(alvo):
    """A primeira metade da ordem, e a razão de ela ser essa.

    Se o túnel caísse **antes** do `escrever`, havia um intervalo com o URL já
    em baixo e nenhum sentinela no disco — e nesse intervalo o servidor do
    outro checkout aceitava perguntas, que é o pedido que o §3.2 (a) diz que
    aquece o chip sem gerar nada.
    """
    t = TunelDuplo(alvo)
    with sentinela.medicao("fase-5z", tunel=t):
        pass
    (evento, existia, de_pe), *_ = t.registo
    assert evento == "parar"
    assert existia is True, "o sentinela já estava escrito quando o URL caiu"
    assert de_pe is True, "e o túnel ainda estava de pé — era ele a cair"


def test_d3_o_tunel_volta_antes_de_o_sentinela_ser_apagado(alvo):
    """A segunda metade: o ficheiro ainda existe enquanto o URL volta.

    Invertido, o URL respondia num instante em que já não havia sentinela
    nenhum mas a fase ainda não tinha fechado — a mesma janela, do outro lado.
    """
    t = TunelDuplo(alvo)
    with sentinela.medicao("fase-5z", tunel=t):
        pass
    evento, existia, de_pe = t.registo[-1]
    assert evento == "arrancar"
    assert existia is True, "o sentinela ainda estava lá quando o URL voltou"
    assert de_pe is False
    assert not alvo.exists(), "e só depois foi retirado"


def test_d3_nunca_ha_um_instante_com_tunel_de_pe_e_medicao_a_correr(alvo):
    """A propriedade inteira, que é a que o §3.3 compra, nas duas direcções.

    O corpo da fase anota-se no mesmo registo, e a asserção é sobre **todas**
    as entradas, as duas transições incluídas: em cada instante observado o
    sentinela está no disco. Juntando a isso o túnel em baixo durante o corpo,
    fica dito que o ficheiro já existia quando o URL caiu, continuava lá quando
    voltou, e no meio não houve URL.

    Com as duas chamadas trocadas em `src/web/sentinela.py`, as duas transições
    passam a observar o ficheiro **ausente** e este teste cai nas duas.
    """
    t = TunelDuplo(alvo)
    with sentinela.medicao("fase-5z", tunel=t):
        t.observar("amostra-1")
        t.observar("amostra-2")
    for evento, existia, _ in t.registo:
        assert existia is True, f"{evento}: sem sentinela no disco"
    for evento, _, de_pe in t.registo:
        if evento.startswith("amostra"):
            assert de_pe is False, f"{evento}: o túnel estava de pé"
    assert t.eventos == ["parar", "amostra-1", "amostra-2", "arrancar"]
    assert t.de_pe is True


def test_d3_o_tunel_volta_mesmo_quando_a_fase_rebenta(alvo):
    """O mesmo argumento do `finally` do passo 7, aplicado ao URL.

    Sem isto, uma fase que levantasse a meio deixava o serviço público em baixo
    até alguém se lembrar — e o sentinela, esse, era apagado, logo nada no
    `/api/estado` explicava o URL morto.
    """
    t = TunelDuplo(alvo)
    with pytest.raises(RuntimeError), sentinela.medicao("rebenta", tunel=t):
        raise RuntimeError("o Ollama desligou-se a meio")
    assert t.de_pe is True
    assert t.eventos == ["parar", "arrancar"]
    assert not alvo.exists()


# --- D3: o que acontece quando parar falha, que é a decisão deliberada ---- #

def test_d3_se_o_tunel_nao_parar_a_fase_nao_arranca(alvo):
    """A assimetria de custos, e porque é que o §2.4 não responde a isto.

    O sentido único do §2.4 — «o servidor cede à medição, nunca o contrário» —
    fala de quem cede entre o servidor e a fase. Aqui quem pode ceder é a
    **medição**, e deixar uma fase correr com o túnel de pé é o que invalida os
    dados que ela vai produzir. Uma fase que não arranca custa um comando; uma
    fase de 3,2 a 7,5 horas corrida com um estranho no CPU custa as horas **e
    não se descobre depois** — é a forma das 4 horas que o cache de KV
    invalidou (`CONTROLO.md` §4).
    """
    t = TunelDuplo(alvo, falha_a_parar=TunelIndisponivel("devolveu 5"))
    corpo_correu = False
    with pytest.raises(TunelIndisponivel, match="devolveu 5"), \
            sentinela.medicao("fase-5z", tunel=t):
        corpo_correu = True
    assert corpo_correu is False, "a fase não começou"
    assert t.eventos == ["parar"], "e não se tentou arrancar o que não parou"


def test_d3_uma_fase_que_nao_arranca_nao_deixa_o_servidor_recusado(alvo):
    """O sentinela é retirado antes de levantar, e tem de ser.

    Senão um túnel avariado deixava o `POST /api/perguntar` a devolver 409 por
    causa de uma fase que nunca correu — exactamente o 409 de sete horas que o
    §3.2 (c) chama «avariado com uma mensagem interna», e sem fase nenhuma do
    outro lado.
    """
    t = TunelDuplo(alvo, falha_a_parar=TunelIndisponivel("não está instalada"))
    with pytest.raises(TunelIndisponivel), \
            sentinela.medicao("fase-5z", tunel=t):
        pass
    assert not alvo.exists()
    assert sentinela.a_correr() is None


def test_d3_se_o_tunel_nao_voltar_a_fase_termina_e_avisa(alvo):
    """A direcção inversa é assimétrica de propósito.

    A fase já correu e os dados são bons: levantar aqui trocava um resultado
    válido por uma excepção. O túnel em baixo é a direcção segura, e
    auto-anuncia-se — o visitante recebe a página do fornecedor.
    """
    t = TunelDuplo(alvo, falha_a_arrancar=TunelIndisponivel("devolveu 1"))
    with pytest.warns(RuntimeWarning, match="NÃO voltou"), \
            sentinela.medicao("fase-5z", tunel=t) as m:
        assert m.fase == "fase-5z"
    assert not alvo.exists(), "o sentinela sai de qualquer maneira"


def test_d3_um_tunel_que_nao_volta_nao_tapa_a_excepcao_da_fase(alvo):
    """Duas falhas ao mesmo tempo, e a que importa é a da fase.

    Se o `arrancar` levantasse, a mensagem que chegava a quem corre a fase era
    a do túnel, e a causa real — o que rebentou na geração — desaparecia.
    """
    t = TunelDuplo(alvo, falha_a_arrancar=TunelIndisponivel("devolveu 1"))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with pytest.raises(ValueError, match="a amostra 7"), \
                sentinela.medicao("fase-5z", tunel=t):
            raise ValueError("a amostra 7 veio vazia")


# --- D3: e o que o passo 5 NÃO acrescentou ao caminho do /api/estado ------ #

def test_d3_o_tunel_por_omissao_e_o_desta_maquina_e_hoje_e_o_ausente(
        alvo, monkeypatch):
    """Sem `PESSOABOT_TUNEL`, uma fase corre — é o estado desta máquina."""
    monkeypatch.delenv(tunel.VARIAVEL, raising=False)
    with sentinela.medicao("fase-5z"):
        assert alvo.exists()
    assert not alvo.exists()


def test_d3_o_caminho_do_estado_nao_pergunta_nada_ao_tunel(alvo, monkeypatch):
    """O portão **I4** não ganhou trabalho nenhum, e isto fixa-o.

    Os 7,9 µs sem ficheiro e 15,6 µs com ele continuam a descrever o que o I4
    mede porque quem fala com o túnel é o `medicao()`, que corre no processo da
    **fase** e nunca no do servidor. Se alguém puser uma pergunta ao túnel no
    `a_correr()` ou no `componente()`, este teste cai — e cai antes de o I4
    precisar de ser medido outra vez.
    """
    def recusar(*a, **kw):
        raise AssertionError("o /api/estado perguntou algo ao túnel")

    monkeypatch.setattr(tunel, "desta_maquina", recusar)
    monkeypatch.setattr(subprocess, "run", recusar)
    assert sentinela.a_correr() is None
    assert sentinela.componente().pronto is True
    sentinela.escrever("fase-5z")
    assert sentinela.a_correr() is not None
    assert sentinela.componente().pronto is False


# --- o passo 7 do serviço público: a janela, portão D5 -------------------- #

@pytest.fixture
def fase(tmp_path):
    """Uma pasta de fase com um `01-cru.jsonl` vazio, e o sentinela à parte."""
    amostras = tmp_path / "fase-x" / "01-cru.jsonl"
    amostras.parent.mkdir(parents=True)
    amostras.write_text("", encoding="utf-8")
    return amostras


def _amostra(amostras, n: int = 1) -> None:
    with amostras.open("a", encoding="utf-8") as f:
        for i in range(n):
            f.write(json.dumps({"pergunta_id": f"q{i:02d}",
                                "segundos": 34.0}) + "\n")


def test_d5_uma_fase_sob_o_ajudante_deixa_a_janela_sem_falhas(fase, tmp_path):
    """O portão D5, na metade que é mensurável com o formato de hoje.

    ⚠️ **A outra metade não é**, e está escrito na docstring da `Janela`: o D5
    dizia «os instantes de túnel de pé não se sobrepõem aos **instantes das
    amostras**», e os dez `01-cru.jsonl` das Fases 5B a 5Z **não têm instante
    nenhum** — têm `segundos`, que é uma duração. O que se mede é que o
    ficheiro das amostras **só cresceu dentro da janela**.
    """
    t = TunelDuplo(tmp_path / "sent")
    with sentinela.medicao("X", alvo=tmp_path / "sent", tunel=t,
                           amostras=fase):
        _amostra(fase, 3)
    j = sentinela.ler_janela(fase.parent / sentinela.NOME_DA_JANELA)

    assert j.falhas() == []
    assert [e for e, _, _ in t.registo] == ["parar", "arrancar"]
    assert j.parado is True and j.tunel == "duplo.service"
    assert j.bytes_no_inicio == 0 and j.bytes_no_fim > 0
    assert j.inicio <= j.mtime_no_fim <= j.fim, (
        "as amostras têm de ter sido escritas dentro da janela")


def test_d5_a_janela_apanha_amostras_escritas_fora_dela(fase):
    """O modo de falha que importa: a fase correu **sem** o ajudante.

    Construída à mão porque é o que um ficheiro assim pareceria: a janela de
    uma corrida, e um `01-cru.jsonl` tocado depois de o túnel voltar.
    """
    j = sentinela.Janela(
        fase="X", pid=1, inicio="2026-10-20T10:00:00Z",
        fim="2026-10-20T10:30:00Z", tunel="duplo.service", parado=True,
        amostras=str(fase), bytes_no_inicio=0, bytes_no_fim=4096,
        mtime_no_fim="2026-10-20T11:15:00Z")
    falhas = j.falhas()
    assert len(falhas) == 1
    assert "fora da janela" in falhas[0] and "sem o ajudante" in falhas[0]


def test_d5_uma_fase_que_nao_escreve_nada_e_uma_falha(fase, tmp_path):
    """Janela aberta e fechada sem o ficheiro crescer: ninguém mediu nada."""
    with sentinela.medicao("X", alvo=tmp_path / "sent", tunel=TunelDuplo(tmp_path / "sent"),
                           amostras=fase):
        pass
    j = sentinela.ler_janela(fase.parent / sentinela.NOME_DA_JANELA)
    assert any("não cresceu durante a janela" in f for f in j.falhas())


def test_d5_a_janela_existe_desde_o_inicio_e_diz_que_nao_fechou(fase, tmp_path):
    """Uma fase morta por `kill -9` não corre `finally` nenhum.

    Sem a escrita à abertura não deixava rasto, e quem lesse a pasta via
    amostras sem janela sem saber porquê. É a ideia do PID no sentinela —
    «um esquecido diagnostica-se» — aplicada ao registo.
    """
    gestor = sentinela.medicao("X", alvo=tmp_path / "sent",
                               tunel=TunelDuplo(tmp_path / "sent"),
                               amostras=fase)
    gestor.__enter__()
    try:
        aberta = sentinela.ler_janela(fase.parent / sentinela.NOME_DA_JANELA)
        assert aberta.fim is None
        assert any("nunca fechou" in f for f in aberta.falhas())
    finally:
        _amostra(fase)
        gestor.__exit__(None, None, None)
    assert sentinela.ler_janela(
        fase.parent / sentinela.NOME_DA_JANELA).falhas() == []


def test_d5_a_janela_fecha_mesmo_quando_a_fase_rebenta(fase, tmp_path):
    """Uma corrida que morreu a meio é a que mais precisa de deixar escrito."""
    with contextlib.suppress(RuntimeError), \
            sentinela.medicao("X", alvo=tmp_path / "sent",
                              tunel=TunelDuplo(tmp_path / "sent"),
                              amostras=fase):
        _amostra(fase)
        raise RuntimeError("a fase rebentou")
    j = sentinela.ler_janela(fase.parent / sentinela.NOME_DA_JANELA)
    assert j.fim is not None and j.falhas() == []


def test_d5_sem_tunel_a_janela_diz_que_nao_havia_porta(fase, tmp_path):
    """`parado: false` com `TunelAusente` — e **não** «o túnel esteve em baixo».

    É o estado desta máquina desde a §7.5, com o passo 6 desligado. Quem ler
    esta fase daqui a seis meses tem de poder distinguir «fechámos o URL
    durante a medição» de «não havia URL nenhum para fechar».
    """
    from src.web.tunel import TunelAusente
    with sentinela.medicao("X", alvo=tmp_path / "sent", tunel=TunelAusente(),
                           amostras=fase):
        _amostra(fase)
    j = sentinela.ler_janela(fase.parent / sentinela.NOME_DA_JANELA)
    assert j.parado is False
    assert "PESSOABOT_TUNEL" in j.tunel
    assert j.falhas() == [], "não haver túnel não é uma falha da janela"


def test_d5_sem_amostras_nomeadas_a_janela_queixa_se(tmp_path):
    """Uma janela que não nomeia ficheiro não diz nada sobre amostra nenhuma."""
    destino = tmp_path / "janela.json"
    with sentinela.medicao("X", alvo=tmp_path / "sent",
                           tunel=TunelDuplo(tmp_path / "sent"),
                           janela=destino):
        pass
    assert any("não nomeia ficheiro" in f
               for f in sentinela.ler_janela(destino).falhas())


def test_o_instante_da_janela_tem_o_formato_do_api_health():
    """O mesmo formato, de propósito: as duas datas vão ser lidas lado a lado.

    O `commit_em` do `/api/health` e o `inicio` da janela saem do mesmo
    repositório; em formatos diferentes, quem as compara desiste. E em UTC
    porque um fuso já custou uma medição a esta casa (`CONTROLO.md` §4, #46).
    """
    from src.web.saude import em_utc
    agora = sentinela.instante()
    assert agora.endswith("Z") and len(agora) == 20
    assert len(em_utc("2026-10-19T10:59:38-03:00")) == len(agora)
    assert sentinela.instante(0) == "1970-01-01T00:00:00Z"
