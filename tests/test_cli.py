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


# --- limpeza do início do fluxo --------------------------------------------
#
# O buffer do CLI só chamava `remover_cercas` e `remover_eco_da_pergunta`. O
# defeito foi visto no terminal: a «qual é o futuro de portugal?» o modelo
# começou por «Aqui está um poema novo, seguindo as instruções:» e essa linha
# apareceu no ecrã, embora o texto validado não a tenha — `verificar` chama
# `remover_preambulo`. O ecrã mostrava mais do que o veredicto julgara.

from src.cli import _limpar_inicio

PERGUNTA = "qual é o futuro de portugal?"


def _consumir(fragmentos, pergunta=PERGUNTA):
    """Simula o laço de streaming: devolve o que seria impresso."""
    buffer, saida, a_reter = "", [], True
    for f in fragmentos:
        if a_reter:
            buffer += f
            retido, a_reter = _limpar_inicio(buffer, pergunta)
            if a_reter:
                buffer = retido
                continue
            buffer = ""
            saida.append(retido)
            continue
        saida.append(f)
    return "".join(saida)


def test_preambulo_observado_nao_chega_ao_ecra():
    frags = ["Aqui está um poema novo, seguindo as instruções:\n",
             "os passos ecoam\n", "silêncio envolve"]
    assert "Aqui está" not in _consumir(frags)
    assert "os passos ecoam" in _consumir(frags)


def test_eco_da_pergunta_continua_a_ser_removido():
    frags = ["Qual é o futuro de Portugal?\n", "Não sei. Olho e vejo.\n"]
    out = _consumir(frags)
    assert "Qual é o futuro" not in out
    assert "Não sei" in out


def test_preambulo_e_eco_em_linhas_separadas():
    """O caso que a retenção de uma só linha deixava passar."""
    frags = ["Aqui está o poema:\n",
             "Qual é o futuro de Portugal?\n",
             "O futuro é não haver futuro.\n"]
    out = _consumir(frags)
    assert "Aqui está" not in out
    assert "Qual é o futuro de Portugal?" not in out
    assert "O futuro é não haver futuro." in out


def test_primeiro_verso_legitimo_nao_e_comido():
    frags = ["O Tejo é mais belo que o rio da minha aldeia,\n", "mas o Tejo\n"]
    assert _consumir(frags).startswith("O Tejo é mais belo")


def test_retem_enquanto_nao_houver_linha_completa():
    texto, a_reter = _limpar_inicio("sem mudança de linha ainda", PERGUNTA)
    assert a_reter
    assert texto == "sem mudança de linha ainda"
