"""Aceite do Passo 3 da Fase 1.

Usa um contador de tokens falso (palavras × 1,47, a razão medida no corpus) na
maioria dos testes, para não carregar o tokenizador real a cada um; e o real
nas asserções que dependem do limite de 512 do e5.
"""
import pytest

from src.corpus.chunk import (LIMITE_TOKENS, chunk_corpus, chunk_poem,
                              _partir_estrofe)
from src.corpus.dedupe import detectar, marcar
from src.corpus.parse import parse_corpus, parse_poem
from src.tokens import contador


def falso(texto: str) -> int:
    """1,469 tokens/palavra foi a mediana medida com o tokenizador do e5."""
    return int(len(texto.split()) * 1.47)


@pytest.fixture(scope="module")
def poemas():
    c = parse_corpus()
    return marcar(c, detectar(c))


@pytest.fixture(scope="module")
def n_tok_real():
    return contador()


# --- poema curto: um chunk só --------------------------------------------

def test_poema_curto_fica_inteiro():
    p = parse_poem("data/pessoa_poems/poem_1019.txt")   # tercete de Caeiro
    cs = chunk_poem(p, falso)
    assert len(cs) == 1
    assert cs[0].chunk_ix == 0
    assert cs[0].text == p.body


def test_texto_e_texto_indexado_sao_distintos():
    """O prompt recebe verso puro; o índice recebe autor e título."""
    p = parse_poem("data/pessoa_poems/poem_1019.txt")
    c = chunk_poem(p, falso)[0]
    assert p.author not in c.text
    assert p.author in c.indexed_text
    assert p.title in c.indexed_text
    assert c.text in c.indexed_text


# --- poema longo: janelas de estrofes -------------------------------------

def test_ode_maritima_e_partida():
    p = parse_poem("data/pessoa_poems/poem_135.txt")
    cs = chunk_poem(p, falso)
    assert len(cs) > 10, len(cs)
    assert [c.chunk_ix for c in cs] == list(range(len(cs)))


def test_nenhum_chunk_excede_o_limite(poemas):
    cs = chunk_corpus(poemas, falso)
    maiores = [(c.poem_id, c.chunk_ix, falso(c.text))
               for c in cs if falso(c.text) > LIMITE_TOKENS]
    assert not maiores, maiores[:5]


def test_nunca_parte_um_verso(poemas):
    """Todo o verso de um chunk tem de ser um verso do poema original."""
    por_id = {p.id: p for p in poemas}
    for c in chunk_corpus(poemas, falso):
        originais = {v.strip() for v in por_id[c.poem_id].body.split("\n") if v.strip()}
        for v in c.text.split("\n"):
            if v.strip():
                assert v.strip() in originais, f"{c.poem_id}#{c.chunk_ix}: {v!r}"


def test_reconstituicao_cobre_todos_os_versos(poemas):
    """A união dos chunks de um poema contém todos os seus versos."""
    por_id = {p.id: p for p in poemas}
    cs_por_poema: dict[str, list] = {}
    for c in chunk_corpus(poemas, falso):
        cs_por_poema.setdefault(c.poem_id, []).append(c)
    for pid, cs in cs_por_poema.items():
        esperados = {v.strip() for v in por_id[pid].body.split("\n") if v.strip()}
        obtidos = {v.strip() for c in cs for v in c.text.split("\n") if v.strip()}
        assert esperados <= obtidos, f"{pid}: faltam {len(esperados - obtidos)} versos"


def test_sobreposicao_entre_janelas_consecutivas():
    """Janelas consecutivas partilham uma estrofe, excepto quando uma estrofe
    sozinha enche a janela (aí não há sobreposição, para garantir progresso)."""
    p = parse_poem("data/pessoa_poems/poem_135.txt")
    cs = chunk_poem(p, falso)
    sobrepostos = 0
    for a, b in zip(cs, cs[1:]):
        if set(a.text.split("\n\n")) & set(b.text.split("\n\n")):
            sobrepostos += 1
    assert sobrepostos > 0, "nenhuma sobreposição em 43 chunks"


# --- estrofes grandes -----------------------------------------------------

def test_estrofe_grande_e_partida_por_versos():
    estrofe = "\n".join(f"verso numero {i} com algumas palavras" for i in range(100))
    grupos = _partir_estrofe(estrofe, falso, 60)
    assert len(grupos) > 1
    for g in grupos:
        assert falso(g) <= 60 or len(g.split("\n")) == 1


def test_verso_unico_maior_que_o_limite_nao_e_partido():
    """Um verso que sozinho excede o limite sai sozinho, com excesso aceite —
    partir um verso é pior que exceder o limite."""
    verso = " ".join(["palavra"] * 500)
    grupos = _partir_estrofe(verso, falso, 60)
    assert len(grupos) == 1
    assert grupos[0] == verso


# --- limite real do e5 ----------------------------------------------------

def test_texto_indexado_cabe_no_e5(poemas, n_tok_real):
    """O que de facto importa: `indexed_text` + «passage: » + tokens especiais
    tem de caber nos 512 do e5."""
    cs = chunk_corpus(poemas, n_tok_real)
    piores = sorted(((n_tok_real("passage: " + c.indexed_text) + 2, c.poem_id, c.chunk_ix)
                     for c in cs), reverse=True)[:3]
    assert piores[0][0] <= 512, piores


# --- duplicados -----------------------------------------------------------

def test_duplicados_excluidos_por_omissao(poemas):
    cs = chunk_corpus(poemas, falso)
    ids = {c.poem_id for c in cs}
    duplicados = {p.id for p in poemas if p.is_duplicate}
    assert not (ids & duplicados), "chunks de poemas duplicados no índice"
    assert len(ids) == sum(1 for p in poemas if not p.is_duplicate)


def test_duplicados_incluidos_se_pedido(poemas):
    cs = chunk_corpus(poemas, falso, incluir_duplicados=True)
    assert len({c.poem_id for c in cs}) == len(poemas)
