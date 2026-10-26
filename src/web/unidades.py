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
#: O túnel. O passo 5 escreveu o `tunel.py` para parar **uma unidade que ainda
#: não existia**, e disse que criá-la era o passo 4 — mas a §5.1 nunca a nomeou
#: na lista desse passo. É esta, e é o que faz o `PESSOABOT_TUNEL` do
#: `tunel.py` ter onde apontar, e o portão **D3** passar de inmensurável a
#: mensurável. Ver a §7.1 do plano.
NOME_TUNEL = "cloudflared.service"
#: A guarda do túnel e o seu temporizador. Existem porque o `Restart=on-failure`
#: **não cobre a queda do túnel**: o `cloudflared` não falha, insiste — 1019
#: tentativas em dez horas, com o `systemctl` a dizer `active` (§7.2 do plano).
NOME_GUARDA = "pessoabot-tunel-guarda.service"
NOME_TEMPORIZADOR = "pessoabot-tunel-guarda.timer"
#: A cópia das sessões e o seu temporizador (passo 10, portão **D8**).
#: Entram nos `GERADORES` ao contrário do túnel: uma unidade de túnel gerada
#: sem pensar é um túnel aberto, e uma cópia gerada sem pensar é uma cópia.
NOME_COPIA = "pessoabot-copia.service"
NOME_TEMPORIZADOR_COPIA = "pessoabot-copia.timer"

#: Onde o `systemctl --user` lê as unidades deste utilizador.
DIRECTORIO = Path.home() / ".config" / "systemd" / "user"

#: O Ollama desta máquina, fora do `PATH` por decisão da Fase 0.
OLLAMA = Path.home() / ".local" / "ollama" / "bin" / "ollama"

#: O `cloudflared`, instalado com a **mesma** disciplina do Ollama: binário
#: oficial em espaço de utilizador, sem `sudo`, **fora do `PATH`**. Não é
#: coerência por gosto: um `ExecStart=cloudflared` dependia de um `PATH` que a
#: unidade não tem, e é o modo de falha que o `test_unidades.py` prende.
CLOUDFLARED = Path.home() / ".local" / "cloudflared" / "bin" / "cloudflared"

#: A lista de convidados do passo 6, **nesta máquina** e não na conta de
#: ninguém. Um endereço por linha; `#` comenta; `*@dominio` é um domínio
#: inteiro, como o `--allowed-mail` aceita.
CONVIDADOS = Path.home() / ".config" / "pessoabot" / "convidados"

#: Existindo, **não há túnel**, e o conteúdo é a razão. Separado da lista de
#: convidados de propósito: a lista responde a «quem entra» e este ficheiro
#: responde a «há porta?», e confundi-los fazia uma decisão tomada por um
#: defeito medido (§7.4) parecer um descuido de quem não convidou ninguém — e
#: desaparecer na primeira reinstalação, que é como as decisões se perdem.
TUNEL_DESLIGADO = Path.home() / ".config" / "pessoabot" / "tunel-desligado"

#: Longo de propósito — ver o cabeçalho. 24 h é «não descarregues».
KEEP_ALIVE = "24h"

#: De quanto em quanto tempo a guarda pergunta ao URL. Cinco minutos é a
#: escolha do dono, e a aritmética que a sustenta: a pergunta custa dois
#: pedidos HTTP e nada de CPU, e o que se perde no pior caso são cinco minutos
#: de URL morto depois de uma suspensão — contra uma noite inteira sem ela.
MINUTOS_DA_GUARDA = 5

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
    cloudflared: Path = CLOUDFLARED

    def __post_init__(self) -> None:
        for nome in ("checkout", "python", "ollama", "cloudflared"):
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
    def de(cls, checkout: Path | str, ollama: Path = OLLAMA,
           cloudflared: Path = CLOUDFLARED) -> Alvo:
        """O alvo derivado de um checkout: o `python` é o `.venv` dele.

        Derivado e não dado, porque dá-los em separado permitia a combinação que
        não faz sentido nenhuma — o `python` de um checkout a correr o código de
        outro — e era exactamente o erro que o segundo checkout existe para
        impedir.
        """
        c = Path(checkout).expanduser().resolve()
        return cls(checkout=c, python=c / ".venv" / "bin" / "python",
                   ollama=Path(ollama).expanduser(),
                   cloudflared=Path(cloudflared).expanduser())


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


class ListaVazia(ErroDeUnidade):
    """Não há convidados, logo não há túnel. Ver `ler_convidados`."""


def ler_convidados(caminho: Path = CONVIDADOS) -> tuple[str, ...]:
    """A lista de convidados do passo 6. **Levanta se estiver vazia.**

    É esta excepção que torna «fechar antes de abrir» (§7) um mecanismo em vez
    de uma recomendação. Sem ela, um ficheiro ausente, vazio ou só com
    comentários dava uma unidade **sem** `--allowed-mail` — um túnel aberto ao
    mundo, com o corpus do outro lado e sem erro nenhum a dizê-lo. É a forma
    «não dá erro: dá respostas erradas», e aqui com o pior resultado possível.

    Cada linha tem de ter `@`: o `--allowed-mail` aceita endereços e domínios
    com curinga (`*@exemplo.pt`), e uma linha sem `@` é um erro de escrita que
    de outro modo passava a ser um convidado que nunca entra — sem ninguém
    perceber porquê.
    """
    caminho = Path(caminho).expanduser()
    if not caminho.exists():
        raise ListaVazia(
            f"não há lista de convidados em {caminho}. O passo 6 do plano é "
            f"«fechar o serviço a estranhos **antes** de o abrir», logo sem "
            f"lista não se gera unidade de túnel nenhuma")
    linhas = [ln.split("#", 1)[0].strip()
              for ln in caminho.read_text(encoding="utf-8").splitlines()]
    nomes = [ln for ln in linhas if ln]
    if not nomes:
        raise ListaVazia(
            f"{caminho} não tem nenhum endereço (só linhas vazias ou "
            f"comentários): um túnel sem `--allowed-mail` é um túnel aberto")
    maus = [n for n in nomes if "@" not in n]
    if maus:
        raise ErroDeUnidade(
            f"estas linhas de {caminho} não são endereços nem domínios com "
            f"curinga: {maus}")
    return tuple(nomes)


def servico_tunel(alvo: Alvo, convidados: tuple[str, ...]) -> str:
    """A unidade do túnel, **sempre** com lista de convidados.

    O `--allowed-mail` entra no `ExecStart` e não num `EnvironmentFile` porque o
    `cloudflared` não lê a lista de nenhuma variável de ambiente (verificado em
    `cloudflared tunnel --help`, versão 2026.10.1). A consequência tem de ficar
    escrita: **mudar a lista é regerar a unidade** e fazer `daemon-reload`, e é
    o que o `src/web/instalar.py` faz.

    `--url` aponta ao `HOST`/`PORTA` do `app.py`, pela mesma razão do
    `__main__.py`: o interface não pode viver em dois sítios.
    """
    if not convidados:
        raise ListaVazia(
            "servico_tunel sem convidados: isso geraria um túnel aberto ao "
            "mundo, e é o que o passo 6 existe para impedir")
    from .app import HOST, PORTA
    return f"""[Unit]
Description=Tunel do PessoaBot (Quick Tunnel protegido por correio, passo 6)
Documentation=file://{alvo.checkout}/docs/PRODUCAO.md
# `After=` e não `Requires=`: um túnel que arranca antes do serviço devolve a
# página de erro do fornecedor, que é a verdade. Com `Requires=`, um serviço
# em baixo derrubava o túnel e o visitante não recebia explicação nenhuma.
After={NOME_SERVICO}

[Service]
Type=exec
# Caminho absoluto: o `cloudflared` está fora do `PATH`, como o Ollama.
# `--allowed-mail` é o que fecha o túnel a estranhos (portão D4). A lista vem de
# {CONVIDADOS} e **fica nesta máquina**: o `cloudflared` compara-a localmente, e
# não há conta em fornecedor nenhum onde ela exista.
ExecStart={alvo.cloudflared} tunnel --no-autoupdate \
    --url http://{HOST}:{PORTA} \
    --allowed-mail {",".join(convidados)}
Restart=on-failure
RestartSec={SEGUNDOS_REINICIO}

[Install]
WantedBy=default.target
"""


def guarda_do_tunel(alvo: Alvo) -> str:
    """O serviço de uma passagem da guarda. `oneshot`: corre e morre."""
    return f"""\
[Unit]
Description=Uma passagem da guarda do túnel do PessoaBot (§7.2)
Documentation=file://{alvo.checkout}/docs/PRODUCAO.md
After={NOME_TUNEL}

[Service]
Type=oneshot
WorkingDirectory={alvo.checkout}
ExecStart={alvo.python} -m src.web.instalar --guardar-tunel
"""


def temporizador_da_guarda(alvo: Alvo) -> str:
    """O temporizador. `WantedBy=timers.target`, para o `linger` o apanhar.

    `OnBootSec` **e** `OnUnitActiveSec`: o primeiro é o que o faz existir
    depois de um reinício da máquina, e o segundo é a cadência. Sem o primeiro,
    um temporizador só agendado a partir da última passagem não tem primeira
    passagem nenhuma depois de um arranque.

    **Sem `Persistent=true`**, e é deliberado: `Persistent` faz o systemd correr
    de imediato a passagem que «faltou» enquanto a máquina esteve suspensa —
    e nesse instante a rede ainda não voltou. A guarda via o URL em baixo e a
    rede em baixo, recusava (é a 3.ª recusa do `decidir_guarda`), e a seguir
    esperava cinco minutos na mesma. Ou seja: `Persistent` não adiantava nada e
    punha a primeira passagem no pior instante possível.
    """
    return f"""\
[Unit]
Description=Pergunta ao URL do túnel de {MINUTOS_DA_GUARDA} em {MINUTOS_DA_GUARDA} minutos (§7.2)
Documentation=file://{alvo.checkout}/docs/PRODUCAO.md

[Timer]
OnBootSec={MINUTOS_DA_GUARDA}min
OnUnitActiveSec={MINUTOS_DA_GUARDA}min
Unit={NOME_GUARDA}

[Install]
WantedBy=timers.target
"""


def copia_das_sessoes(alvo: Alvo) -> str:
    """Uma passagem da cópia. `oneshot`: corre, copia, verifica e morre.

    Sem `After=` do `pessoabot.service`, e é deliberado: o `Connection.backup`
    coopera com um escritor vivo (ver a decisão 1 do `copias.py`), logo não há
    razão para a cópia esperar pelo serviço nem para o serviço esperar por ela.
    E uma base que ainda não existe não é uma falha: o `--copiar` di-lo e sai
    com 0, senão o temporizador enchia o registo de vermelho num serviço que
    ninguém ainda usou.
    """
    return f"""\
[Unit]
Description=Uma cópia verificada do data/sessoes.db do PessoaBot (§5.3)
Documentation=file://{alvo.checkout}/docs/PRODUCAO.md

[Service]
Type=oneshot
WorkingDirectory={alvo.checkout}
ExecStart={alvo.python} -m src.web.instalar --copiar
"""


def temporizador_da_copia(alvo: Alvo) -> str:
    """Diário, e **com** `Persistent=true` — ao contrário do da guarda.

    A diferença não é descuido, é o oposto da razão que o outro tem. O
    temporizador da guarda recusa o `Persistent` porque a passagem «que faltou»
    corre no instante em que a máquina acorda, quando a rede ainda não voltou —
    e uma guarda que pergunta a um URL sem rede não serve para nada. Uma cópia
    não pergunta nada a ninguém: lê um ficheiro local. A passagem que faltou é
    exactamente a que interessa recuperar, porque um dia sem cópia é um dia de
    perguntas que se perdem se o disco falhar nesse dia.
    """
    return f"""\
[Unit]
Description=Copia as sessões do PessoaBot uma vez por dia (§5.3, portão D8)
Documentation=file://{alvo.checkout}/docs/PRODUCAO.md

[Timer]
OnBootSec=15min
OnUnitActiveSec=1d
Persistent=true
Unit={NOME_COPIA}

[Install]
WantedBy=timers.target
"""


#: Os **serviços de arranque**: os que ficam a correr e que o `linger` levanta.
#: A ordem é a do arranque. O túnel **não** está aqui de propósito: gerá-lo
#: exige a lista de convidados, e uma unidade de túnel que se gere sem pensar é
#: um túnel aberto.
#:
#: ⚠️ **E a cópia também não está, por outra razão.** O `test_unidades.py` varre
#: este dicionário a exigir `Type=exec` e `WantedBy=default.target` — que é o
#: que o portão **D2** afirma destas duas unidades e **não** do que uma cópia
#: é. Uma `oneshot` disparada por temporizador cumpre o contrário dos dois, e
#: metê-la aqui não era arrumação: era afrouxar o D2 para quatro unidades para
#: acomodar duas. Ficam no dicionário abaixo, com o seu próprio contrato.
GERADORES = {NOME_OLLAMA: servico_ollama, NOME_SERVICO: servico_pessoabot}

#: A cópia das sessões e o seu temporizador. Escrevem-se **sempre**, ao
#: contrário do túnel: o que custa caro aqui é não os ter. Separados dos de
#: cima porque são outra espécie de unidade — `oneshot` e `timer`, em
#: `timers.target` —, e não porque sejam opcionais.
GERADORES_DA_COPIA = {NOME_COPIA: copia_das_sessoes,
                      NOME_TEMPORIZADOR_COPIA: temporizador_da_copia}


def escrever(alvo: Alvo, directorio: Path = DIRECTORIO, *,
             convidados: Path | None = None,
             mudadas: set[str] | None = None) -> dict[str, Path]:
    """Escreve as unidades. Devolve `{nome: caminho}`.

    Não corre `systemctl` nenhum: escrever ficheiros e mudar o estado dos
    serviços são dois actos com riscos diferentes, e misturá-los fazia um teste
    de geração tocar no `systemd` desta máquina.

    `mudadas`, se for dado, recebe os nomes das unidades cujo **conteúdo** ficou
    diferente do que estava no disco. Serve a quem decide o que reiniciar:
    reiniciar o `cloudflared` **troca o URL público** e deita abaixo as sessões
    de quem estiver autenticado, logo não pode ser o preço de correr o
    instalador por outro motivo. Observado a 2026-10-20, com o dono dentro da
    página: a instalação da guarda trocou-lhe o URL debaixo dos pés.

    A unidade do **túnel** só se escreve quando `convidados` for dado, e por
    omissão **não** é: quem decide se há túnel é o `instalar.py`, que lê a lista
    e relata. Aqui, uma lista inutilizável levanta e **nada** se escreve.
    """
    directorio = Path(directorio).expanduser()
    # Gera-se **tudo** antes de escrever o primeiro ficheiro: uma lista de
    # convidados má fazia o `ler_convidados` levantar depois de as outras duas
    # unidades já estarem no disco, e meia instalação é pior do que nenhuma
    # porque parece feita.
    mudadas = mudadas if mudadas is not None else set()
    textos = {nome: gerar(alvo) for nome, gerar in
              (GERADORES | GERADORES_DA_COPIA).items()}
    if convidados is not None:
        textos[NOME_TUNEL] = servico_tunel(alvo, ler_convidados(convidados))
        # A guarda só nasce com o túnel: sem túnel não há o que guardar, e um
        # temporizador a perguntar por um URL que não existe é ruído de cinco
        # em cinco minutos.
        textos[NOME_GUARDA] = guarda_do_tunel(alvo)
        textos[NOME_TEMPORIZADOR] = temporizador_da_guarda(alvo)
    directorio.mkdir(parents=True, exist_ok=True)
    feitos = {}
    for nome, texto in textos.items():
        caminho = directorio / nome
        antigo = (caminho.read_text(encoding="utf-8")
                  if caminho.exists() else None)
        caminho.write_text(texto, encoding="utf-8")
        feitos[nome] = caminho
        if antigo != texto:
            mudadas.add(nome)
    return feitos
