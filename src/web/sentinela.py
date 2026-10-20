"""O interbloqueio entre processos: o servidor cede à medição, nunca o contrário.

Passo 7 da Fase 6, portão **I8**. O trinco do `app.py` é um `asyncio.Lock`,
logo é **por processo**, e há um segundo processo que não é hipotético: o
`gerar_amostras.py` de cada fase importa `src.generation.ollama.OllamaGenerator`
e fala com o **mesmo** `127.0.0.1:11434` e o mesmo modelo. Contra ele o trinco
dá zero (§2.4 do [plano](../../docs/FASE-6.md)).

O custo de os deixar competir já tem precedente nesta casa e está no
`CONTROLO.md` §4, na lista de «defeitos encontrados nos meus próprios
instrumentos»: um cache de KV reaproveitado entre repetições de um *benchmark*
reportou prefill a **25 625 tok/s e invalidou 4 horas de dados**. O modo de
falha é o mesmo — uma variável não controlada no instrumento, descoberta
depois — e aqui a variável é o `campo segundos` do `01-cru.jsonl` de uma fase a
medir o que o servidor lhe roubou.

## O sentido é único, e isso é a decisão

**O servidor é que cede.** Uma medição interrompida a meio perde-se — a Fase 5Z
são 60 amostras a ~34 s, meia hora só de geração, e a construção do índice são
383 s. Uma pergunta recusada repete-se com uma tecla. Logo quem escreve o
ficheiro é quem corre a fase, e quem o lê e desiste é o servidor.

Nada disto entra em `src/generation/ollama.py`. Era o sítio
arquitectonicamente certo e a decisão errada: acrescentava um `flock` a cada
chamada HTTP do caminho que as Fases 0 a 5Y mediram, e isso é uma mudança que
precisava de medição própria. **Zero alterações ao caminho medido.**

## Porque é que o caminho é absoluto, e não `data/.medicao-a-correr`

O plano da Fase 6 especificou `data/.medicao-a-correr` — relativo ao checkout.
A correcção veio de [`PRODUCAO.md`](../../docs/PRODUCAO.md) §4, **antes** deste
código ser escrito, e é de desenho e não de manutenção: o serviço público corre
num **segundo checkout** na mesma máquina, logo há **dois `data/`**. A fase
escreve no seu, o servidor verifica o outro:

> O ficheiro nunca é visto, o `/api/estado` diz que está tudo bem, e o
> mecanismo que existe para tornar o túnel seguro está **silenciosamente
> desligado**.

É o modo de falha do manifesto do índice outra vez — «um índice velho carregado
por engano não dá erro: dá respostas erradas» (`src/retrieval/index.py`) — e
desta vez no instrumento que protege as medições. Um caminho relativo passa nos
testes (um processo, um directório) e falha na máquina, que é a pior das duas
combinações. Daí o portão I8 ter ganho uma asserção: **a fase escreve de um
checkout e o servidor, no outro, vê-o** (`tests/test_sentinela.py`).

E daí haver **uma** variável de ambiente e não duas. O `XDG_STATE_HOME` ficou
de fora de propósito, apesar de ser o padrão que `~/.local/state` implementa:
os dois processos têm de concordar no caminho, e cada fonte de verdade a mais é
outra maneira de discordarem — que é exactamente o defeito que esta secção
existe para fechar. Quem quiser mudar o sítio muda-o num lugar só.

## O guarda de alcance, que é o passo 5 do `PRODUCAO.md`, está feito

O `medicao()` deixou de só escrever o ficheiro: **para e arranca o túnel**. O
§3.3 do [plano](../../docs/PRODUCAO.md) argumenta porquê — com um URL público,
409 durante as sete horas de uma fase de enriquecimento não é honestidade, é
uma avaria com uma mensagem interna; e um pedido que chega na pausa de 60 s da
Fase 0 §3.2 não gera nada e **aquece o chip**, pondo duas causas
indistinguíveis na mesma queda monotónica de tok/s (*throttling* medido até
101 °C). O remédio é o túnel cair, não o 409.

O túnel entra por **indirecção**, e não como um `systemctl` em linha: não há
túnel instalado nesta máquina, logo este código foi escrito antes de haver o
que parar. O porquê, o `TunelAusente` que declara o estado de hoje, e a decisão
sobre **o que acontece quando parar falha** (a fase recusa arrancar) estão em
[`tunel.py`](tunel.py), que é o dono dessa prosa.

A **janela registada** com as amostras (os instantes em que o túnel esteve de
pé, para uma célula lenta ser interpretável dentro de seis meses) é o passo 7
do mesmo plano, e não é daqui.

E nada disto entra no caminho do `GET /api/estado`: o `a_correr()` e o
`componente()` continuam a ler **só o ficheiro**, e não perguntam nada a
nenhuma unidade. O portão **I4** (menos de 100 ms durante uma geração) não
ganhou trabalho nenhum — os 7,9 µs sem ficheiro e 15,6 µs com ele continuam a
descrever o que ele mede. Quem fala com o túnel é o `medicao()`, que corre no
processo da **fase** e nunca no do servidor.
"""
from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .estado import Componente
from .tunel import (
    Tunel,
    TunelAusente,
    TunelIndisponivel,
    avisar_que_nao_voltou,
)
from .tunel import desta_maquina as tunel_desta_maquina

#: O sítio, **absoluto e único na máquina**, fora de qualquer checkout. Ver a
#: secção do cabeçalho: com dois checkouts, um caminho relativo desliga o
#: mecanismo em silêncio.
CAMINHO_OMISSAO = Path.home() / ".local" / "state" / "pessoabot" / ".medicao-a-correr"

#: A única sobreposição, para os testes poderem apontar os dois lados ao mesmo
#: ficheiro sem escrever no estado real desta máquina.
VARIAVEL = "PESSOABOT_SENTINELA"


def caminho() -> Path:
    """O sentinela desta máquina, lido **a cada chamada** e não à importação.

    Lido a cada chamada porque é o que permite a um teste apontar dois
    directórios de trabalho ao mesmo ficheiro — e porque uma constante fixada
    na importação tornava a variável de ambiente inútil num processo de vida
    longa como o `uvicorn`.

    Não valida que é absoluto: um caminho relativo na variável é escolha de
    quem a define, e levantar aqui rebentava o `GET /api/estado`, que é o canal
    que tem de responder sempre. A asserção vive no teste do portão I8.
    """
    bruto = os.environ.get(VARIAVEL)
    return Path(bruto) if bruto else CAMINHO_OMISSAO


@dataclass(frozen=True)
class Medicao:
    """A fase que está a correr, como o ficheiro a declara.

    O `pid` existe para que um sentinela esquecido **se diagnostique**: sem
    ele, um ficheiro deixado para trás por um `gerar_amostras.py` que rebentou
    deixava o servidor a recusar para sempre sem dizer de quem era a culpa.
    """

    fase: str
    pid: int
    inicio: float
    #: `False` quando o PID já não existe: sentinela esquecido. Continua a
    #: bloquear — ver `a_correr` —, mas o remédio passa a ser nomeável.
    vivo: bool = True

    @property
    def decorrido_s(self) -> float:
        return max(0.0, time.time() - self.inicio)

    def descricao(self) -> str:
        quanto = f"há {self.decorrido_s / 60:.0f} min"
        if not self.vivo:
            return (f"«{self.fase}» (PID {self.pid}, {quanto}) — e o processo "
                    f"{self.pid} já não existe: sentinela esquecido")
        return f"«{self.fase}» (PID {self.pid}, {quanto})"


def _processo_vivo(pid: int) -> bool:
    """O PID do ficheiro ainda corre?

    `os.kill(pid, 0)` não envia sinal nenhum: pergunta se o processo existe e
    se há permissão para lhe falar. `PermissionError` é resposta afirmativa —
    existe, é de outro utilizador.
    """
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return True
    return True


def a_correr(*, alvo: Path | None = None) -> Medicao | None:
    """A medição em curso, ou `None`. **Barato**: um `stat` e um JSON pequeno.

    Barato porque está no caminho do `GET /api/estado`, que o portão **I4**
    obriga a responder em menos de 100 ms **durante** uma geração.

    Um ficheiro ilegível ou mal formado devolve uma `Medicao` e não `None`, e
    isso é deliberado: o sentido é único (§2.4) e a direcção segura é o
    servidor ceder. Tratar lixo como «não há medição» era escolher a única
    saída que pode invalidar horas de dados — e é literalmente a forma «não dá
    erro: dá respostas erradas» que este módulo existe para não repetir.
    """
    c = caminho() if alvo is None else alvo
    try:
        bruto = c.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except OSError as e:
        return Medicao(f"ilegível ({e.strerror})", 0, time.time(), vivo=False)
    try:
        d = json.loads(bruto)
        fase, pid = str(d["fase"]), int(d["pid"])
        inicio = float(d.get("inicio", time.time()))
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        # Um ficheiro existe e não se entende: bloqueia, e diz o que viu
        # (truncado, porque o conteúdo vai ao `/api/estado` e à página).
        return Medicao(f"ficheiro ininteligível: {bruto[:60]!r}", 0,
                       time.time(), vivo=False)
    return Medicao(fase, pid, inicio, vivo=_processo_vivo(pid))


def componente(*, alvo: Path | None = None) -> Componente:
    """O sentinela como componente do `/api/estado`, ao lado do `ollama` (§2.4).

    «Pronto» aqui é **não haver medição** — é a leitura que o resto do
    `/api/estado` já faz: pronto significa «dá para responder». E o `remedio`
    nomeia o ficheiro por caminho completo, porque com dois checkouts na mesma
    máquina «apaga o sentinela» não diz onde.
    """
    c = caminho() if alvo is None else alvo
    m = a_correr(alvo=c)
    if m is None:
        return Componente("sentinela", True, "nenhuma medição a correr")
    return Componente("sentinela", False,
                      f"medição a correr: {m.descricao()}",
                      remedio=f"acaba a fase, ou apaga {c}")


def escrever(fase: str, *, alvo: Path | None = None) -> Medicao:
    """Declara a medição. Chamado por quem corre a fase, não pelo servidor."""
    c = caminho() if alvo is None else alvo
    c.parent.mkdir(parents=True, exist_ok=True)
    m = Medicao(fase, os.getpid(), time.time())
    c.write_text(json.dumps({"fase": m.fase, "pid": m.pid,
                             "inicio": m.inicio}, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    return m


def limpar(*, alvo: Path | None = None) -> bool:
    """Retira o sentinela. Devolve se havia um. Idempotente de propósito."""
    c = caminho() if alvo is None else alvo
    try:
        c.unlink()
    except FileNotFoundError:
        return False
    return True


@contextmanager
def medicao(fase: str, *, alvo: Path | None = None, tunel: Tunel | None = None,
            amostras: Path | None = None, janela: Path | None = None):
    """O ajudante das fases **futuras**: `with medicao("5Z"): ...`.

    As fases fechadas ficam como estão. Não se retroajusta um trinco aos
    `gerar_amostras.py` commitados: são artefactos de registo, e o
    `pyproject.toml` já explica porque é que nem o formatador lhes toca —
    «reformatá-los reescrevia o registo».

    O `finally` é o que torna isto mecanismo em vez de disciplina: uma fase que
    rebenta a meio não deixa o servidor recusado para sempre. Quando deixa —
    um `kill -9` —, o PID no ficheiro diagnostica-o (ver `Medicao.descricao`).

    ⚠️ **A ordem é a decisão, e não é invertível.** Parar o túnel vem
    imediatamente **depois** do `escrever` e arrancá-lo imediatamente **antes**
    do `limpar`, por fora — de modo que o ficheiro já exista quando o URL cai e
    ainda exista enquanto ele volta, e **nunca haja um instante com túnel de pé
    e medição a correr**. Invertê-la abre exactamente a janela que o mecanismo
    fecha: um pedido que entrasse nela gerava contra o Ollama da fase, e o
    `campo segundos` do `01-cru.jsonl` ficava ininterpretável sem o dizer.
    Verificado **por mutação** em `tests/test_sentinela.py` — com a ordem
    trocada, o teste da ordem cai.

    **Parar falha ⇒ a fase não arranca**, e o sentinela que já tinha sido
    escrito é retirado antes de levantar (senão um `TunelIndisponivel` deixava
    o servidor a recusar perguntas por causa de uma fase que nunca começou). O
    porquê desta decisão — a assimetria de custos, e porque é que o sentido
    único do §2.4 **não** a responde — está no cabeçalho do `tunel.py`.

    **Arrancar falha ⇒ avisa, e não levanta.** A fase já correu, os dados são
    bons, e levantar aqui trocava um resultado válido por uma excepção — ou,
    pior, tapava a excepção do corpo da fase.
    """
    c = caminho() if alvo is None else alvo
    t = tunel_desta_maquina() if tunel is None else tunel
    m = escrever(fase, alvo=c)
    # Houve porta a fechar? `TunelAusente.parar()` devolve `None` sem fazer
    # nada — e correctamente, porque sem `PESSOABOT_TUNEL` não há alcance a
    # fechar. Mas na janela isso **não** pode aparecer como «o túnel esteve em
    # baixo»: é «não havia túnel», e quem ler a fase daqui a seis meses precisa
    # de distinguir as duas. É a única coisa que esta linha decide.
    parado = not isinstance(t, TunelAusente)
    try:
        t.parar()
    except TunelIndisponivel:
        # O ficheiro é de uma fase que não vai correr. Retirá-lo é o que
        # impede isto de recusar perguntas ao servidor para sempre.
        limpar(alvo=c)
        raise
    j = Janela(fase=fase, pid=m.pid, inicio=instante(m.inicio),
               tunel=t.nome, parado=parado,
               amostras=str(amostras) if amostras else "",
               bytes_no_inicio=_bytes(amostras))
    # Escrita **já aberta**, com `fim: null`, e não só no fim. Uma fase morta
    # por `kill -9` não corre `finally` nenhum: sem esta escrita não deixava
    # rasto algum, e quem lesse a pasta via amostras sem janela sem saber
    # porquê. Com ela, fica lá a dizer que começou e não fechou — que é a
    # mesma ideia do PID no sentinela, aplicada ao registo.
    _escrever_janela(j, janela_de(amostras, janela))
    try:
        yield m
    finally:
        try:
            t.arrancar()
        except TunelIndisponivel as e:
            avisar_que_nao_voltou(t, e)
        limpar(alvo=c)
        # **Depois** do `arrancar` e do `limpar`, e no `finally`: a janela tem
        # de fechar mesmo quando a fase rebenta — uma corrida que morreu a meio
        # é precisamente a que mais precisa de deixar escrito até onde foi.
        _fechar_janela(j, amostras, janela)


# --- a janela: o passo 7 do plano do serviço público, portão D5 ---------- #

#: Onde a janela de uma fase se escreve, ao lado das amostras dela. O nome
#: começa por `00-` de propósito: numa pasta de fase, o que explica a corrida
#: tem de aparecer **antes** do que ela produziu.
NOME_DA_JANELA = "00-janela.json"


def instante(t: float | None = None) -> str:
    """Um instante em UTC com `Z`, no mesmo formato do `saude.em_utc`.

    O **mesmo** formato de propósito, e há um teste a compará-los: a janela vai
    ser lida ao lado do `commit_em` do `/api/health`, e duas datas do mesmo
    repositório em formatos diferentes é o tipo de atrito que faz quem as lê
    desistir de as comparar. E em UTC porque o `journalctl` desta casa já
    custou uma medição por causa de um fuso (`CONTROLO.md` §4, correcção 46).
    """
    from datetime import datetime, timezone
    d = datetime.fromtimestamp(time.time() if t is None else t, timezone.utc)
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class Janela:
    """Os instantes em que uma fase correu, e o que o túnel fez nesse tempo.

    ## Porque é que isto não mede o que o portão D5 dizia que media

    O **D5** afirma: «o ficheiro de uma fase corrida sob o ajudante contém os
    instantes de túnel de pé, e eles **não se sobrepõem aos instantes das
    amostras**». A segunda metade **não é mensurável com o formato de hoje**:
    os dez `01-cru.jsonl` das Fases 5B a 5Z **não têm instante nenhum** —
    verificado, campo a campo. Têm `segundos`, que é uma duração, e ninguém
    sabe quando é que cada amostra aconteceu.

    Então o que aqui se mede é outra coisa, e é dizível: **o ficheiro das
    amostras só cresceu enquanto a janela esteve aberta.** `bytes_no_inicio`,
    `bytes_no_fim` e `mtime_no_fim` são três instantes/medidas que existem hoje,
    sem tocar em nenhum `gerar_amostras.py` — e o `pyproject.toml` já explica
    porque é que nem o formatador lhes toca, «reformatá-los reescrevia o
    registo».

    Isto apanha o modo de falha que importa — **a fase correu fora do
    ajudante**, ou alguém acrescentou amostras depois de o túnel voltar — e não
    apanha uma amostra individual mal colocada dentro da janela. A diferença
    está escrita em vez de escondida.
    """

    fase: str
    pid: int
    #: Instantes em UTC. `fim` é `None` quando o processo morreu com a janela
    #: aberta — e isso **é** um resultado: as amostras dessa corrida não têm
    #: janela fechada, logo não se sabe o que o túnel fez no fim.
    inicio: str
    fim: str | None = None
    #: O que o `tunel.py` diz ser o túnel desta máquina. Hoje, com o passo 6
    #: desligado (§7.5), é «nenhum» — e registá-lo é o que distingue «o túnel
    #: esteve em baixo» de «não havia túnel nenhum».
    tunel: str = ""
    #: O túnel foi mesmo parado? `False` com `TunelAusente`, e aí a fase correu
    #: sem público possível **por não haver porta**, não por ela se ter fechado.
    parado: bool = False
    amostras: str = ""
    bytes_no_inicio: int = 0
    bytes_no_fim: int = 0
    mtime_no_fim: str | None = None

    def falhas(self) -> list[str]:
        """O que está errado nesta janela. Vazio é o que o portão D5 pede."""
        ms = []
        if self.fim is None:
            ms.append("a janela nunca fechou: a fase morreu a meio, e não se "
                      "sabe o que o túnel fez depois")
        if not self.amostras:
            ms.append("a janela não nomeia ficheiro de amostras, logo não diz "
                      "nada sobre elas")
        elif self.bytes_no_fim == self.bytes_no_inicio:
            ms.append(f"{self.amostras} não cresceu durante a janela: a fase "
                      f"não escreveu amostra nenhuma debaixo do ajudante")
        elif self.mtime_no_fim is not None and self.fim is not None and not (
                self.inicio <= self.mtime_no_fim <= self.fim):
            ms.append(f"{self.amostras} foi escrito em {self.mtime_no_fim}, "
                      f"fora da janela [{self.inicio}, {self.fim}]: houve "
                      f"amostras geradas sem o ajudante")
        return ms

    def como_dicionario(self) -> dict:
        from dataclasses import asdict
        return asdict(self)


def _bytes(caminho: Path | None) -> int:
    try:
        return Path(caminho).stat().st_size if caminho else 0
    except OSError:
        return 0


def janela_de(amostras: Path | None, janela: Path | None) -> Path | None:
    """Onde a janela se escreve: o que lhe derem, ou ao lado das amostras."""
    if janela is not None:
        return Path(janela)
    return Path(amostras).parent / NOME_DA_JANELA if amostras else None


def _escrever_janela(j: Janela, destino: Path | None) -> None:
    """Nunca levanta. Ver o `_fechar_janela`."""
    if destino is None:
        return
    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            json.dumps(j.como_dicionario(), ensure_ascii=False, indent=1)
            + "\n", encoding="utf-8")
    except OSError as e:
        print(f"⚠️ a janela de «{j.fase}» não se escreveu em {destino}: {e}")


def _fechar_janela(j: Janela, amostras: Path | None,
                   janela: Path | None) -> None:
    """Fecha a janela, se houver onde. Nunca levanta.

    Nunca levanta porque isto corre num `finally` **depois** de a fase ter
    produzido os dados: uma falha a escrever o registo da janela não pode
    deitar fora meia hora de geração, nem tapar a excepção do corpo da fase. É
    a mesma decisão do `arrancar` acima, pela mesma razão.
    """
    destino = janela_de(amostras, janela)
    if destino is None:
        return
    mtime = None
    try:
        if amostras is not None and Path(amostras).exists():
            mtime = instante(Path(amostras).stat().st_mtime)
    except OSError:
        mtime = None
    fechada = Janela(**(j.como_dicionario() | {
        "fim": instante(), "bytes_no_fim": _bytes(amostras),
        "mtime_no_fim": mtime}))
    _escrever_janela(fechada, destino)


def ler_janela(caminho: Path) -> Janela:
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    return Janela(**dados)

