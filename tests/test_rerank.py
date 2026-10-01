"""Reranking — Fase 3.

O reranker **não está no caminho de execução**: a medição foi inconclusiva (ver
docs/FASE-3-RELATORIO.md). O sinal do efeito inverte-se conforme o gabarito
usado, e o apt@3 fica a 95% com e sem ele.
"""
import pytest

from src.corpus.models import Chunk, Lang, Voice
from src.retrieval.rerank import BGE_M3, MINILM, PADRAO, Reranker


def ch(pid: str, texto: str) -> Chunk:
    return Chunk(poem_id=pid, chunk_ix=0, text=texto, indexed_text=texto,
                 voice=Voice.CAEIRO, language=Lang.PT, n_words=len(texto.split()))


@pytest.fixture(scope="module")
def rr():
    """MiniLM: o `PADRAO`, porque nada foi integrado. Note-se que é o **pior**
    dos três medidos (−0,022 sem truncagem) — ver test_minilm_erra_em_portugues."""
    return Reranker(MINILM, truncar_tokens=120)


@pytest.fixture(scope="module")
def rr_bge():
    return Reranker(BGE_M3, truncar_tokens=120)


def test_bge_m3_reordena_por_relevancia(rr_bge):
    """O bge-m3 acerta: para «o que vês numa árvore?» põe as árvores primeiro."""
    cands = [ch("p1", "O mar é azul e vasto."),
             ch("p2", "As árvores do campo ao fim da tarde."),
             ch("p3", "Uma pedra no caminho.")]
    r = rr_bge.rerank("o que vês numa árvore?", cands)
    assert r[0][0].poem_id == "p2", [(c.poem_id, round(s, 5)) for c, s in r]


def test_bge_m3_pontua_em_zero_a_um_com_margem_grande(rr_bge):
    """O bge-m3 passa por sigmoide: pontuações em [0,1], com margens enormes.

    Isto enganou-me duas vezes na Fase 3. Primeiro vi «0.000» num `print`
    arredondado num caso de brinquedo e suspeitei que o modelo não discriminava,
    pondo em dúvida o ganho de +0,074 — discrimina. Depois escrevi que a
    sigmoide «comprime tudo perto de zero» e afirmei que as pontuações ficam na
    ordem de 1e-3 — também errado: a resposta certa aqui dá **0,77**.

    O que é verdade: a gama é [0,1] e usada toda, e a razão entre o certo e o
    errado é de várias ordens de magnitude (0,77 contra 1,6e-05). Os 0,0091 que
    observei antes eram de uma pergunta em que **nenhum** dos 12 candidatos era
    correspondência forte.
    """
    cands = [ch("p1", "O mar é azul."), ch("p2", "As árvores do campo.")]
    pontos = [s for _, s in rr_bge.rerank("árvores", cands)]
    assert all(0.0 <= s <= 1.0 for s in pontos), pontos
    assert pontos[0] > 0.5, f"a resposta certa devia pontuar alto: {pontos}"
    assert pontos[0] / max(pontos[1], 1e-12) > 100, f"margem pequena: {pontos}"


def test_minilm_erra_em_portugues(rr):
    """Achado medido: o MiniLM é mau em poesia portuguesa.

    Treinado em mMARCO — recuperação web traduzida — põe o poema das árvores em
    **último** quando a pergunta é sobre árvores. Consistente com os −0,022 de
    nDCG@5 que mediu sem truncagem. O teste fixa o defeito para que, se algum
    dia for corrigido a montante, se note.
    """
    cands = [ch("p1", "O mar é azul e vasto."),
             ch("p2", "As árvores do campo ao fim da tarde."),
             ch("p3", "Uma pedra no caminho.")]
    r = rr.rerank("o que vês numa árvore?", cands)
    assert r[-1][0].poem_id == "p2", (
        "o MiniLM deixou de errar este caso — reavaliar a Fase 3")


def test_pontuacoes_ordenadas(rr_bge):
    cands = [ch(f"p{i}", t) for i, t in enumerate(
        ["o mar", "as árvores verdes do campo", "uma pedra"])]
    pontos = [s for _, s in rr_bge.rerank("árvores", cands)]
    assert pontos == sorted(pontos, reverse=True)


def test_top_k(rr):
    cands = [ch(f"p{i}", f"verso número {i} sobre coisas") for i in range(6)]
    assert len(rr.rerank("coisas", cands, top_k=3)) == 3


def test_sem_candidatos(rr):
    assert rr.rerank("qualquer", []) == []


def test_truncagem_reduz_o_texto(rr):
    longo = " ".join(["palavra"] * 500)
    assert len(rr._truncar(longo)) < len(longo)


def test_sem_truncagem_mantem():
    r = Reranker(MINILM, truncar_tokens=None)
    t = " ".join(["palavra"] * 500)
    assert r._truncar(t) == t


def test_modelo_medido_como_melhor_e_o_bge_m3():
    """bge-m3 n=8 trunc=120 deu +0,074 no gabarito ampliado e −0,048 no
    original. O PADRAO fica no MiniLM porque nada foi integrado."""
    assert PADRAO == MINILM
    assert "bge-reranker-v2-m3" in BGE_M3
