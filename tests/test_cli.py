"""Aceite do Passo 9 da Fase 1.

Testa as peças do CLI que não precisam de modelo. A validação real foi a
travessia completa, registada em `docs/FASE-1.md` §Passo 9.
"""

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


# --- roteador no CLI — Passo A4 da Fase 4 ---------------------------------
#
# O que importa aqui não é a exactidão (medida em `docs/fase-4/`), é que o
# roteador **propõe e não decide**: a proposta aparece antes de gerar, e um
# comando de voz desliga-o.

from src.cli import COMANDOS_AUTO, _propor
from src.generation.base import Resposta


class _GeradorDeVoz:
    def __init__(self, texto: str):
        self.texto = texto

    @property
    def nome(self) -> str:
        return "falso"

    @property
    def janela_contexto(self) -> int:
        return 4096

    def gerar(self, system, user, *, max_tokens=220, temperatura=None):
        return Resposta(texto=self.texto, prefill_s=0.1, decode_s=0.1,
                        prefill_tokens=331, decode_tokens=2)

    def gerar_em_fluxo(self, system, user, *, max_tokens=220):
        raise NotImplementedError


class _PipelineFalso:
    def __init__(self, texto: str):
        self.gerador = _GeradorDeVoz(texto)


def test_comandos_auto_ligam_e_desligam():
    assert {"/auto", "/manual"} == COMANDOS_AUTO


def test_propor_usa_a_voz_do_roteador(capsys):
    voz = _propor(_PipelineFalso("campos"), "o ruído das máquinas",
                  Voice.ORTONIMO)
    assert voz is Voice.CAMPOS
    saida = capsys.readouterr().out
    assert "Álvaro de Campos" in saida


def test_a_proposta_nomeia_os_comandos_de_override(capsys):
    """A 72% de acerto, o que separa «custa uma tecla» de «custa 30 s» é o
    utilizador ver como mudar enquanto a proposta ainda não gerou nada."""
    _propor(_PipelineFalso("reis"), "beber sem pensar no fim", Voice.ORTONIMO)
    saida = capsys.readouterr().out
    for comando in ("/caeiro", "/campos", "/reis", "/pessoa"):
        assert comando in saida


def test_propor_mantem_a_voz_corrente_quando_o_roteador_nao_sabe(capsys):
    voz = _propor(_PipelineFalso("não tenho a certeza"), "qualquer coisa",
                  Voice.CAEIRO)
    assert voz is Voice.CAEIRO
    assert "sem opinião" in capsys.readouterr().out
