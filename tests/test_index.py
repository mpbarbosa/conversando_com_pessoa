"""Aceite do Passo 4 da Fase 1.

Usa o índice já construído em `data/index.npy`. Se não existir, salta — não
reconstrói (6,4 min).
"""
import json

import numpy as np
import pytest

from src.corpus.build import load as load_corpus
from src.corpus.models import Lang, Voice
from src.retrieval.encoder import Encoder
from src.retrieval.index import Index

pytestmark = pytest.mark.skipif(
    not __import__("os").path.exists("data/index.npy"),
    reason="índice não construído; correr src/corpus/build.py e Index.build",
)


@pytest.fixture(scope="module")
def corpus():
    return load_corpus()


@pytest.fixture(scope="module")
def enc():
    return Encoder()


@pytest.fixture(scope="module")
def idx(corpus, enc):
    meta, chunks = corpus
    i = Index.load(chunks, enc, meta["assinatura"])
    assert i is not None, "índice recusado — assinatura ou encoder mudaram"
    return i


# --- prefixos do e5 --------------------------------------------------------

def test_prefixos_sao_aplicados(enc):
    """O e5 degrada em silêncio sem «query: »/«passage: ». A API tem dois
    métodos distintos para que não haja caminho sem prefixo; este teste prova
    que o prefixo de facto altera o vector."""
    t = "o mar e a saudade"
    q = enc.encode_queries([t])[0]
    p = enc.encode_passages([t])[0]
    assert float(q @ p) < 0.999, "query e passage deram o mesmo vector"


def test_vectores_estao_normalizados(enc):
    v = enc.encode_queries(["qualquer coisa", "outra"])
    np.testing.assert_allclose(np.linalg.norm(v, axis=1), 1.0, atol=1e-5)


# --- manifesto e confiança -------------------------------------------------

def test_alinhamento_id_para_chunk(idx, corpus):
    """Os ids são posicionais: a ordem do manifesto é o que lhes dá sentido."""
    _, chunks = corpus
    assert idx.manifesto.n_chunks == len(chunks)
    assert idx.manifesto.chunk_ids == [[c.poem_id, c.chunk_ix] for c in chunks]
    assert idx.vectores.shape == (len(chunks), idx.manifesto.dim)


def test_recusa_assinatura_diferente(corpus, enc):
    _, chunks = corpus
    assert Index.load(chunks, enc, "assinatura-errada") is None


def test_recusa_contagem_diferente(corpus, enc):
    meta, chunks = corpus
    assert Index.load(chunks[:-1], enc, meta["assinatura"]) is None


def test_recusa_ordem_diferente(corpus, enc):
    """Trocar dois chunks de ordem invalida o índice, mesmo com o mesmo conjunto."""
    meta, chunks = corpus
    trocados = list(chunks)
    trocados[0], trocados[1] = trocados[1], trocados[0]
    assert Index.load(trocados, enc, meta["assinatura"]) is None


def test_recusa_encoder_diferente(corpus, enc):
    meta, chunks = corpus

    class Outro:
        nome = "outro/encoder"
        dim = enc.dim
    assert Index.load(chunks, Outro(), meta["assinatura"]) is None


# --- busca -----------------------------------------------------------------

def test_busca_devolve_top_k_ordenado(idx, enc):
    v = enc.encode_queries(["o mar e o cais"])[0]
    r = idx.search(v, top_k=5)
    assert len(r) == 5
    pontos = [s for _, s in r]
    assert pontos == sorted(pontos, reverse=True)


def test_filtro_por_voz(idx, enc):
    v = enc.encode_queries(["a natureza e as árvores"])[0]
    for voz in (Voice.CAEIRO, Voice.REIS, Voice.CAMPOS):
        for c, _ in idx.search(v, top_k=5, voz=voz):
            assert c.voice is voz


def test_filtro_de_idioma_por_omissao(idx, enc):
    """Português por omissão: é assim que a duplicação por tradução se
    resolve, em vez de a detectar (ver dedupe.py)."""
    v = enc.encode_queries(["the sea and the morning"])[0]
    for c, _ in idx.search(v, top_k=10):
        assert c.language is Lang.PT


def test_ode_maritima_inglesa_fica_fora(idx, enc):
    """poem_1794 é a tradução inglesa de poem_135; o filtro de idioma exclui-a."""
    v = enc.encode_queries(["um navio entra no cais de manhã"])[0]
    ids = {c.poem_id for c, _ in idx.search(v, top_k=50)}
    assert "poem_1794" not in ids


def test_busca_rejeita_dimensao_errada(idx):
    with pytest.raises(ValueError):
        idx.search(np.zeros(13, dtype="float32"))


def test_duplicados_fora_do_indice(idx):
    """Os 21 poemas marcados no Passo 2 não devem estar indexados."""
    meta, _ = load_corpus()
    duplicados = {k for k, v in meta["representantes"].items() if k != v}
    assert len(duplicados) == 21
    indexados = {c.poem_id for c in idx.chunks}
    assert not (indexados & duplicados)


def test_latencia_de_busca(idx, enc):
    """7,0 MB de vectores: a busca é um produto matriz-vector."""
    import time
    qs = [s["q"] for s in json.load(open("docs/fase-0/smoke-set.json"))]
    vs = enc.encode_queries(qs)
    t0 = time.perf_counter()
    for v in vs:
        idx.search(v, top_k=10)
    media_ms = 1000 * (time.perf_counter() - t0) / len(vs)
    assert media_ms < 100, f"{media_ms:.1f} ms por consulta"
