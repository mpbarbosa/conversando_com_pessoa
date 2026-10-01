"""Aceite do Passo 9 da Fase 1.

Testa as peças do CLI que não precisam de modelo. A validação real foi a
travessia completa, registada em `docs/FASE-1.md` §Passo 9.
"""
import pytest

from src.cli import COMANDOS_VOZ, SAIR, _cinza
from src.corpus.models import Voice
from src.voices import VOZES_COM_PERSONA, persona


def test_comandos_cobrem_as_quatro_vozes_principais():
    assert set(COMANDOS_VOZ.values()) == set(VOZES_COM_PERSONA)


def test_pessoa_e_ortonimo_sao_a_mesma_voz():
    assert COMANDOS_VOZ["/pessoa"] is COMANDOS_VOZ["/ortonimo"] is Voice.ORTONIMO


def test_comandos_de_saida():
    assert "/sair" in SAIR and "sair" in SAIR


def test_cada_voz_tem_persona_com_nome():
    for voz in VOZES_COM_PERSONA:
        p = persona(voz)
        assert p.nome and p.poetica and p.forma
        assert p.voz is voz


def test_cinza_nao_perde_o_texto():
    assert "olá" in _cinza("olá")


def test_resumo_marca_truncagem():
    from src.generation.base import Resposta
    inteira = Resposta("x", 1.0, 1.0, 10, 10, truncada=False)
    cortada = Resposta("x", 1.0, 1.0, 10, 10, truncada=True)
    assert "truncada" not in inteira.resumo()
    assert "truncada" in cortada.resumo()


def test_num_predict_subiu_depois_da_truncagem_observada():
    """A 150 uma ode de Reis foi cortada a meio da palavra, no Passo 9."""
    from src.generation.ollama import NUM_PREDICT
    assert NUM_PREDICT >= 200, "voltou a um valor que corta respostas"
