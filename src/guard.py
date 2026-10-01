"""Guardas de saída.

Cada uma destas combate um modo de falha **observado** na avaliação às cegas da
Fase 0 (adenda A.4 do relatório), não um risco imaginado.

A guarda de plágio (§6.3 do plano) fica para o Passo 7: o seu limiar tem de ser
calibrado sobre 30 respostas reais, que ainda não existem.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .corpus.models import Lang
from .voices import INTERDICOES, PERSONAS

# --- detecção de quebra de persona ---------------------------------------
#
# Observado: «(este poema não é do Reis, mas da minha voz...)», «Reis, na minha
# voz», «Álvaro suspira em espírito de fuga».
#
# A primeira versão desta lista procurava «Pessoa», «Reis» e «Campos» sem
# distinguir maiúsculas, e isso é um gerador de falsos positivos: em português
# `pessoa` é palavra comum, `reis` são reis e `campos` são campos — e Caeiro
# escreve sobre os campos constantemente («Olho os campos, Neera» é Reis a
# sério). A lista foi dividida em dois níveis.

#: Nomes que nunca aparecem inocentemente num poema português.
_NOMES_INEQUIVOCOS = (
    "Álvaro de Campos", "Alberto Caeiro", "Ricardo Reis", "Fernando Pessoa",
    "Bernardo Soares", "Álvaro", "Caeiro", "Soares",
)

#: Nomes que coincidem com palavras comuns. Só contam com linguagem meta à volta.
_NOMES_AMBIGUOS = ("Reis", "Campos", "Pessoa")

#: Linguagem que fala do poema em vez de o ser.
_RE_META = re.compile(
    r"\b(est[ea]s? (poema|poesia|versos|texto)|"
    r"(na |da |a )?minha voz|heter[oó]nimos?|"
    r"o poema (não |nao )?[ée])\b", re.I)

#: Preâmbulos meta. Observado: «Aqui está um breve poema em português europeu...»
#: As formas inglesas vêm do padrão típico destes modelos («Here is a poem...»,
#: «Sure, here's...») e não de observação neste corpus — por medir.
_RE_PREAMBULO = re.compile(
    r"^\s*("
    r"aqui (está|vai|tens)|eis|segue(-se)?|este (é|e) (um|o)"          # pt
    r"|here (is|are)|here's|sure[,!]|certainly[,!]|of course[,!]"       # en
    r"|below (is|are)|the following"
    r")\b.*$",
    re.I,
)

#: Stopwords por língua, para detectar resposta na língua errada. Observado:
#: uma amostra inteiramente em latim, porque «dicção latinizante» foi tomada à
#: letra.
_STOPWORDS: dict[Lang, frozenset[str]] = {
    Lang.PT: frozenset("de a o e que do da em não os as uma um com por para se "
                       "na no mais como mas eu ao dos das à é são tem ser me te "
                       "lhe".split()),
    # Inclui as formas arcaicas que Pessoa de facto usa no seu inglês: «thy»,
    # «thou», «doth», «hath». Sem elas, um poema à maneira dos *35 Sonnets*
    # pontuaria baixo na língua em que foi escrito.
    Lang.EN: frozenset("the and of to in is it that i my a an with for not but "
                       "was are be have his her this all as on at by from or "
                       "thy thou thee doth hath which who what no nor so if "
                       "than then there here been were am".split()),
}


@dataclass(frozen=True)
class Veredicto:
    ok: bool
    motivos: tuple[str, ...]
    texto: str          # texto já limpo do que é removível
    #: Palavras que nem o corpus nem o dicionário conhecem. **Não falham o
    #: veredicto**: uma palavra inventada não estraga um poema, e rejeitar
    #: custa ~28 s. Ver src/lexico.py.
    suspeitas: tuple = ()

    def __bool__(self) -> bool:
        return self.ok


def _sem_acentos(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def remover_preambulo(texto: str) -> str:
    """Descarta linhas de enquadramento antes do primeiro verso.

    Removível, logo removido em vez de rejeitado — rejeitar custaria uma
    regeneração de ~30 s por uma linha a mais.
    """
    linhas = texto.strip().split("\n")
    i = 0
    while i < len(linhas):
        l = linhas[i].strip()
        if not l:
            i += 1
            continue
        if _RE_PREAMBULO.match(l) or (l.endswith(":") and len(l.split()) > 3):
            i += 1
            continue
        break
    return "\n".join(linhas[i:]).strip()


def remover_eco_da_pergunta(texto: str, pergunta: str,
                            limiar: float = 0.72) -> str:
    """Descarta a primeira linha quando é a pergunta repetida.

    Observado no CLI: à pergunta «o que vês quando olhas para uma árvore?» o
    modelo respondeu com essa linha como primeiro verso. Não é plágio do
    contexto, logo a guarda de plágio não a vê; e é removível, logo remove-se
    em vez de se rejeitar.
    """
    import difflib
    linhas = texto.strip().split("\n")
    if not linhas:
        return texto

    def normalizar(t: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", t.lower())).strip()

    alvo = normalizar(pergunta)
    primeira = normalizar(linhas[0])
    if primeira and difflib.SequenceMatcher(None, primeira, alvo).ratio() >= limiar:
        return "\n".join(linhas[1:]).strip()
    return texto


def remover_cercas(texto: str) -> str:
    """Remove cercas de código e aspas que envolvem o poema todo."""
    t = texto.strip()
    t = re.sub(r"^```[a-z]*\n?|\n?```$", "", t).strip()
    if len(t) > 2 and t[0] in "\"«'" and t[-1] in "\"»'":
        t = t[1:-1].strip()
    return t


def fracao_lingua(texto: str, idioma: Lang = Lang.PT) -> float:
    """Fracção de palavras que são stopwords da língua esperada."""
    palavras = re.findall(r"[a-zà-úA-ZÀ-Ú]+", texto.lower())
    if not palavras:
        return 0.0
    alvo = _STOPWORDS.get(idioma, _STOPWORDS[Lang.PT])
    return sum(1 for p in palavras if p in alvo) / len(palavras)


def fracao_pt(texto: str) -> float:
    """Compatibilidade: a fracção em português."""
    return fracao_lingua(texto, Lang.PT)


#: Fracção mínima de palavras que o dicionário da língua tem de reconhecer.
#: Medida nos poemas reais: p1 de 0,857 em português e 0,900 em inglês, contra
#: **0,043** da amostra em latim. 0,50 fica no meio dessa lacuna, longe de ambos
#: — folga deliberada, porque o dicionário é pós-acordo de 1990 e rejeita 7,1%
#: do vocabulário real de Pessoa (ver `src/lexico.py`).
MIN_FRACAO_DICIONARIO = 0.50


def _fracao_reconhecida(texto: str, idioma: Lang) -> float | None:
    """Fracção das palavras que o dicionário da língua reconhece.

    `None` quando não há dicionário — e aí quem chama tem de decidir, porque
    «não sei» não é «está bem».
    """
    from .lexico import (MIN_LETRAS, _RE_PALAVRA, aspell_disponivel,
                         desconhecidas_do_dicionario)
    if not aspell_disponivel(idioma):
        return None
    palavras = {p.lower() for p in _RE_PALAVRA.findall(texto)
                if len(p) >= MIN_LETRAS}
    if not palavras:
        return 1.0
    return 1.0 - len(desconhecidas_do_dicionario(palavras, idioma)) / len(palavras)


def lingua_errada(texto: str, esperada: Lang, piso: float = 0.12) -> bool:
    """A resposta está numa língua que não a pedida?

    ## O falso positivo que isto corrige

    Observado no CLI, a «qual é o futuro de portugal?»:

        os passos ecoam / silêncio envolve / vogais cantam
        pés descalços ligam terra ar / brotam esperanças

    Fracção pt de 0,077, rejeitado, 38 s de regeneração perdidos. É português
    inequívoco — `silêncio`, `raízes`, `descalços` — mas telegráfico, sem artigos
    nem preposições, logo sem as palavras funcionais que a fracção conta. **O
    limiar media registo e chamava-lhe língua.**

    Baixar o limiar não era a correcção, e a medição di-lo: contra o corpus, 0,12
    rejeita 3 de 1906 poemas portugueses (0,16%) e um deles é francês
    (`poem_561`). Os poemas reais têm mediana 0,385 e p5 0,267. O limiar está bem
    posto; o instrumento é que é o errado.

    ## As três perguntas, em ordem de custo

    1. **Há stopwords em abundância?** Acima do piso não há dúvida nenhuma, e é
       o caso de 99,8% dos textos. Sai aqui, sem subprocessos.
    2. **Outra língua pontua mais que a pedida?** Discriminação medida:
       poemas pt dão 0,385 na própria língua e 0,048 na alheia; os ingleses
       0,375 e 0,035. Em 2058 poemas, **zero** pontuam mais na língua errada.
    3. **O dicionário da língua reconhece o vocabulário?** É a única das três
       que não depende do registo, e é ela que distingue o caso telegráfico do
       latim. O teste relativo sozinho não o faria: o latim de
       `tests/test_guard.py` contém `se`, stopword portuguesa, logo pontua 0,040
       em pt contra 0,000 em inglês e passaria. Medido: dicionário pt reconhece
       **1,000** do telegráfico e **0,043** do latim.

    ## Quando não há dicionário

    Volta ao limiar absoluto, que é o comportamento antigo: rejeita. «Não sei»
    não pode virar «está bem» — sem esta ressalva, uma máquina sem `aspell`
    perderia a guarda contra o latim, que é o modo de falha que ela existe para
    apanhar. O preço é o falso positivo telegráfico voltar nessas máquinas.

    ## Línguas sem autoridade

    `Lang.INDETERMINADO` existe para poemas curtos demais para classificar, e
    `_STOPWORDS` não o cobre. Antes disto, `fracao_lingua` caía silenciosamente
    no português e a guarda dava quatro poemas reais por língua errada
    (`poem_3516`, `poem_3525`, `poem_4281`, `poem_4372` — entre eles «Iniguais
    pertencemos.»). Sem autoridade sobre a língua, a guarda é inerte.

    Medido: 0 falsos positivos em 2058 poemas reais, e apanha os três modos de
    falha (latim, inglês quando se pediu português, e o inverso).
    """
    if esperada not in _STOPWORDS:
        return False

    f_esperada = fracao_lingua(texto, esperada)
    if f_esperada >= piso:
        return False

    outras = [fracao_lingua(texto, l) for l in _STOPWORDS if l is not esperada]
    if f_esperada <= max(outras, default=0.0):
        return True

    reconhecida = _fracao_reconhecida(texto, esperada)
    if reconhecida is None:
        return True            # sem dicionário, vale o limiar absoluto
    return reconhecida < MIN_FRACAO_DICIONARIO


def brasileirismos(texto: str) -> tuple[str, ...]:
    baixo = texto.lower()
    return tuple(k for k in INTERDICOES if re.search(rf"\b{re.escape(k)}\b", baixo))


def corrigir_brasileirismos(texto: str) -> str:
    """Substitui as formas medidas na Fase 0, preservando a capitalização."""
    def troca(m: re.Match) -> str:
        orig = m.group(0)
        novo = INTERDICOES[orig.lower()]
        return novo.capitalize() if orig[0].isupper() else novo

    for k in sorted(INTERDICOES, key=len, reverse=True):
        texto = re.sub(rf"\b{re.escape(k)}\b", troca, texto, flags=re.I)
    return texto


def e_verso(texto: str) -> bool:
    """Verso tem quebras deliberadas: várias linhas, a maioria curta."""
    linhas = [l for l in texto.split("\n") if l.strip()]
    if len(linhas) < 3:
        return False
    curtas = sum(1 for l in linhas if len(l.split()) <= 14)
    return curtas / len(linhas) >= 0.7


def _nomes_indevidos(texto: str) -> tuple[str, ...]:
    """Nomes de heterónimo usados como referência, não como poema.

    Dois níveis: nomes inequívocos contam sempre; nomes que coincidem com
    palavras comuns («reis», «campos», «pessoa») só contam quando há linguagem
    meta à volta.
    """
    sem = _sem_acentos(texto)
    tem_meta = bool(_RE_META.search(texto))
    achados: list[str] = []
    for n in _NOMES_INEQUIVOCOS:
        if re.search(rf"\b{re.escape(_sem_acentos(n))}\b", sem, re.I):
            achados.append(n)
    if tem_meta:
        achados.append("linguagem meta")
        for n in _NOMES_AMBIGUOS:
            if re.search(rf"\b{re.escape(_sem_acentos(n))}\b", sem):
                achados.append(n)
    # «Álvaro de Campos» já implica «Álvaro»: manter só o mais específico
    completos = [a for a in achados if " " in a]
    for c in completos:
        achados = [a for a in achados if a == c or a not in c]
    return tuple(dict.fromkeys(achados))


def verificar(texto: str, *, pergunta: str | None = None,
              idioma: Lang = Lang.PT,
              min_fracao_pt: float = 0.12,
              corrigir: bool = True,
              lexico: bool = True) -> Veredicto:
    """Limpa o que é removível e julga o que resta.

    `min_fracao_pt` a 0,12 é o **piso** do teste de língua, não o seu critério:
    medido no corpus, poemas portugueses ficam bem acima disso (mediana 0,385,
    p5 0,267). Quem decide é `lingua_errada`, que exige também que nenhuma outra
    língua pontue mais — ver a sua docstring para o falso positivo que isso
    corrige.
    """
    t = remover_preambulo(remover_cercas(texto))
    if pergunta:
        t = remover_eco_da_pergunta(t, pergunta)
    motivos: list[str] = []

    if not t.strip():
        return Veredicto(False, ("vazio",), "", ())

    if lingua_errada(t, idioma, min_fracao_pt):
        fr = fracao_lingua(t, idioma)
        motivos.append(f"idioma improvável (fracção {idioma.value} {fr:.3f})")

    if not e_verso(t):
        motivos.append("não parece verso")

    nomeados = _nomes_indevidos(t)
    if nomeados:
        motivos.append(f"quebra de persona: {', '.join(nomeados)}")

    # Brasileirismos e colocação pronominal só fazem sentido em português.
    br = brasileirismos(t) if idioma is Lang.PT else ()
    if br:
        if corrigir:
            t = corrigir_brasileirismos(t)
        else:
            motivos.append(f"brasileirismos: {', '.join(br)}")

    susp: tuple = ()
    if lexico:
        try:
            from .lexico import suspeitas as _suspeitas
            susp = _suspeitas(t, idioma=idioma)
        except Exception:
            susp = ()      # a guarda lexical é opcional; nunca quebra o fluxo

    return Veredicto(not motivos, tuple(motivos), t, susp)
