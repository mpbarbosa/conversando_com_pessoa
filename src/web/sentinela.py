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

## O que este módulo **não** faz, e tem dono

Parar e arrancar o túnel a partir do `with` é o **passo 5 do
`PRODUCAO.md`**, não deste. O §3.3 desse plano mostra porquê: com um URL
público, 409 durante as sete horas de uma fase de enriquecimento não é
honestidade, é uma avaria com uma mensagem interna — e um pedido que chega na
pausa de 60 s da Fase 0 §3.2 não gera nada e **aquece o chip**, pondo duas
causas indistinguíveis na mesma queda monotónica de tok/s. O remédio é o túnel
cair, não o 409. A emenda entra em volta das duas linhas que o `medicao()`
abaixo marca, e não dentro delas.

A **janela registada** com as amostras (os instantes em que o túnel esteve de
pé, para uma célula lenta ser interpretável dentro de seis meses) é o passo 7
do mesmo plano, e também não é daqui.
"""
from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .estado import Componente

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
def medicao(fase: str, *, alvo: Path | None = None):
    """O ajudante das fases **futuras**: `with medicao("5Z"): ...`.

    As fases fechadas ficam como estão. Não se retroajusta um trinco aos
    `gerar_amostras.py` commitados: são artefactos de registo, e o
    `pyproject.toml` já explica porque é que nem o formatador lhes toca —
    «reformatá-los reescrevia o registo».

    O `finally` é o que torna isto mecanismo em vez de disciplina: uma fase que
    rebenta a meio não deixa o servidor recusado para sempre. Quando deixa —
    um `kill -9` —, o PID no ficheiro diagnostica-o (ver `Medicao.descricao`).

    ⚠️ **O ponto de extensão do passo 5 do `PRODUCAO.md` é aqui**, nas duas
    linhas marcadas: parar o túnel vem imediatamente depois do `escrever` e
    arrancá-lo imediatamente antes do `limpar`, **por fora** — de modo que o
    ficheiro já exista quando o URL cai e ainda exista enquanto ele volta, e
    nunca haja um instante com túnel de pé e medição a correr. A ordem é essa e
    não a inversa; invertê-la abria exactamente a janela que o mecanismo fecha.
    """
    c = caminho() if alvo is None else alvo
    m = escrever(fase, alvo=c)
    # ↓ passo 5 do PRODUCAO.md: parar o túnel entra nesta linha.
    try:
        yield m
    finally:
        # ↑ passo 5 do PRODUCAO.md: arrancar o túnel entra nesta linha.
        limpar(alvo=c)
