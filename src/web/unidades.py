"""As unidades de utilizador do serviço público. Passo 4 e portão **D2** do
[plano](../../docs/PRODUCAO.md) §5.1.

## O que o D2 afirma, e porque é que isto não é «pôr no arranque»

> **D2 — o serviço sobrevive à sessão.** Com `enable-linger`, fechar a sessão
> gráfica e reiniciar a máquina deixam o serviço de pé e o URL a responder.

Três factos desta máquina, verificados nela, decidem tudo o que está aqui:

- **`Linger=no`.** Unidades de utilizador morrem quando a sessão termina. Um
  serviço que cai ao fechar a sessão gráfica não é um serviço — e um URL
  público que cai ao fim da tarde é pior do que não haver URL, porque promete.
  `loginctl enable-linger` é metade do passo 4, e é a diferença entre «corre» e
  **«fica a correr»**.
- **O Ollama está em `~/.local/ollama/bin/ollama` e fora do `PATH`.** Decisão
  da Fase 0: instalado em espaço de utilizador a partir do tarball oficial, sem
  `sudo` e sem serviço de sistema, «por não haver razão para alterar o sistema
  numa fase de medição». Sob a saída D **mantém-se** — continua a não haver essa
  razão. O que muda é passar a haver uma unidade de **utilizador** a arrancá-lo,
  com o **caminho absoluto** no `ExecStart`. Não se põe no `PATH`: isso mexia no
  ambiente do dono para resolver um problema da unidade.
- **O serviço corre num segundo checkout** (§4), com o seu próprio `data/` e o
  seu próprio `.venv`. Nenhuma unidade escrita aqui pode nomear o checkout de
  trabalho, e há um teste a exigi-lo.

## `After=ollama.service`, e **não** `Requires=`

É a dependência do plano da Fase 6, e não é frouxidão. O `/api/estado` foi
desenhado para reportar «Ollama em baixo» **com o remédio** (`ollama serve`) em
vez de o processo morrer, e o portão **I3** mede-o. Com `Requires=`, um Ollama
que falhasse levava o `pessoabot` com ele: o utilizador perdia a página que
sabia explicar o que estava mal, e ficava com um URL morto. **Uma dependência
rígida desfazia uma decisão medida.**

## `OLLAMA_KEEP_ALIVE` longo, e o que isso afirma sobre a latência

Sem ele, o modelo descarrega entre perguntas e a primeira de cada ciclo paga o
carregamento inteiro. Num serviço de tráfego esparso — que é o que isto vai ser,
com autenticação e lista de convidados (passo 6) — essa seria **a latência
típica** e não um caso de arranque, e todos os números das Fases 0 a 5 deixavam
de descrever o que o utilizador sente.

## Porque é que isto é Python e não um `.service` no repositório

Porque os caminhos são absolutos e **da máquina**: o checkout do serviço, o
`python` do `.venv` dele, o `ollama` do dono. Um ficheiro versionado com
`/home/mpb/...` dentro é um ficheiro que só serve a esta máquina e que ninguém
verifica; e um ficheiro com marcadores para substituir é um ficheiro sem testes.
Aqui as decisões que importam — caminho absoluto, `After` sem `Requires`,
`WantedBy=default.target`, nunca o checkout de trabalho — são **asserções em
`tests/test_unidades.py`**, e três delas foram verificadas a morder.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

#: Os nomes das duas unidades. O `ollama` fica com o nome do serviço de sistema
#: que a Fase 0 recusou instalar, e isso é deliberado: é o mesmo programa e o
#: mesmo papel, e inventar-lhe um nome diferente só dificultava a procura.
NOME_OLLAMA = "ollama.service"
NOME_SERVICO = "pessoabot.service"

#: Onde o `systemctl --user` lê as unidades deste utilizador.
DIRECTORIO = Path.home() / ".config" / "systemd" / "user"

#: O Ollama desta máquina, fora do `PATH` por decisão da Fase 0.
OLLAMA = Path.home() / ".local" / "ollama" / "bin" / "ollama"

#: Longo de propósito — ver o cabeçalho. 24 h é «não descarregues».
KEEP_ALIVE = "24h"

#: Quanto esperar antes de voltar a arrancar depois de uma falha. Curto o
#: bastante para o URL voltar sem ninguém olhar, e longo o bastante para um
#: erro de arranque em ciclo não ocupar o CPU que as medições usam.
SEGUNDOS_REINICIO = 5


class ErroDeUnidade(Exception):
    """Uma unidade que se gerasse assim estaria errada na máquina."""


@dataclass(frozen=True)
class Alvo:
    """A máquina, como as unidades a vão nomear. Tudo absoluto, por asserção."""

    #: O checkout **do serviço**. Nunca o de trabalho: ver `recusar_o_trabalho`.
    checkout: Path
    #: O `python` do `.venv` desse checkout — e não o do sistema, nem o do
    #: checkout de trabalho. O recuo do passo 8 corre `pip install` **neste**.
    python: Path
    ollama: Path = OLLAMA

    def __post_init__(self) -> None:
        for nome in ("checkout", "python", "ollama"):
            c = getattr(self, nome)
            if not isinstance(c, Path):
                # Converte-se em vez de levantar `TypeError`: quem passa uma
                # cadeia merece a mensagem sobre o caminho e não um
                # `AttributeError` de dentro do `__post_init__` — foi assim que
                # o teste da recusa falhou a primeira vez.
                c = Path(c)
                object.__setattr__(self, nome, c)
            if not c.is_absolute():
                raise ErroDeUnidade(
                    f"{nome} tem de ser absoluto, e é «{c}»: uma unidade de "
                    f"systemd não tem directório de trabalho até o declarar, "
                    f"e um relativo resolve-se contra o que o systemd quiser")

    @classmethod
    def de(cls, checkout: Path | str, ollama: Path = OLLAMA) -> Alvo:
        """O alvo derivado de um checkout: o `python` é o `.venv` dele.

        Derivado e não dado, porque dá-los em separado permitia a combinação que
        não faz sentido nenhuma — o `python` de um checkout a correr o código de
        outro — e era exactamente o erro que o segundo checkout existe para
        impedir.
        """
        c = Path(checkout).expanduser().resolve()
        return cls(checkout=c, python=c / ".venv" / "bin" / "python",
                   ollama=Path(ollama).expanduser())


def recusar_o_trabalho(alvo: Alvo, trabalho: Path) -> None:
    """Levanta se o checkout do serviço **é** o de trabalho (§4 do plano).

    O serviço público não pode servir o checkout onde se edita: um `git switch`
    a meio de uma fase, ou um passo a meio de ser escrito, ficava no ar sob um
    URL público. É a regra de que os dois checkouts nascem, e é a única que uma
    instalação distraída quebra com um argumento por omissão.
    """
    t = Path(trabalho).expanduser().resolve()
    if alvo.checkout == t:
        raise ErroDeUnidade(
            f"o checkout do serviço é o de trabalho ({t}). A §4 do plano existe "
            f"por isto: é onde se edita, e um URL público não pode servir o que "
            f"está a ser escrito")


def servico_ollama(alvo: Alvo) -> str:
    """A unidade do Ollama. Caminho absoluto, e `PATH` nenhum."""
    return f"""\
[Unit]
Description=Ollama em espaço de utilizador (decisão da Fase 0: sem sudo)
Documentation=file://{alvo.checkout}/docs/PRODUCAO.md
# Sem `Requires=` de rede: o Ollama serve em 127.0.0.1 e não precisa dela.
After=network-online.target

[Service]
Type=exec
# Caminho absoluto: a Fase 0 instalou-o fora do `PATH` de propósito, e pô-lo
# no `PATH` era mexer no ambiente do dono para resolver um problema da unidade.
ExecStart={alvo.ollama} serve
# Longo: sem isto o modelo descarrega entre perguntas e a primeira de cada
# ciclo paga o carregamento inteiro — que num serviço de tráfego esparso
# passava a ser a latência típica, e não um caso de arranque.
Environment=OLLAMA_KEEP_ALIVE={KEEP_ALIVE}
Restart=on-failure
RestartSec={SEGUNDOS_REINICIO}

[Install]
WantedBy=default.target
"""


def servico_pessoabot(alvo: Alvo) -> str:
    """A unidade do serviço. O interface e a porta **não** estão aqui.

    `python -m src.web` e não `uvicorn ... --host ... --port ...`: o `HOST` e a
    `PORTA` vivem no `app.py`, e repeti-los aqui punha a decisão que o portão
    **I7′** protege num ficheiro que nenhum teste lê. Ver `src/web/__main__.py`.
    """
    return f"""\
[Unit]
Description=PessoaBot, o serviço público (saída D: esta máquina, atrás de um túnel)
Documentation=file://{alvo.checkout}/docs/PRODUCAO.md
# `After=` e **não** `Requires=`: o /api/estado reporta «Ollama em baixo» com o
# remédio em vez de o processo morrer, e o portão I3 mede-o. Com `Requires=`, um
# Ollama que falhasse levava com ele a página que sabia explicar a avaria.
After={NOME_OLLAMA}

[Service]
Type=exec
WorkingDirectory={alvo.checkout}
# O interface e a porta vêm do `app.py`, num sítio só. Ver o `__main__.py`.
ExecStart={alvo.python} -m src.web
Restart=on-failure
RestartSec={SEGUNDOS_REINICIO}

[Install]
WantedBy=default.target
"""


#: As duas unidades, por nome. A ordem é a do arranque.
GERADORES = {NOME_OLLAMA: servico_ollama, NOME_SERVICO: servico_pessoabot}


def escrever(alvo: Alvo, directorio: Path = DIRECTORIO) -> dict[str, Path]:
    """Escreve as duas unidades. Devolve `{nome: caminho}`.

    Não corre `systemctl` nenhum: escrever ficheiros e mudar o estado dos
    serviços são dois actos com riscos diferentes, e misturá-los fazia um teste
    de geração tocar no `systemd` desta máquina.
    """
    directorio = Path(directorio).expanduser()
    directorio.mkdir(parents=True, exist_ok=True)
    feitos = {}
    for nome, gerar in GERADORES.items():
        caminho = directorio / nome
        caminho.write_text(gerar(alvo), encoding="utf-8")
        feitos[nome] = caminho
    return feitos
