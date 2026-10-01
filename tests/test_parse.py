"""Aceite do Passo 1 da Fase 1: todos os 2083 ficheiros parseiam, e a
distribuição de vozes bate na medição feita antes de haver código."""
from collections import Counter

import pytest

from src.corpus.models import Lang, Voice
from src.corpus.parse import detectar_idioma, parse_corpus, parse_poem

# Medido na análise do corpus, independentemente deste código.
DISTRIBUICAO_ESPERADA = {
    Voice.ORTONIMO: 1298,
    Voice.CAMPOS: 324,     # 323 + 1 com mojibake (poem_224)
    Voice.REIS: 252,
    Voice.CAEIRO: 120,
    Voice.SEARCH: 52,
    Voice.SOARES: 6,
}
TOTAL = 2083


@pytest.fixture(scope="module")
def corpus():
    return parse_corpus()


def test_todos_parseiam(corpus):
    assert len(corpus) == TOTAL


def test_distribuicao_de_vozes(corpus):
    contagem = Counter(p.voice for p in corpus)
    for voz, n in DISTRIBUICAO_ESPERADA.items():
        assert contagem[voz] == n, f"{voz}: {contagem[voz]} != {n}"
    # o resto cai em OUTRO
    assert contagem[Voice.OUTRO] == TOTAL - sum(DISTRIBUICAO_ESPERADA.values())


def test_nenhum_campo_vazio(corpus):
    for p in corpus:
        assert p.id and p.author and p.title, p.id
        assert p.voice in Voice
        assert p.language in Lang


def test_mojibake_normalizado():
    """poem_224 tem bytes espúrios antes de «lvaro de Campos»."""
    p = parse_poem("data/pessoa_poems/poem_224.txt")
    assert p.author == "Álvaro de Campos"
    assert p.voice is Voice.CAMPOS


def test_titulo_repetido_removido():
    """poem_100: cabeçalho «Titulo: Quarto: AS ILHAS AFORTUNADAS» e o corpo
    abria com «Quarto / AS ILHAS AFORTUNADAS» — as mesmas palavras outra vez."""
    p = parse_poem("data/pessoa_poems/poem_100.txt")
    assert p.title == "Quarto: AS ILHAS AFORTUNADAS"
    assert p.body.startswith("Que voz vem no som das ondas"), p.body[:60]


def test_estrofes_segmentadas():
    p = parse_poem("data/pessoa_poems/poem_100.txt")
    assert len(p.stanzas) == 3
    p2 = parse_poem("data/pessoa_poems/poem_1019.txt")  # tercete de Caeiro
    assert len(p2.stanzas) == 1


def test_idioma():
    assert detectar_idioma("Não sou nada. Nunca serei nada.") is Lang.PT
    assert detectar_idioma("Not Cecrops kept my bees. My olives bore") is Lang.EN
    assert detectar_idioma("") is Lang.INDETERMINADO


def test_distribuicao_de_idiomas(corpus):
    """Medido antes: 1928 pt / 154 en / 1 indeterminado."""
    c = Counter(p.language for p in corpus)
    assert c[Lang.PT] + c[Lang.EN] + c[Lang.INDETERMINADO] == TOTAL
    assert c[Lang.EN] > 100, "os sonetos ingleses e o Search devem aparecer"
    assert c[Lang.PT] > 1800


def test_ode_maritima_e_o_maior(corpus):
    maior = max(corpus, key=lambda p: p.n_words)
    assert maior.id == "poem_135"
    assert "ODE MAR" in maior.title.upper()


def test_poema_de_um_verso_sobrevive_a_limpeza():
    """Em poem_2873 o título É o poema («Vou atirar uma bomba ao destino.»).
    A limpeza de título repetido esvaziava-o; deve manter o original."""
    for pid in ("poem_2873", "poem_2886", "poem_4347"):
        p = parse_poem(f"data/pessoa_poems/{pid}.txt")
        assert p.body.strip(), f"{pid} ficou sem corpo"
        assert p.n_words > 3, f"{pid}: {p.body!r}"


def test_nenhum_corpo_vazio(corpus):
    vazios = [p.id for p in corpus if not p.body.strip()]
    assert not vazios, f"corpos vazios: {vazios}"
