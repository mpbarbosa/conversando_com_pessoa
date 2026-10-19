"""De que código é que este processo foi lançado. Portão **D1** do plano do
[serviço público](../../docs/PRODUCAO.md) §6.

## Porque é que o `/api/estado` não serve de sonda

O `GET /api/estado` é bom no que faz — prontidão por componente, sem carregar
nada, a responder em menos de 100 ms **durante** uma geração (portão I4). Falha
como sonda de serviço por duas razões, e as duas estão medidas:

1. **Não diz de onde o código veio.** É a disciplina que transfere do
   repositório irmão: o `sha` estampado é a verificação forte, o `uptime` a
   fraca. Um serviço que não sabe nomear o seu próprio código não se pode
   verificar, e «recuar» (passo 8) não se pode confirmar.
2. **`pronto` é `false` antes da primeira pergunta, por construção.** O índice
   só se verifica quando há corpus carregado, e o corpus só se carrega na 1.ª
   pergunta. Uma sonda que exigisse `pronto` reprovava **todos** os arranques
   saudáveis; uma que aceitasse `pronto: false` não verificava nada. O campo é o
   `pode_perguntar`, que nasceu precisamente deste defeito, observado a correr a
   página do passo 5.

## O `sha` lê-se **à importação**, e isso é a decisão que importa

Não por ser mais barato (são 3,6 ms, medidos). É porque o campo afirma **de que
código este processo foi lançado**, e não «o que está no directório agora». Um
`git rev-parse` por pedido dizia a verdade sobre o disco e **mentia sobre o
processo**: depois de um `git checkout` no checkout do serviço, o `uvicorn`
continua a correr os módulos que já importou, e a sonda passava a nomear código
que não está em memória. Seria a forma exacta do que este plano passa o tempo a
corrigir — o mecanismo a dizer «certo» depois de deixar de descrever o que
protege — e no sítio mais caro de todos, porque é a sonda que o passo 8 usa para
confirmar um recuo.

Consequência aceite e escrita: **reiniciar é o que actualiza o `sha`**, e é
assim que o recuo do passo 8 funciona de qualquer maneira (`git checkout` da
etiqueta, `systemctl --user restart`).

## A raiz é a deste ficheiro, e não o directório de trabalho

`RAIZ` deriva de `__file__`. O `cwd` de uma unidade de utilizador é o que o
`WorkingDirectory` disser, e com **dois checkouts** (§4 do plano) o `git` do
directório errado respondia com o `sha` do checkout de **trabalho** enquanto o
serviço corria o outro — e respondia com sucesso, sem erro nenhum. É o mesmo
defeito que o sentinela teve com `data/.medicao-a-correr` relativo
(`CONTROLO.md` §4 #39), e a mesma correcção: caminho absoluto, derivado do
módulo, com a asserção no teste.

## Sem `git`, sem etiqueta, sem nada: diz-se, não se adivinha

Três faltas possíveis, e nenhuma levanta: o `git` ausente do `PATH`, a raiz que
não é um checkout, e o `git` a demorar. Todas dão `sha: None` e um `erro` em
texto, e o `status` deixa de ser `ok` — porque uma sonda que devolve `ok` sem
saber nomear o código é pior do que não haver sonda.

A **etiqueta** é `None` hoje e isso não é falha: não há etiquetas neste
repositório, e criá-las é o passo 8. `None` é o estado verdadeiro.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

#: O checkout de que este módulo foi importado. Ver o cabeçalho: **não** é o
#: `cwd`.
RAIZ = Path(__file__).resolve().parents[2]

#: Generoso para um `git` local, e curto para não pendurar a importação se o
#: directório estiver num disco que não responde.
TEMPO_LIMITE_S = 5.0


@dataclass(frozen=True)
class Lancamento:
    """O código de que o processo foi lançado, como o `git` do checkout o diz."""

    #: `git rev-parse --short HEAD`. `None` quando não se conseguiu ler.
    sha: str | None
    #: A etiqueta que aponta para o `HEAD`, se houver uma. `None` é legítimo.
    etiqueta: str | None
    #: Data do commit do `HEAD`, em UTC. **Não** é o instante do arranque: o
    #: `uptime` é a verificação fraca que a §6 do plano recusa.
    commit_em: str | None
    #: Porque é que o `sha` é `None`. `""` quando está tudo bem.
    erro: str = ""

    @property
    def nomeia_o_codigo(self) -> bool:
        return self.sha is not None


def _git(raiz: Path, *args: str) -> tuple[str, str]:
    """Corre um `git` no checkout. Devolve `(saida, erro)`; nunca levanta."""
    try:
        r = subprocess.run(("git", "-C", str(raiz), *args),
                           capture_output=True, text=True,
                           timeout=TEMPO_LIMITE_S)
    except FileNotFoundError:
        return "", "git não está no PATH"
    except subprocess.TimeoutExpired:
        return "", f"git não respondeu em {TEMPO_LIMITE_S:.0f} s"
    except OSError as e:
        return "", f"git falhou: {e}"
    if r.returncode != 0:
        detalhe = r.stderr.strip().splitlines()
        return "", (f"git {args[0]} falhou: "
                    f"{detalhe[0] if detalhe else f'código {r.returncode}'}")
    return r.stdout, ""


def ler_lancamento(raiz: Path = RAIZ) -> Lancamento:
    """Interroga o `git` do checkout. Chamada **uma vez**, à importação do `app`.

    Recebe `raiz` para o teste do portão D1 poder apontá-la a um checkout
    construído de propósito — e é isso que torna a asserção «o `sha` é o do
    checkout do serviço e não o do `cwd`» mensurável em vez de declarada.
    """
    saida, erro = _git(raiz, "show", "-s", "--format=%h%n%cI", "HEAD")
    if erro:
        return Lancamento(sha=None, etiqueta=None, commit_em=None, erro=erro)
    linhas = saida.strip().split("\n")
    if len(linhas) != 2 or not linhas[0]:
        return Lancamento(sha=None, etiqueta=None, commit_em=None,
                          erro=f"git show deu {saida.strip()!r}")
    sha, data = linhas
    etiquetas, _ = _git(raiz, "tag", "--points-at", "HEAD")
    nomes = [x for x in etiquetas.strip().split("\n") if x]
    return Lancamento(sha=sha, etiqueta=nomes[0] if nomes else None,
                      commit_em=em_utc(data))


def em_utc(bruto: str) -> str | None:
    """`2026-10-19T10:59:38-03:00` → `2026-10-19T13:59:38Z`.

    O `%cI` do git traz o desvio de quem fez o commit (`-03:00` nesta máquina).
    Duas sondas a comparar datas de fusos diferentes comparam cadeias que
    diferem por motivo nenhum, logo normaliza-se num sítio só.
    """
    try:
        d = datetime.fromisoformat(bruto.strip())
    except ValueError:
        return None
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
