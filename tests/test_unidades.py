"""O passo 4 e o portão **D2** do [plano](../docs/PRODUCAO.md): as unidades.

**A afirmação do D2:** com `enable-linger`, fechar a sessão gráfica e reiniciar
a máquina deixam o serviço de pé e o URL a responder.

## O que se pode e o que não se pode fixar por teste

**Não se pode** medir o D2 aqui: fechar a sessão gráfica e reiniciar não são
coisas que um `pytest` corrido dentro dessa sessão possa fazer e ver o
resultado. Isso fica por medir até o dono correr os dois comandos que o
`src/web/instalar.py` imprime, e está escrito como pendente em vez de dado por
cumprido.

**Pode-se** fixar tudo o que torna o D2 possível, e é aqui que ele se perde na
prática — não num reinício dramático, mas numa linha de unidade errada que
ninguém lê:

| o que | o que se perdia sem isto |
|---|---|
| caminhos **absolutos** | o Ollama está fora do `PATH` por decisão da Fase 0, e o `PATH` de uma unidade de utilizador não é o do dono: um `ExecStart=ollama serve` falha com «not found» depois de funcionar na consola |
| `After=` e **não** `Requires=` | uma dependência rígida desfazia a decisão medida do portão I3 — o `/api/estado` reporta «Ollama em baixo» com o remédio em vez de o processo morrer |
| `WantedBy=default.target` | só `start` dava um serviço que corre hoje e não volta amanhã: a forma «funciona e não fica a funcionar», que é exactamente o que o D2 nega |
| nunca o checkout de **trabalho** | é a regra da §4, e a que uma instalação distraída quebra com um argumento por omissão |
| o interface e a porta **não** estarem na unidade | um `--host 0.0.0.0` numa unidade é o «copiado de um tutorial» que a Fase 6 listou como risco, e nenhum teste deste repositório o veria |

E o validador: **`systemd-analyze --user verify`**, o do próprio systemd. Um
`configparser` diz que o ficheiro é um INI; só o systemd diz que é uma unidade.
"""
from __future__ import annotations

import configparser
import shutil
import subprocess

import pytest

from src.web.app import HOST, PORTA
from src.web.instalar import DESTINO, main
from src.web.saude import RAIZ
from src.web.unidades import (
    DIRECTORIO,
    GERADORES,
    KEEP_ALIVE,
    NOME_OLLAMA,
    NOME_SERVICO,
    Alvo,
    ErroDeUnidade,
    escrever,
    recusar_o_trabalho,
    servico_ollama,
    servico_pessoabot,
)


@pytest.fixture
def alvo(tmp_path) -> Alvo:
    """Um alvo com `python` e `ollama` que **existem e são executáveis**.

    Existem porque o `systemd-analyze verify` verifica o `ExecStart` no disco, e
    um alvo de mentira dava um erro que não é o que se está a medir.
    """
    checkout = tmp_path / "servico"
    (checkout / ".venv" / "bin").mkdir(parents=True)
    py = checkout / ".venv" / "bin" / "python"
    ollama = tmp_path / "ollama"
    for f in (py, ollama):
        f.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        f.chmod(0o755)
    return Alvo(checkout=checkout, python=py, ollama=ollama)


def _ini(texto: str) -> configparser.ConfigParser:
    """A unidade como INI. `strict=False` porque o systemd permite chaves
    repetidas (`After=` duas vezes é legítimo) e o `configparser` não."""
    c = configparser.ConfigParser(strict=False)
    c.optionxform = str
    c.read_string(texto)
    return c


# --- caminhos absolutos ---------------------------------------------------- #

def test_d2_os_execstart_sao_absolutos(alvo):
    """O `PATH` de uma unidade de utilizador não é o do dono."""
    for gerar in GERADORES.values():
        exec_start = _ini(gerar(alvo))["Service"]["ExecStart"]
        comando = exec_start.split()[0]
        assert comando.startswith("/"), f"ExecStart relativo: {exec_start}"


def test_d2_nenhuma_unidade_invoca_um_nome_do_path(alvo):
    """`ollama`, `python` ou `uvicorn` soltos — o modo de falha da Fase 0."""
    for nome, gerar in GERADORES.items():
        exec_start = _ini(gerar(alvo))["Service"]["ExecStart"]
        primeiro = exec_start.split()[0]
        assert primeiro not in ("ollama", "python", "python3", "uvicorn"), (
            f"{nome} conta com o PATH: {exec_start}")


def test_d2_o_alvo_recusa_caminhos_relativos(tmp_path):
    with pytest.raises(ErroDeUnidade, match="absoluto"):
        Alvo(checkout=tmp_path, python="bin/python", ollama=tmp_path)  # type: ignore[arg-type]


def test_o_alvo_deriva_o_python_de_dentro_do_checkout(tmp_path):
    a = Alvo.de(tmp_path / "x")
    assert a.python.is_relative_to(a.checkout), (
        "o python de um checkout a correr o código de outro é o erro que o "
        "segundo checkout existe para impedir")


# --- a dependência que não pode endurecer ---------------------------------- #

def test_d2_o_servico_espera_o_ollama_e_nao_depende_dele(alvo):
    """`After=` sim, `Requires=` não — a decisão medida do portão I3."""
    u = _ini(servico_pessoabot(alvo))["Unit"]
    assert u["After"] == NOME_OLLAMA
    for chave in ("Requires", "BindsTo", "Requisite", "PartOf"):
        assert chave not in u, (
            f"{chave}={u.get(chave)} endurece a dependência: um Ollama em baixo "
            f"passava a levar com ele a página que sabia explicar a avaria")


def test_o_ollama_guarda_o_modelo_carregado(alvo):
    """Sem isto, a primeira pergunta de cada ciclo paga o carregamento inteiro."""
    assert _ini(servico_ollama(alvo))["Service"]["Environment"] == \
        f"OLLAMA_KEEP_ALIVE={KEEP_ALIVE}"
    assert KEEP_ALIVE.endswith("h"), "o ponto do campo é ser longo"


# --- ficar a correr, e não só correr --------------------------------------- #

def test_d2_as_duas_unidades_entram_no_default_target(alvo):
    """É isto que faz o `enable-linger` significar algo depois de um reinício."""
    for nome, gerar in GERADORES.items():
        assert _ini(gerar(alvo))["Install"]["WantedBy"] == "default.target", nome


def test_d2_o_tipo_e_exec_para_o_arranque_nao_mentir(alvo):
    """`Type=exec` e não `simple`: com `simple` o systemd dá a unidade por
    arrancada antes de o `execve` ter sucedido, e um `ExecStart` errado
    aparecia como «started» seguido de uma falha."""
    for gerar in GERADORES.values():
        assert _ini(gerar(alvo))["Service"]["Type"] == "exec"


# --- o checkout de trabalho, que nunca pode aparecer ----------------------- #

def test_d2_nenhuma_unidade_nomeia_o_checkout_de_trabalho(alvo):
    for nome, gerar in GERADORES.items():
        assert str(RAIZ) not in gerar(alvo), (
            f"{nome} nomeia o checkout de trabalho: a §4 do plano existe por "
            f"isto")


def test_o_workingdirectory_e_o_checkout_do_servico(alvo):
    assert _ini(servico_pessoabot(alvo))["Service"]["WorkingDirectory"] == \
        str(alvo.checkout)


def test_recusar_o_trabalho_recusa_exactamente_o_trabalho(tmp_path):
    recusar_o_trabalho(Alvo.de(tmp_path / "outro"), RAIZ)   # não levanta
    with pytest.raises(ErroDeUnidade, match="é o de trabalho"):
        recusar_o_trabalho(Alvo.de(RAIZ), RAIZ)


def test_o_instalador_recusa_instalar_sobre_o_checkout_de_trabalho(capsys):
    """A recusa como mecanismo e não como aviso, e é o que um `--destino`
    distraído encontra."""
    assert main(["--destino", str(RAIZ), "--ensaio"]) == 2
    assert "recusado" in capsys.readouterr().err


# --- o interface e a porta vivem no app.py, num sítio só ------------------- #

def test_i7_a_unidade_nao_declara_interface_nem_porta(alvo):
    """Um `--host 0.0.0.0` numa unidade não falha nenhum teste deste
    repositório — a não ser este."""
    texto = servico_pessoabot(alvo)
    for proibido in ("--host", "--port", "0.0.0.0", str(PORTA)):
        assert proibido not in texto, (
            f"«{proibido}» na unidade: o interface e a porta têm de vir do "
            f"app.py, senão a decisão que o portão I7′ protege vive em dois "
            f"sítios e um deles não se testa")
    assert "-m src.web" in texto


def test_o_modulo_executavel_usa_o_host_e_a_porta_do_app():
    """E o outro lado da mesma asserção: o `__main__` lê as constantes."""
    import inspect

    from src.web import __main__ as executavel
    fonte = inspect.getsource(executavel.main)
    assert "HOST" in fonte and "PORTA" in fonte
    assert "0.0.0.0" not in fonte
    assert HOST == "127.0.0.1"


# --- o validador do próprio systemd --------------------------------------- #

@pytest.mark.skipif(shutil.which("systemd-analyze") is None,
                    reason="sem systemd-analyze nesta máquina")
def test_d2_o_systemd_aceita_as_duas_unidades(alvo, tmp_path):
    """Um `configparser` diz que é um INI; só o systemd diz que é uma unidade.

    Filtra-se o que ele diz sobre **outras** unidades do sistema: numa máquina
    real ele comenta as que já lá estão (`spice-vdagent.service`, observado), e
    isso não é deste repositório.
    """
    d = tmp_path / "unidades"
    escrever(alvo, d)
    for nome in GERADORES:
        r = subprocess.run(("systemd-analyze", "--user", "verify",
                            str(d / nome)), capture_output=True, text=True)
        meus = [ln for ln in r.stderr.splitlines() if ln.startswith(nome)]
        assert not meus, f"{nome}: {meus}"


# --- o ensaio não toca em nada -------------------------------------------- #

def test_o_ensaio_nao_cria_nada(tmp_path, capsys):
    destino = tmp_path / "nao-deve-nascer"
    assert main(["--destino", str(destino), "--ensaio"]) == 0
    assert not destino.exists(), "o ensaio criou o checkout"
    saida = capsys.readouterr().out
    assert "ENSAIO" in saida
    assert "git clone" in saida and "enable-linger" in saida
    assert "por medir" in saida, (
        "o ensaio tem de dizer que o D2 não está cumprido")


def test_os_caminhos_por_omissao_sao_desta_maquina_e_nao_do_cwd():
    """Dois caminhos que, relativos, davam a mesma classe de defeito do #39."""
    assert DESTINO.is_absolute() and DIRECTORIO.is_absolute()
    assert DIRECTORIO.name == "user" and DIRECTORIO.parent.name == "systemd"
    assert NOME_OLLAMA.endswith(".service") and NOME_SERVICO.endswith(".service")
