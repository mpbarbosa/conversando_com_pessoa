"""Aceite do Passo 6 da Fase 1.

A maioria dos testes usa um servidor Ollama falso (`responses` via monkeypatch
do `requests.post`), para não depender de modelo carregado nem gastar 40 s por
caso. Os testes de integração saltam se o Ollama não estiver a correr.
"""
import json
import types

import pytest
import requests

from src.generation.base import ErroDeGeracao, Generator, Resposta
from src.generation.ollama import OllamaGenerator

# Resposta típica do /api/chat com stream=false.
NAO_FLUXO = {
    "model": "qwen2.5:7b-instruct-q4_K_M",
    "message": {"role": "assistant", "content": "  A árvore está ali.\nE mais nada.  "},
    "done": True,
    "prompt_eval_count": 493, "prompt_eval_duration": 10_670_000_000,
    "eval_count": 137, "eval_duration": 23_100_000_000,
    "total_duration": 33_800_000_000,
}

LINHAS_FLUXO = [
    {"message": {"content": "A árvore"}, "done": False},
    {"message": {"content": " está"}, "done": False},
    {"message": {"content": " ali."}, "done": False},
    {"message": {"content": ""}, "done": True,
     "prompt_eval_count": 493, "prompt_eval_duration": 10_670_000_000,
     "eval_count": 137, "eval_duration": 23_100_000_000},
]


class FalsaResposta:
    def __init__(self, dados=None, linhas=None, status=200, texto=""):
        self._dados, self._linhas = dados, linhas
        self.status_code, self.text = status, texto
        self.ok = 200 <= status < 300

    def json(self):
        return self._dados

    def iter_lines(self, decode_unicode=False):
        for d in self._linhas:
            yield json.dumps(d, ensure_ascii=False)


@pytest.fixture
def gen():
    return OllamaGenerator()


def _patch(monkeypatch, resposta):
    def falso_post(url, **kw):
        return resposta
    monkeypatch.setattr(requests, "post", falso_post)


# --- contrato --------------------------------------------------------------

def test_cumpre_o_protocolo(gen):
    assert isinstance(gen, Generator)


def test_parametros_vem_da_fase_0(gen):
    o = gen._opcoes(150)
    assert o["num_thread"] == 10, "varredura monotónica deu 10"
    assert o["repeat_penalty"] == 1.1, "sem isto o modelo degenerou em ciclo"
    assert o["temperature"] == 0.9
    assert o["top_p"] == 0.9


def test_keep_alive_mantem_o_cache():
    """Sem keep_alive a persona voltaria a custar 13,63s em cada pergunta."""
    from src.generation.ollama import KEEP_ALIVE
    corpo = OllamaGenerator()._corpo("s", "u", 150, False)
    assert corpo["keep_alive"] == KEEP_ALIVE
    assert KEEP_ALIVE.endswith("m")


def test_system_e_user_separados(gen):
    """A persona tem de ficar no system para ser prefixo estável."""
    corpo = gen._corpo("PERSONA", "PERGUNTA", 150, False)
    papeis = [m["role"] for m in corpo["messages"]]
    assert papeis == ["system", "user"]
    assert corpo["messages"][0]["content"] == "PERSONA"
    assert corpo["messages"][1]["content"] == "PERGUNTA"


# --- geração simples -------------------------------------------------------

def test_gerar_devolve_resposta_com_tempos(monkeypatch, gen):
    _patch(monkeypatch, FalsaResposta(dados=NAO_FLUXO))
    r = gen.gerar("s", "u")
    assert isinstance(r, Resposta)
    assert r.texto == "A árvore está ali.\nE mais nada."   # aparado
    assert r.prefill_s == pytest.approx(10.67, abs=0.01)
    assert r.decode_s == pytest.approx(23.1, abs=0.01)
    assert r.total_s == pytest.approx(33.77, abs=0.05)
    assert r.decode_tps == pytest.approx(137 / 23.1, abs=0.01)


def test_resumo_menciona_as_duas_fases(monkeypatch, gen):
    _patch(monkeypatch, FalsaResposta(dados=NAO_FLUXO))
    s = gen.gerar("s", "u").resumo()
    assert "prefill" in s and "decode" in s and "tok/s" in s


# --- fluxo -----------------------------------------------------------------

def test_fluxo_emite_fragmentos_e_depois_a_resposta(monkeypatch, gen):
    _patch(monkeypatch, FalsaResposta(linhas=LINHAS_FLUXO))
    itens = list(gen.gerar_em_fluxo("s", "u"))
    *fragmentos, final = itens
    assert fragmentos == ["A árvore", " está", " ali."]
    assert isinstance(final, Resposta)
    assert final.texto == "A árvore está ali."
    assert final.prefill_s == pytest.approx(10.67, abs=0.01)


def test_fluxo_sem_mensagem_final_falha(monkeypatch, gen):
    _patch(monkeypatch, FalsaResposta(linhas=LINHAS_FLUXO[:-1]))
    with pytest.raises(ErroDeGeracao, match="sem mensagem final"):
        list(gen.gerar_em_fluxo("s", "u"))


def test_fluxo_ignora_linhas_parciais(monkeypatch, gen):
    class ComLixo(FalsaResposta):
        def iter_lines(self, decode_unicode=False):
            yield '{"message": {"content": "A"}, "done": false}'
            yield '{"message": {"conte'          # linha partida
            yield ""
            yield json.dumps(LINHAS_FLUXO[-1])
    _patch(monkeypatch, ComLixo())
    itens = list(gen.gerar_em_fluxo("s", "u"))
    assert itens[0] == "A"
    assert isinstance(itens[-1], Resposta)


def test_erro_do_ollama_no_fluxo(monkeypatch, gen):
    class ComErro(FalsaResposta):
        def iter_lines(self, decode_unicode=False):
            yield json.dumps({"error": "model requires more system memory"})
    _patch(monkeypatch, ComErro())
    with pytest.raises(ErroDeGeracao, match="more system memory"):
        list(gen.gerar_em_fluxo("s", "u"))


# --- erros com mensagem útil ----------------------------------------------

def test_servidor_em_baixo_da_mensagem_accionavel(monkeypatch, gen):
    def recusa(url, **kw):
        raise requests.exceptions.ConnectionError("refused")
    monkeypatch.setattr(requests, "post", recusa)
    with pytest.raises(ErroDeGeracao, match="ollama serve"):
        gen.gerar("s", "u")


def test_modelo_ausente_da_mensagem_accionavel(monkeypatch, gen):
    _patch(monkeypatch, FalsaResposta(status=404, texto="not found"))
    with pytest.raises(ErroDeGeracao, match="ollama pull"):
        gen.gerar("s", "u")


def test_timeout_da_mensagem_accionavel(monkeypatch, gen):
    def estoura(url, **kw):
        raise requests.exceptions.Timeout()
    monkeypatch.setattr(requests, "post", estoura)
    with pytest.raises(ErroDeGeracao, match="excedeu"):
        gen.gerar("s", "u")


def test_erro_http_generico(monkeypatch, gen):
    _patch(monkeypatch, FalsaResposta(status=500, texto="boom"))
    with pytest.raises(ErroDeGeracao, match="500"):
        gen.gerar("s", "u")


# --- integração (salta sem servidor) ---------------------------------------

@pytest.fixture(scope="module")
def vivo():
    return OllamaGenerator().disponivel()


def test_servidor_e_modelo(vivo):
    if not vivo:
        pytest.skip("Ollama não está a correr")
    g = OllamaGenerator()
    assert g.modelo_instalado(), f"{g.modelo} não instalado"


# --- Fase 5S: o modelo de serviço, e o roteador que o partilha ----------- #

def test_o_modelo_de_servico_e_o_llama_e_o_roteador_partilha_o():
    """Fixa a decisão da Fase 5S e a sua consequência medida.

    A troca entrou com +0,667 em 3a′ replicado por um terceiro avaliador cego
    (5O) e AUC 0,526 ao poeta contra 0,851 do qwen. O custo medido é o
    **roteador**, que usa esta mesma constante por partilhar a instância de
    gerador: 72% -> 68%, duas perguntas em 40.

    Se alguém separar os dois modelos, este teste é o sítio onde se vê que a
    partilha era deliberada e não um acidente.
    """
    from src.generation.ollama import MODELO, OllamaGenerator

    assert MODELO == "llama3.1:8b-instruct-q4_K_M"
    assert OllamaGenerator().modelo == MODELO, (
        "o roteador recebe o gerador do pipeline, logo herda esta constante")
