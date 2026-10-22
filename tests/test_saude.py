"""O portão **D1** do [plano do serviço público](../docs/PRODUCAO.md) §6:
a saúde não mente.

**A afirmação.** `GET /api/health` nomeia o código a correr: o `sha` devolvido é
o do `HEAD` do **checkout do serviço**, em 3 arranques seguidos, e com o Ollama
em baixo o `status` **não** é `ok`.

## As três coisas que este ficheiro mede, e porque é que a 2.ª é a que importa

1. **O `sha` é o do `HEAD`.** Comparado com um `git rev-parse` corrido à parte,
   em **três processos** e não três chamadas no mesmo — «arranque» é o que o
   campo afirma, e três chamadas numa importação só não são três arranques.
2. **O `sha` é o do checkout do *serviço*, e não o do directório de trabalho.**
   Medido com um checkout construído de propósito e um processo lançado **lá
   dentro**: o `sha` que sai continua a ser o deste repositório. Sem esta
   asserção o D1 passava numa máquina com um checkout só e **não dizia nada
   sobre a máquina real**, que tem dois (§4 do plano) — é palavra por palavra o
   defeito que o sentinela teve com o `data/.medicao-a-correr` relativo
   (`CONTROLO.md` §4 #39), e aqui está medido em vez de evitado por cuidado.
3. **O `status` não mente nos dois sentidos.** Com o Ollama em baixo não é `ok`;
   com tudo de pé é `ok` **embora `pronto` seja `false`** — que é o §6 ponto 2
   do plano, e a razão de a sonda ler `pode_perguntar` e não `pronto`. Uma sonda
   que exigisse `pronto` reprovava todos os arranques saudáveis.

## E a leitura à importação, fixada por inspecção do código

O `sha` lê-se **uma vez, à importação** (`app.LANCAMENTO`), porque o campo
afirma o que está em memória e não o que está no disco agora: depois de um
`git checkout` no checkout do serviço, o `uvicorn` continua a correr os módulos
que importou, e um `git rev-parse` por pedido nomeava código que não está a
correr. Isso não se mede com um cliente — mede-se a olhar para a função, e é o
que o `test_d1_o_sha_nao_se_le_por_pedido` faz, com a disciplina do
`test_i1_a_api_constroi_o_pipeline_com_os_mesmos_parametros_do_cli`.
"""
from __future__ import annotations

import ast
import dataclasses
import inspect
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.web import app as modulo_app
from src.web import sentinela
from src.web.app import LANCAMENTO, Servico, criar_app
from src.web.saude import RAIZ, Lancamento, em_utc, ler_lancamento

from .test_perguntar import GeradorDeterminista

#: Importar o `app` e imprimir o `sha`: um arranque, visto de fora. 0,36 s
#: medidos, e é o que torna «três arranques seguidos» mensurável de verdade.
UM_ARRANQUE = "import src.web.app as a; print(a.LANCAMENTO.sha or '')"


def _git(*args: str, cwd: Path | str = RAIZ) -> str:
    return subprocess.run(("git", "-C", str(cwd), *args), check=True,
                          capture_output=True, text=True).stdout.strip()


def _se_o_head_andou() -> str:
    """O postscriptum que nomeia a causa mais provável num checkout partilhado.

    O `sha` lê-se **à importação** (ver o cabeçalho) e o `git` destas asserções
    corre-se **agora**: entre os dois momentos outra sessão pode ter comutado de
    ramo neste checkout, e então a falha não é do serviço — é da medição. Em
    2026-10-21 foi o que aconteceu, e a mensagem de falha culpou o directório de
    trabalho: uma sessão inteira foi atrás de um defeito que não existia. Daí
    esta frase, que acrescenta à falha em vez de a esconder.
    """
    try:
        agora = _git("rev-parse", "--short", "HEAD")
    except Exception:  # o `git` em falta já tem o seu próprio teste
        return ""
    if agora == LANCAMENTO.sha:
        return ""
    return (f"\nATENÇÃO: o HEAD andou desde a importação "
            f"({LANCAMENTO.sha} -> {agora}) — alguém comutou de ramo neste "
            f"checkout a meio da corrida, e a falha é disso e não do serviço. "
            f"Repita a medição num worktree próprio.")


def _arrancar(cwd: Path | str) -> str:
    """O `sha` que um processo novo reporta, lançado em `cwd`."""
    r = subprocess.run((sys.executable, "-c", UM_ARRANQUE), cwd=str(cwd),
                       capture_output=True, text=True,
                       env=os.environ | {"PYTHONPATH": str(RAIZ)})
    assert r.returncode == 0, r.stderr[-2000:]
    return r.stdout.strip()


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    """Um checkout **outro**, com um commit próprio e um `sha` diferente.

    É o segundo checkout da §4 do plano, reduzido ao que a asserção precisa.
    """
    d = tmp_path / "outro"
    d.mkdir()
    _git("init", "-q", "-b", "main", cwd=d)
    _git("config", "user.email", "t@t", cwd=d)
    _git("config", "user.name", "t", cwd=d)
    (d / "a.txt").write_text("outro checkout\n", encoding="utf-8")
    _git("add", "a.txt", cwd=d)
    _git("-c", "commit.gpgsign=false", "commit", "-q", "-m", "outro", cwd=d)
    return d


# --- 1. o sha é o do HEAD, em três arranques ------------------------------- #

def test_d1_o_sha_e_o_do_head_em_tres_arranques():
    """Três processos, e o `sha` de cada um igual ao `git` corrido à parte."""
    esperado = _git("rev-parse", "--short", "HEAD")
    arranques = [_arrancar(RAIZ) for _ in range(3)]
    assert arranques == [esperado] * 3, (
        f"os três arranques deram {arranques}, o HEAD é {esperado}")


def test_d1_a_rota_devolve_o_mesmo_sha_que_o_git():
    esperado = _git("rev-parse", "--short", "HEAD")
    with TestClient(criar_app(Servico(gerador=GeradorDeterminista()))) as c:
        d = c.get("/api/health").json()
    assert d["sha"] == esperado, (
        f"a rota deu {d['sha']!r} e o git diz {esperado!r}" + _se_o_head_andou())
    esperado_em = em_utc(_git("show", "-s", "--format=%cI", "HEAD"))
    assert d["commit_em"] == esperado_em, (
        f"a rota deu {d['commit_em']!r} e o git diz {esperado_em!r}"
        + _se_o_head_andou())


# --- 2. o checkout do serviço, e não o directório de trabalho -------------- #

def test_d1_o_sha_e_do_checkout_do_servico_e_nao_do_cwd(checkout: Path):
    """A asserção que faz o D1 dizer algo sobre uma máquina com dois checkouts.

    Lança-se o processo **dentro** do outro checkout. Um `git` sem `-C` — ou com
    `-C .` — respondia com sucesso e com o `sha` errado, que é o modo de falha
    que não dá erro.
    """
    do_outro = _git("rev-parse", "--short", "HEAD", cwd=checkout)
    assert do_outro != LANCAMENTO.sha, "o duplo tem de ter um sha diferente"
    assert _arrancar(checkout) == LANCAMENTO.sha, (
        "o sha seguiu o directório de trabalho em vez do checkout do serviço"
        + _se_o_head_andou())


def test_a_mensagem_de_falha_nomeia_o_head_que_andou(monkeypatch):
    """O postscriptum só corre numa falha — ou seja, quando ninguém está a olhar.

    Sem este teste a frase era código que nunca se exercita e que apodrece até
    ao dia em que é precisa, que é exactamente o dia mau. Mede-se nos dois
    sentidos: calada com o `HEAD` quieto, e a nomeá-lo quando ele andou.
    """
    assert _se_o_head_andou() == "", "com o HEAD quieto a frase tem de calar-se"
    monkeypatch.setattr(sys.modules[__name__], "LANCAMENTO",
                        dataclasses.replace(LANCAMENTO, sha="0000000"))
    aviso = _se_o_head_andou()
    assert "0000000" in aviso, aviso
    assert _git("rev-parse", "--short", "HEAD") in aviso, aviso
    assert "worktree" in aviso, "a frase tem de dizer o que fazer a seguir"


def test_d1_a_raiz_e_derivada_do_modulo_e_e_absoluta():
    """O `RAIZ` é o checkout de onde o módulo foi importado, e não um relativo."""
    assert RAIZ.is_absolute()
    assert (RAIZ / "src" / "web" / "saude.py").is_file()
    assert (RAIZ / ".git").exists()


def test_ler_lancamento_le_o_checkout_que_lhe_dao(checkout: Path):
    """O argumento existe para o teste acima, e tem de funcionar."""
    x = ler_lancamento(checkout)
    assert x.sha == _git("rev-parse", "--short", "HEAD", cwd=checkout)
    assert x.erro == ""
    assert x.etiqueta is None, "o duplo nasce sem etiquetas"


def test_a_etiqueta_sai_quando_existe(checkout: Path):
    """`etiqueta` é `None` hoje porque não há etiquetas, não porque não se lê.

    O passo 8 do plano cria-as — o recuo é `git checkout` de uma etiqueta —, e
    sem este teste a leitura só seria exercitada quando alguém dependesse dela.
    """
    assert ler_lancamento(checkout).etiqueta is None
    _git("tag", "servico-2026-10-19", cwd=checkout)
    assert ler_lancamento(checkout).etiqueta == "servico-2026-10-19"


# --- 3. o status não mente, nos dois sentidos ------------------------------ #

class GeradorEmBaixo(GeradorDeterminista):
    """O Ollama que não responde: a falha mais provável de todas."""

    def disponivel(self) -> bool:
        return False


@pytest.fixture
def sem_medicao(tmp_path, monkeypatch):
    """Aponta o sentinela a um ficheiro que não existe, para o estado ser deste
    teste e não desta máquina — que pode ter uma fase a correr."""
    monkeypatch.setenv(sentinela.VARIAVEL, str(tmp_path / "nenhum"))


def test_d1_com_o_ollama_em_baixo_o_status_nao_e_ok(sem_medicao):
    with TestClient(criar_app(Servico(gerador=GeradorEmBaixo()))) as c:
        d = c.get("/api/health").json()
    assert d["status"] != "ok"
    assert d["pode_perguntar"] is False
    assert any("ollama" in m for m in d["motivos"]), d["motivos"]
    # E continua a nomear o código: uma sonda degradada que não diz de onde
    # veio o código não serve para confirmar um recuo, que é para o que ela é.
    assert d["sha"] == LANCAMENTO.sha


def test_d1_com_tudo_de_pe_e_ok_embora_pronto_seja_falso(sem_medicao):
    """O §6 ponto 2, medido: é por isto que a sonda lê `pode_perguntar`.

    Sem pipeline construído o índice **não está verificado**, logo o `pronto` do
    `/api/estado` é `false` — e o arranque é saudável. Uma sonda sobre `pronto`
    reprovava-o.
    """
    with TestClient(criar_app(Servico(gerador=GeradorDeterminista()))) as c:
        saude = c.get("/api/health").json()
        estado = c.get("/api/estado").json()
    assert estado["pronto"] is False, "o duplo devia ter o índice não verificado"
    assert saude["status"] == "ok", saude["motivos"]
    assert saude["pode_perguntar"] is True
    assert saude["motivos"] == []
    assert saude["indice"]["aceito"] is False


def test_d1_uma_medicao_a_correr_da_degradado_e_diz_qual(tmp_path, monkeypatch):
    """Não é avaria, e mesmo assim o serviço não responde — §3.3 do plano.

    Sob a saída D o URL **cai** durante as medições (passo 5), e este é o campo
    que explica a queda a quem a vê.
    """
    alvo = tmp_path / "sentinela"
    monkeypatch.setenv(sentinela.VARIAVEL, str(alvo))
    sentinela.escrever("fase-7-ensaio")
    with TestClient(criar_app(Servico(gerador=GeradorDeterminista()))) as c:
        d = c.get("/api/health").json()
    assert d["status"] == "degradado"
    assert d["medicao_a_correr"] is True
    assert any("fase-7-ensaio" in m for m in d["motivos"]), d["motivos"]


def test_sem_git_nao_ha_sha_e_isso_vai_ao_fio(tmp_path):
    """Um directório que não é checkout: `sha` a `None` e o motivo em texto.

    O `status` do serviço deixa de ser `ok` por isto (ver `app.health`): uma
    sonda que devolve `ok` sem saber nomear o código é pior do que não haver
    sonda.
    """
    x = ler_lancamento(tmp_path)
    assert x == Lancamento(sha=None, etiqueta=None, commit_em=None,
                           erro=x.erro)
    assert x.erro, "a falha tem de ir ao fio em texto"
    assert x.nomeia_o_codigo is False


def test_git_fora_do_path_nao_levanta(monkeypatch, tmp_path):
    """O `git` ausente é uma das três faltas previstas, e não rebenta a sonda."""
    monkeypatch.setenv("PATH", str(tmp_path))
    x = ler_lancamento(RAIZ)
    assert x.sha is None
    assert "PATH" in x.erro


# --- a leitura à importação, fixada por inspecção -------------------------- #

def test_d1_o_sha_nao_se_le_por_pedido():
    """A rota não chama o `git`: lê o `LANCAMENTO` que a importação fixou.

    Isto não se mede com um cliente — os dois desenhos devolvem o mesmo `sha`
    enquanto o `HEAD` não se mexer, e o errado só aparece depois de um
    `git checkout` com o serviço de pé, que é quando não há ninguém a olhar.
    Mede-se a olhar para o código, com a disciplina do portão I1.
    """
    fonte = textwrap.dedent(inspect.getsource(criar_app))
    corpo = next(n for n in ast.walk(ast.parse(fonte))
                 if isinstance(n, ast.FunctionDef) and n.name == "health")
    chamadas = {getattr(n.func, "id", getattr(n.func, "attr", ""))
                for n in ast.walk(corpo) if isinstance(n, ast.Call)}
    assert not chamadas & {"ler_lancamento", "run", "check_output", "Popen"}, (
        f"a rota /api/health passou a interrogar o git por pedido: {chamadas}")
    assert isinstance(modulo_app.LANCAMENTO, Lancamento)


def test_em_utc_normaliza_o_desvio_do_git():
    """`%cI` traz o desvio de quem fez o commit; duas sondas comparavam fusos."""
    assert em_utc("2026-10-19T10:59:38-03:00") == "2026-10-19T13:59:38Z"
    assert em_utc("2026-10-19T13:59:38+00:00") == "2026-10-19T13:59:38Z"
    assert em_utc("não é uma data") is None
