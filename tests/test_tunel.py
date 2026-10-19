"""O túnel: a indirecção, e as duas maneiras de o mecanismo ficar desligado.

Passo 5 do `PRODUCAO.md`, a metade que não é a ordem (essa está no
`test_sentinela.py`). O que estes testes protegem são as duas decisões do
cabeçalho do `src/web/tunel.py`:

1. **A ausência é declarada, e um nome errado não é ausência.** Sem
   `PESSOABOT_TUNEL` há `TunelAusente` e uma fase corre — é o estado desta
   máquina em 2026-10-18, verificado: nem `cloudflared` nem `tailscale`. Com a
   variável definida para uma unidade que não existe, **falha** — porque
   `systemctl --user stop` de uma unidade inexistente devolve **0**, e sem a
   verificação de `LoadState` isso dava «túnel parado» com o URL de pé. É o
   mecanismo silenciosamente desligado da correcção 39, agora com o público do
   outro lado.
2. **A simetria é falsa de propósito:** parar que falha levanta, arrancar que
   falha avisa.

⚠️ **Nenhum teste deste ficheiro toca em unidade nenhuma desta máquina.** O
`systemctl` é substituído por um duplo que registra os argumentos; o único
`systemctl` real que aqui corre é o do teste marcado, e é um `show -p
LoadState` de uma unidade inventada — uma leitura, que não arranca nem para
nada.
"""
from __future__ import annotations

import subprocess
import warnings

import pytest

from src.web import tunel


class _Systemctl:
    """Um `subprocess.run` de mentira, que registra o que lhe pediram.

    `codigos` mapeia o verbo (`show`, `stop`, `start`) ao código de saída, e o
    `LoadState` responde-se à parte — é a distinção que importa aqui.
    """

    def __init__(self, *, carregada: str = "loaded", codigos=None, erro=None):
        self.carregada = carregada
        self.codigos = codigos or {}
        self.erro = erro
        self.chamadas: list[list[str]] = []

    def __call__(self, args, **kw):
        assert args[:2] == ["systemctl", "--user"], "sempre `--user` (§5.1)"
        self.chamadas.append(args[2:])
        if self.erro is not None:
            raise self.erro
        verbo = args[2]
        if verbo == "show":
            return subprocess.CompletedProcess(args, 0, self.carregada, "")
        return subprocess.CompletedProcess(args, self.codigos.get(verbo, 0),
                                           "", "falhou por desenho do teste")

    @property
    def verbos(self) -> list[str]:
        return [c[0] for c in self.chamadas]


@pytest.fixture
def systemctl(monkeypatch):
    def _montar(**kw):
        duplo = _Systemctl(**kw)
        monkeypatch.setattr(subprocess, "run", duplo)
        return duplo
    return _montar


# --- a ausência, que é o estado desta máquina ----------------------------- #

def test_sem_a_variavel_o_tunel_e_o_ausente(monkeypatch):
    """Hoje não há túnel, e uma fase tem de poder correr."""
    monkeypatch.delenv(tunel.VARIAVEL, raising=False)
    t = tunel.desta_maquina()
    assert isinstance(t, tunel.TunelAusente)
    t.parar()
    t.arrancar()  # não levanta: não há alcance a fechar


def test_o_ausente_diz_que_nao_faz_nada(monkeypatch):
    """Um no-op anónimo era indistinguível de um túnel que não parou."""
    monkeypatch.delenv(tunel.VARIAVEL, raising=False)
    assert tunel.VARIAVEL in tunel.desta_maquina().nome


def test_uma_variavel_vazia_ou_de_espacos_conta_como_ausente(monkeypatch):
    for bruto in ("", "   "):
        monkeypatch.setenv(tunel.VARIAVEL, bruto)
        assert isinstance(tunel.desta_maquina(), tunel.TunelAusente)


def test_com_a_variavel_o_tunel_e_a_unidade_nomeada(monkeypatch):
    monkeypatch.setenv(tunel.VARIAVEL, "pessoabot-tunel.service")
    t = tunel.desta_maquina()
    assert isinstance(t, tunel.TunelSystemd)
    assert t.nome == "pessoabot-tunel.service"


def test_a_variavel_e_lida_a_cada_chamada_e_nao_na_importacao(monkeypatch):
    """O `uvicorn` e um `gerar_amostras.py` são processos de vida longa."""
    monkeypatch.delenv(tunel.VARIAVEL, raising=False)
    assert isinstance(tunel.desta_maquina(), tunel.TunelAusente)
    monkeypatch.setenv(tunel.VARIAVEL, "outra.service")
    assert tunel.desta_maquina().nome == "outra.service"


# --- o nome errado, que é o modo de falha que esta classe existe para fechar #

def test_uma_unidade_que_nao_existe_falha_em_vez_de_dizer_que_parou(systemctl):
    """A verificação do `LoadState`, e a razão de ela existir.

    `systemctl --user stop` de uma unidade inexistente devolve **0**. Sem esta
    pergunta, uma variável mal escrita dava «túnel parado» com o URL de pé —
    e o público a aquecer o chip durante uma fase.
    """
    s = systemctl(carregada="not-found", codigos={"stop": 0})
    with pytest.raises(tunel.TunelIndisponivel, match="não está instalada"):
        tunel.TunelSystemd("inventada.service").parar()
    assert "stop" not in s.verbos, "não se para o que não se sabe que existe"


def test_o_stop_so_corre_depois_de_a_unidade_ser_conhecida(systemctl):
    s = systemctl()
    tunel.TunelSystemd("tunel.service").parar()
    assert s.verbos == ["show", "stop"]


def test_o_arrancar_verifica_a_unidade_do_mesmo_modo(systemctl):
    s = systemctl(carregada="masked")
    with pytest.raises(tunel.TunelIndisponivel, match="masked"):
        tunel.TunelSystemd("tunel.service").arrancar()
    assert s.verbos == ["show"]


def test_o_codigo_de_saida_do_stop_nao_e_ignorado(systemctl):
    systemctl(codigos={"stop": 5})
    with pytest.raises(tunel.TunelIndisponivel, match="devolveu 5"):
        tunel.TunelSystemd("tunel.service").parar()


def test_o_codigo_de_saida_do_start_nao_e_ignorado(systemctl):
    systemctl(codigos={"start": 1})
    with pytest.raises(tunel.TunelIndisponivel, match="devolveu 1"):
        tunel.TunelSystemd("tunel.service").arrancar()


def test_sem_systemctl_na_maquina_falha_com_mensagem_e_nao_com_filenotfound(
        systemctl):
    """Um `FileNotFoundError` cru subia como avaria de código, e é de ambiente."""
    systemctl(erro=FileNotFoundError(2, "systemctl"))
    with pytest.raises(tunel.TunelIndisponivel, match="não há `systemctl`"):
        tunel.TunelSystemd("tunel.service").parar()


def test_um_systemctl_que_nao_responde_em_15s_falha_e_nao_pendura(systemctl):
    systemctl(erro=subprocess.TimeoutExpired("systemctl", tunel.TIMEOUT_S))
    with pytest.raises(tunel.TunelIndisponivel, match="não respondeu"):
        tunel.TunelSystemd("tunel.service").parar()


def test_o_systemctl_real_desta_maquina_nao_conhece_a_unidade_inventada():
    """A única chamada real deste ficheiro, e é uma **leitura**.

    Fixa o facto de que o `PRODUCAO.md` §5.1 registou — não há túnel instalado
    — contra o código real em vez de contra um duplo. Se um dia houver uma
    unidade com este nome, este teste cai e a mensagem diz porquê.
    """
    t = tunel.TunelSystemd("pessoabot-tunel-que-nao-existe.service")
    try:
        t._exigir_conhecida()
    except tunel.TunelIndisponivel as e:
        assert "não está instalada" in str(e)
    else:
        pytest.fail("existe uma unidade com este nome nesta máquina")


# --- a assimetria: parar levanta, arrancar avisa -------------------------- #

def test_o_aviso_de_que_o_tunel_nao_voltou_nomeia_a_unidade_e_o_remedio():
    """Um aviso que não diz o comando obriga a ler o código para o descobrir."""
    t = tunel.TunelSystemd("pessoabot-tunel.service")
    with pytest.warns(RuntimeWarning) as capturado:
        tunel.avisar_que_nao_voltou(t, tunel.TunelIndisponivel("devolveu 1"))
    msg = str(capturado[0].message)
    assert "pessoabot-tunel.service" in msg
    assert "systemctl --user start" in msg
    assert "devolveu 1" in msg


def test_o_aviso_e_um_aviso_e_nao_uma_excepcao():
    """A fase já correu: os dados são bons e não se trocam por uma excepção."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        tunel.avisar_que_nao_voltou(tunel.TunelAusente(), RuntimeError("x"))


# --- o duplo dos testes é aceite sem herdar nada -------------------------- #

def test_o_protocolo_aceita_um_duplo_que_nao_herda_nada():
    """É por isto que o `Tunel` é `Protocol` e não classe base.

    Se deixar de ser verificável em tempo de execução, o duplo do
    `test_sentinela.py` deixa de ser comparável com a implementação real.
    """
    class Duplo:
        nome = "duplo"

        def parar(self) -> None: ...
        def arrancar(self) -> None: ...

    assert isinstance(Duplo(), tunel.Tunel)
    assert isinstance(tunel.TunelAusente(), tunel.Tunel)
    assert isinstance(tunel.TunelSystemd("x.service"), tunel.Tunel)
