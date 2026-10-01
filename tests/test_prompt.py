"""Aceite do orçamento de prompt (Passo 5 da Fase 1)."""
import pytest

from src.corpus.build import load
from src.corpus.models import Voice
from src.generation.prompt import ORCAMENTO_USER, montar
from src.voices import persona


def falso(texto: str) -> int:
    """~1,32 tokens/palavra: a razão do qwen2.5 em português (1,166 × 1,13)."""
    return int(len(texto.split()) * 1.32) + 1


@pytest.fixture(scope="module")
def chunks():
    _, cs = load()
    return cs


@pytest.fixture(scope="module")
def caeiro(chunks):
    return [c for c in chunks if c.voice is Voice.CAEIRO]


def test_cabe_no_orcamento(caeiro):
    p = montar("O que é a saudade?", caeiro[:20], persona(Voice.CAEIRO), falso)
    assert p.tokens_user <= ORCAMENTO_USER, p.tokens_user


def test_pergunta_esta_sempre_presente(caeiro):
    """O defeito do main.py original: o contexto empurrava a pergunta fora."""
    q = "o que é a saudade para ti?"
    p = montar(q, caeiro[:20], persona(Voice.CAEIRO), falso)
    assert q in p.user


def test_pergunta_vem_antes_do_contexto(caeiro):
    q = "o que é a saudade?"
    p = montar(q, caeiro[:5], persona(Voice.CAEIRO), falso)
    assert p.user.index(q) < p.user.index(p.chunks_usados[0].text.strip()[:20])


def test_ode_maritima_nao_estoura_o_orcamento(chunks):
    """O caso que quebrava o sistema antigo: 12 790 tokens num só poema."""
    ode = [c for c in chunks if c.poem_id == "poem_135"]
    assert ode, "poem_135 não está indexado"
    p = montar("o que é o mar?", ode, persona(Voice.CAMPOS), falso)
    assert p.tokens_user <= ORCAMENTO_USER
    assert "o que é o mar?" in p.user


def test_chunk_que_nao_cabe_e_saltado_nao_truncado(chunks):
    """Meio poema não é contexto, é ruído."""
    grande = max(chunks, key=lambda c: c.n_words)
    p = montar("pergunta", [grande], persona(Voice.CAMPOS), falso)
    assert p.chunks_usados == ()
    assert p.tokens_user <= ORCAMENTO_USER


def test_sem_contexto_ainda_produz_prompt_valido():
    p = montar("o que é a saudade?", [], persona(Voice.REIS), falso)
    assert "o que é a saudade?" in p.user
    assert p.chunks_usados == ()


def test_ordem_da_recuperacao_e_respeitada(caeiro):
    p = montar("pergunta", caeiro[:6], persona(Voice.CAEIRO), falso)
    ids = [c.poem_id for c in p.chunks_usados]
    esperado = [c.poem_id for c in caeiro[:6] if c.poem_id in ids]
    assert ids == esperado


def test_system_contem_persona_e_regras():
    p = montar("q", [], persona(Voice.REIS), falso)
    # As instruções estão escritas com mudanças de linha por legibilidade, logo
    # a busca tem de normalizar o espaço em branco. Para o modelo é indiferente.
    plano = " ".join(p.system.lower().split())
    assert "ricardo reis" in plano
    assert "enclítica" in plano
    assert "nunca escrevas em latim" in plano, "falta a interdição do latim"
    assert "nunca escrevas o nome do heterónimo" in plano


def test_system_nao_entra_no_user():
    """O sistema é prefixo estável e fica em cache; duplicá-lo no user
    desperdiçaria o orçamento variável."""
    p = montar("q", [], persona(Voice.CAEIRO), falso)
    assert p.system not in p.user


def test_tokens_variaveis_e_so_o_user():
    p = montar("q", [], persona(Voice.CAEIRO), falso)
    assert p.tokens_variaveis == p.tokens_user
    assert p.tokens_system > 100
