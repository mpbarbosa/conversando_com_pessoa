"""Instalar o serviço público nesta máquina. Passo 4 e portão **D2**.

    python -m src.web.instalar --ensaio      # imprime o que faria, e não faz
    python -m src.web.instalar               # faz

## Porque é que isto é um programa e não uma lista de comandos no `README`

Porque o passo 8 do [plano](../../docs/PRODUCAO.md) exige que **recuar seja um
comando ensaiado**, e um recuo instala por cima: `git checkout` da etiqueta
anterior, `pip install` (as dependências podem ter mudado entre etiquetas) e
reiniciar a unidade. Uma lista de comandos no `README` divergia do que está
instalado, e ninguém o saberia até ao dia em que o recuo fosse preciso — que é o
pior dia possível para descobrir.

E porque **três das decisões aqui são recusas**, não acções: não servir o
checkout de trabalho (§4), não copiar o `.venv` de outro checkout, e não seguir
em frente com um passo que falhou. Uma recusa que vive num `README` é um aviso;
numa função é um mecanismo.

## O que é caro, o que se copia e o que se partilha — medido nesta máquina

| | |
|---|---|
| `git clone --local` do checkout de trabalho | **8,4 MB** de corpus versionado vêm com ele (correcção **42**: o corpus **está** no repositório) e os objectos são ligados por `hardlink` |
| `data/corpus.jsonl`, `data/index.*` | **12,9 MB**, copiados. Estão no `.gitignore`, logo o clone não os traz — e reconstruí-los custava **40 s** o corpus e **383 s** o índice |
| `.venv` próprio | **5,7 GB**, medido no do serviço a 2026-10-20 (os 1,3 GB que aqui estiveram eram os do checkout de **trabalho**). Partilhar o de trabalho era deixar um `pip install` de desenvolvimento mudar, nesse instante, o que o serviço corre — a acoplagem que o segundo checkout existe para cortar |
| Ollama e o modelo de 4,9 GB | **partilhados**: um processo, uma cópia em memória, a unidade `ollama.service` de utilizador |
| cache do Hugging Face (encoder) | **partilhado**, 11 GB em `~/.cache/huggingface` |

Total novo em disco: **~5,7 GB**, contra 102 GB livres. O custo da saída D é de
CPU e de atenção, não de disco.

⚠️ **O `data/pessoa_poems/` não se liga por `symlink` nem se copia.** A §4 do
plano dizia «duplica-se ou liga-se por *symlink*, e não há razão de direitos para
preferir uma das duas — já está fora do repositório nas duas». As duas metades
dessa frase são falsas desde a correcção **42**: os 2083 ficheiros **estão**
versionados, logo o clone traz-os, e não há nada para ligar.

## O que este programa **não** faz

Não cria o túnel (passo 5, já feito, e corre à parte), não trata da
autenticação (passo 6), e **não mede o D2**: fechar a sessão gráfica e reiniciar
a máquina não são coisas que um programa que corre dentro dessa sessão possa
fazer e ver o resultado. O que faz é deixar a máquina no estado em que o D2 é
mensurável, e dizer quais são os dois comandos que o medem.
"""
from __future__ import annotations

import argparse
import getpass
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from . import copias
from .app import PORTA
from .sessoes import caminho_padrao as sessoes_padrao
from .saude import RAIZ, ler_lancamento
from .unidades import (
    CONVIDADOS,
    DIRECTORIO,
    GERADORES,
    NOME_GUARDA,
    NOME_OLLAMA,
    NOME_SERVICO,
    NOME_TEMPORIZADOR,
    NOME_TUNEL,
    TUNEL_DESLIGADO,
    Alvo,
    ErroDeUnidade,
    ListaVazia,
    escrever,
    ler_convidados,
    recusar_o_trabalho,
)

#: Onde o serviço vive, por omissão. Debaixo do mesmo `pessoabot` que o
#: sentinela já usa (`~/.local/state/pessoabot/`), para quem procurar encontrar
#: as duas peças no mesmo sítio.
DESTINO = Path.home() / ".local" / "share" / "pessoabot" / "servico"

#: O que o `.gitignore` deixa de fora e custa caro reconstruir. Ver o cabeçalho:
#: 40 s o corpus, 383 s o índice.
ARTEFACTOS = ("data/corpus.jsonl", "data/index.npy", "data/index.faiss",
              "data/index.manifest.json")


class Falhou(Exception):
    """Um passo não deu o que prometeu. Nenhum passo seguinte corre."""


def _correr(*args: str, ensaio: bool, cwd: Path | None = None) -> str:
    """Corre um comando, ou imprime-o. Levanta `Falhou` se correr mal.

    Não há modo «continua mesmo assim»: metade de uma instalação é pior do que
    nenhuma, porque parece feita.
    """
    linha = " ".join(args)
    if ensaio:
        print(f"    $ {linha}" + (f"   (em {cwd})" if cwd else ""))
        return ""
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        raise Falhou(f"{linha}\n{r.stderr.strip()[:2000]}")
    return r.stdout


def clonar(alvo: Alvo, ref: str, *, ensaio: bool) -> None:
    """O checkout do serviço, numa referência fixa.

    `--local` liga os objectos por `hardlink` em vez de os copiar: o clone de um
    repositório com 2083 ficheiros de corpus versionados custa quase nada.

    Um checkout que já exista **não** se re-clona: isso apagava o `.venv` e os
    artefactos. Reinstalar sobre um existente é mudar de referência, que é o que
    o recuo do passo 8 faz.

    ⚠️ **E é por isso que há um `git fetch` aqui, achado a correr.** A primeira
    versão desta função ia direita ao `checkout` quando o directório já
    existia — e um clone feito ontem **não tem os objectos de hoje**. O `git`
    não diz «esse commit não existe»: não reconhecendo a referência,
    interpreta-a como um **caminho** e responde `--detach does not take a path
    argument '79e4dbb'`, que manda quem o lê procurar um erro de sintaxe. A
    segunda instalação desta máquina falhou assim.

    Donde as duas correcções: **buscar** antes de mudar de referência, e
    **verificar** que ela resolve para um commit, para a mensagem falar da
    referência em vez de falar de caminhos.
    """
    if alvo.checkout.exists():
        print(f"  · o checkout já existe: {alvo.checkout}")
        # `origin` é o checkout de trabalho: foi de lá que o `clone --local`
        # veio. Sem isto, só se pode mudar para referências que já lá estavam.
        #
        # **`--tags`, e não é detalhe.** Sem ele o `git` só traz as etiquetas
        # **alcançáveis a partir dos ramos que buscou** — e uma etiqueta de
        # recuo é precisamente a que pode não estar em ramo nenhum. Observado
        # no ensaio do D6: a `servico-2026-10-20b`, criada num ramo que foi
        # apagado a seguir (o commit doente não entra no `main`), não vinha, e
        # o recuo recusava uma etiqueta que existia no checkout de trabalho.
        _correr("git", "-C", str(alvo.checkout), "fetch", "--prune", "--tags",
                "origin", ensaio=ensaio)
    else:
        alvo.checkout.parent.mkdir(parents=True, exist_ok=True)
        _correr("git", "clone", "--local", str(RAIZ), str(alvo.checkout),
                ensaio=ensaio)
    if not ensaio:
        r = subprocess.run(("git", "-C", str(alvo.checkout), "rev-parse",
                            "--verify", "--quiet", f"{ref}^{{commit}}"),
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise Falhou(
                f"a referência «{ref}» não existe no checkout do serviço "
                f"({alvo.checkout}) nem veio no `fetch` do de trabalho. Se é "
                f"um commit, falta publicá-lo em {RAIZ}; se é uma etiqueta, "
                f"`git push` dela não se aplica aqui — o `fetch` traz as de "
                f"origin")
    _correr("git", "-C", str(alvo.checkout), "checkout", "--detach", ref,
            ensaio=ensaio)


def copiar_artefactos(alvo: Alvo, *, ensaio: bool) -> None:
    """O corpus construído e o índice, que o `.gitignore` não deixa clonar."""
    for rel in ARTEFACTOS:
        origem, destino = RAIZ / rel, alvo.checkout / rel
        if not origem.exists():
            print(f"  · {rel} não existe no checkout de trabalho: o serviço "
                  f"reconstrói-o no arranque")
            continue
        if ensaio:
            print(f"    $ cp {origem} {destino}")
            continue
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origem, destino)


def criar_venv(alvo: Alvo, *, ensaio: bool) -> None:
    """Um `.venv` **próprio**, com o `uv` que criou o do checkout de trabalho.

    Próprio e não partilhado: ver o cabeçalho. 5,7 GB é o preço de o serviço não
    mudar debaixo dos pés por causa de um `pip install` de desenvolvimento.
    """
    if alvo.python.exists():
        print(f"  · o .venv já existe: {alvo.python}")
        return
    _correr("uv", "venv", "--python", "3.12", ".venv",
            ensaio=ensaio, cwd=alvo.checkout)
    _correr("uv", "pip", "install", "--python", str(alvo.python),
            "-r", "requirements.txt", ensaio=ensaio, cwd=alvo.checkout)


def instalar_unidades(alvo: Alvo, *, ensaio: bool) -> None:
    """Escreve as duas unidades, recarrega e activa-as.

    `enable --now` e não `start`: `enable` é o que as liga ao
    `default.target`, e é isso que faz o `enable-linger` abaixo significar algo
    depois de um reinício. Só `start` deixava um serviço que corre hoje e não
    volta amanhã — a forma «funciona e não fica a funcionar».

    ⚠️ **E um `restart` depois, achado a correr.** `enable --now` arranca uma
    unidade **inactiva** e não toca numa que já corra. A segunda instalação
    desta máquina mudou o checkout para `79e4dbb` e **deixou o processo de
    `734f77a` a servir** — sem erro nenhum, com os dois comandos a devolver 0.
    Num recuo (passo 8) isso é o pior resultado possível: o `git checkout` da
    etiqueta anterior «sucede», o `systemctl` «sucede», e o código doente
    continua a responder.

    Quem o disse foi o `/api/health`, e disse-o porque o `sha` é lido **à
    importação** e nomeia o que está em memória (§6.1). Um `sha` lido por pedido
    teria respondido `79e4dbb` — o do disco — e o defeito ficava invisível.
    """
    lista = decidir_tunel()
    mudadas: set[str] = set()
    unidades = [NOME_OLLAMA, NOME_SERVICO] + ([NOME_TUNEL] if lista else [])
    if ensaio:
        # Os ficheiros, e não as unidades a activar: o `escrever` também põe o
        # serviço da guarda e o temporizador, e um ensaio que os omitisse
        # mentia sobre o que a instalação a sério faz.
        ficheiros = list(GERADORES) + (
            [NOME_TUNEL, NOME_GUARDA, NOME_TEMPORIZADOR] if lista else [])
        for nome in ficheiros:
            print(f"    $ escreve {DIRECTORIO / nome}")
    else:
        for nome, caminho in escrever(
                alvo, convidados=CONVIDADOS if lista else None,
                mudadas=mudadas).items():
            print(f"  · {nome} → {caminho}"
                  f"{'  (mudou)' if nome in mudadas else ''}")
    _correr("systemctl", "--user", "daemon-reload", ensaio=ensaio)
    _correr("systemctl", "--user", "enable", "--now", *unidades, ensaio=ensaio)
    # Ver a docstring: sem isto uma instalação sobre um serviço a correr troca
    # o checkout e não troca o processo. O `restart` corta uma geração a meio,
    # e é o preço certo — é o mesmo comando que a §5.2 prescreve para o recuo.
    #
    # **Mas só o que precisa.** Reiniciar não custa o mesmo em cada unidade:
    #
    # - o `pessoabot` reinicia-se **sempre**, porque é a referência do checkout
    #   que pode ter mudado, e é a razão de alguém correr isto;
    # - o `ollama` só se a unidade dele mudar: um reinício descarrega o modelo
    #   de 4,9 GB e a pergunta seguinte paga ~50 s de prefill a frio;
    # - o `cloudflared` só se a unidade mudar **ou** o URL não responder,
    #   porque reiniciá-lo **troca o URL** e deita abaixo quem estiver
    #   autenticado. Observado a 2026-10-20, com o dono dentro da página.
    reiniciar = [NOME_SERVICO]
    if NOME_OLLAMA in mudadas:
        reiniciar.append(NOME_OLLAMA)
    if lista and (NOME_TUNEL in mudadas or not _tunel_responde(ensaio=ensaio)):
        reiniciar.append(NOME_TUNEL)
    elif lista:
        print("  · o túnel responde e a unidade não mudou: **não** se reinicia "
              "(reiniciar trocava o URL)")
    _correr("systemctl", "--user", "restart", *reiniciar, ensaio=ensaio)
    if not lista:
        # Desactivar e não só «não escrever»: uma unidade que já esteja
        # activada continua activada, e a instalação seguinte deixava o túnel
        # de pé a dizer que não havia túnel. Idempotente — `disable --now` de
        # algo que não existe não falha nada que importe.
        _correr("systemctl", "--user", "disable", "--now",
                NOME_TEMPORIZADOR, NOME_TUNEL, ensaio=ensaio)
    if lista:
        # O temporizador **não** leva `restart`: reiniciá-lo repõe a contagem,
        # e um `enable --now` já o deixa agendado. E o serviço da guarda é
        # `oneshot` — activá-lo à mão corria uma passagem fora de horas.
        _correr("systemctl", "--user", "enable", "--now", NOME_TEMPORIZADOR,
                ensaio=ensaio)
        provar_a_guarda(alvo, ensaio=ensaio)


def provar_a_guarda(alvo: Alvo, *, ensaio: bool) -> None:
    """Corre a guarda **uma vez**, pelo `python` do checkout do serviço.

    ⚠️ **Existe por uma falha observada, e a falha é de acoplagem entre os dois
    checkouts.** A unidade da guarda é escrita pelo checkout de **trabalho**,
    e corre o código do checkout do **serviço**, que está preso numa
    referência. A 2026-10-20 a unidade saiu a invocar `--guardar-tunel` numa
    referência onde essa opção ainda não existia: o `systemctl enable --now`
    devolveu **0**, o temporizador ficou agendado, e a primeira passagem
    morreu com `status=2/INVALIDARGUMENT` — uma guarda instalada com sucesso e
    incapaz de guardar.

    É a forma desta casa outra vez, e o remédio é o mesmo do `conferir_sha`:
    **não se acredita no código de saída do comando que se correu; corre-se a
    coisa e vê-se.** Não levanta — uma guarda que não corre não justifica
    desfazer uma instalação boa —, mas **diz**, e com o remédio.
    """
    if ensaio:
        return
    r = subprocess.run((str(alvo.python), "-m", "src.web.instalar",
                        "--guardar-tunel"), cwd=str(alvo.checkout),
                       capture_output=True, text=True)
    if r.returncode == 0:
        print(f"  · a guarda corre: {r.stdout.strip().splitlines()[-1]}"
              if r.stdout.strip() else "  · a guarda corre")
        return
    print(f"  · ⚠️ a guarda **não corre** no checkout do serviço "
          f"(código {r.returncode}): {(r.stderr or r.stdout).strip()[:300]}\n"
          f"       a referência servida não conhece `--guardar-tunel`. "
          f"Instala uma referência que a tenha.", file=sys.stderr)


def _tunel_responde(*, ensaio: bool) -> bool:
    """O URL actual responde? `True` no ensaio, que não toca na rede."""
    if ensaio:
        return True
    url = url_do_tunel(tentativas=1)
    return bool(url) and tunel_vivo(url)[0]


def decidir_tunel() -> tuple[str, ...]:
    """Há túnel? Lê a lista de convidados e **relata**, em vez de adivinhar.

    Três respostas, e as três são estados legítimos do plano:

    - **o `tunel-desligado` existe** → alguém decidiu que não há porta, e
      escreveu porquê. Fica à frente de tudo o resto: uma decisão tomada por
      um defeito medido (§7.4) não pode desaparecer porque se correu o
      instalador outra vez.
    - **sem ficheiro** → o passo 6 ainda não foi dado. Não se instala túnel, e
      isso não é falha: é «fechar antes de abrir» (§7) com o serviço fechado
      por não haver URL nenhum.
    - **ficheiro sem endereços** → alguém começou e não acabou. Também não se
      instala, e diz-se porquê. **Nunca** se instala um túnel sem
      `--allowed-mail`: a `servico_tunel` recusa-o, e é essa recusa que faz do
      §7 um mecanismo e não um conselho.
    - **endereços a sério** → instala-se, com a lista no `ExecStart`.

    Um endereço mal escrito **não** cai em nenhuma destas: levanta
    `ErroDeUnidade`, e o passo falha. Um convidado que nunca entra, sem
    ninguém perceber porquê, é pior do que uma instalação que pára.
    """
    if TUNEL_DESLIGADO.exists():
        razao = TUNEL_DESLIGADO.read_text(encoding="utf-8").strip()
        print(f"  · túnel **desligado** por {TUNEL_DESLIGADO}:")
        for ln in (razao or "(sem razão escrita)").splitlines():
            print(f"      {ln}")
        return ()
    try:
        # Explícito, e não pelo valor por omissão do `unidades`: assim há um
        # caminho só dentro deste módulo, e um teste que o troque troca-o
        # mesmo. Sem isto, o teste do interruptor passava a ler a lista real
        # desta máquina — e estava a medir outra coisa.
        lista = ler_convidados(CONVIDADOS)
    except ListaVazia as e:
        print(f"  · sem túnel: {e}")
        return ()
    print(f"  · {len(lista)} convidado(s) em {CONVIDADOS}")
    return lista


def ligar_linger(*, ensaio: bool) -> None:
    """`Linger=no` é o que faz o serviço morrer com a sessão gráfica.

    É metade do passo 4 e a diferença entre «corre» e «fica a correr». Não pede
    `sudo`: `enable-linger` sobre o próprio utilizador é permitido por omissão
    no `polkit` do Ubuntu.
    """
    _correr("loginctl", "enable-linger", getpass.getuser(), ensaio=ensaio)


#: O URL que o `cloudflared` anuncia no registo. É daqui que ele se lê, e não
#: de um ficheiro: o nome **muda de cada vez** que o túnel arranca (§7.1), logo
#: guardá-lo em qualquer lado era guardar uma mentira a partir do reinício
#: seguinte.
_URL_TUNEL = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


def extrair_url(registo: str) -> str | None:
    """O **último** URL anunciado no registo do túnel, ou `None`.

    O último e não o primeiro: o registo acumula os arranques anteriores, e
    cada um anunciou um nome diferente. Devolver o primeiro dava um URL morto
    com ar de bom — e quem o recebesse ia culpar o serviço.
    """
    achados = _URL_TUNEL.findall(registo)
    return achados[-1] if achados else None


def url_do_tunel(unidade: str = NOME_TUNEL,
                 tentativas: int = 20) -> str | None:
    """O URL **desta** execução do túnel, e não de uma anterior.

    ⚠️ **A primeira versão lia o registo inteiro logo a seguir ao `restart`, e
    devolvia o URL da execução anterior** — porque o novo ainda não tinha sido
    escrito. Um URL morto com ar de bom é pior do que nenhum: quem o recebe
    culpa o serviço. Observado nesta máquina: o instalador imprimiu
    `keyboards-auburn-bean-apparent` quando o túnel a correr já era
    `charging-arrangements-whether-burst`.

    A correcção é ler só o registo **desde o instante em que esta execução
    ficou activa**, que é o que o próprio systemd reporta — e no **mesmo fuso**
    em que o `journalctl` lê, que é o que a correcção 46 ensinou a não presumir.
    """
    desde = subprocess.run(
        ("systemctl", "--user", "show", "-p", "ActiveEnterTimestamp",
         "--value", unidade), capture_output=True, text=True).stdout.strip()
    for n in range(tentativas):
        cmd = ["journalctl", "--user", "-u", unidade, "--no-pager", "-o", "cat"]
        if desde:
            cmd += ["--since", desde]
        achado = extrair_url(subprocess.run(cmd, capture_output=True,
                                            text=True).stdout)
        if achado:
            return achado
        if n + 1 < tentativas:
            time.sleep(1)
    return None


#: As respostas do URL público que **provam que o túnel está vivo**. 403 e 302
#: são o ecrã de autenticação do fornecedor a funcionar; 200 seria o serviço a
#: responder a quem não entrou, e aí o problema era outro e maior.
VIVO = (200, 301, 302, 403)


def tunel_vivo(url: str, *, tempo_limite: float = 20.0) -> tuple[bool, str]:
    """O túnel responde? Pergunta-se **ao URL**, nunca ao `systemctl`.

    ⚠️ **Esta função existe por uma falha observada, e a falha é o `systemctl`
    a mentir.** A 2026-10-20 a máquina suspendeu às 02:22; ao acordar, a rede
    demorou, e a Cloudflare já tinha largado o registo do *quick tunnel*. O
    `cloudflared` **não morreu**: ficou a tentar registar um túnel que já não
    existe — **1019 vezes em dez horas** —, e durante essas dez horas o
    `systemctl --user is-active cloudflared.service` respondeu **`active`**,
    com `NRestarts=0`, enquanto o URL dava `NXDOMAIN` no navegador do dono.

    Logo `Restart=on-failure` não serve de nada aqui: o processo não falha,
    insiste. E «a unidade está activa» deixou de ser evidência de «o serviço
    está acessível» — exactamente a separação que o portão **I7′** teve de
    fazer entre «escuta em 127.0.0.1» e «não é alcançável de fora». A única
    pergunta que não mente é feita ao URL.
    """
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=tempo_limite) as r:
            codigo = r.status
    except urllib.error.HTTPError as e:
        codigo = e.code
    except OSError as e:
        return False, f"não responde: {e}"
    if codigo in VIVO:
        return True, f"responde {codigo}"
    return False, f"responde {codigo}, que não é o ecrã de autenticação"


#: Um ponto da Cloudflare que responde sempre e não é o nosso túnel. Serve
#: para distinguir «o túnel caiu» de «esta máquina não tem rede» — e essa
#: distinção é o que impede a guarda de gerar túneis contra uma rede morta.
SONDA_DE_REDE = "https://www.cloudflare.com/cdn-cgi/trace"


def rede_viva(url: str = SONDA_DE_REDE, *, tempo_limite: float = 10.0) -> bool:
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=tempo_limite):
            return True
    except urllib.error.HTTPError:
        return True          # respondeu, logo há rede
    except OSError:
        return False


def decidir_guarda(url_responde: bool, ha_rede: bool,
                   medicao: object | None,
                   desligado: bool = False) -> tuple[bool, str]:
    """Reiniciar o túnel? Função pura, porque é aqui que mora o perigo.

    Quatro recusas. A **primeira foi acrescentada depois de a guarda ter
    ressuscitado um túnel que o dono mandou desligar**, e a lição é precisa:
    `systemctl --user restart` **arranca uma unidade desactivada**. `disable`
    tira-a do arranque; não a tranca. Logo a guarda, que só olhava para o URL,
    via o último URL do registo a não responder, concluía «morreu» e levantava
    o túnel outra vez — de cinco em cinco minutos, contra uma decisão tomada
    sobre uma medição (§7.5). Um mecanismo automático a desfazer uma decisão de
    segurança, que é a família inteira de defeitos que este plano persegue.

    As outras três, e a segunda continua a ser a mais perigosa das que restam:

    1. **Há uma medição a correr.** O passo 5 derruba o túnel de propósito
       durante uma fase — é o portão **D3** e a razão de o `tunel.py` existir.
       Uma guarda que não soubesse disto via o URL em baixo, concluía «morreu»,
       e **levantava o túnel no meio da medição**: desfazia a protecção do
       sentinela, punha público no mesmo CPU das amostras, e deixava um
       `01-cru.jsonl` em que uma célula lenta pode ser térmica ou pode ser um
       estranho. Seria um mecanismo automático a desfazer, em silêncio, o
       mecanismo que o plano inteiro existe para construir.
    2. **O URL responde.** Nada a fazer.
    3. **O URL não responde e a rede também não.** Reiniciar aqui não dá túnel
       nenhum — dá um `cloudflared` novo a falhar contra a mesma rede — e de
       cinco em cinco minutos isso é só ruído no registo.
    """
    if desligado:
        return False, (f"o túnel está desligado por {TUNEL_DESLIGADO}: a "
                       f"guarda não ressuscita o que alguém mandou parar")
    if medicao is not None:
        return False, f"medição a correr ({medicao}): o túnel está em baixo de propósito"
    if url_responde:
        return False, "o URL responde"
    if not ha_rede:
        return False, "o URL não responde, e a rede desta máquina também não"
    return True, "o URL não responde e a rede está de pé"


def guardar_tunel() -> int:
    """Uma passagem da guarda. Chamada pelo temporizador, de 5 em 5 minutos.

    Devolve **0 mesmo quando não faz nada**: um temporizador que falha de cinco
    em cinco minutos enquanto a rede está em baixo enche o registo e ensina
    quem o lê a ignorá-lo.
    """
    from . import sentinela
    if TUNEL_DESLIGADO.exists():
        # Antes de tudo, e antes de sequer ler o registo: ver `decidir_guarda`.
        agir, porque = decidir_guarda(False, False, None, desligado=True)
        print(porque)
        return 0
    url = url_do_tunel(tentativas=1)
    if url is None:
        print("sem URL anunciado nesta execução do túnel; nada a guardar")
        return 0
    responde, detalhe = tunel_vivo(url)
    medicao = sentinela.a_correr()
    agir, porque = decidir_guarda(responde, rede_viva() if not responde else True,
                                  medicao.descricao() if medicao else None)
    print(f"{url}: {detalhe} — {porque}")
    if not agir:
        return 0
    print(f"a reiniciar {NOME_TUNEL}; o URL vai mudar")
    subprocess.run(("systemctl", "--user", "restart", NOME_TUNEL),
                   capture_output=True, text=True)
    novo = url_do_tunel()
    print(f"URL novo: {novo or 'ainda não anunciado'}")
    return 0


#: Corre **dentro** do checkout do serviço e com o `python` dele: o diagnóstico
#: do manifesto compara o índice com o corpus **daquele** `data/`, e correr isto
#: do checkout de trabalho media o índice errado — a mesma classe de defeito do
#: sentinela relativo (`CONTROLO.md` §4, #39).
_DIAGNOSTICO = (
    "import sys;"
    "from src.corpus.build import load;"
    "from src.web.estado import diagnosticar_indice;"
    "m,c=load();ok,d=diagnosticar_indice(c,m['assinatura']);"
    "print('OK' if ok else 'NAO', d, sep='|')"
)


def manifesto_aceite(alvo: Alvo) -> tuple[bool, str]:
    """O índice do checkout do serviço serve, ou vai ser reconstruído?

    É **a única peça do plano retirado que sobrevive inteira** (§5.2), e a razão
    é um número: o manifesto compara encoder, assinatura do corpus, contagem e
    ordem, e **devolve `None` em vez de reconstruir em silêncio**. Num recuo
    isso é o comportamento certo e a consequência é má — o serviço arranca, e a
    primeira pergunta de quem estiver à espera reconstrói o índice durante
    **383 s** de CPU saturado.

    Por isso o recuo pergunta isto **antes** de reiniciar, e recusa se divergir:
    um recuo que deixa o serviço de pé a cobrar 383 s à primeira pergunta não é
    um recuo, é outra avaria.
    """
    r = subprocess.run((str(alvo.python), "-c", _DIAGNOSTICO),
                       cwd=str(alvo.checkout), capture_output=True, text=True)
    if r.returncode != 0:
        return False, f"o diagnóstico não correu: {r.stderr.strip()[:300]}"
    cabeca, _, detalhe = r.stdout.strip().partition("|")
    return cabeca == "OK", detalhe


def recuar(alvo: Alvo, ref: str, *, ensaio: bool) -> int:
    """Voltar a uma etiqueta. Portão **D6** — «recuar é um comando, e foi
    ensaiado».

        python -m src.web.instalar --recuar servico-2026-10-20a

    A ordem é a asserção, e não é invertível:

    1. **buscar e mudar de referência** (o `clonar`, com as duas correcções da
       §7.1: sem `fetch` o `git` recusa a etiqueta com uma mensagem sobre
       caminhos);
    2. **`pip install`**, porque as dependências podem ter mudado entre
       etiquetas — é o mesmo motivo pelo qual o `06_redeploy.sh` do repositório
       irmão corre `npm ci` no recuo e não só restaura o `dist/`;
    3. **verificar o manifesto**, e **recusar** se divergir. Antes do reinício,
       nunca depois: ver `manifesto_aceite`;
    4. só então **reiniciar**, e
    5. **conferir pelo `/api/health`** que o processo é o da etiqueta — porque
       `systemctl` a devolver 0 não é evidência de nada (§7.1, correcção 48).
    """
    print(f"a recuar para «{ref}» em {alvo.checkout}")
    try:
        print("\n[referência]")
        clonar(alvo, ref, ensaio=ensaio)
        print("\n[dependências]")
        _correr("uv", "pip", "install", "--python", str(alvo.python),
                "-r", "requirements.txt", ensaio=ensaio, cwd=alvo.checkout)
    except Falhou as e:
        print(f"\nrecuo abortado: {e}", file=sys.stderr)
        return 1

    print("\n[manifesto, **antes** do reinício]")
    if ensaio:
        print("    (o ensaio não diagnostica o índice)")
    else:
        ok, detalhe = manifesto_aceite(alvo)
        print(f"  · {'aceite' if ok else 'RECUSADO'}: {detalhe}")
        if not ok:
            print("\nRECUO ABORTADO, e o serviço **não** foi reiniciado: com "
                  "este índice a primeira pergunta reconstruía-o durante 383 s "
                  "de CPU saturado. Resolve-se copiando o índice da etiqueta, "
                  "ou reconstruindo-o à mão antes de reiniciar.",
                  file=sys.stderr)
            return 1

    print("\n[reinício]")
    _correr("systemctl", "--user", "restart", NOME_SERVICO, ensaio=ensaio)
    if ensaio:
        return 0
    do_checkout = ler_lancamento(alvo.checkout).sha
    da_saude = _sha_da_saude()
    print(f"  · sha do checkout: {do_checkout}")
    print(f"  · sha do /api/health: {da_saude}")
    queixa = conferir_sha(do_checkout, da_saude)
    if queixa is not None:
        print(f"\nO RECUO NÃO PEGOU: {queixa}", file=sys.stderr)
        return 1
    print(f"\nrecuado para {do_checkout}, e o serviço a correr é esse.")
    return 0


#: Quanto tempo depois do arranque da máquina ainda se considera que uma
#: unidade «subiu no arranque». Generoso: o `pessoabot` espera o
#: `ollama.service`, e o `ollama` espera a rede. 5 minutos é folga a mais do
#: que o necessário e muito menos do que uma sessão de trabalho.
ARRANQUE_S = 300

#: Veredictos. «por medir» **não** é «passa»: é o estado em que o portão não
#: pode ser avaliado com o que a máquina mostra agora, e dizê-lo é o ponto.
PASSA, FALHA, POR_MEDIR = "passa", "falha", "por medir"


def avaliar_d2(servico_us: int, sessao_us: int, linger: bool,
               arranque_s: int = ARRANQUE_S) -> list[tuple[str, str, str]]:
    """O portão **D2**, julgado em **tempo monótono desde o arranque**.

    Devolve `[(metade, veredicto, porquê)]`.

    ## Porque é que os instantes são monótonos, e não datas

    `ActiveEnterTimestampMonotonic` e `TimestampMonotonic` vêm em microssegundos
    **desde o arranque da máquina**, logo o arranque é o zero e **não há fuso
    nenhum na comparação**. É a lição da correcção 46 aplicada antes de custar:
    o portão D4 passou uma vez por eu ter comparado um carimbo em UTC com um
    `journalctl` em hora local, e aqui há três instantes para trocar.

    ## As duas metades, e porque é que são separadas

    O D2 afirma duas coisas que falham por razões diferentes:

    - **sobrevive ao logout** — o serviço é mais velho do que a sessão de onde
      se pergunta. Se tivesse nascido com o login, seria da idade dela;
    - **sobrevive ao reinício** — o serviço subiu **no arranque**, antes de
      haver login nenhum. É isto, e só isto, que o `enable-linger` compra.

    ⚠️ **E a razão de haver «por medir»:** um `python -m src.web.instalar`
    reinicia o `pessoabot`, e com isso **apaga a evidência** — o serviço passa
    a ser mais novo que o arranque e mais novo que a sessão, sem que isso diga
    nada sobre o `linger`. Um portão que respondesse «falha» aí ensinava quem o
    lê a ignorá-lo. Responde «por medir», e diz o que fazer.
    """
    us = arranque_s * 1_000_000
    perto = 60 * 1_000_000
    if not linger:
        porque = ("`Linger=no`: as unidades de utilizador morrem com a sessão. "
                  "`loginctl enable-linger` é metade do passo 4")
        return [("sobrevive ao logout", FALHA, porque),
                ("sobrevive ao reinício", FALHA, porque)]

    subiu_no_arranque = servico_us <= us
    sessao_do_arranque = sessao_us <= us

    if subiu_no_arranque:
        reinicio = (PASSA, f"o serviço subiu {servico_us / 1e6:.0f} s depois do "
                           f"arranque, antes de qualquer login")
    elif not sessao_do_arranque and abs(servico_us - sessao_us) <= perto:
        # O único caso em que se pode culpar o `linger`: a máquina arrancou, o
        # login veio muito depois, e o serviço nasceu **com ele**.
        reinicio = (FALHA,
                    f"o serviço ({servico_us / 1e6:.0f} s) nasceu com esta "
                    f"sessão ({sessao_us / 1e6:.0f} s) e não com o arranque: o "
                    f"`linger` não o levantou")
    else:
        reinicio = (POR_MEDIR,
                    f"o serviço foi reiniciado {servico_us / 3.6e9:.1f} h depois "
                    f"do arranque — provavelmente por uma instalação —, logo "
                    f"não se sabe se teria subido sozinho. Reinicia a máquina e "
                    f"volta a correr isto **antes** de entrar na sessão gráfica")

    # A ordem é a correcção: **primeiro** pergunta-se se houve logout. Sem
    # isto, um arranque limpo dava «passa» ao logout — o serviço sobe antes da
    # sessão e parecia mais velho que ela — sem que ninguém tivesse saído de
    # sessão nenhuma. Isso prova a metade do reinício, não esta.
    if sessao_do_arranque:
        logout = (POR_MEDIR,
                  "a sessão mais recente começou com a máquina, logo **não "
                  "houve logout nenhum desde o arranque**. Termina a sessão "
                  "gráfica, volta a entrar, e corre isto outra vez")
    elif servico_us < sessao_us - perto:
        logout = (PASSA, f"o serviço é {(sessao_us - servico_us) / 1e6:.0f} s "
                         f"mais velho que esta sessão, logo não nasceu com ela")
    else:
        logout = (FALHA,
                  f"o serviço ({servico_us / 1e6:.0f} s) é da idade desta "
                  f"sessão ({sessao_us / 1e6:.0f} s): nasceu com o login, e não "
                  f"sobreviveu ao anterior")
    return [("sobrevive ao logout", *logout),
            ("sobrevive ao reinício", *reinicio)]


def _monotono(*args: str) -> int:
    r = subprocess.run(args, capture_output=True, text=True)
    try:
        return int(r.stdout.strip())
    except ValueError:
        return 0


def _sessao_mais_recente_us() -> int:
    """A sessão **mais nova** deste utilizador, em µs desde o arranque.

    A mais nova, e não a de onde isto corre: depois de um logout e de um login
    novo, é a nova que interessa — e o processo pode estar a correr de um
    terminal sem sessão própria.
    """
    r = subprocess.run(("loginctl", "list-sessions", "--no-legend"),
                       capture_output=True, text=True)
    utilizador = getpass.getuser()
    marcas = [_monotono("loginctl", "show-session", ln.split()[0],
                        "-p", "TimestampMonotonic", "--value")
              for ln in r.stdout.splitlines()
              if len(ln.split()) > 2 and ln.split()[2] == utilizador]
    return max(marcas, default=0)


def _pid_do_servico() -> int | None:
    """O `MainPID` da unidade, ou `None` se estiver parada.

    Existe porque o PID é a prova directa de que a unidade foi mesmo substituída
    — a mesma asserção que o guião do portão D2 usa para o logout. Um
    `systemctl stop` seguido de `start` que devolvam 0 com o mesmo PID significa
    que nada aconteceu.
    """
    r = subprocess.run(("systemctl", "--user", "show", "-p", "MainPID",
                        "--value", NOME_SERVICO),
                       capture_output=True, text=True)
    try:
        return int(r.stdout.strip()) or None
    except ValueError:
        return None


def copiar_sessoes(*, ensaio: bool) -> int:
    """Uma cópia verificada do `data/sessoes.db`. É o que o temporizador corre.

        python -m src.web.instalar --copiar

    **Não há base ⇒ sai com 0.** Um serviço que ninguém ainda usou não tem
    sessões, e tratar isso como falha enchia o registo de vermelho diário num
    sistema são — e ensinava a ignorar o vermelho, que é o custo real.
    """
    origem = sessoes_padrao()
    destino = copias.directorio_padrao()
    print(f"base:    {origem}")
    print(f"cópias:  {destino}")
    if not Path(origem).exists():
        print("não há base ainda: nada a copiar, e isso não é uma falha")
        return 0
    if ensaio:
        print(f"    (o ensaio não copia; copiaria para {destino})")
        return 0
    try:
        alvo = copias.copiar(origem, destino)
    except copias.ErroDeCopia as e:
        print(f"\nA CÓPIA NÃO SE FEZ: {e}", file=sys.stderr)
        return 1
    estado = copias.verificar(alvo)
    print(f"  · {alvo.name}: {estado.detalhe}")
    guardadas = copias.listar(destino)
    n = len(guardadas)
    print(f"  · {n} cópia{'s' if n != 1 else ''} guardada"
          f"{'s' if n != 1 else ''} (máximo {copias.A_GUARDAR})")
    return 0


def listar_copias() -> int:
    """As cópias, e o que cada uma tem dentro.

        python -m src.web.instalar --listar-copias

    Abre **cada uma** em vez de listar nomes e tamanhos: o tamanho de um
    ficheiro de SQLite não diz se ele abre, e o que esta casa quer saber antes
    de precisar de uma cópia é se ela serve.
    """
    destino = copias.directorio_padrao()
    guardadas = copias.listar(destino)
    print(f"cópias:  {destino}")
    if not guardadas:
        print("não há nenhuma")
        return 0
    for c in guardadas:
        estado = copias.verificar(c)
        print(f"  {'·' if estado.ok else '✗'} {c.name}: {estado.detalhe}")
    return 0


def restaurar_sessoes(ficheiro: str | None, *, ensaio: bool) -> int:
    """Põe uma cópia no lugar da base. Portão **D8**.

        python -m src.web.instalar --restaurar                  # a mais recente
        python -m src.web.instalar --restaurar <caminho>

    A ordem é a asserção, e é a mesma que o §5.5 fixou para o recuo — verificar
    **antes** e nunca depois:

    1. **verificar a cópia**, e recusar se não servir. Antes de tocar em nada:
       verificada depois, já não há o que salvar;
    2. **parar o serviço**. Parar que falha ⇒ **não se restaura** — é a mesma
       assimetria do §3.4, e aqui é mais fácil de justificar: restaurar por
       baixo de um escritor vivo é trocar o ficheiro a quem tem o WAL aberto;
    3. **restaurar**, guardando a base anterior em `.substituido`;
    4. **verificar a base** restaurada;
    5. **arrancar o serviço** outra vez.
    """
    base = sessoes_padrao()
    copia = (Path(ficheiro) if ficheiro
             else copias.ultima(copias.directorio_padrao()))
    if copia is None:
        print(f"não há cópias em {copias.directorio_padrao()}",
              file=sys.stderr)
        return 1
    print(f"cópia:   {copia}")
    print(f"base:    {base}")

    print("\n[a cópia, **antes** de tocar na base]")
    estado = copias.verificar(copia)
    print(f"  · {'aceite' if estado.ok else 'RECUSADA'}: {estado.detalhe}")
    if not estado.ok:
        print("\nRESTAURO ABORTADO, e a base está como estava.", file=sys.stderr)
        return 1
    if ensaio:
        print("\n    (o ensaio não para o serviço nem mexe na base)")
        return 0

    print("\n[parar o serviço]")
    antes = _pid_do_servico()
    print(f"  · MainPID antes: {antes or '(parado)'}")
    try:
        _correr("systemctl", "--user", "stop", NOME_SERVICO, ensaio=False)
    except Falhou as e:
        print(f"\nRESTAURO ABORTADO: não consegui parar o serviço ({e}). "
              f"Restaurar com um escritor vivo é trocar o ficheiro a quem tem "
              f"o WAL aberto.", file=sys.stderr)
        return 1

    print("\n[restauro]")
    try:
        final = copias.restaurar(copia, base)
    except copias.ErroDeCopia as e:
        print(f"\nO RESTAURO FALHOU: {e}", file=sys.stderr)
        print("o serviço fica parado de propósito: arranca-se à mão depois de "
              "olhar para a base.", file=sys.stderr)
        return 1
    print(f"  · base restaurada: {final.detalhe}")
    anterior = Path(str(base) + ".substituido")
    if anterior.exists():
        print(f"  · a base anterior ficou em {anterior.name}")

    print("\n[arranque]")
    _correr("systemctl", "--user", "start", NOME_SERVICO, ensaio=False)
    depois = _pid_do_servico()
    print(f"  · MainPID depois: {depois or '(parado)'}")
    # O `systemctl` a devolver 0 **não é evidência de nada** — é a correcção 48
    # do §7.1, e este ensaio quase a repetiu: as duas secções acima não
    # imprimiam nada e o sucesso do restauro era a palavra do `systemctl`.
    # Pergunta-se ao serviço, como o recuo faz.
    sha = _sha_da_saude()
    print(f"  · sha do /api/health: {sha or '(não respondeu)'}")
    if sha is None:
        print("\nA BASE FOI RESTAURADA e o serviço **não** voltou a responder: "
              "o restauro está feito, o arranque não. `systemctl --user status "
              f"{NOME_SERVICO}` diz porquê.", file=sys.stderr)
        return 1
    print(f"\nrestaurado de {copia.name}: {final.sessoes} sessões, "
          f"{final.mensagens} mensagens. O serviço voltou "
          f"({antes or '—'} → {depois or '—'}).")
    return 0


def verificar_d2() -> int:
    """Portão **D2**, contra o estado actual da máquina.

        python -m src.web.instalar --verificar-d2

    Corre-se **duas vezes**: depois de um logout e de um login novo, e depois
    de um reinício, de um terminal virtual, **antes** de abrir a sessão
    gráfica.
    """
    servico_us = _monotono("systemctl", "--user", "show", "-p",
                           "ActiveEnterTimestampMonotonic", "--value",
                           NOME_SERVICO)
    sessao_us = _sessao_mais_recente_us()
    linger = subprocess.run(
        ("loginctl", "show-user", getpass.getuser(), "-p", "Linger", "--value"),
        capture_output=True, text=True).stdout.strip() == "yes"

    print(f"  · Linger: {'yes' if linger else 'no'}")
    print("  · arranque da máquina: 0 s (é o zero do tempo monótono)")
    print(f"  · sessão mais recente: +{sessao_us / 1e6:.0f} s")
    print(f"  · {NOME_SERVICO} a correr desde: +{servico_us / 1e6:.0f} s")
    print()
    veredictos = avaliar_d2(servico_us, sessao_us, linger)
    for metade, veredicto, porque in veredictos:
        print(f"  {veredicto.upper():<10} {metade}")
        print(f"             {porque}")
    estados = {v for _, v, _ in veredictos}
    if FALHA in estados:
        return 1
    if POR_MEDIR in estados:
        print("\nO D2 continua **por medir**, e por medir não é cumprido.")
        return 2
    print("\nD2 cumprido, nas duas metades.")
    return 0


def conferir_sha(do_checkout: str | None, da_saude: str | None) -> str | None:
    """A queixa, se o serviço a correr não for o código instalado. `None` se for.

    Função à parte e pura para ter teste: é o predicado do portão **D1**
    aplicado como verificação de instalação, e é ele que apanha um `restart`
    que não aconteceu. A disciplina é a que o plano transfere do repositório
    irmão — **verifica-se pela saúde do serviço, nunca pelo código de saída dos
    comandos que se correram**.
    """
    if do_checkout is None:
        return "o checkout do serviço não diz de que commit é"
    if da_saude is None:
        return (f"o /api/health não respondeu, logo não se sabe o que está a "
                f"correr (o checkout está em {do_checkout})")
    if da_saude != do_checkout:
        return (f"o serviço está a correr {da_saude} e o checkout está em "
                f"{do_checkout}: o processo não foi substituído")
    return None


#: Quantas vezes se pergunta a saúde depois de um `restart`, de segundo a
#: segundo. Há-as porque a primeira pergunta depois de um `restart` chega antes
#: de o `uvicorn` ligar o socket, e sem elas a verificação dizia «não
#: respondeu» a um serviço que estava a arrancar — um falso alarme a seguir a
#: uma instalação boa é o que faz uma verificação deixar de se ler.
#:
#: 20 e não 30: o `uvicorn` deste serviço **não** carrega modelos no arranque
#: (o encoder vem na 1.ª pergunta), logo ligar o socket é imediato. A nota do
#: plano retirado sobre o `HEALTH_ATTEMPTS=30` curto era para um arranque que
#: podia tocar o índice, e este não toca.
TENTATIVAS_SAUDE = 20


def _sha_da_saude(tentativas: int = TENTATIVAS_SAUDE) -> str | None:
    """O `sha` que o serviço a correr declara, ou `None` se não responder."""
    import json
    import urllib.error
    import urllib.request
    for n in range(tentativas):
        try:
            with urllib.request.urlopen(
                    f"http://127.0.0.1:{PORTA}/api/health", timeout=5) as r:
                return json.load(r).get("sha")
        except (OSError, urllib.error.HTTPError, ValueError):
            if n + 1 < tentativas:
                time.sleep(1)
    return None


def verificar(alvo: Alvo, *, ensaio: bool,
              tunel: bool = False) -> tuple[list[str], str | None]:
    """O que se pode medir **sem** fechar a sessão nem reiniciar.

    Devolve `(linhas do relatório, queixa)`. O que fica de fora é o D2 inteiro,
    e está dito no fim em vez de assumido.
    """
    if ensaio:
        return (["    (o ensaio não verifica nada: não há nada instalado)"],
                None)
    linhas = []
    linger = _correr("loginctl", "show-user", getpass.getuser(),
                     "--property=Linger", ensaio=False).strip()
    linhas.append(f"  · {linger}")
    instaladas = list(GERADORES) + ([NOME_TUNEL, NOME_TEMPORIZADOR]
                                    if tunel else [])
    for nome in instaladas:
        estado = subprocess.run(
            ("systemctl", "--user", "is-enabled", nome),
            capture_output=True, text=True).stdout.strip()
        activo = subprocess.run(
            ("systemctl", "--user", "is-active", nome),
            capture_output=True, text=True).stdout.strip()
        linhas.append(f"  · {nome}: {estado or '?'} · {activo or '?'}")
    do_servico = ler_lancamento(alvo.checkout)
    linhas.append(f"  · sha do checkout do serviço: {do_servico.sha}"
                  f"{f' ({do_servico.erro})' if do_servico.erro else ''}")
    da_saude = _sha_da_saude()
    linhas.append(f"  · sha que o /api/health declara: {da_saude}")
    if tunel:
        url = url_do_tunel()
        linhas.append(f"  · URL público: {url or 'ainda não anunciado'}")
        if url:
            linhas.append(f"    confirmar o D4:  python -m src.web.instalar "
                          f"--verificar-d4 {url}")
    return linhas, conferir_sha(do_servico.sha, da_saude)


def contar_acessos(registo: str) -> int:
    """As linhas de acesso do `uvicorn` num registo. Função pura, para a testar.

    O predicado é o do formato dele — `INFO: 127.0.0.1:x - "GET /… HTTP/1.1"` —
    e **não** uma contagem de linhas: o mesmo registo leva o arranque, os avisos
    do Hugging Face e as barras de progresso do carregamento de pesos, e contar
    tudo fazia o D4 falhar por o modelo ter carregado.
    """
    return sum(1 for ln in registo.splitlines()
               if '"GET ' in ln or '"POST ' in ln)


def acessos_registados(unidade: str = NOME_SERVICO) -> int:
    """Quantas linhas de acesso o `uvicorn` escreveu, desde sempre.

    **Conta linhas, e não uma janela de tempo.** A primeira versão desta
    medição usou `journalctl --since` com um carimbo de `date -u`, e o
    `journalctl` lê a hora **local**: a janela ficava três horas no futuro e o
    registo vinha vazio — o que, num portão cuja asserção é «o registo não tem
    o pedido», é um falso **sucesso**. Contar linhas não tem fuso.
    """
    r = subprocess.run(("journalctl", "--user", "-u", unidade,
                        "--no-pager", "-o", "cat"),
                       capture_output=True, text=True)
    return contar_acessos(r.stdout)


def verificar_d4(url: str) -> int:
    """Portão **D4**: de fora, o URL nunca toca no `uvicorn`.

        python -m src.web.instalar --verificar-d4 https://....trycloudflare.com

    Quatro pedidos pelo URL público, de quem **não** está na lista de
    convidados, e o registo do serviço não pode ganhar uma linha. E depois um
    pedido local, que **tem** de ganhar uma — senão «zero linhas» não distingue
    «ninguém chegou» de «o registo não regista», e foi essa verificação que
    apanhou o defeito do fuso horário acima.
    """
    import urllib.error
    import urllib.request

    antes = acessos_registados()
    print(f"  · acessos no registo, antes: {antes}")
    for caminho in ("/", "/api/perguntar", "/api/health", "/api/estado"):
        pedido = urllib.request.Request(url.rstrip("/") + caminho)
        try:
            with urllib.request.urlopen(pedido, timeout=30) as r:
                codigo = r.status
        except urllib.error.HTTPError as e:
            codigo = e.code
        except OSError as e:
            codigo = f"erro: {e}"
        print(f"    {caminho} → {codigo}")
    time.sleep(3)
    depois = acessos_registados()
    print(f"  · acessos no registo, depois dos 4 pedidos de fora: {depois}")

    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORTA}/api/health",
                                    timeout=10):
            pass
    except OSError as e:
        print(f"recusado: o serviço local não respondeu ({e}), logo o "
              f"instrumento não se pode verificar", file=sys.stderr)
        return 2
    time.sleep(2)
    com_local = acessos_registados()
    print(f"  · acessos depois de **um pedido local**: {com_local}")

    de_fora, do_local = depois - antes, com_local - depois
    if do_local < 1:
        print("\nINVÁLIDO: um pedido que chegou ao serviço não deixou linha no "
              "registo. «Zero de fora» não prova nada enquanto isto não "
              "crescer.", file=sys.stderr)
        return 2
    if de_fora:
        print(f"\nD4 FALHA: {de_fora} pedido(s) de fora chegaram ao uvicorn.",
              file=sys.stderr)
        return 1
    print(f"\nD4 passa: 0 de {4} pedidos de fora tocaram no uvicorn, e o "
          f"instrumento morde (+{do_local} com um pedido local).")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Instala o serviço público nesta máquina (passo 4).")
    p.add_argument("--destino", type=Path, default=DESTINO,
                   help=f"o checkout do serviço (omissão: {DESTINO})")
    p.add_argument("--ref", default=None,
                   help="etiqueta ou commit a servir (omissão: o HEAD do "
                        "checkout de trabalho)")
    p.add_argument("--ensaio", action="store_true",
                   help="imprime o que faria, e não toca em nada")
    p.add_argument("--verificar-d4", metavar="URL", default=None,
                   help="mede o portão D4 contra um URL público já de pé, e "
                        "não instala nada")
    p.add_argument("--verificar-d2", action="store_true",
                   help="julga o portão D2 pelo tempo monótono: o serviço é "
                        "mais velho que a sessão, e subiu no arranque?")
    p.add_argument("--copiar", action="store_true",
                   help="uma cópia verificada do data/sessoes.db, e roda as "
                        "antigas. É o que o temporizador corre (portão D8)")
    p.add_argument("--restaurar", metavar="FICHEIRO", nargs="?",
                   const="", default=None,
                   help="põe uma cópia no lugar da base, verificando-a antes "
                        "de tocar em nada; sem argumento, a mais recente")
    p.add_argument("--listar-copias", action="store_true",
                   help="as cópias que existem, da mais antiga para a mais "
                        "recente, com o que cada uma tem dentro")
    p.add_argument("--recuar", metavar="ETIQUETA", default=None,
                   help="volta o serviço a uma etiqueta, verificando o "
                        "manifesto antes de reiniciar (portão D6)")
    p.add_argument("--guardar-tunel", action="store_true",
                   help="uma passagem da guarda: reinicia o túnel se o URL "
                        "não responder. É o que o temporizador corre")
    p.add_argument("--verificar-tunel", action="store_true",
                   help="pergunta ao URL se o túnel está vivo, e não ao "
                        "systemctl — que responde «active» com o URL morto")
    a = p.parse_args(argv)

    if a.verificar_d4:
        return verificar_d4(a.verificar_d4)

    if a.verificar_d2:
        return verificar_d2()
    if a.copiar:
        return copiar_sessoes(ensaio=a.ensaio)
    if a.restaurar is not None:
        return restaurar_sessoes(a.restaurar or None, ensaio=a.ensaio)
    if a.listar_copias:
        return listar_copias()

    if a.recuar:
        try:
            alvo_recuo = Alvo.de(a.destino)
            recusar_o_trabalho(alvo_recuo, RAIZ)
        except ErroDeUnidade as e:
            print(f"recusado: {e}", file=sys.stderr)
            return 2
        return recuar(alvo_recuo, a.recuar, ensaio=a.ensaio)

    if a.guardar_tunel:
        return guardar_tunel()

    if a.verificar_tunel:
        url = url_do_tunel()
        if url is None:
            print("o túnel não anunciou URL nenhum nesta execução",
                  file=sys.stderr)
            return 1
        vivo, detalhe = tunel_vivo(url)
        activa = subprocess.run(
            ("systemctl", "--user", "is-active", NOME_TUNEL),
            capture_output=True, text=True).stdout.strip()
        print(f"  · URL:        {url}")
        print(f"  · o URL diz:  {detalhe}")
        print(f"  · o systemd diz: {activa}")
        if not vivo:
            print(f"\nTÚNEL MORTO com a unidade «{activa}». Remédio:\n"
                  f"  systemctl --user restart {NOME_TUNEL}\n"
                  f"e o URL muda — ver a §7.2 do plano.", file=sys.stderr)
            return 1
        return 0

    ref = a.ref or (ler_lancamento().sha or "HEAD")
    try:
        alvo = Alvo.de(a.destino)
        recusar_o_trabalho(alvo, RAIZ)
    except ErroDeUnidade as e:
        print(f"recusado: {e}", file=sys.stderr)
        return 2

    print(f"{'ENSAIO — nada será alterado' if a.ensaio else 'A instalar'}")
    print(f"  trabalho: {RAIZ}")
    print(f"  serviço:  {alvo.checkout}  (ref {ref})")
    passos = (("clone", lambda: clonar(alvo, ref, ensaio=a.ensaio)),
              ("artefactos", lambda: copiar_artefactos(alvo, ensaio=a.ensaio)),
              ("venv", lambda: criar_venv(alvo, ensaio=a.ensaio)),
              ("unidades", lambda: instalar_unidades(alvo, ensaio=a.ensaio)),
              ("linger", lambda: ligar_linger(ensaio=a.ensaio)))
    for nome, correr in passos:
        print(f"\n[{nome}]")
        try:
            correr()
        except Falhou as e:
            print(f"\nfalhou em «{nome}»: {e}", file=sys.stderr)
            print("nenhum passo seguinte correu.", file=sys.stderr)
            return 1

    print("\n[verificação, do que não precisa de reinício]")
    linhas, queixa = verificar(alvo, ensaio=a.ensaio,
                               tunel=bool(decidir_tunel()))
    for linha in linhas:
        print(linha)
    if queixa is not None:
        print(f"\nINSTALAÇÃO INCOMPLETA: {queixa}", file=sys.stderr)
        return 1
    print(f"""
O portão **D2** não se mede daqui. Os dois comandos que o medem, e que só o
dono pode correr, são:

  1. fechar a sessão gráfica e voltar a entrar, e depois:
       curl -s http://127.0.0.1:{PORTA}/api/health
  2. reiniciar a máquina, e correr o mesmo `curl` **antes** de abrir a sessão
     gráfica (por SSH, ou num terminal virtual).

Em ambos, o `sha` tem de ser o do checkout do serviço. Enquanto os dois não
forem corridos, o D2 está **por medir** — e não cumprido.""")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
