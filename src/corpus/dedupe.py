"""Detecção de duplicados e de relações entre poemas.

O desenho desta fase mudou por medição (ver FASE-1.md §0 e as notas abaixo).
Três conclusões empíricas moldaram o que aqui está:

1. **Duplicados exactos existem**: 3 pares, não 1 como a contagem inicial
   sobre os ficheiros em bruto sugeria. Normalizar o corpo limpo revela-os.

2. **Variantes existem e são comuns**: ~12 pares com forte sobreposição,
   incluindo esboços («ODE MARCIAL»), revisões («D. FERNANDO» / «GLÁDIO»),
   transcrições divergentes («umbrela» / «umbela») e **contenção** — poemas
   que são fragmentos de outros (`poem_12` tem 26 versos, todos presentes nos
   47 de `poem_619`).

   O Jaccard de n-gramas de palavra **não serve**: pequenas diferenças
   palavra-a-palavra destroem a sobreposição sem mudar o poema. A métrica usada
   é ao nível do verso, normalizada pelo poema mais curto, que é onde as
   variantes de facto se parecem.

3. **Duplicados por tradução NÃO são detectáveis** por similaridade. O caso
   conhecido (`poem_135` *ODE MARÍTIMA* / `poem_1794` *NAVAL ODE*) tem
   similaridade de verso 0,000 e é uma versão **parcial** (1094 palavras contra
   7325), logo nem a razão de comprimento o apanha.

   **E possivelmente não são duplicados.** Pessoa foi educado em inglês em
   Durban e escreveu obra em inglês — os *35 Sonnets*, o *Antinous*, as
   *Inscriptions* —, e Alexander Search é um heterónimo que escrevia em inglês.
   A `NAVAL ODE` está catalogada sob Álvaro de Campos; quem a verteu não está
   estabelecido aqui, e tratá-la como duplicado descartável foi uma decisão sem
   evidência sobre a sua autoria.

   Por isso **não são marcados**, e o filtro de idioma da busca não existe para
   os «resolver»: existe porque uma resposta em português deve ser fundamentada
   em poemas em português. É preferência de consulta, não juízo sobre o corpus.

Há ainda um fenómeno distinto de duplicação, que não deve ser colapsado:
**incipits partilhados** — 18 grupos, 40 poemas. Reis escreveu várias odes
diferentes com o mesmo primeiro verso («Coroai-me de rosas» aparece em 3).
`poem_17` e `poem_23` são desse tipo: similaridade de verso 0,111. São poemas
distintos e ficam registados como grupo, não como duplicados.
"""
from __future__ import annotations

import difflib
import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass, replace

from .models import Poem

#: Acima disto, dois poemas são a mesma composição. Calibrado sobre os casos
#: inspeccionados à mão: variantes confirmadas caem em 0,875–1,000; o par com
#: incipit partilhado mas poemas distintos cai em 0,111. A folga é grande.
LIMIAR_VARIANTE = 0.70

#: Similaridade mínima entre dois versos para os considerar o mesmo verso.
LIMIAR_VERSO = 0.82

_RE_PONTUACAO = re.compile(r"[^\w\s]")
_RE_ESPACOS = re.compile(r"\s+")


def _normalizar(texto: str) -> str:
    return _RE_ESPACOS.sub(" ", _RE_PONTUACAO.sub(" ", texto.lower())).strip()


def _versos(texto: str) -> list[str]:
    """Versos normalizados, ignorando os de menos de 3 palavras."""
    saida = []
    for linha in texto.split("\n"):
        v = _normalizar(linha)
        if len(v.split()) >= 3:
            saida.append(v)
    return saida


def similaridade_versos(a: str, b: str) -> float:
    """Fracção de versos do poema mais curto com par próximo no outro.

    Normalizar pelo mais curto é deliberado: faz com que a contenção (um poema
    ser fragmento de outro) pontue alto, que é a relação certa a detectar num
    corpus de esboços.
    """
    va, vb = _versos(a), _versos(b)
    if not va or not vb:
        return 0.0
    curto, longo = (va, vb) if len(va) <= len(vb) else (vb, va)
    casados = sum(
        1 for v in curto
        if difflib.get_close_matches(v, longo, n=1, cutoff=LIMIAR_VERSO)
    )
    return casados / len(curto)


def _trigramas(texto: str) -> set[str]:
    palavras = _normalizar(texto).split()
    return {" ".join(palavras[i:i + 3]) for i in range(max(0, len(palavras) - 2))}


def _pares_candidatos(poemas: list[Poem], min_partilhados: int = 2) -> set[tuple[str, str]]:
    """Blocagem por índice invertido de trigramas.

    Comparar os 2083² / 2 pares com difflib seria inviável. Trigramas de
    palavra são baratos e só servem para gerar candidatos — a decisão é da
    métrica de verso.
    """
    invertido: dict[str, list[str]] = defaultdict(list)
    for p in poemas:
        for g in _trigramas(p.body):
            invertido[g].append(p.id)

    contagem: dict[tuple[str, str], int] = defaultdict(int)
    for ids in invertido.values():
        # Trigramas ubíquos não informam e inflacionam o custo.
        if not 2 <= len(ids) <= 12:
            continue
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                contagem[tuple(sorted((ids[i], ids[j])))] += 1
    return {par for par, n in contagem.items() if n >= min_partilhados}


@dataclass(frozen=True)
class RelatorioDedupe:
    grupos_exactos: list[list[str]]
    grupos_variantes: list[list[str]]
    grupos_incipit: list[list[str]]
    representantes: dict[str, str]   # id -> id do representante do grupo

    @property
    def n_marcados(self) -> int:
        return sum(1 for k, v in self.representantes.items() if k != v)


def _agrupar(pares: list[tuple[str, str]]) -> list[list[str]]:
    """Componentes conexas por union-find simples."""
    pai: dict[str, str] = {}

    def raiz(x: str) -> str:
        pai.setdefault(x, x)
        while pai[x] != x:
            pai[x] = pai[pai[x]]
            x = pai[x]
        return x

    for a, b in pares:
        ra, rb = raiz(a), raiz(b)
        if ra != rb:
            pai[ra] = rb

    grupos: dict[str, list[str]] = defaultdict(list)
    for x in pai:
        grupos[raiz(x)].append(x)
    return [sorted(g) for g in grupos.values() if len(g) > 1]


def detectar(poemas: list[Poem]) -> RelatorioDedupe:
    por_id = {p.id: p for p in poemas}

    # --- 1. exactos ---
    por_hash: dict[str, list[str]] = defaultdict(list)
    for p in poemas:
        por_hash[hashlib.sha256(_normalizar(p.body).encode()).hexdigest()].append(p.id)
    pares_exactos = [
        (ids[0], outro) for ids in por_hash.values() if len(ids) > 1 for outro in ids[1:]
    ]
    grupos_exactos = _agrupar(pares_exactos)

    # --- 2. variantes (inclui contenção) ---
    exactos_planos = {i for g in grupos_exactos for i in g}
    pares_variantes = []
    for a, b in _pares_candidatos([p for p in poemas if len(p.body.split()) >= 8]):
        if (a, b) in pares_exactos or (a in exactos_planos and b in exactos_planos):
            continue
        if similaridade_versos(por_id[a].body, por_id[b].body) >= LIMIAR_VARIANTE:
            pares_variantes.append((a, b))
    grupos_variantes = _agrupar(pares_variantes)

    # --- 3. incipits partilhados (relação, NÃO duplicação) ---
    por_incipit: dict[str, list[str]] = defaultdict(list)
    for p in poemas:
        primeiro = next((l for l in p.body.split("\n") if l.strip()), "")
        chave = _normalizar(primeiro)
        if len(chave.split()) >= 4:
            por_incipit[chave].append(p.id)
    grupos_incipit = [sorted(v) for v in por_incipit.values() if len(v) > 1]

    # --- representantes: o mais longo de cada grupo (a versão mais completa) ---
    representantes = {p.id: p.id for p in poemas}
    for grupo in grupos_exactos + grupos_variantes:
        rep = max(grupo, key=lambda i: (por_id[i].n_words, i))
        for i in grupo:
            representantes[i] = rep

    return RelatorioDedupe(
        grupos_exactos=grupos_exactos,
        grupos_variantes=grupos_variantes,
        grupos_incipit=sorted(grupos_incipit, key=len, reverse=True),
        representantes=representantes,
    )


def marcar(poemas: list[Poem], relatorio: RelatorioDedupe) -> list[Poem]:
    """Marca os duplicados com `duplicate_of`. **Não apaga nada** — variantes
    são material legítimo, e a busca colapsa o grupo no representante."""
    return [
        p if relatorio.representantes[p.id] == p.id
        else replace(p, duplicate_of=relatorio.representantes[p.id])
        for p in poemas
    ]
