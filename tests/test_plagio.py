"""Aceite do Passo 7 da Fase 1.

O caso central é real: a primeira resposta que o pipeline produziu, no Passo 6,
copiou 3 de 8 versos do contexto — e a sobreposição de 8-gramas era 2%. É por
isso que a métrica é ao nível do verso.
"""
import pytest

from src.corpus.models import Chunk, Lang, Voice
from src.plagio import LIMIAR_FRACAO, LIMIAR_VERSO, analisar


def chunk(pid: str, texto: str) -> Chunk:
    return Chunk(poem_id=pid, chunk_ix=0, text=texto,
                 indexed_text=texto, voice=Voice.CAEIRO,
                 language=Lang.PT, n_words=len(texto.split()))


# Contexto real da primeira travessia do pipeline.
CTX = [
    chunk("poem_1019",
          "Nunca sei como é que se pode achar um poente triste.\n"
          "Só se é por um poente não ser uma madrugada.\n"
          "Mas se ele é um poente, como é que ele havia de ser uma madrugada?"),
    chunk("poem_1027", "Ambos existem; cada um como é."),
]

# Saída real do Passo 6.
SAIDA_REAL = """Nunca sei como se pode achar um poente triste.

Só se for por não ser madrugada.
Mas se é poente, de que será feito?

Ambos existem; cada um seu caminho.
E é por isso que parece triste,
Porque o fim é o início do outro,
E uma metade sem a outra,
Não é inteiro."""

ORIGINAL = """O sol desce atrás do monte
e a luz muda de cor.
Não há nada nisso
que queira dizer outra coisa.
As pedras ficam mais frias.
É tudo."""


# --- o caso que motivou a métrica -----------------------------------------

def test_apanha_a_copia_real_do_passo_6():
    a = analisar(SAIDA_REAL, CTX)
    assert len(a.copiados) == 3, [c.verso for c in a.copiados]
    assert a.fracao_copiada == pytest.approx(3 / 8, abs=0.01)
    assert a.plagiou
    assert a.max_similaridade > 0.9


def test_ngramas_nao_apanhariam():
    """Prova por contraste: a sobreposição de 8-gramas é ~2% no mesmo caso."""
    import re

    def ng(t, n=8):
        w = re.sub(r"[^\w\s]", " ", t.lower()).split()
        return {" ".join(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}

    saida, ctx = ng(SAIDA_REAL), ng(" ".join(c.text for c in CTX))
    sobreposicao = len(saida & ctx) / len(saida)
    assert sobreposicao < 0.10, sobreposicao
    # ... enquanto a métrica de verso vê 38%
    assert analisar(SAIDA_REAL, CTX).fracao_copiada > 0.3


def test_identifica_a_origem_de_cada_verso():
    a = analisar(SAIDA_REAL, CTX)
    origens = {c.poema for c in a.copiados}
    assert origens == {"poem_1019", "poem_1027"}


# --- o caso limpo ----------------------------------------------------------

def test_poema_original_nao_plagia():
    a = analisar(ORIGINAL, CTX)
    assert not a.plagiou
    assert a.copiados == ()


def test_copia_literal_e_detectada_a_100():
    a = analisar(CTX[0].text, CTX)
    assert a.fracao_copiada == 1.0
    assert a.max_similaridade == pytest.approx(1.0, abs=0.001)


# --- casos de borda -------------------------------------------------------

def test_sem_contexto_nao_ha_plagio():
    a = analisar(ORIGINAL, [])
    assert a.fracao_copiada == 0.0
    assert a.n_versos > 0


def test_saida_vazia():
    a = analisar("   \n ", CTX)
    assert a.n_versos == 0
    assert not a.plagiou


def test_versos_muito_curtos_sao_ignorados():
    """«É tudo.» coincidiria por acidente; não é plágio."""
    a = analisar("É tudo.\nE mais.\nNada.", CTX)
    assert a.n_versos == 0


def test_resumo_legivel():
    assert "sem versos copiados" in analisar(ORIGINAL, CTX).resumo()
    assert "3/8" in analisar(SAIDA_REAL, CTX).resumo()


# --- limiares --------------------------------------------------------------

def test_limiares_estao_no_intervalo_calibrado():
    assert 0.6 <= LIMIAR_VERSO <= 0.85, "fora do intervalo inspeccionado"
    assert 0.0 < LIMIAR_FRACAO <= 0.5


def test_limiar_de_verso_separa_parafrase_de_poema_distinto():
    """«Só se for por não ser madrugada» (0,76) é paráfrase;
    «Mas se é poente, de que será feito?» (0,52) é reescrita a sério."""
    a = analisar(SAIDA_REAL, CTX)
    copiados = {c.verso for c in a.copiados}
    assert "Só se for por não ser madrugada." in copiados
    assert "Mas se é poente, de que será feito?" not in copiados
