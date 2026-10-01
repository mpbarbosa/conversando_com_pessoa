"""Aceite do Passo 2 da Fase 1.

Os limiares foram calibrados sobre casos inspeccionados à mão, não escolhidos
a priori. Estes testes fixam esse comportamento.
"""
import pytest

from src.corpus.dedupe import (LIMIAR_VARIANTE, detectar, marcar,
                               similaridade_versos)
from src.corpus.parse import parse_corpus


@pytest.fixture(scope="module")
def corpus():
    return parse_corpus()


@pytest.fixture(scope="module")
def relatorio(corpus):
    return detectar(corpus)


@pytest.fixture(scope="module")
def por_id(corpus):
    return {p.id: p for p in corpus}


# --- a métrica -------------------------------------------------------------

def test_metrica_separa_variante_de_incipit_partilhado(por_id):
    """O caso que motivou trocar Jaccard de n-gramas por similaridade de verso.

    poem_3222/poem_955 SÃO a mesma composição («umbrela»/«umbela»,
    «Ah, como outrora»/«Eh, como outrora») mas o Jaccard de 4-gramas dá 0,457.
    poem_17/poem_23 partilham só o incipit e são poemas distintos.
    """
    variante = similaridade_versos(por_id["poem_3222"].body, por_id["poem_955"].body)
    incipit = similaridade_versos(por_id["poem_17"].body, por_id["poem_23"].body)
    assert variante >= LIMIAR_VARIANTE, variante
    assert incipit < 0.3, incipit
    assert variante - incipit > 0.5, "a folga entre os dois regimes é pequena"


def test_metrica_apanha_contencao(por_id):
    """poem_12 tem 26 versos, todos presentes nos 47 de poem_619."""
    s = similaridade_versos(por_id["poem_12"].body, por_id["poem_619"].body)
    assert s >= 0.95, s


def test_metrica_nao_apanha_traducao(por_id):
    """A tradução parcial pt/en não é detectável por similaridade — é por isso
    que o filtro de idioma faz este trabalho em vez da deduplicação."""
    s = similaridade_versos(por_id["poem_135"].body, por_id["poem_1794"].body)
    assert s < 0.1, s


# --- os três modos ---------------------------------------------------------

def test_exactos(relatorio):
    """3 pares, não 1: normalizar o corpo limpo revela mais do que o hash do
    ficheiro em bruto."""
    assert len(relatorio.grupos_exactos) == 3
    planos = {i for g in relatorio.grupos_exactos for i in g}
    assert {"poem_1883", "poem_1954"} <= planos
    assert {"poem_328", "poem_482"} <= planos
    assert {"poem_3526", "poem_4367"} <= planos


def test_variantes_incluem_os_casos_verificados(relatorio):
    pares = {tuple(g) for g in relatorio.grupos_variantes}
    esperados = [
        ("poem_2140", "poem_2810"),   # «Não só» / «Não sei aonde»
        ("poem_177", "poem_567"),     # D. FERNANDO / GLÁDIO
        ("poem_2550", "poem_2890"),   # «p'lo rio» / «pelo rio»
        ("poem_3222", "poem_955"),    # umbrela / umbela
        ("poem_12", "poem_619"),      # contenção
        ("poem_1000", "poem_629"),    # «comovida» / «como vida»
    ]
    for par in esperados:
        assert par in pares, f"{par} não detectado"


def test_incipits_nao_sao_duplicados(relatorio, por_id):
    """18 grupos, 40 poemas. Reis escreveu odes distintas com o mesmo primeiro
    verso; colapsá-las perderia poemas."""
    assert len(relatorio.grupos_incipit) == 18
    marcados = marcar(list(por_id.values()), relatorio)
    m = {p.id: p for p in marcados}
    assert not m["poem_17"].is_duplicate
    assert not m["poem_23"].is_duplicate


def test_traducao_nao_e_marcada(relatorio, por_id):
    marcados = {p.id: p for p in marcar(list(por_id.values()), relatorio)}
    assert not marcados["poem_1794"].is_duplicate


# --- marcação --------------------------------------------------------------

def test_marcar_nao_apaga(corpus, relatorio):
    marcados = marcar(corpus, relatorio)
    assert len(marcados) == len(corpus), "marcar não deve remover poemas"
    assert relatorio.n_marcados == sum(1 for p in marcados if p.is_duplicate)


def test_representante_e_o_mais_completo(relatorio, por_id):
    """Para contenção, o representante deve ser a versão longa."""
    assert relatorio.representantes["poem_12"] == "poem_619"
    assert relatorio.representantes["poem_1644"] == "poem_1062"
    assert relatorio.representantes["poem_2904"] == "poem_4481"


def test_representante_e_idempotente(relatorio):
    """O representante de um representante é ele mesmo."""
    for pid, rep in relatorio.representantes.items():
        assert relatorio.representantes[rep] == rep, f"{pid} -> {rep}"
