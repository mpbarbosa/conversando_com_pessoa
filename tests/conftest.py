"""Configuração da suíte. Uma coisa só, e é uma protecção.

## Nenhum teste escreve no `data/sessoes.db` real

O passo 8 da Fase 6 deu ao `Servico` um `Arquivo` por omissão, e por omissão
ele aponta para `data/sessoes.db` **do checkout onde a suíte corre**. Os testes
que constroem `Servico(...)` sem lhe passar um arquivo — e são dezenas, de
`tests/test_perguntar.py` a `tests/test_i7.py` — gravavam lá as sessões de
mentira que inventam.

**Isto não é hipotético: aconteceu.** Na primeira corrida da suíte com a
persistência ligada apareceram **180 KB** em `data/sessoes.db`, com as
perguntas dos testes dentro. O ficheiro está no `.gitignore` (por direitos e
por privacidade), logo o `git status` não o mostrava, logo nada o denunciava a
não ser olhar para a pasta.

A protecção é uma variável de ambiente para a sessão de testes inteira, e é
`autouse`: não há como um teste novo escapar por esquecimento. Vale notar que
ela só funciona porque o `sessoes.py` lê `PESSOABOT_SESSOES` **na construção**
do `Arquivo` e não na importação do módulo — uma constante de módulo era lida
antes de qualquer `fixture` existir, e esta protecção não protegia nada.
"""
from __future__ import annotations

import pytest


@pytest.fixture(scope="session", autouse=True)
def sessoes_fora_do_checkout(tmp_path_factory):
    """Aponta `PESSOABOT_SESSOES` a um ficheiro temporário, para toda a suíte.

    `scope="session"` e não por teste: a isolação que interessa é em relação ao
    **checkout**, não entre testes. Quem precisa de uma base limpa por teste
    constrói o `Arquivo` com o seu próprio caminho — é o que o
    `tests/test_sessoes.py` faz, e por isso lê melhor.
    """
    caminho = tmp_path_factory.mktemp("sessoes") / "suite.db"
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("PESSOABOT_SESSOES", str(caminho))
        yield caminho
