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
import pathlib
import shutil
import subprocess

import pytest

from src.web import instalar
from src.web.app import HOST, PORTA
from src.web.instalar import (
    DESTINO,
    Falhou,
    clonar,
    conferir_sha,
    contar_acessos,
    main,
)
from src.web.saude import RAIZ
from src.web.unidades import (
    DIRECTORIO,
    GERADORES,
    KEEP_ALIVE,
    NOME_OLLAMA,
    NOME_SERVICO,
    NOME_TUNEL,
    Alvo,
    ErroDeUnidade,
    ListaVazia,
    escrever,
    ler_convidados,
    recusar_o_trabalho,
    servico_ollama,
    servico_pessoabot,
    servico_tunel,
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
    cloudflared = tmp_path / "cloudflared"
    for f in (py, ollama, cloudflared):
        f.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        f.chmod(0o755)
    return Alvo(checkout=checkout, python=py, ollama=ollama,
                cloudflared=cloudflared)


@pytest.fixture
def convidados(tmp_path):
    """Uma lista com um endereço, um domínio com curinga, um comentário e ruído."""
    f = tmp_path / "convidados"
    f.write_text("# quem pode entrar\n"
                 "alguem@exemplo.pt\n"
                 "\n"
                 "*@outro.exemplo.pt   # a casa toda\n", encoding="utf-8")
    return f


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


# --- passo 6: fechar antes de abrir --------------------------------------- #

def test_d4_a_lista_de_convidados_le_se_e_ignora_comentarios(convidados):
    assert ler_convidados(convidados) == ("alguem@exemplo.pt",
                                          "*@outro.exemplo.pt")


def test_d4_sem_lista_nao_ha_tunel_e_isso_e_uma_excepcao(tmp_path):
    """A asserção que torna «fechar antes de abrir» mecanismo e não conselho.

    Três estados dariam, sem isto, uma unidade **sem** `--allowed-mail` — um
    túnel aberto ao mundo com o corpus do outro lado, e sem erro nenhum a
    dizê-lo. É a forma «não dá erro: dá respostas erradas» com o pior resultado
    possível desta casa.
    """
    with pytest.raises(ListaVazia, match="não há lista"):
        ler_convidados(tmp_path / "nao-existe")

    vazia = tmp_path / "vazia"
    vazia.write_text("", encoding="utf-8")
    with pytest.raises(ListaVazia, match="nenhum endereço"):
        ler_convidados(vazia)

    so_comentarios = tmp_path / "comentada"
    so_comentarios.write_text("# ninguém ainda\n\n   \n", encoding="utf-8")
    with pytest.raises(ListaVazia, match="nenhum endereço"):
        ler_convidados(so_comentarios)


def test_d4_uma_linha_sem_arroba_e_erro_e_nao_um_convidado_silencioso(tmp_path):
    """Senão era um convidado que nunca entra, e ninguém saberia porquê."""
    f = tmp_path / "convidados"
    f.write_text("alguem@exemplo.pt\nalguem.exemplo.pt\n", encoding="utf-8")
    with pytest.raises(ErroDeUnidade, match="não são endereços"):
        ler_convidados(f)


def test_d4_a_unidade_do_tunel_recusa_nascer_sem_convidados(alvo):
    with pytest.raises(ListaVazia, match="túnel aberto ao mundo"):
        servico_tunel(alvo, ())


def test_d4_a_unidade_do_tunel_leva_a_lista_e_o_caminho_absoluto(alvo,
                                                                 convidados):
    texto = servico_tunel(alvo, ler_convidados(convidados))
    exec_start = _ini(texto)["Service"]["ExecStart"]
    assert exec_start.split()[0] == str(alvo.cloudflared), (
        "o cloudflared está fora do PATH, como o Ollama")
    assert "--allowed-mail alguem@exemplo.pt,*@outro.exemplo.pt" in exec_start
    assert f"--url http://{HOST}:{PORTA}" in exec_start, (
        "o interface e a porta vêm do app.py, aqui como no __main__.py")
    assert _ini(texto)["Unit"]["After"] == NOME_SERVICO
    assert "Requires" not in _ini(texto)["Unit"]


def test_d4_escrever_sem_lista_da_duas_unidades_e_com_lista_da_tres(
        alvo, tmp_path, convidados):
    sem = escrever(alvo, tmp_path / "sem", convidados=None)
    assert set(sem) == set(GERADORES), (
        "sem lista não se escreve túnel, e isso não é erro: é o passo 6 "
        "ainda não dado")

    com = escrever(alvo, tmp_path / "com", convidados=convidados)
    assert set(com) == set(GERADORES) | {NOME_TUNEL}
    assert "--allowed-mail" in com[NOME_TUNEL].read_text(encoding="utf-8")


@pytest.mark.skipif(shutil.which("systemd-analyze") is None,
                    reason="sem systemd-analyze nesta máquina")
def test_d4_o_systemd_aceita_a_unidade_do_tunel(alvo, tmp_path, convidados):
    d = tmp_path / "unidades"
    escrever(alvo, d, convidados=convidados)
    r = subprocess.run(("systemd-analyze", "--user", "verify",
                        str(d / NOME_TUNEL)), capture_output=True, text=True)
    meus = [ln for ln in r.stderr.splitlines() if ln.startswith(NOME_TUNEL)]
    assert not meus, meus


# --- o instrumento do D4, e o defeito que ele quase teve ------------------ #

#: Um registo real desta máquina, recortado: arranque, avisos do Hugging Face,
#: uma barra de progresso, e **três** pedidos.
REGISTO = """\
Starting pessoabot.service - PessoaBot, o serviço público...
INFO:     Started server process [477112]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:32856 - "GET /api/health HTTP/1.1" 200 OK
INFO:     127.0.0.1:51494 - "POST /api/perguntar HTTP/1.1" 200 OK
Warning: You are sending unauthenticated requests to the HF Hub.
Loading weights:   0%|          | 0/199 [00:00<?, ?it/s]Loading weights: 100%|#| 199/199
INFO:     127.0.0.1:43572 - "GET /api/health HTTP/1.1" 200 OK
"""


def test_d4_o_contador_conta_pedidos_e_nao_linhas():
    """Contar linhas fazia o D4 falhar por o modelo ter carregado.

    O registo da unidade leva o arranque, os avisos do Hugging Face e as barras
    de progresso dos pesos — e todos crescem entre a contagem de antes e a de
    depois sem ninguém ter pedido nada.
    """
    assert contar_acessos(REGISTO) == 3
    assert contar_acessos("") == 0
    sem_pedidos = "\n".join(ln for ln in REGISTO.splitlines()
                            if '"GET ' not in ln and '"POST ' not in ln)
    assert contar_acessos(sem_pedidos) == 0
    assert len(sem_pedidos.splitlines()) == 6, (
        "o recorte sem pedidos tem de continuar a ter linhas, senão este "
        "teste não distingue «não conta ruído» de «não conta nada»")


# --- o clone, e o defeito que a segunda instalação encontrou -------------- #

def _repo(d: pathlib.Path, ficheiro: str, mensagem: str) -> str:
    """Um commit num repositório, e o seu `sha` curto."""
    (d / ficheiro).write_text(mensagem + "\n", encoding="utf-8")
    subprocess.run(("git", "-C", str(d), "add", ficheiro), check=True,
                   capture_output=True)
    subprocess.run(("git", "-C", str(d), "-c", "commit.gpgsign=false",
                    "commit", "-q", "-m", mensagem), check=True,
                   capture_output=True)
    return subprocess.run(("git", "-C", str(d), "rev-parse", "--short", "HEAD"),
                          check=True, capture_output=True,
                          text=True).stdout.strip()


@pytest.fixture
def par(tmp_path, monkeypatch):
    """Um checkout de trabalho e um do serviço já clonado dele — a máquina a sério.

    O `clonar` clona do `RAIZ` do módulo, logo é o `RAIZ` que se troca: assim o
    teste exercita o caminho real sem tocar neste repositório.
    """
    trabalho = tmp_path / "trabalho"
    trabalho.mkdir()
    subprocess.run(("git", "init", "-q", "-b", "main", str(trabalho)),
                   check=True, capture_output=True)
    for chave, valor in (("user.email", "t@t"), ("user.name", "t")):
        subprocess.run(("git", "-C", str(trabalho), "config", chave, valor),
                       check=True, capture_output=True)
    primeiro = _repo(trabalho, "a.txt", "primeiro")
    monkeypatch.setattr(instalar, "RAIZ", trabalho)

    servico = tmp_path / "servico"
    alvo = Alvo.de(servico)
    clonar(alvo, primeiro, ensaio=False)
    return trabalho, alvo, primeiro


def _head(d: pathlib.Path) -> str:
    return subprocess.run(("git", "-C", str(d), "rev-parse", "--short", "HEAD"),
                          check=True, capture_output=True,
                          text=True).stdout.strip()


def test_reinstalar_numa_referencia_nova_busca_os_objectos_primeiro(par):
    """**O defeito que a segunda instalação desta máquina encontrou.**

    Um clone feito ontem não tem os objectos de hoje, e o `git` não diz «esse
    commit não existe»: não reconhecendo a referência, interpreta-a como um
    **caminho** e responde `--detach does not take a path argument '79e4dbb'`,
    que manda quem o lê procurar um erro de sintaxe. É o caminho de que o
    **recuo do passo 8** depende — mudar a referência de um checkout que já
    existe — logo falhava no dia em que fosse preciso.
    """
    trabalho, alvo, primeiro = par
    assert _head(alvo.checkout) == primeiro

    segundo = _repo(trabalho, "b.txt", "segundo")
    assert segundo != primeiro
    clonar(alvo, segundo, ensaio=False)
    assert _head(alvo.checkout) == segundo, (
        "o checkout do serviço não seguiu para a referência nova")


def test_recuar_para_uma_etiqueta_anterior_tambem_funciona(par):
    """O passo 8 ao contrário: da referência nova para a antiga, por etiqueta."""
    trabalho, alvo, primeiro = par
    subprocess.run(("git", "-C", str(trabalho), "tag", "servico-1"),
                   check=True, capture_output=True)
    segundo = _repo(trabalho, "b.txt", "segundo")
    clonar(alvo, segundo, ensaio=False)
    clonar(alvo, "servico-1", ensaio=False)
    assert _head(alvo.checkout) == primeiro
    assert not (alvo.checkout / "b.txt").exists()


def test_uma_referencia_que_nao_existe_falha_a_falar_da_referencia(par):
    """E não a falar de caminhos, que é o que o `git` faz sozinho."""
    _, alvo, _ = par
    with pytest.raises(Falhou, match="não existe no checkout do serviço"):
        clonar(alvo, "0000000", ensaio=False)


# --- verificar pelo serviço, e não pelo código de saída dos comandos ------ #

def test_a_instalacao_confere_se_o_processo_foi_substituido():
    """**O segundo defeito que a segunda instalação encontrou.**

    `systemctl --user enable --now` arranca uma unidade **inactiva** e não toca
    numa que já corra: o checkout passou a `79e4dbb` e o processo continuou a
    servir `734f77a`, com os dois comandos a devolver 0 e sem erro nenhum.
    Num recuo (passo 8) é o pior resultado possível — o `git checkout` «sucede»,
    o `systemctl` «sucede», e o código doente continua a responder.

    A defesa não é cuidado: é o predicado do portão **D1** aplicado como
    verificação de instalação, que é a disciplina que o plano transfere do
    repositório irmão — verifica-se pela **saúde do serviço**, nunca pelo
    código de saída do que se correu.
    """
    assert conferir_sha("79e4dbb", "79e4dbb") is None

    queixa = conferir_sha("79e4dbb", "734f77a")
    assert queixa is not None
    assert "79e4dbb" in queixa and "734f77a" in queixa
    assert "não foi substituído" in queixa

    assert "não respondeu" in (conferir_sha("79e4dbb", None) or "")
    assert "de que commit" in (conferir_sha(None, "79e4dbb") or "")


def test_a_instalacao_reinicia_e_nao_so_activa():
    """O `restart` em si **nenhum teste o vê correr**, e isto é o que resta.

    Tirá-lo não faz falhar asserção nenhuma deste ficheiro: quem o apanha é a
    `conferir_sha` numa instalação **a sério**, contra um serviço que já estava
    de pé. Então prende-se por inspecção, que é honesto sobre o que mede — a
    presença da chamada — e impede a regressão de voltar sem ninguém notar.
    Mesma disciplina do portão I1 sobre as duas chamadas a `Pipeline(...)`.
    """
    import ast
    import inspect
    import textwrap

    from src.web.instalar import instalar_unidades
    fonte = textwrap.dedent(inspect.getsource(instalar_unidades))
    comandos = [n.value for n in ast.walk(ast.parse(fonte))
                if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    assert "restart" in comandos, (
        "sem o `restart`, uma instalação sobre um serviço a correr troca o "
        "checkout e não troca o processo — e os dois `systemctl` devolvem 0")
    assert "enable" in comandos, "o `enable` é o que faz o linger significar algo"
