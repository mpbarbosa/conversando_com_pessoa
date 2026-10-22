"""A direcção proibida: a **política** não importa o **transporte**.

O §9 do [plano do serviço público](../docs/PRODUCAO.md) fecha a lista do que
muda em `src/` com uma frase que não é um comentário, é a afirmação de carga de
todo o plano:

> «Nada em `src/pipeline.py`, `src/grafo.py`, `src/guard.py`, `src/retrieval/`
> ou `src/generation/`. **Um plano de publicação que precise de mexer na
> política está mal desenhado.**»

E o código honra-a numa direcção só. O `src/web/` **lê** constantes e
*dataclasses* da política — o `serial.py` importa de `pipeline`, `guard`,
`plagio`, `roteador`, `voices` e `corpus.models`, o `app.py` de `roteador`,
`voices` e `apresentacao` — e nunca lhe escreve. É por isso que o
`src/web/retencao.py` existe **no transporte**: a retenção do corpo é uma
decisão de publicação, e a política não tem de saber que ela existe.

A direcção que falta é a inversa: **nenhum módulo da política importa
`src.web`**. Se o `plagio.py` ou o `pipeline.py` precisassem do `retencao.py`
para decidir algo, a retenção deixava de ser uma política de publicação
removível e passava a ser parte da política de geração — e o §9 passava a ser
falso sem ninguém o reescrever.

## Porque é que este ficheiro nasceu verde

O [`NOTACAO.md`](../docs/twowayflow/NOTACAO.md) §6 nomeia esta restrição como
«a única linha da tabela que o grafo de imports não resolveu»: o grafo mede o
que é **alcançável**, e isto é uma direcção que **nunca** pode ser tomada. E
diz, re-verificado a 2026-10-22, que «não há teste nenhum sobre a direcção dos
imports para dentro de `src/web/`».

Passou à primeira, porque a violação não existe. **Passar não prova nada**: foi
verificado a morder, com um `from .web.retencao import redigir` posto à mão no
`src/plagio.py`, e a falha nomeia o módulo —
`src/plagio.py:14 importa src.web.retencao` — antes de ser revertido. Um guarda
que só se viu verde não é prova de nada.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
FONTE = RAIZ / "src"

TRANSPORTE = "src.web"
"""A camada de transporte, em nome pontuado — o que a política não pode importar."""


def _modulos_da_politica() -> list[Path]:
    """Tudo sob `src/` que **não** é o transporte, nem o seu `__init__`."""
    return sorted(
        f
        for f in FONTE.rglob("*.py")
        if "web" not in f.relative_to(FONTE).parts
    )


def _nome_pontuado(ficheiro: Path) -> str:
    """`src/retrieval/lexical.py` → `src.retrieval.lexical`."""
    partes = ficheiro.relative_to(RAIZ).with_suffix("").parts
    if partes[-1] == "__init__":
        partes = partes[:-1]
    return ".".join(partes)


def _pacote(ficheiro: Path) -> list[str]:
    """O pacote **onde o módulo vive**, que é o ponto de partida do `from .x`."""
    partes = _nome_pontuado(ficheiro).split(".")
    if ficheiro.name == "__init__.py":
        return partes
    return partes[:-1]


def _resolver(pacote: list[str], nivel: int, modulo: str | None) -> str:
    """`from ..web import x` dentro de `src.retrieval` → `src.web`.

    O nível 1 é o próprio pacote do módulo; cada nível a mais sobe um.
    """
    subida = pacote[: len(pacote) - (nivel - 1)] if nivel > 1 else pacote
    return ".".join([*subida, *(modulo.split(".") if modulo else [])])


def _importados(ficheiro: Path) -> list[tuple[int, str]]:
    """Os imports de um ficheiro, em nome absoluto, com a linha.

    Os relativos são resolvidos contra o pacote do próprio módulo, porque é
    `from ..web import x` — e não `import src.web.x` — o que um módulo de
    dentro do `src/` escreveria se violasse isto.
    """
    arvore = ast.parse(ficheiro.read_text(encoding="utf-8"), filename=str(ficheiro))
    saida: list[tuple[int, str]] = []
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            saida.extend((no.lineno, a.name) for a in no.names)
        elif isinstance(no, ast.ImportFrom):
            if no.level == 0:
                if no.module:
                    saida.append((no.lineno, no.module))
                continue
            saida.append(
                (no.lineno, _resolver(_pacote(ficheiro), no.level, no.module))
            )
    return saida


def _viola(nome: str) -> bool:
    """`src.web` e tudo por baixo; `src.webhooks` não contaria."""
    return nome == TRANSPORTE or nome.startswith(TRANSPORTE + ".")


def test_a_politica_nao_importa_o_transporte():
    """§9 do `PRODUCAO.md`: a direcção política → `src/web/` não existe.

    A asserção é sobre a árvore toda de uma vez e não módulo a módulo, para que
    a falha possa nomear **todos** os infractores de um arranque — um `import`
    acrescentado em dois sítios no mesmo *commit* é o caso em que ver só o
    primeiro custa uma segunda volta.
    """
    infraccoes = [
        f"{f.relative_to(RAIZ)}:{linha} importa {nome}"
        for f in _modulos_da_politica()
        for linha, nome in _importados(f)
        if _viola(nome)
    ]
    assert not infraccoes, (
        "A política importa o transporte, e o §9 do docs/PRODUCAO.md diz que "
        "um plano de publicação que precise de mexer na política está mal "
        "desenhado:\n  " + "\n  ".join(infraccoes)
    )


def test_o_transporte_importa_a_politica():
    """A direcção **permitida**, afirmada para que o teste de cima tenha sentido.

    Sem isto, apagar o `src/web/` inteiro deixaria o teste de cima verde, e um
    varrimento que passa por vacuidade é o modo de falha que o
    [`test_i7.py`](test_i7.py) já apanhou uma vez em si mesmo.
    """
    assert len(_modulos_da_politica()) > 20, "o varrimento não está a ver o src/"

    serial = FONTE / "web" / "serial.py"
    lidos = {nome for _, nome in _importados(serial)}
    assert "src.plagio" in lidos
    assert "src.pipeline" in lidos


@pytest.mark.parametrize(
    ("relativo", "esperado"),
    [
        ("src/plagio.py", "src.plagio"),
        ("src/retrieval/lexical.py", "src.retrieval.lexical"),
        ("src/retrieval/__init__.py", "src.retrieval"),
    ],
)
def test_nome_pontuado(relativo, esperado):
    """O instrumento: um nome mal formado leria `src.web` como `web` e calava-se."""
    assert _nome_pontuado(RAIZ / relativo) == esperado


@pytest.mark.parametrize(
    ("ficheiro", "nivel", "modulo", "esperado"),
    [
        ("src/plagio.py", 1, "web.retencao", "src.web.retencao"),
        ("src/retrieval/lexical.py", 2, "web", "src.web"),
        ("src/retrieval/lexical.py", 2, "web.retencao", "src.web.retencao"),
        ("src/retrieval/lexical.py", 1, "normalize", "src.retrieval.normalize"),
        ("src/retrieval/__init__.py", 1, "lexical", "src.retrieval.lexical"),
    ],
)
def test_resolucao_de_import_relativo(ficheiro, nivel, modulo, esperado):
    """Um `from ..web import x` tem de chegar a `src.web`, ou o guarda não morde.

    É a metade do instrumento que a violação de controlo não exercitou — a
    mutação foi escrita com um nível só, num módulo da raiz do `src/` — e sem
    isto um erro de aritmética nos níveis deixava passar as violações escritas
    de dentro de um subpacote.
    """
    assert _resolver(_pacote(RAIZ / ficheiro), nivel, modulo) == esperado
