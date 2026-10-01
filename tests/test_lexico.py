"""Guarda lexical — palavras inventadas pelo modelo.

Os casos vêm de uma medição em 28 respostas reais (2026-10-01): 10 delas (36%)
continham pelo menos um defeito lexical, distribuído pelas quatro vozes.
"""
import pytest

from src.corpus.models import Lang
from src.lexico import (aspell_disponivel, suspeitas, vocabulario_do_corpus)

sem_aspell = pytest.mark.skipif(
    not aspell_disponivel(),
    reason="aspell com dicionário pt_PT não instalado",
)


@pytest.fixture(scope="module")
def vocab():
    v = vocabulario_do_corpus()
    assert len(v) > 10_000, f"vocabulário suspeito: {len(v)} tipos"
    return v


# --- os defeitos que o dicionário apanha ----------------------------------

#: Os 10 de 13 defeitos medidos que o aspell desconhece.
#:
#: Na primeira versão deste teste listei 7 e dei `invisiveis`, `numo` e
#: `dispers` como escapando — por os ter testado em conjunto com outros numa
#: linha e extrapolado, em vez de os verificar um a um. São apanhados.
APANHAVEIS = [
    ("poniente", "a leste ou a poniente.", "castelhanismo de «poente»"),
    ("río", "O río murmura enquanto corre,", "castelhanismo de «rio»"),
    ("tus", "Tus formas, minhas dúvidas.", "castelhanismo de «tuas»"),
    ("veo", "Veo flashes do teu eu.", "castelhanismo de «vejo»"),
    ("brevítil", "Dilui-se nas nuvens, brevítil, leve.", "inventada"),
    ("naufragios", "naufragios invisiveis", "falta acento: «naufrágios»"),
    ("invisiveis", "naufragios invisiveis", "falta acento: «invisíveis»"),
    ("numo", "Numo arco eterno, sem ponto de volta.", "inventada/truncada"),
    ("dispers", "É o pensamento que se dispers", "truncada"),
    ("cutuca", "cutuca, tira e volta", "brasileirismo"),
]


@sem_aspell
@pytest.mark.parametrize("palavra,verso,porque", APANHAVEIS,
                         ids=[p for p, _, _ in APANHAVEIS])
def test_apanha_defeitos_medidos(palavra, verso, porque, vocab):
    s = suspeitas(f"Um verso qualquer antes,\n{verso}\ne outro depois.", vocab)
    assert palavra in {x.palavra for x in s}, f"{porque}: não apanhado"


@sem_aspell
def test_identifica_o_verso_de_origem(vocab):
    s = suspeitas("a leste ou a poniente.", vocab)
    assert s[0].verso == "a leste ou a poniente."


# --- os defeitos que escapam, e é esperado --------------------------------

#: O dicionário aceita-os: são formas válidas noutros contextos ou erros de
#: acentuação que tolera. Continuam a depender de `voices.INTERDICOES`.
ESCAPAM = ["caiem", "risada", "perpetua"]


@sem_aspell
@pytest.mark.parametrize("palavra", ESCAPAM)
def test_limites_conhecidos_da_guarda(palavra, vocab):
    """Documenta o que esta guarda NÃO apanha, para não se confiar demais."""
    s = suspeitas(f"verso com {palavra} no meio dele", vocab)
    assert palavra not in {x.palavra for x in s}, (
        f"«{palavra}» passou a ser apanhado — actualizar a cobertura no "
        f"docstring de src/lexico.py")


# --- regressão: o vocabulário de Pessoa não pode ser sinalizado -----------

#: O aspell rejeita 593 tipos do corpus (7,1%). Nenhum pode ser sinalizado,
#: porque o corpus é a autoridade sobre o que Pessoa escrevia. Amostra das
#: mais frequentes.
LEGITIMAS = [
    "inda", "cousas", "abstracta", "abstracto", "nocturno", "objectos",
    "eléctrico", "acção", "actual", "dize", "vêem", "dêem", "reflecte",
    "Lídia", "Portugal", "Lisboa", "Tejo", "Apolo", "hup", "heia",
]


@sem_aspell
@pytest.mark.parametrize("palavra", LEGITIMAS)
def test_vocabulario_de_pessoa_nao_e_sinalizado(palavra, vocab):
    """Estas estão no corpus e o dicionário moderno rejeita-as. A guarda tem de
    as deixar passar, senão sinalizaria 593 palavras legítimas."""
    s = suspeitas(f"um verso com {palavra} dentro dele", vocab)
    assert palavra.lower() not in {x.palavra for x in s}


@sem_aspell
def test_poema_bom_nao_tem_suspeitas(vocab):
    bom = ("A árvore estende-se no terreiro,\n"
           "desnuda de folhas, mas ainda verde,\n"
           "o sol bate-lhe nas ramas, aquecendo-a,\n"
           "sem que nada mais aconteça.")
    assert suspeitas(bom, vocab) == ()


# --- degradação e casos de borda ------------------------------------------

def test_palavras_curtas_sao_ignoradas(vocab):
    assert suspeitas("ah oh eh ui", vocab) == ()


def test_texto_vazio(vocab):
    assert suspeitas("", vocab) == ()
    assert suspeitas("   \n  ", vocab) == ()


def test_sem_aspell_fica_inerte(vocab, monkeypatch):
    """Sem dicionário, a guarda não sinaliza nada — em vez de sinalizar tudo o
    que não está no corpus, que teria 87% de falsos positivos."""
    import src.lexico as lex
    monkeypatch.setattr(lex, "desconhecidas_do_dicionario",
                        lambda p, idioma=None: set())
    assert lex.suspeitas("a leste ou a poniente zzqq", vocab) == ()


def test_filtro_de_idioma_tira_a_maior_parte_do_ingles(vocab):
    """O filtro por poema não é perfeito: 4 palavras inglesas sobrevivem.

    Vêm do poem_135 (*Ode Marítima*), que tem versos em inglês a meio e está
    classificado como PT porque a maioria o é. Significa que estas quatro não
    seriam sinalizadas se o modelo as emitisse. Teste documenta o limite em vez
    de o esconder.
    """
    sobrevivem = {p for p in ("and", "the", "that", "this") if p in vocab}
    assert sobrevivem <= {"and", "the", "that", "this"}
    # mas o grosso do inglês ficou fora
    for p in ("thou", "doth", "whence", "hath", "thy"):
        assert p not in vocab, f"«{p}» no vocabulário: o filtro de idioma falhou"


@sem_aspell
def test_falso_positivo_conhecido_reflectem(vocab):
    """`reflecte` está no corpus, `reflectem` não — e é PT-PT pré-acordo
    correcto. O dicionário moderno rejeita-o, logo é sinalizado indevidamente.

    Limitação estrutural: o corpus não cobre todas as flexões das palavras que
    contém. Documentada, não resolvida.
    """
    s = suspeitas("as águas reflectem o céu", vocab)
    assert "reflectem" in {x.palavra for x in s}, (
        "o falso positivo desapareceu — se foi por o corpus ou o dicionário "
        "mudarem, actualizar a limitação em src/lexico.py")


# --- suporte a inglês ------------------------------------------------------

sem_aspell_en = pytest.mark.skipif(
    not aspell_disponivel(Lang.EN),
    reason="aspell com dicionário en não instalado",
)


@pytest.fixture(scope="module")
def vocab_en():
    v = vocabulario_do_corpus(Lang.EN)
    assert len(v) > 2000, f"vocabulário inglês suspeito: {len(v)} tipos"
    return v


def test_vocabularios_sao_separados_por_lingua(vocab, vocab_en):
    """Os 152 poemas em inglês são obra de Pessoa, não ruído: os *35 Sonnets*,
    as *Inscriptions*, e Alexander Search com 50 poemas."""
    assert "thou" in vocab_en and "thou" not in vocab
    assert "saudade" in vocab


@sem_aspell_en
def test_ingles_arcaico_de_pessoa_nao_e_sinalizado(vocab_en):
    """O dicionário moderno desconhece «giveth» e «storiless», que Pessoa usa.
    O corpus salva-os — o mesmo padrão do português pré-acordo."""
    for p in ("giveth", "storiless", "aught", "dost", "hath"):
        s = suspeitas(f"a line with {p} inside it", vocab_en, idioma=Lang.EN)
        assert p not in {x.palavra for x in s}, f"«{p}» sinalizado indevidamente"


@sem_aspell_en
def test_palavra_inventada_em_ingles_e_apanhada(vocab_en):
    s = suspeitas("My soul is a zorbish thing,\nand giveth naught but doubt.",
                  vocab_en, idioma=Lang.EN)
    assert "zorbish" in {x.palavra for x in s}


@sem_aspell_en
def test_dicionario_errado_sinalizaria_o_corpus_todo(vocab_en):
    """Usar o dicionário português sobre inglês marcaria tudo. Prova que a
    escolha de dicionário por língua é load-bearing."""
    from src.lexico import desconhecidas_do_dicionario
    palavras = {"soul", "doubt", "mystery", "horror"}
    assert desconhecidas_do_dicionario(palavras, Lang.EN) == set()
    assert len(desconhecidas_do_dicionario(palavras, Lang.PT)) >= 3
