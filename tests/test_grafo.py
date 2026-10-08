"""Paridade entre o grafo (LangGraph) e o pipeline escrito à mão.

Estes testes existem para responder a uma pergunta só: **o porte mudou o
comportamento?** Se mudar, os números medidos (nDCG@5, taxa de plágio, custo por
pergunta) deixam de valer para o caminho novo, e o porte deixa de ser porte.

Reutilizam deliberadamente o `GeradorFalso` do `test_pipeline.py`: é o duplo que
reproduz o modo de falha real — copiar do contexto até deixar de o ver — e é o
que exercita o ciclo de repetição, que é a parte interessante do grafo.
"""
import pytest

from src.corpus.build import load
from src.corpus.models import Lang, Voice
from src.grafo import PipelineGrafo, construir
from src.pipeline import Pipeline

from .test_pipeline import GeradorFalso, _pipeline


@pytest.fixture(scope="module")
def chunks_caeiro():
    _, cs = load()
    return [c for c in cs if c.voice is Voice.CAEIRO][:8]


def _par(chunks, copiar_de: str) -> tuple[Pipeline, PipelineGrafo]:
    """Dois caminhos com geradores equivalentes mas independentes.

    Independentes porque o `GeradorFalso` acumula os prompts que viu; partilhar
    a instância faria o segundo caminho ver o histórico do primeiro.
    """
    a = _pipeline(chunks, GeradorFalso(copiar_de))
    b = _pipeline(chunks, GeradorFalso(copiar_de))
    return a, PipelineGrafo.de(b)


def test_paridade_no_caminho_limpo(chunks_caeiro):
    """Sem plágio, o grafo devolve o mesmo turno — e numa tentativa só."""
    reto, grafo = _par(chunks_caeiro, "nada disto aparece no contexto")
    t1 = reto.responder("o que é a natureza?", Voice.CAEIRO)
    t2 = grafo.responder("o que é a natureza?", Voice.CAEIRO)

    assert t2.texto == t1.texto
    assert t2.tentativas == t1.tentativas == 1
    assert t2.aprovado is t1.aprovado is True
    assert [c.poem_id for c in t2.usados] == [c.poem_id for c in t1.usados]
    assert [c.poem_id for c in t2.recuperados] == [c.poem_id for c in t1.recuperados]


def test_paridade_no_ciclo_de_repeticao(chunks_caeiro):
    """Com plágio na 1ª tentativa, os dois repetem e chegam ao mesmo sítio.

    É este o teste que vale: o ciclo é a única coisa que o grafo declara de
    forma diferente, e é onde um porte descuidado quebraria.
    """
    alvo = chunks_caeiro[0]
    reto, grafo = _par(chunks_caeiro, alvo.text)
    t1 = reto.responder("o que é a natureza?", Voice.CAEIRO)
    t2 = grafo.responder("o que é a natureza?", Voice.CAEIRO)

    assert t1.tentativas == 2, "o duplo devia ter forçado uma repetição"
    assert t2.tentativas == t1.tentativas
    assert t2.texto == t1.texto
    assert t2.aprovado is t1.aprovado
    assert t2.plagio.plagiou is t1.plagio.plagiou


def test_o_poema_copiado_sai_do_contexto_tambem_no_grafo(chunks_caeiro):
    """A política medida do `_repetir_sem` sobrevive ao porte.

    O poema de que o modelo copiou não pode voltar ao prompt da repetição — foi
    isso que resolveu o caso real das duas rejeições em ~80 s.
    """
    alvo = chunks_caeiro[0]
    g = GeradorFalso(alvo.text)
    grafo = PipelineGrafo.de(_pipeline(chunks_caeiro, g))
    grafo.responder("o que é a natureza?", Voice.CAEIRO)

    assert len(g.prompts) == 2, "devia ter havido exactamente uma repetição"
    assert alvo.text in g.prompts[0]
    assert alvo.text not in g.prompts[1], "o poema copiado voltou ao contexto"


def test_o_limite_de_tentativas_e_respeitado(chunks_caeiro):
    """Com `max_tentativas=1` não há ciclo, mesmo havendo plágio.

    Garante que quem decide a paragem é a nossa regra e não o
    `recursion_limit` do LangGraph.
    """
    alvo = chunks_caeiro[0]
    grafo = PipelineGrafo.de(_pipeline(chunks_caeiro, GeradorFalso(alvo.text)))
    t = grafo.responder("o que é a natureza?", Voice.CAEIRO, max_tentativas=1)

    assert t.tentativas == 1
    assert t.plagio.plagiou is True
    assert t.aprovado is False


def test_o_grafo_declara_o_ciclo(chunks_caeiro):
    """A aresta de repetição existe no desenho, não só no comportamento."""
    grafo = PipelineGrafo.de(_pipeline(chunks_caeiro, GeradorFalso("x")))
    g = grafo.grafo.get_graph()
    nos = {n for n in g.nodes}
    assert {"recuperar", "montar", "gerar", "verificar", "repetir"} <= nos
    arestas = {(e.source, e.target) for e in g.edges}
    assert ("repetir", "gerar") in arestas, "o ciclo tem de estar declarado"
    assert ("gerar", "verificar") in arestas


def test_construir_devolve_grafo_compilado(chunks_caeiro):
    """`construir` é utilizável sem o adaptador, para quem quiser `stream()`."""
    compilado = construir(_pipeline(chunks_caeiro, GeradorFalso("x")))
    estado = compilado.invoke(
        {"pergunta": "o que é a natureza?", "voz": Voice.CAEIRO,
         "idioma": Lang.PT, "max_tentativas": 2})
    assert estado["resposta"].texto
    assert estado["tentativa"] >= 1
