"""Roteador de voz — Passo A4 da Fase 4.

Não há aqui teste de exactidão: a exactidão foi medida contra 52 perguntas em
`docs/fase-4/` e um teste que a reproduzisse precisaria do Ollama e de ~1 min.
O que se testa é o **contrato**: interpretar a resposta, não inventar quando não
sabe, e não derrubar a conversa quando o gerador falha.
"""
from __future__ import annotations

import pytest

from src.corpus.models import Voice
from src.generation.base import ErroDeGeracao, Resposta
from src.roteador import (MAX_TOKENS, ROTEAVEIS, SYSTEM, TEMPERATURA,
                          interpretar, rotear)


class GeradorFalso:
    """Devolve um texto fixo e regista como foi chamado."""

    def __init__(self, texto: str = "campos"):
        self.texto = texto
        self.chamadas: list[dict] = []

    @property
    def nome(self) -> str:
        return "falso"

    @property
    def janela_contexto(self) -> int:
        return 4096

    def gerar(self, system: str, user: str, *, max_tokens: int = 220,
              temperatura: float | None = None) -> Resposta:
        self.chamadas.append({"system": system, "user": user,
                              "max_tokens": max_tokens,
                              "temperatura": temperatura})
        return Resposta(texto=self.texto, prefill_s=0.5, decode_s=0.1,
                        prefill_tokens=331, decode_tokens=2)

    def gerar_em_fluxo(self, system, user, *, max_tokens=220):
        raise NotImplementedError


class GeradorEmBaixo(GeradorFalso):
    def gerar(self, system, user, *, max_tokens=220, temperatura=None):
        raise ErroDeGeracao("Ollama não responde")


# --- interpretar -----------------------------------------------------------

@pytest.mark.parametrize("texto,esperada", [
    ("campos", Voice.CAMPOS),
    ("CAEIRO", Voice.CAEIRO),
    ("reis.", Voice.REIS),
    ("ortonimo\n", Voice.ORTONIMO),
    ("A voz é: campos", Voice.CAMPOS),
    # «pessoa» é o nome do comando do CLI, e o modelo escolhe-o às vezes
    ("pessoa", Voice.ORTONIMO),
    ("ortónimo", Voice.ORTONIMO),
])
def test_interpretar_reconhece(texto, esperada):
    assert interpretar(texto) is esperada


@pytest.mark.parametrize("texto", ["", "   ", "não sei", "soares", "Lídia"])
def test_interpretar_devolve_none_em_vez_de_palpitar(texto):
    """«Não sei» tem de poder sair. Um palpite silencioso é pior que nada."""
    assert interpretar(texto) is None


def test_todas_as_roteaveis_se_interpretam_pelo_proprio_valor():
    for v in ROTEAVEIS:
        assert interpretar(v.value) is v


def test_search_nao_e_roteavel():
    """Propor o Search a uma pergunta em português trocaria a língua da
    resposta sem o utilizador pedir."""
    assert Voice.SEARCH not in ROTEAVEIS
    assert interpretar("search") is None


# --- rotear ----------------------------------------------------------------

def test_rotear_propoe_a_voz_do_gerador():
    g = GeradorFalso("campos")
    p = rotear("o ruído das máquinas", g)
    assert p.voz is Voice.CAMPOS
    assert p.decidiu
    assert p.bruto == "campos"
    assert p.segundos >= 0


def test_rotear_e_determinista_por_construcao():
    """Temperatura 0: a mesma pergunta não pode dar vozes diferentes."""
    g = GeradorFalso()
    rotear("qualquer coisa", g)
    assert g.chamadas[0]["temperatura"] == 0.0
    assert TEMPERATURA == 0.0


def test_rotear_passa_a_pergunta_como_user_e_a_postura_como_system():
    g = GeradorFalso()
    rotear("pensar estraga o ver", g)
    c = g.chamadas[0]
    assert c["user"] == "pensar estraga o ver"
    assert c["system"] == SYSTEM
    assert c["max_tokens"] == MAX_TOKENS


def test_rotear_nao_derruba_a_conversa_quando_o_gerador_falha():
    """O roteador é conveniência; uma conveniência não tem o direito de
    derrubar a conversa. Ollama em baixo tem de dar «não sei»."""
    p = rotear("qualquer coisa", GeradorEmBaixo())
    assert p.voz is None
    assert not p.decidiu


def test_rotear_devolve_nao_sei_quando_o_modelo_divaga():
    p = rotear("qualquer coisa", GeradorFalso("Não tenho a certeza, talvez."))
    assert p.voz is None
    assert p.bruto == "Não tenho a certeza, talvez."


def test_o_system_nomeia_as_quatro_vozes_roteaveis():
    """O prompt medido descreve a postura de cada voz; se uma desaparecer do
    texto, o modelo deixa de a poder escolher."""
    for v in ROTEAVEIS:
        assert v.value.upper() in SYSTEM.upper()


# --- aquecimento — Passo A4b -----------------------------------------------

def test_aquecer_chama_o_gerador_uma_vez_e_devolve_o_custo():
    """O prefill a frio dos 331 tokens do SYSTEM custou 20 s a correr o CLI.
    `aquecer` existe para esse custo cair onde o utilizador o pediu."""
    from src.roteador import AQUECIMENTO, aquecer
    g = GeradorFalso()
    s = aquecer(g)
    assert len(g.chamadas) == 1
    assert g.chamadas[0]["user"] == AQUECIMENTO
    assert g.chamadas[0]["system"] == SYSTEM      # é o prefixo que se quer em cache
    assert s >= 0


def test_aquecer_nao_levanta_com_o_gerador_em_baixo():
    from src.roteador import aquecer
    assert aquecer(GeradorEmBaixo()) >= 0
