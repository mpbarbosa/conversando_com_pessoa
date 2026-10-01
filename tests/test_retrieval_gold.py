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

**Este é o instrumento que autoriza ou veta as Fases 2, 3, 3B e 4.** Todas
existem exclusivamente para melhorar um número, e é este.

A Fase 3B **fechou o pool**: julgou os 142 candidatos do top-20 do denso que
faltavam, e o gabarito passou de 291 para 433 julgamentos. A consequência é a
que importa — para um reranker que opere **dentro do top-20**, o pooling deixa
de o penalizar, porque não há lá documento sem nota. Foi isso que permitiu
decidir o que a Fase 3 não conseguiu.

Fora do top-20 o enviesamento volta, e o procedimento obrigatório acima
mantém-se em vigor.

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
#: Os 291 julgamentos do pooling aberto das Fases 1-3, **mais** os 142 da Fase
#: 3B que fecharam o top-20 do denso. Ficheiros separados para a proveniência de
#: cada julgamento ser recuperável; fundidos aqui porque o gabarito de medir é
#: o mais completo que existe.
JULGAMENTOS = "docs/fase-1/08-julgamentos.json"
JULGAMENTOS_3B = "docs/fase-3b/02-julgamentos-novos.json"

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
    notas: dict[str, dict[str, int]] = {}
    for caminho in (JULGAMENTOS, JULGAMENTOS_3B):
        j = json.load(open(caminho, encoding="utf-8"))
        for q, d in j.items():
            if q.startswith("_"):
                continue
            notas.setdefault(q, {}).update(d)
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
def denso20(corpus):
    """Recuperação à **profundidade do pool fechado**, que é 20.

    A fixture `denso` pede 10, e usá-la para afirmar algo sobre o top-20 seria
    afirmar menos do que o nome diz.
    """
    from src.retrieval.encoder import Encoder
    from src.retrieval.index import Index
    meta, chunks = corpus
    enc = Encoder()
    idx = Index.load(chunks, enc, meta["assinatura"])
    assert idx is not None, "índice recusado"

    def recuperar(q: str, voz: str):
        qv = enc.encode_queries([q])[0]
        return [c for c, _ in idx.search(qv, top_k=20, voz=Voice(voz))]
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
    """Fixa a linha de base que as fases de melhoria têm de bater.

    A margem é folgada de propósito: o teste existe para apanhar regressões,
    não para congelar o número.
    """
    r = avaliar(denso, perguntas, gabarito)
    print(f"\ndenso: {r}")
    assert r.n_perguntas >= 20
    # O número desceu quatro vezes **sem nada mudar no denso**, porque de cada
    # vez o ideal ficou mais completo:
    #
    #   176 candidatos (Fase 1) .................. 0,719
    #   209 (Fase 2 julgou os 33 da fusão) ....... 0,677
    #   291 (Fase 3 julgou os 82 dos rerankers) .. 0,638
    #   433 (Fase 3B fechou o top-20) ............ 0,606
    #
    # Um gabarito mais completo dá nDCG mais baixo e mais verdadeiro. Esta é a
    # última descida por esta razão dentro do top-20: o pool está fechado.
    assert r.ndcg5 >= 0.58, f"regressão: nDCG@5 = {r.ndcg5:.3f} (medido 0,606)"
    assert r.apt3 >= 0.85, f"regressão: apt@3 = {r.apt3:.0%} (medido 95%)"


def test_linha_de_base_do_lexical(lexical, perguntas, gabarito):
    r = avaliar(lexical, perguntas, gabarito)
    print(f"\nBM25: {r}")
    assert r.n_perguntas >= 20
    # Também desceu com o ideal: 0,464 com 291 julgamentos.
    assert r.ndcg5 >= 0.36, f"regressão: nDCG@5 = {r.ndcg5:.3f}"


def test_filtro_de_voz_e_respeitado(denso, perguntas):
    for p in perguntas[:8]:
        for c in denso(p["q"], p["voz"]):
            assert c.voice is Voice(p["voz"])


# --- o pool fechado, que é o que a Fase 3B entregou -----------------------

def test_o_top20_do_denso_esta_completamente_julgado(denso20, perguntas,
                                                     gabarito):
    """A propriedade que faz o Δ de um reranker significar algo.

    Se um documento do top-20 não tiver nota, um reranker que o promova é
    penalizado por construção — foi o que deu os −0,048 da Fase 3. Este teste
    falha se alguém mexer no índice, no encoder ou no corpus sem voltar a
    julgar o que passou a entrar no top-20.
    """
    sem_nota = []
    for p in perguntas:
        if not gabarito.tem(p["id"]):
            continue
        vistos = set()
        for c in denso20(p["q"], p["voz"]):
            rep = gabarito.representantes.get(c.poem_id, c.poem_id)
            if rep in vistos:
                continue
            vistos.add(rep)
            julgados = gabarito.notas[p["id"]]
            if not (c.poem_id in julgados or rep in julgados or any(
                    gabarito.representantes.get(x, x) == rep for x in julgados)):
                sem_nota.append(f"{p['id']}/{c.poem_id}")
    assert not sem_nota, (
        f"{len(sem_nota)} documentos do top-20 sem nota: {sem_nota[:10]}")


def test_o_gabarito_fechado_tem_433_julgamentos(gabarito):
    n = sum(len(v) for v in gabarito.notas.values())
    assert n == 433, f"{n} julgamentos; 291 das Fases 1-3 + 142 da 3B"
