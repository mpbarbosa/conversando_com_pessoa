"""Aceite da política de repetição do pipeline.

O caso que motivou estes testes foi observado a correr o chatbot, à pergunta
«você conhece o senhor fernando pessoa?»: a primeira tentativa copiou 9 de 14
versos do `poem_1164` por substituição de palavras, e a repetição — com o mesmo
contexto — voltou ao mesmo poema (5 de 14). Duas rejeições, ~80 s, e o
utilizador interrompeu.
"""
import pytest

from src.corpus.build import load
from src.corpus.models import Chunk, Lang, Voice
from src.generation.base import Resposta
from src.pipeline import Pipeline
from src.plagio import REFORCO, REFORCO_EN


@pytest.fixture(scope="module")
def chunks_caeiro():
    _, cs = load()
    return [c for c in cs if c.voice is Voice.CAEIRO][:8]


class GeradorFalso:
    """Copia o primeiro poema do contexto até deixar de o ver."""

    def __init__(self, copiar_de: str):
        self.copiar_de = copiar_de
        self.prompts: list[str] = []

    def _texto(self, user: str) -> str:
        self.prompts.append(user)
        if self.copiar_de in user:
            # Reproduz o modo de falha real: versos do contexto, quase intactos.
            versos = [l for l in self.copiar_de.split("\n") if l.strip()][:6]
            return "\n".join(versos)
        return ("Um poema sem nada de empréstimo,\n"
                "feito de palavras minhas e curtas,\n"
                "que não vêm de nenhum verso dado,\n"
                "e por isso mesmo nada provam.")

    def gerar(self, system: str, user: str) -> Resposta:
        return Resposta(texto=self._texto(user), prefill_s=0.1, decode_s=0.1,
                        prefill_tokens=10, decode_tokens=10)

    def gerar_em_fluxo(self, system: str, user: str):
        r = self.gerar(system, user)
        yield r.texto
        yield r


def _pipeline(chunks, gerador) -> Pipeline:
    p = Pipeline.__new__(Pipeline)
    p.gerador = gerador
    p.n_tokens = lambda t: int(len(t.split()) * 1.32) + 1
    p.top_k = 5
    # `recuperar` devolve `(chunks, ms, ms_rerank)` desde a Fase 3B; `None` no
    # terceiro é «sem reordenação», que é o que estes testes exercitam.
    p.recuperar = lambda pergunta, voz, idioma=Lang.PT: (list(chunks), 1.0, None)
    return p


def test_o_poema_copiado_sai_do_contexto_na_repeticao(chunks_caeiro):
    alvo = chunks_caeiro[0]
    g = GeradorFalso(alvo.text)
    t = _pipeline(chunks_caeiro, g).responder("o que é a natureza?", Voice.CAEIRO)

    assert len(g.prompts) == 2, "devia ter repetido uma vez"
    assert alvo.text in g.prompts[0]
    assert alvo.text not in g.prompts[1], "o poema copiado ficou no contexto"
    assert t.aprovado, t.plagio.resumo()


def test_a_repeticao_traz_poemas_novos_e_nao_so_menos(chunks_caeiro):
    """`montar` corta pelo orçamento, logo tirar um poema deixa entrar outro."""
    alvo = chunks_caeiro[0]
    g = GeradorFalso(alvo.text)
    _pipeline(chunks_caeiro, g).responder("o que é a natureza?", Voice.CAEIRO)

    def ids(prompt):
        return {c.poem_id for c in chunks_caeiro if c.text in prompt}

    novos = ids(g.prompts[1]) - ids(g.prompts[0])
    assert novos, "a repetição não trouxe nenhum poema novo"


def test_o_reforco_segue_a_lingua_no_caminho_do_cli(chunks_caeiro):
    """`REFORCO_EN` existia e nunca era usado: `responder_em_fluxo` não tinha
    ramo de língua, e é esse o caminho que o CLI corre."""
    alvo = chunks_caeiro[0]
    g = GeradorFalso(alvo.text)
    p = _pipeline(chunks_caeiro, g)
    list(p.responder_em_fluxo("what is nature?", Voice.CAEIRO, Lang.EN))

    assert len(g.prompts) == 2
    assert REFORCO_EN.strip() in g.prompts[1]
    assert REFORCO.strip() not in g.prompts[1]


def test_plagio_e_medido_contra_tudo_o_que_foi_mostrado(chunks_caeiro):
    """Tirar um poema do prompt não torna aceitável devolvê-lo ao utilizador."""
    alvo = chunks_caeiro[0]

    class SempreCopia(GeradorFalso):
        def _texto(self, user: str) -> str:
            self.prompts.append(user)
            return "\n".join(l for l in self.copiar_de.split("\n") if l.strip())[:400]

    g = SempreCopia(alvo.text)
    t = _pipeline(chunks_caeiro, g).responder("o que é a natureza?", Voice.CAEIRO)
    assert not t.aprovado
    assert t.plagio.plagiou, t.plagio.resumo()
    assert alvo.poem_id in {v.poema for v in t.plagio.copiados}


def test_contexto_mantem_se_quando_tudo_seria_descartado(chunks_caeiro):
    """Sem contexto a resposta perde o fundamento: melhor o reforço textual."""
    um = chunks_caeiro[:1]
    g = GeradorFalso(um[0].text)
    p = _pipeline(um, g)
    p.responder("o que é a natureza?", Voice.CAEIRO)
    assert um[0].text in g.prompts[1], "ficou sem contexto nenhum"
    assert REFORCO.strip() in g.prompts[1]


# --- reordenação opcional — Fase 3B ---------------------------------------
#
# O contrato que importa: sem reranker o pipeline pede `top_k` ao índice e não
# paga nada; com reranker pede `N_RERANK` e deixa o cross-encoder escolher
# quais `top_k` sobrevivem. Dar-lhe só `top_k` candidatos não lhe deixava nada
# para reordenar — era o defeito mais fácil de introduzir aqui.

class _IndiceEspiao:
    """Registo do `top_k` que o pipeline pediu."""

    def __init__(self, chunks):
        self._chunks = chunks
        self.pedidos: list[int] = []

    def search(self, vector, top_k=10, voz=None, idioma=None):
        self.pedidos.append(top_k)
        return [(c, 1.0 - i / 100) for i, c in enumerate(self._chunks[:top_k])]


class _EncoderFalso:
    def encode_queries(self, textos):
        import numpy as np
        return np.zeros((len(textos), 4), dtype="float32")


class _RerankerInverso:
    """Devolve os candidatos ao contrário: basta para ver se foi aplicado."""

    def __init__(self):
        self.vistos: list[int] = []

    def rerank(self, consulta, candidatos, top_k=None):
        self.vistos.append(len(candidatos))
        ordenados = [(c, float(i)) for i, c in enumerate(reversed(list(candidatos)))]
        return ordenados[:top_k] if top_k else ordenados


def _pipeline_espiao(chunks, reranker=None):
    from src.pipeline import Pipeline
    idx = _IndiceEspiao(chunks)
    p = Pipeline(idx, _EncoderFalso(), gerador=None,
                 n_tokens=lambda t: len(t.split()), top_k=3,
                 reranker=reranker)
    return p, idx


def test_sem_reranker_pede_top_k_e_nao_cobra_nada(chunks_caeiro):
    p, idx = _pipeline_espiao(chunks_caeiro)
    res, ms, ms_rr = p.recuperar("pergunta", Voice.CAEIRO)
    assert idx.pedidos == [3]
    assert ms_rr is None
    assert len(res) == 3


def test_com_reranker_pede_n_rerank_e_nao_top_k(chunks_caeiro):
    """Se pedisse `top_k`, o reranker não teria nada para reordenar."""
    from src.retrieval.rerank import N_RERANK
    rr = _RerankerInverso()
    p, idx = _pipeline_espiao(chunks_caeiro, reranker=rr)
    res, ms, ms_rr = p.recuperar("pergunta", Voice.CAEIRO)
    assert idx.pedidos == [N_RERANK]
    assert rr.vistos == [min(N_RERANK, len(chunks_caeiro))]
    assert ms_rr is not None and ms_rr >= 0
    assert len(res) == 3, "o reranker corta de novo para top_k"


def test_a_ordem_do_reranker_e_a_que_vale(chunks_caeiro):
    rr = _RerankerInverso()
    p, _ = _pipeline_espiao(chunks_caeiro, reranker=rr)
    com, _, _ = p.recuperar("pergunta", Voice.CAEIRO)
    sem, _, _ = _pipeline_espiao(chunks_caeiro)[0].recuperar("pergunta", Voice.CAEIRO)
    assert [c.poem_id for c in com] != [c.poem_id for c in sem]
