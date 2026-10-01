"""RRF e normalização ortográfica — Fase 2.

A fusão **não está no caminho de execução**: a medição deu resultado negativo
(ver docs/FASE-2-RELATORIO.md). Os testes existem porque o código fica no
repositório e o tecto que o limita — top_k=5 contra a redundância do corpus —
pode mudar.
"""
import pytest

from src.corpus.models import Chunk, Lang, Voice
from src.retrieval.fusion import K, rrf
from src.retrieval.lexical import tokenizar
from src.retrieval.normalize import normalizar


def ch(pid: str, ix: int = 0) -> Chunk:
    return Chunk(poem_id=pid, chunk_ix=ix, text=f"texto {pid}",
                 indexed_text=f"texto {pid}", voice=Voice.CAEIRO,
                 language=Lang.PT, n_words=2)


# --- RRF -------------------------------------------------------------------

def test_rrf_premia_quem_aparece_nas_duas_listas():
    a = [ch("p1"), ch("p2"), ch("p3")]
    b = [ch("p3"), ch("p4"), ch("p1")]
    r = rrf([a, b])
    ordem = [c.poem_id for c, _ in r]
    # p1 (1.º e 3.º) e p3 (3.º e 1.º) batem p2 e p4, que só aparecem numa
    assert set(ordem[:2]) == {"p1", "p3"}, ordem


def test_rrf_nao_normaliza_pontuacoes():
    """O cosseno do e5 anda em 0,80–0,86 e o BM25 em 5–11. O RRF usa só a
    posição, logo escalas incomparáveis não são problema."""
    a, b = [ch("p1"), ch("p2")], [ch("p2"), ch("p1")]
    r = rrf([a, b])
    assert len(r) == 2
    # empate perfeito: as duas posições somadas são iguais
    assert abs(r[0][1] - r[1][1]) < 1e-9


def test_rrf_desduplica_por_poema():
    """Dois chunks do mesmo poema são a mesma resposta: contá-los duas vezes
    dava-lhes o dobro do peso."""
    a = [ch("p1", 0), ch("p1", 1), ch("p1", 2), ch("p2")]
    r = rrf([a])
    assert [c.poem_id for c, _ in r] == ["p1", "p2"]


def test_rrf_respeita_pesos():
    a, b = [ch("pA")], [ch("pB")]
    r = rrf([a, b], pesos=[3.0, 1.0])
    assert r[0][0].poem_id == "pA"


def test_rrf_rejeita_pesos_desalinhados():
    with pytest.raises(ValueError):
        rrf([[ch("p1")], [ch("p2")]], pesos=[1.0])


def test_rrf_com_lista_vazia():
    assert rrf([[], []]) == []
    assert [c.poem_id for c, _ in rrf([[ch("p1")], []])] == ["p1"]


def test_k_e_o_do_artigo():
    """Cormack, Clarke & Buettcher, SIGIR 2009. Não afinado: 20 perguntas
    julgadas não bastam para o ajustar sem sobreajustar."""
    assert K == 60


# --- normalização ----------------------------------------------------------

def test_corrige_o_token_lixo_da_elisao():
    """O defeito que motivou a camada: `p'ra` reduzia-se ao token `ra`."""
    assert "ra" not in tokenizar("p'ra sempre")
    assert "para" not in tokenizar("p'ra sempre")   # stopword, removida
    assert tokenizar("p'ra sempre") == ["sempre"]


def test_os_dois_apostrofos_do_corpus():
    """`p'ra` (59x, U+0027) e `p’ra` (36x, U+2019)."""
    assert normalizar("p'ra") == normalizar("p’ra") == "para"


def test_alternancia_ou_oi():
    for antiga, moderna in [("cousa", "coisa"), ("cousas", "coisas"),
                            ("oiro", "ouro"), ("oiço", "ouço"),
                            ("loira", "loura"), ("papoula", "papoila")]:
        assert normalizar(antiga) == moderna


def test_elisoes_expandidas():
    assert normalizar("d'alma") == "de alma"
    assert normalizar("n'alma") == "em alma"
    assert normalizar("p'lo rio") == "pelo rio"
    assert normalizar("prò brando") == "para o brando"


def test_acentos_nao_sao_removidos():
    """O sinal que o meu gerador de candidatos usou e que a FASE-2.md já
    proibia: em português o acento distingue palavras."""
    for a, b in [("para", "pára"), ("pais", "país"), ("bebe", "bebé"),
                 ("faca", "faça"), ("sois", "sóis"), ("dois", "dóis"),
                 ("mares", "marés"), ("seria", "séria"), ("esta", "está"),
                 ("pode", "pôde")]:
        assert normalizar(a) != normalizar(b), f"{a}/{b} fundidos indevidamente"


def test_facto_e_fato_ficam_distintos():
    """Em português europeu são palavras diferentes: um facto e um fato."""
    assert normalizar("facto") != normalizar("fato")


def test_normalizacao_desligavel():
    assert tokenizar("cousa", normalizacao=False) == ["cousa"]
    assert tokenizar("cousa", normalizacao=True) == ["coisa"]
