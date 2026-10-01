"""`.txt` -> `Poem`.

Cobertura medida: 2083/2083 ficheiros têm linha de autor e linha `Titulo:`.
Não há excepções, logo o parsing não precisa de ramo de recurso — mas falha
alto se um ficheiro novo não encaixar, em vez de produzir um `Poem` silenciosamente errado.
"""
from __future__ import annotations

import os
import re
import unicodedata

from .models import Lang, Poem, Voice

_RE_TITULO = re.compile(r"^Titulo:\s*(.*)$", re.M)

#: Nome canónico -> voz. A chave é a forma normalizada (ver `_chave`).
_AUTORES: dict[str, tuple[str, Voice]] = {
    "fernando pessoa": ("Fernando Pessoa", Voice.ORTONIMO),
    "alvaro de campos": ("Álvaro de Campos", Voice.CAMPOS),
    # poem_224.txt: o «Á» foi substituído por bytes espúrios ('ร\x81'), não
    # prefixado por eles, logo a letra desapareceu do ficheiro e a forma
    # normalizada perde o A inicial. Mapeada explicitamente para documentar
    # o defeito nos dados em vez de o esconder numa heurística.
    "lvaro de campos": ("Álvaro de Campos", Voice.CAMPOS),
    "ricardo reis": ("Ricardo Reis", Voice.REIS),
    "alberto caeiro": ("Alberto Caeiro", Voice.CAEIRO),
    "alexander search": ("Alexander Search", Voice.SEARCH),
    "bernardo soares": ("Bernardo Soares", Voice.SOARES),
    # Pré-heterónimos, semi-heterónimos e atribuições avulsas.
    "charles robert anon": ("Charles Robert Anon", Voice.OUTRO),
    "joaquim moura costa": ("Joaquim Moura Costa", Voice.OUTRO),
    "dr. pancracio": ("Dr. Pancrácio", Voice.OUTRO),
    "carlos otto": ("Carlos Otto", Voice.OUTRO),
    "vicente guedes": ("Vicente Guedes", Voice.OUTRO),
    "antonio mora": ("António Mora", Voice.OUTRO),
    "ibis": ("Íbis", Voice.OUTRO),
    "eduardo lanca": ("Eduardo Lança", Voice.OUTRO),
    "david merrick": ("David Merrick", Voice.OUTRO),
    "j. h. hyslop": ("J. H. Hyslop", Voice.OUTRO),
    "wardour + pessoa": ("Wardour + Pessoa", Voice.OUTRO),
    "vadooisf": ("Vadooisf", Voice.OUTRO),
}

_PT = frozenset("de a o e que do da em não os as uma um com por para se na no "
                "mais como mas eu ao dos das à é são tem ser".split())
_EN = frozenset("the and of to in is it that i my thou thy with for not but "
                "was are be have his her this all".split())


def _chave(autor: str) -> str:
    """Forma normalizada para casar autores, tolerante a acentos e mojibake.

    `poem_224.txt` tem bytes espúrios antes de «lvaro de Campos»; remover os
    caracteres não-latinos iniciais resolve-o sem caso especial.
    """
    s = unicodedata.normalize("NFKD", autor)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = "".join(c for c in s if c.isascii() or c.isalpha())
    s = re.sub(r"^[^A-Za-z]+", "", s)       # lixo de codificação à cabeça
    return re.sub(r"\s+", " ", s).strip().lower()


def detectar_idioma(texto: str) -> Lang:
    palavras = re.findall(r"[a-zà-úA-ZÀ-Ú]+", texto.lower())
    if not palavras:
        return Lang.INDETERMINADO
    pt = sum(1 for p in palavras if p in _PT) / len(palavras)
    en = sum(1 for p in palavras if p in _EN) / len(palavras)
    if pt > en:
        return Lang.PT
    if en > pt:
        return Lang.EN
    return Lang.INDETERMINADO


def _limpar_corpo(corpo: str, titulo: str) -> str:
    """Remove o título repetido no início do corpo (82% dos ficheiros).

    O cabeçalho é «Titulo: Quarto: AS ILHAS AFORTUNADAS» e o corpo abre com
    «Quarto\\n\\nAS ILHAS AFORTUNADAS» — as mesmas palavras outra vez. Removê-las
    evita que o título domine o vector de um poema curto.
    """
    linhas = corpo.split("\n")
    partes = [p.strip().lower() for p in titulo.split(":") if p.strip()]
    i = 0
    while i < len(linhas) and partes:
        atual = linhas[i].strip().lower()
        if not atual:
            i += 1
            continue
        if atual == partes[0]:
            partes.pop(0)
            i += 1
            continue
        break
    limpo = "\n".join(linhas[i:]).strip()
    # Poemas de um só verso em que o título É o poema (poem_2873 «Vou atirar
    # uma bomba ao destino.», poem_2886, poem_4347). Aqui o título não é
    # redundante: é o conteúdo todo. Remover deixaria o poema vazio.
    return limpo if limpo else corpo.strip()


def parse_poem(caminho: str) -> Poem:
    bruto = open(caminho, encoding="utf-8").read()
    linhas = bruto.split("\n")
    if not linhas or not linhas[0].strip():
        raise ValueError(f"{caminho}: sem linha de autor")

    autor_bruto = linhas[0].strip()
    chave = _chave(autor_bruto)
    if chave not in _AUTORES:
        raise ValueError(f"{caminho}: autor desconhecido {autor_bruto!r} "
                         f"(normalizado: {chave!r})")
    autor, voz = _AUTORES[chave]

    m = _RE_TITULO.search(bruto)
    if m is None:
        raise ValueError(f"{caminho}: sem linha 'Titulo:'")
    titulo = m.group(1).strip()

    corpo = _limpar_corpo(bruto[m.end():].strip(), titulo)
    estrofes = tuple(e.strip() for e in re.split(r"\n\s*\n", corpo) if e.strip())

    return Poem(
        id=os.path.basename(caminho).removesuffix(".txt"),
        author=autor,
        voice=voz,
        title=titulo,
        body=corpo,
        language=detectar_idioma(corpo or titulo),
        stanzas=estrofes,
        n_words=len(corpo.split()),
    )


def parse_corpus(data_dir: str = "data/pessoa_poems") -> list[Poem]:
    nomes = sorted(f for f in os.listdir(data_dir) if f.endswith(".txt"))
    return [parse_poem(os.path.join(data_dir, n)) for n in nomes]
