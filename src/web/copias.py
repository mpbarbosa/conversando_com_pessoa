"""Cópias do `data/sessoes.db`, e o restauro delas. Passo 10 e portão **D8**.

O §5.3 do [plano](../../docs/PRODUCAO.md) nomeou isto antes de haver o que
copiar: «quando o passo 8 existir, `data/sessoes.db` passa a ser essa peça [...]
a cópia é um `sqlite3 .backup` num temporizador de utilizador, e o que a torna
uma cópia é o **ensaio de restauro**». O passo 8 existe desde 2026-10-25, e esta
é a primeira peça deste projecto que **nenhum script regenera**: o corpus, o
`corpus.jsonl` e o índice reconstroem-se dos 2083 ficheiros; as perguntas de
quem usou o serviço não.

## 1. `Connection.backup` e não `cp`, e a razão é o WAL

A base abre em `journal_mode = WAL`, logo o estado comprometido vive em **dois**
ficheiros: o `sessoes.db` e o `sessoes.db-wal`. Um `cp` do primeiro enquanto o
serviço escreve dá um ficheiro ou **atrasado** (as transacções do WAL não
entraram) ou **roto** (copiado a meio de uma escrita de página), e nos dois
casos o ficheiro existe, tem tamanho plausível e abre. É a família de defeito
que esta casa já conhece: «um índice velho carregado por engano não dá erro: dá
respostas erradas».

A API `sqlite3.Connection.backup` é a mesma coisa que o `.backup` da consola:
atravessa a base página a página **a partir de uma ligação**, logo vê o WAL e
coopera com quem está a escrever. É a única forma correcta com um escritor vivo,
e é de graça — a base são KB, não GB.

## 2. A cópia escreve-se com outro nome e só depois se chama cópia

Primeiro para `<nome>.parcial`, depois **verifica-se**, e só então `os.replace`
para o nome final. Duas razões, e a segunda é a que importa:

- um leitor (o restauro, ou quem lista as cópias) nunca vê um ficheiro meio
  escrito, porque o `os.replace` é atómico no mesmo sistema de ficheiros;
- **uma cópia que não se abre não chega a ter nome de cópia.** Se a verificação
  falhar, o parcial é removido e a cópia anterior continua a ser a mais recente.
  O contrário — escrever com o nome final e verificar depois — substituía a
  última cópia boa por uma má, que é o pior resultado possível de um programa
  cujo trabalho é não perder dados.

## 3. Verificar é abrir e contar, não olhar para o tamanho

`PRAGMA integrity_check`, a versão do esquema, e as contagens das tabelas que
interessam. Um ficheiro truncado a meio tem tamanho plausível e falha o
`integrity_check`; um ficheiro de outra versão passa o `integrity_check` e
mente sobre o que as colunas significam.

## 4. O restauro recusa-se antes de tocar no original

A ordem é a mesma que o §5.5 fixou para o recuo — «o manifesto **antes** e
nunca depois» — e por isso mesmo: verificado depois, já não há o que salvar. E o
original não se apaga, guarda-se: `sessoes.db` passa a `sessoes.db.substituido`
antes de a cópia entrar. Um restauro do ficheiro errado é um erro humano a uma
tecla de distância, e não se corrige se o anterior tiver sido apagado.

Os `-wal` e `-shm` do original **são removidos**, e isso não é limpeza: um WAL
antigo ao lado de uma base restaurada é a mistura de dois estados, que o SQLite
tenta aplicar e que não significa nada.

## 5. As cópias vivem fora de qualquer checkout

`~/.local/state/pessoabot/copias/`, como o sentinela e pela mesma lição do §4 do
plano: uma cópia dentro do checkout do serviço morre com aquilo de que é cópia.
Um recuo é um `git checkout` de outra etiqueta no mesmo sítio, e a coisa de que
uma cópia tem de sobreviver é precisamente uma operação naquele directório.

E podem ir para lá **porque não são cópias do corpus**: é a segunda função que o
§5.3 atribui ao portão **I6** — a base guarda `poem_id` e `chunk_ix`, nunca
corpos, logo esta cópia pode ir para onde o corpus não pode. Continua a conter
as **perguntas** de quem usou o serviço, que é a outra razão do `.gitignore`.
"""
from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .sessoes import VERSAO, caminho_padrao

#: Onde vivem. Ver a decisão 5. `PESSOABOT_COPIAS` sobrepõe-se, e é o que os
#: testes e o ensaio usam.
def directorio_padrao() -> Path:
    bruto = os.environ.get("PESSOABOT_COPIAS")
    if bruto:
        return Path(bruto)
    return Path.home() / ".local" / "state" / "pessoabot" / "copias"


#: Quantas se guardam. Sete porque a cadência é diária e uma semana é o tempo
#: que alguém leva a notar que uma sessão desapareceu; o custo é ridículo (a
#: base são KB) e o critério de apagar é «a mais antiga», nunca «a maior».
A_GUARDAR = 7

PREFIXO = "sessoes-"
SUFIXO = ".db"


class ErroDeCopia(RuntimeError):
    """A cópia não serve, ou o restauro não pode prosseguir."""


@dataclass(frozen=True)
class Estado:
    """O que uma verificação viu. `ok` é a única coisa que o portão exige."""

    ok: bool
    detalhe: str
    versao: int | None = None
    sessoes: int | None = None
    mensagens: int | None = None


def agora_para_nome() -> str:
    """O instante no nome do ficheiro, em UTC e ordenável como texto.

    `20261026T014500Z`: sem dois-pontos, porque um nome de ficheiro com `:`
    é hostil em metade dos sistemas e indistinguível de um fluxo alternativo
    noutra metade. Ordena por texto na mesma ordem que no tempo, que é o que o
    `ultima()` usa em vez de confiar no `mtime` — um `cp -p` ou um restauro
    mexem no `mtime` e não mexem no nome.
    """
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def verificar(caminho: str | Path) -> Estado:
    """Abre a cópia e conta o que lá está. Ver a decisão 3."""
    caminho = Path(caminho)
    if not caminho.exists():
        return Estado(False, f"{caminho} não existe")
    if caminho.stat().st_size == 0:
        return Estado(False, f"{caminho} está vazio")
    try:
        c = sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)
    except sqlite3.Error as e:
        return Estado(False, f"{caminho} não abre: {e}")
    try:
        integridade = c.execute("PRAGMA integrity_check").fetchone()[0]
        if integridade != "ok":
            return Estado(False, f"integrity_check: {integridade}")
        versao = c.execute("SELECT versao FROM esquema_versao").fetchone()[0]
        sessoes = c.execute("SELECT COUNT(*) FROM sessao").fetchone()[0]
        mensagens = c.execute("SELECT COUNT(*) FROM mensagem").fetchone()[0]
    except sqlite3.Error as e:
        # Um ficheiro que abre e não tem as tabelas é um SQLite qualquer, não
        # uma cópia disto. Acontece com um restauro do ficheiro errado.
        return Estado(False, f"{caminho} não tem o esquema das sessões: {e}")
    finally:
        c.close()
    if versao != VERSAO:
        return Estado(False, f"esquema versão {versao}, e este código lê a "
                             f"{VERSAO}", versao, sessoes, mensagens)
    return Estado(True, f"{sessoes} sessões · {mensagens} mensagens · "
                        f"esquema {versao}", versao, sessoes, mensagens)


def copiar(origem: str | None = None, destino: Path | None = None,
           *, a_guardar: int = A_GUARDAR) -> Path:
    """Uma cópia verificada, e devolve o caminho dela.

    Levanta `ErroDeCopia` se a base não existir ou se a cópia não passar a
    verificação — e nesse caso **não** mexe nas cópias que já existem.
    """
    origem = origem or caminho_padrao()
    destino = Path(destino) if destino is not None else directorio_padrao()
    if not Path(origem).exists():
        raise ErroDeCopia(f"não há base em {origem}: nada a copiar")
    destino.mkdir(parents=True, exist_ok=True)
    alvo = destino / f"{PREFIXO}{agora_para_nome()}{SUFIXO}"
    parcial = alvo.with_suffix(".parcial")
    # Ligação de leitura à origem: uma cópia não tem motivo para poder escrever
    # no que está a copiar, e `mode=ro` é a diferença entre não ter motivo e
    # não poder.
    fonte = sqlite3.connect(f"file:{origem}?mode=ro", uri=True)
    try:
        copia = sqlite3.connect(parcial)
        try:
            fonte.backup(copia)
        finally:
            copia.close()
    finally:
        fonte.close()
    estado = verificar(parcial)
    if not estado.ok:
        parcial.unlink(missing_ok=True)
        raise ErroDeCopia(f"a cópia não passou a verificação ({estado.detalhe}) "
                          f"— as cópias anteriores ficam como estavam")
    os.replace(parcial, alvo)   # atómico: ver a decisão 2
    _rodar(destino, a_guardar)
    return alvo


def listar(destino: Path | None = None) -> list[Path]:
    """As cópias, da mais antiga para a mais recente, por **nome**."""
    destino = Path(destino) if destino is not None else directorio_padrao()
    if not destino.exists():
        return []
    return sorted(p for p in destino.iterdir()
                  if p.name.startswith(PREFIXO) and p.suffix == SUFIXO)


def ultima(destino: Path | None = None) -> Path | None:
    copias = listar(destino)
    return copias[-1] if copias else None


def _rodar(destino: Path, a_guardar: int) -> list[Path]:
    """Apaga as mais antigas acima de `a_guardar`. Devolve as apagadas.

    **Nunca apaga a mais recente**, nem com `a_guardar` a zero: um programa de
    cópias que pode ficar sem nenhuma cópia por causa de um argumento mal posto
    não é um programa de cópias. É a mesma assimetria do §3.4 do plano — o lado
    que custa caro decide.
    """
    copias = listar(destino)
    de_mais = copias[:-max(a_guardar, 1)]
    for p in de_mais:
        p.unlink()
    return de_mais


def restaurar(copia: str | Path, base: str | None = None) -> Estado:
    """Põe `copia` no lugar da base, guardando a que estava. Ver a decisão 4.

    Devolve o `Estado` da cópia restaurada — já verificado **antes** de tocar
    em nada. Levanta `ErroDeCopia` se a cópia não servir, e aí o original fica
    exactamente onde estava.
    """
    copia, base = Path(copia), Path(base or caminho_padrao())
    estado = verificar(copia)
    if not estado.ok:
        raise ErroDeCopia(f"não restauro de {copia}: {estado.detalhe}")
    base.parent.mkdir(parents=True, exist_ok=True)
    if base.exists():
        # Guardar e não apagar: restaurar o ficheiro errado é um erro humano a
        # uma tecla de distância, e não se corrige se o anterior desaparecer.
        os.replace(base, base.with_suffix(base.suffix + ".substituido"))
    # Os sidecars do WAL do original: um WAL antigo ao lado de uma base nova é
    # a mistura de dois estados, e o SQLite **tenta aplicá-lo**.
    for lado in ("-wal", "-shm"):
        Path(str(base) + lado).unlink(missing_ok=True)
    # Copia-se o ficheiro em vez de o mover: a cópia continua a ser uma cópia
    # depois de servir para um restauro, e um restauro que consome a cópia
    # deixa-nos sem rede na segunda tentativa.
    fonte = sqlite3.connect(f"file:{copia}?mode=ro", uri=True)
    try:
        novo = sqlite3.connect(base)
        try:
            fonte.backup(novo)
        finally:
            novo.close()
    finally:
        fonte.close()
    final = verificar(base)
    if not final.ok:
        raise ErroDeCopia(f"a base restaurada não passa a verificação: "
                          f"{final.detalhe}")
    return final
