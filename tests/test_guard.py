"""Aceite das guardas de saída (Passo 5 da Fase 1).

Cada teste usa um caso **observado** na avaliação às cegas da Fase 0, não um
caso inventado.
"""
import pytest

from src.guard import (brasileirismos, corrigir_brasileirismos, e_verso,
                       fracao_pt, remover_cercas, remover_preambulo, verificar)

# Amostras reais, de docs/fase-0/05-teste-voz.md e 05b-teste-voz-cego.md
LATIM = """Vitam brevis, spem longum; nec metuamus,
Sic laus et praemia sunt vitæ nosse suum.
Tempora fugit, omnia mutantur;
Nos cernimus, velox est qui se cernit."""

PERSONA_QUEBRADA = """Ó vida fugaz, como és breve,
não te faças vítima do meu medo.
Em teu breve fôlego, eu não vejo
a morte que me aguarda, somente
um fim sem dor, um sono leve.

(Luís de Camões, que te inspira, este poema não é do Reis, mas da minha voz...)"""

PREAMBULO = """Aqui está um breve poema em português europeu, falando da tua saudade de algo que nunca aconteceu:

Tua alma em sonhos flutua,
Sobre arcos de esperança.
Quente lembrança que não brota,
Da florescida promessa."""

BOM = """A árvore estende-se no terreiro,
desnuda de folhas, mas ainda verde,
o sol bate-lhe nas ramas, aquecendo-a,
sem que nada mais aconteça.

E eu, que estou aqui, de pé,
sinto a presença da árvore,
sem pensar que é uma coisa viva."""


# --- limpeza (removível, logo removido) -----------------------------------

def test_remove_preambulo_meta():
    t = remover_preambulo(PREAMBULO)
    assert t.startswith("Tua alma em sonhos flutua")
    assert "Aqui está" not in t


def test_remove_cercas_e_aspas():
    assert remover_cercas("```\nverso\n```") == "verso"
    assert remover_cercas('"um verso"') == "um verso"
    assert remover_cercas("«um verso»") == "um verso"


# --- idioma ----------------------------------------------------------------

def test_fracao_pt_distingue_latim_de_portugues():
    assert fracao_pt(BOM) > 0.12
    assert fracao_pt(LATIM) < 0.12


def test_latim_e_rejeitado():
    v = verificar(LATIM)
    assert not v
    assert any("idioma" in m for m in v.motivos), v.motivos


# --- persona ---------------------------------------------------------------

def test_quebra_de_persona_e_rejeitada():
    v = verificar(PERSONA_QUEBRADA)
    assert not v
    assert any("persona" in m for m in v.motivos), v.motivos


def test_deteccao_de_nome_ignora_acentos():
    """«Álvaro suspira em espírito de fuga» foi observado numa amostra."""
    v = verificar("Alvaro suspira em espirito de fuga,\nnas ruas da cidade,\n"
                  "e o dia nasce sem nada.\nAssim é a manhã.")
    assert any("persona" in m for m in v.motivos), v.motivos


# --- brasileirismos --------------------------------------------------------

def test_deteccao_de_brasileirismos():
    assert "fumaça" in brasileirismos("Fios de fumaça de tabaco")
    assert "demônios" in brasileirismos("Dos demônios da noite em torno")
    assert "galhos" in brasileirismos("Seus galhos erguem-se no ar")
    assert not brasileirismos("o fumo do tabaco e os ramos da árvore")


def test_correccao_preserva_capitalizacao():
    assert corrigir_brasileirismos("Fumaça densa") == "Fumo densa"
    assert corrigir_brasileirismos("a fumaça") == "a fumo"
    assert corrigir_brasileirismos("Os galhos") == "Os ramos"


def test_brasileirismos_corrigidos_nao_reprovam():
    t = "Fios de fumaça no ar,\ne os galhos da árvore,\ne o dia a acabar.\nNada mais."
    v = verificar(t, corrigir=True)
    assert "fumaça" not in v.texto
    assert "fumo" in v.texto
    assert not any("brasileir" in m for m in v.motivos)


def test_brasileirismos_reprovam_se_nao_corrigir():
    t = "Fios de fumaça no ar,\ne os galhos da árvore,\ne o dia a acabar.\nNada mais."
    v = verificar(t, corrigir=False)
    assert any("brasileir" in m for m in v.motivos), v.motivos


# --- verso -----------------------------------------------------------------

def test_prosa_nao_passa():
    prosa = ("A saudade é um sentimento complexo que envolve a memória de algo "
             "que já não existe, e que por isso mesmo se torna mais presente do "
             "que aquilo que de facto nos rodeia no dia a dia.")
    assert not e_verso(prosa)
    assert any("verso" in m for m in verificar(prosa).motivos)


def test_verso_passa():
    assert e_verso(BOM)


def test_amostra_boa_passa_inteira():
    v = verificar(BOM)
    assert v, v.motivos
    assert v.texto.startswith("A árvore estende-se")


def test_vazio():
    v = verificar("   \n  ")
    assert not v
    assert v.motivos == ("vazio",)


# --- falsos positivos que a primeira versão da guarda produzia -------------

FALSOS_POSITIVOS = [
    ("os campos", "Olho os campos e vejo as ervas,\ne os campos são campos,\n"
                  "nada mais que isso.\nE o sol é pontual."),
    ("os reis", "Os reis passaram e nada ficou,\ne as coroas ficaram no pó,\n"
                "e o pó não se lembra de nada.\nAssim é tudo."),
    ("uma pessoa", "Sou uma pessoa entre pessoas,\ne nenhuma delas me conhece,\n"
                   "nem eu a nenhuma.\nÉ assim a cidade."),
    ("Neera", "Olho os campos, Neera,\ne vejo quanto o tempo passa.\n"
              "Colhe as rosas, que são breves.\nNada mais nos resta."),
]


@pytest.mark.parametrize("etiqueta,texto", FALSOS_POSITIVOS,
                         ids=[e for e, _ in FALSOS_POSITIVOS])
def test_palavras_comuns_nao_quebram_persona(etiqueta, texto):
    """«pessoa», «reis» e «campos» são palavras comuns em português, e «Olho os
    campos, Neera» é um verso real de Ricardo Reis."""
    v = verificar(texto)
    assert not any("persona" in m for m in v.motivos), (etiqueta, v.motivos)


def test_nome_ambiguo_com_linguagem_meta_e_apanhado():
    """«Reis» sozinho não; «Reis» com «minha voz» sim."""
    sem_meta = "Reis houve que nada souberam,\ne coroas que nada valeram,\n" \
               "e o pó que a todos cobriu.\nAssim é o fado."
    assert not any("persona" in m for m in verificar(sem_meta).motivos)

    com_meta = "Reis, na minha voz,\nsou alegre e sombrio,\n" \
               "mas sou aquele homem.\nEspero a noite."
    v = verificar(com_meta)
    assert any("persona" in m for m in v.motivos), v.motivos


# --- eco da pergunta (observado no CLI, Passo 9) --------------------------

def test_remove_eco_da_pergunta():
    """Observado: à pergunta «o que vês quando olhas para uma árvore?» o modelo
    respondeu com essa linha como primeiro verso. Não é plágio do contexto,
    logo a guarda de plágio não a vê."""
    from src.guard import remover_eco_da_pergunta
    saida = ("O que vês quando olhas para uma árvore?\n\n"
             "Verde se estende, não mais.\n"
             "Raízes enterradas, não menos.")
    t = remover_eco_da_pergunta(saida, "o que vês quando olhas para uma árvore?")
    assert t.startswith("Verde se estende")


def test_eco_removido_por_verificar():
    saida = ("A vida é breve?\n"
             "Breve é a sombra na tarde,\n"
             "e a noite não tarda,\n"
             "e nada mais nos resta.")
    v = verificar(saida, pergunta="a vida é breve?")
    assert not v.texto.startswith("A vida é breve?")
    assert v.texto.startswith("Breve é a sombra")


def test_primeiro_verso_parecido_mas_distinto_fica():
    """«Nunca sei como é que se pode achar um poente triste» não é eco de
    «por que é que as pessoas acham melancólico o fim do dia?»"""
    from src.guard import remover_eco_da_pergunta
    saida = "Nunca sei como se pode achar um poente triste.\nSó se for por não ser madrugada."
    t = remover_eco_da_pergunta(saida, "por que é que as pessoas acham melancólico o fim do dia?")
    assert t == saida


def test_sem_pergunta_nao_altera():
    saida = "Verde se estende, não mais.\nRaízes enterradas."
    assert verificar(saida).texto == saida
