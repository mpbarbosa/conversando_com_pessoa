"""Conjunto dourado — Passo 8 da Fase 1.

## Enviesamento de pooling — ler antes de comparar sistemas

O gabarito foi construído agrupando o top-5 do **denso** e do **BM25**. Ambos
são depois avaliados sobre um gabarito que ajudaram a criar, o que inflaciona os
dois. Um sistema **terceiro** — o reranker da Fase 3, ou a fusão da Fase 2 se
mudar a ordem — pode trazer documentos relevantes que nunca foram julgados, e
que contam **0** por omissão.

**Procedimento obrigatório ao avaliar um sistema novo:** agrupar também o seu
top-5, julgar os candidatos que surgirem pela primeira vez, e só então comparar.
Sem isso, qualquer sistema novo é penalizado por construção.

Foi executado na Fase 2: a fusão RRF trouxe **33 candidatos** nunca julgados em
17 das 20 perguntas, **12 com nota 2**. Sem os julgar, o resultado negativo da
fusão teria sido um artefacto em vez de um facto.

**Este é o instrumento que autoriza ou veta as Fases 2 e 3.** Ambas existem
exclusivamente para melhorar um número, e é este.

Relevância **graduada** (0/1/2) sobre candidatos agrupados por pooling TREC, não
gabarito único — ver `src/avaliacao.py` para o porquê.
"""
import json
import os

import pytest

from src.avaliacao import Gabarito, avaliar
from src.corpus.build import load
from src.corpus.models import Voice

PERGUNTAS = "docs/fase-1/08-perguntas.json"
JULGAMENTOS = "docs/fase-1/08-julgamentos.json"

pytestmark = pytest.mark.skipif(
    not os.path.exists("data/index.npy"),
    reason="índice não construído",
)


@pytest.fixture(scope="module")
def corpus():
    return load()


@pytest.fixture(scope="module")
def gabarito(corpus):
    meta, _ = corpus
    j = json.load(open(JULGAMENTOS, encoding="utf-8"))
    notas = {k: v for k, v in j.items() if not k.startswith("_")}
    return Gabarito(notas=notas, representantes=meta["representantes"])


@pytest.fixture(scope="module")
def perguntas():
    return json.load(open(PERGUNTAS, encoding="utf-8"))["perguntas"]


@pytest.fixture(scope="module")
def denso(corpus):
    from src.retrieval.encoder import Encoder
    from src.retrieval.index import Index
    meta, chunks = corpus
    enc = Encoder()
    idx = Index.load(chunks, enc, meta["assinatura"])
    assert idx is not None, "índice recusado"

    def recuperar(q: str, voz: str):
        qv = enc.encode_queries([q])[0]
        return [c for c, _ in idx.search(qv, top_k=10, voz=Voice(voz))]
    return recuperar


@pytest.fixture(scope="module")
def lexical(corpus):
    from src.retrieval.lexical import IndiceLexical
    _, chunks = corpus
    lex = IndiceLexical(chunks)

    def recuperar(q: str, voz: str):
        return [c for c, _ in lex.search(q, top_k=10, voz=Voice(voz))]
    return recuperar


# --- integridade do gabarito ----------------------------------------------

def test_gabarito_tem_perguntas_julgadas(gabarito):
    assert len(gabarito.perguntas_julgadas) >= 20


def test_notas_sao_validas(gabarito):
    for q, notas in gabarito.notas.items():
        for pid, n in notas.items():
            assert n in (0, 1, 2), f"{q}/{pid} = {n}"


def test_cada_pergunta_julgada_tem_pelo_menos_um_dois(gabarito):
    """Uma pergunta sem resposta de nota 2 não discrimina nada."""
    sem = [q for q in gabarito.perguntas_julgadas
           if 2 not in gabarito.notas[q].values()]
    assert not sem, sem


def test_gabarito_resolve_grupos_de_deduplicacao(gabarito):
    """poem_1000 é gabarito de q05 e passou a não-representante de poem_629.
    Procurar por qualquer um dos dois tem de dar a mesma nota."""
    assert gabarito.nota("q05", "poem_629") == 2
    assert gabarito.nota("q05", "poem_1000") == 2


def test_poema_nao_julgado_vale_zero(gabarito):
    assert gabarito.nota("q01", "poem_9999") == 0


# --- linha de base ---------------------------------------------------------

def test_linha_de_base_do_denso(denso, perguntas, gabarito):
    """Fixa a linha de base que a Fase 2 tem de bater.

    Os valores vêm da medição de 2026-10-01 (ver 08-RELATORIO.md). A margem é
    folgada de propósito: o teste existe para apanhar regressões, não para
    congelar o número.
    """
    r = avaliar(denso, perguntas, gabarito)
    print(f"\ndenso: {r}")
    assert r.n_perguntas >= 20
    # Baixado de 0,65 para 0,62: o gabarito cresceu de 176 para 209 candidatos
    # quando a Fase 2 agrupou e julgou os 33 que só a fusão trazia, e 12 têm
    # nota 2. Um ideal mais completo dá nDCG mais baixo e mais verdadeiro —
    # o denso passou de 0,719 para 0,677 sem nada mudar no denso.
    assert r.ndcg5 >= 0.62, f"regressão: nDCG@5 = {r.ndcg5:.3f} (medido 0,677)"
    assert r.apt3 >= 0.85, f"regressão: apt@3 = {r.apt3:.0%} (medido 95%)"


def test_linha_de_base_do_lexical(lexical, perguntas, gabarito):
    r = avaliar(lexical, perguntas, gabarito)
    print(f"\nBM25: {r}")
    assert r.n_perguntas >= 20
    assert r.ndcg5 >= 0.40, f"regressão: nDCG@5 = {r.ndcg5:.3f} (medido 0,464)"


def test_filtro_de_voz_e_respeitado(denso, perguntas):
    for p in perguntas[:8]:
        for c in denso(p["q"], p["voz"]):
            assert c.voice is Voice(p["voz"])
