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
| `.venv` próprio | **1,3 GB**. Partilhar o do checkout de trabalho era deixar um `pip install` de desenvolvimento mudar, nesse instante, o que o serviço corre — a acoplagem que o segundo checkout existe para cortar |
| Ollama e o modelo de 4,9 GB | **partilhados**: um processo, uma cópia em memória, a unidade `ollama.service` de utilizador |
| cache do Hugging Face (encoder) | **partilhado**, 11 GB em `~/.cache/huggingface` |

Total novo em disco: **~1,32 GB**, contra 108 GB livres. O custo da saída D é de
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
import shutil
import subprocess
import sys
from pathlib import Path

from .app import PORTA
from .saude import RAIZ, ler_lancamento
from .unidades import (
    DIRECTORIO,
    GERADORES,
    NOME_OLLAMA,
    NOME_SERVICO,
    Alvo,
    ErroDeUnidade,
    escrever,
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
    """
    if alvo.checkout.exists():
        print(f"  · o checkout já existe: {alvo.checkout}")
    else:
        alvo.checkout.parent.mkdir(parents=True, exist_ok=True)
        _correr("git", "clone", "--local", str(RAIZ), str(alvo.checkout),
                ensaio=ensaio)
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

    Próprio e não partilhado: ver o cabeçalho. 1,3 GB é o preço de o serviço não
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
    """
    if ensaio:
        for nome in GERADORES:
            print(f"    $ escreve {DIRECTORIO / nome}")
    else:
        for nome, caminho in escrever(alvo).items():
            print(f"  · {nome} → {caminho}")
    _correr("systemctl", "--user", "daemon-reload", ensaio=ensaio)
    _correr("systemctl", "--user", "enable", "--now", NOME_OLLAMA, NOME_SERVICO,
            ensaio=ensaio)


def ligar_linger(*, ensaio: bool) -> None:
    """`Linger=no` é o que faz o serviço morrer com a sessão gráfica.

    É metade do passo 4 e a diferença entre «corre» e «fica a correr». Não pede
    `sudo`: `enable-linger` sobre o próprio utilizador é permitido por omissão
    no `polkit` do Ubuntu.
    """
    _correr("loginctl", "enable-linger", getpass.getuser(), ensaio=ensaio)


def verificar(alvo: Alvo, *, ensaio: bool) -> list[str]:
    """O que se pode medir **sem** fechar a sessão nem reiniciar.

    Devolve as linhas do relatório. O que fica de fora é o D2 inteiro, e está
    dito no fim em vez de assumido.
    """
    if ensaio:
        return ["    (o ensaio não verifica nada: não há nada instalado)"]
    linhas = []
    linger = _correr("loginctl", "show-user", getpass.getuser(),
                     "--property=Linger", ensaio=False).strip()
    linhas.append(f"  · {linger}")
    for nome in GERADORES:
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
    return linhas


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
    a = p.parse_args(argv)

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
    for linha in verificar(alvo, ensaio=a.ensaio):
        print(linha)
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
