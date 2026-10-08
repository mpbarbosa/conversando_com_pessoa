#!/usr/bin/env python
"""Fase 5T / A1-A4 — as três regras de língua da persona, verificadas na saída.

Protocolo: `../FASE-5T.md` §2-4.

Três detectores, **declarados no §2 antes de qualquer contagem**:

  **R-PRO**  próclise onde o português europeu exige ênclise
  **R-GER**  perífrase progressiva com gerúndio («está caindo»)
  **R-VOC**  «você» como tratamento

Corre em três conjuntos, todos já comprometidos no repositório — **nenhuma
geração nova**: o corpus pt (o nulo do T1), os 48 gerados e 24 reais da 5Q (o
T2), e os 180 da 5M (o descritivo por voz e modelo).

Escreve `01-deteccao.json`.
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
from collections import Counter

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, RAIZ)

from src.corpus.models import Lang                         # noqa: E402
from src.corpus.parse import parse_corpus                  # noqa: E402

#: §4 T1 — o mesmo limiar do R1 da 5R.
LIMIAR_T1 = 0.01
#: §4.1 — o nivel a que o `lingua_errada` ja autorizou uma rejeicao.
NIVEL_REJEICAO = 0.002

# --------------------------------------------------------------------------- #
# §2.1 — proclise
# --------------------------------------------------------------------------- #
#: Os pronomes considerados. `o/a/os/as` e `nos/vos` ficam FORA (homografia com
#: artigos e preposicoes): sacrificio de cobertura a favor da precisao, §2.1.
PRONOMES = frozenset({"me", "te", "lhe", "lhes"})
#: §2.1 — `se` vai num ramo separado, porque e tambem conjuncao.
PRONOME_AMBIGUO = "se"

_NEGACAO = "não nao nunca nada ninguém ninguem nem jamais nenhum nenhuma"
_SUBORD = ("que quem se quando onde como porque cujo cuja cujos cujas qual "
           "quais quanto quanta enquanto embora caso conforme pois segundo")
_FOCO = ("já ja ainda sempre também tambem só so apenas talvez bem mal tudo "
         "todo todos toda todas muito pouco tanto mais menos antes depois até "
         "ate logo aqui ali lá la cá ca hoje ontem amanhã amanha assim")
#: §2.1 — qualquer preposicao licencia (o infinitivo preposicionado leva
#: proclise: «para se ver»). Inclui as formas contraidas.
_PREP = ("a de em por para com sem sobre sob entre até ate ante após apos "
         "contra desde perante trás tras ao à a aos às as do da dos das no na "
         "nos nas pelo pela pelos pelas num numa nuns numas dum duma duns "
         "dumas pra")
LICENCIADORES = frozenset((_NEGACAO + " " + _SUBORD + " " + _FOCO + " "
                           + _PREP).split())

#: §2.1 — fronteira de oracao. Conta como NAO licenciador: e ai que a proclise
#: e inequivocamente brasileira.
_FRONTEIRA = frozenset('.,;:!?—–-()«»"“”…[]')

#: Palavra, mantendo o hifen: «enche-me» e UM token, logo a enclise correcta
#: nunca chega a ser examinada.
_RE_TOKEN = re.compile(r"[a-zà-ÿ]+(?:-[a-zà-ÿ]+)*|[^\sa-zà-ÿ]", re.I)


def _tokens(linha: str) -> list[str]:
    return _RE_TOKEN.findall(linha.lower())


def proclise(texto: str) -> tuple[list[str], list[str]]:
    """([ocorrencias dos pronomes inequivocos], [ocorrencias do ramo `se`]).

    Cada ocorrencia e o trigrama anterior-pronome-seguinte, para o relatorio
    poder mostrar o que foi marcado em vez de so contar.
    """
    firmes: list[str] = []
    ambiguas: list[str] = []
    for linha in texto.split("\n"):
        toks = _tokens(linha)
        for i, t in enumerate(toks):
            if t not in PRONOMES and t != PRONOME_AMBIGUO:
                continue
            ant = toks[i - 1] if i else None
            # Inicio de linha ou pontuacao: fronteira de oracao, §2.1.
            fronteira = ant is None or ant in _FRONTEIRA
            if not fronteira and ant in LICENCIADORES:
                continue
            seg = toks[i + 1] if i + 1 < len(toks) else ""
            ctx = f"{ant or '^'} [{t}] {seg}".strip()
            if t == PRONOME_AMBIGUO:
                # §2.1: no ramo do `se` exige-se que o anterior NAO seja
                # fronteira de oracao — «Se me vires» e conjuncao, nao proclise.
                if not fronteira:
                    ambiguas.append(ctx)
            else:
                firmes.append(ctx)
    return firmes, ambiguas


# --------------------------------------------------------------------------- #
# §2.2 — gerundio progressivo
# --------------------------------------------------------------------------- #
_AUX = frozenset((
    "estou estás estas está esta estamos estais estão estao estava estavas "
    "estávamos estavamos estavam estive esteve estiveram estarei estará estara "
    "estaremos estarão estarao estaria estariam esteja estejam estivesse "
    "estivessem estar "
    "ando andas anda andamos andam andava andavam andar "
    "vou vais vai vamos ides vão vao ia ias íamos iamos iam irei irá ira "
    "iremos irão irao "
    "fico ficas fica ficamos ficam ficava ficavam ficar ficou ficaram "
    "continuo continuas continua continuamos continuam continuar continuava"
).split())
#: §2.2 — **so a perifrase**: o gerundio solto («andando por ai») e portugues
#: europeu correcto e nao se marca. No maximo UM token de intervalo.
MAX_INTERVALO = 1


def _e_gerundio(t: str) -> bool:
    return len(t) >= 5 and t.endswith("ndo")


def gerundio(texto: str) -> list[str]:
    out: list[str] = []
    for linha in texto.split("\n"):
        toks = [t for t in _tokens(linha) if t not in _FRONTEIRA]
        for i, t in enumerate(toks):
            if t not in _AUX:
                continue
            for j in range(i + 1, min(i + 2 + MAX_INTERVALO, len(toks))):
                if _e_gerundio(toks[j]):
                    out.append(" ".join(toks[i:j + 1]))
                    break
    return out


# --------------------------------------------------------------------------- #
# §2.3 — «voce»
# --------------------------------------------------------------------------- #
_RE_VOCE = re.compile(r"\bvoc[êe]s?\b", re.I)
#: Declarado no §2.3 do protocolo e **errado**: `vosso` e portugues europeu
#: correcto (possessivo da 2.a do plural). Conta-se a parte e NAO entra no
#: portao — a correccao fica no relatorio em vez de a emenda ser silenciosa.
_RE_VOSSO = re.compile(r"\bvoss[oa]s?\b", re.I)


def voce(texto: str) -> list[str]:
    return [m.group(0).lower() for m in _RE_VOCE.finditer(texto)]


# --------------------------------------------------------------------------- #
def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """IC de Wilson a 95%. Sem scipy, como todo o resto do projecto."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - r) / d, (c + r) / d)


REGRAS = ("R-PRO", "R-GER", "R-VOC")


def avalia(texto: str) -> dict[str, list[str]]:
    firmes, ambiguas = proclise(texto)
    return {"R-PRO": firmes, "R-GER": gerundio(texto), "R-VOC": voce(texto),
            "_se": ambiguas, "_vosso": _RE_VOSSO.findall(texto)}


def taxas(textos: list[str]) -> dict:
    """Fracção de TEXTOS com ao menos uma marcação, por regra."""
    n = len(textos)
    achados = [avalia(t) for t in textos]
    out = {}
    for r in REGRAS + ("_se", "_vosso"):
        marcados = [a for a in achados if a[r]]
        k = len(marcados)
        lo, hi = wilson(k, n)
        out[r] = {"n": n, "marcados": k, "taxa": round(k / n, 5) if n else None,
                  "wilson95": [round(lo, 5), round(hi, 5)],
                  "exemplos": [e for a in marcados for e in a[r]][:10]}
    return out


def main() -> None:
    # ---------------- A2: o nulo do corpus ------------------------------- #
    poemas = [p for p in parse_corpus(os.path.join(RAIZ, "data/pessoa_poems"))
              if p.language is Lang.PT]
    print(f"corpus: {len(poemas)} poemas em pt")
    corpus = taxas([p.body for p in poemas])
    # quais poemas, para o relatorio poder mostrar
    marcados_quais = {r: [p.id for p in poemas if avalia(p.body)[r]][:12]
                      for r in REGRAS}

    # ---------------- A3: os 48 gerados e 24 reais da 5Q ----------------- #
    chave = json.load(open(os.path.join(RAIZ, "docs/fase-5q/01-chave.json"),
                           encoding="utf-8"))["chave"]
    ger5q = [c for c in chave if c["grupo"] != "R"]
    real5q = [c for c in chave if c["grupo"] == "R"]
    assert len(ger5q) == 48 and len(real5q) == 24, (len(ger5q), len(real5q))
    g = taxas([c["texto"] for c in ger5q])
    rr = taxas([c["texto"] for c in real5q])

    # ---------------- A4: descritivo, por modelo e por voz --------------- #
    cru5m = [json.loads(l) for l in
             open(os.path.join(RAIZ, "docs/fase-5m/01-cru.jsonl"),
                  encoding="utf-8")]
    por_modelo, por_voz = {}, {}
    for chave_g, destino in (("modelo", por_modelo), ("voz", por_voz)):
        grupos: dict[str, list[str]] = {}
        for x in cru5m:
            grupos.setdefault(x[chave_g], []).append(x["texto"])
        for k, ts in sorted(grupos.items()):
            destino[k] = {r: taxas(ts)[r]["taxa"] for r in REGRAS}
    # e nos 48 da 5Q, por modelo (sao as 3 vozes que falham)
    q5q: dict[str, dict] = {}
    for m in sorted({c["modelo"] for c in ger5q}):
        ts = [c["texto"] for c in ger5q if c["modelo"] == m]
        q5q[m] = {r: taxas(ts)[r]["taxa"] for r in REGRAS}

    # ---------------- portoes ------------------------------------------- #
    portoes = {}
    for r in REGRAS:
        t1 = corpus[r]["taxa"] < LIMIAR_T1
        # T2: limite inferior de Wilson nos gerados acima da taxa do corpus
        t2 = g[r]["wilson95"][0] > corpus[r]["taxa"]
        if not t1:
            trat = "nao entra (T1 nao dispara)"
        elif not t2:
            trat = "nao entra (T2 nao dispara)"
        elif corpus[r]["taxa"] <= NIVEL_REJEICAO:
            trat = "REJEICAO (nivel do lingua_errada)"
        else:
            trat = "AVISO em suspeitas"
        portoes[r] = {"T1": {"taxa_corpus": corpus[r]["taxa"],
                             "limiar": LIMIAR_T1, "dispara": t1},
                      "T2": {"taxa_gerados": g[r]["taxa"],
                             "wilson_inf": g[r]["wilson95"][0],
                             "dispara": t2},
                      "tratamento_pre_escrito": trat}
    t3 = any(p["T1"]["dispara"] and p["T2"]["dispara"] for p in portoes.values())

    out = {"_meta": {"protocolo": "docs/FASE-5T.md §2-4",
                     "geracao_nova": False,
                     "pronomes": sorted(PRONOMES),
                     "n_licenciadores": len(LICENCIADORES),
                     "n_poemas_pt": len(poemas)},
           "T1_corpus": corpus, "T1_quais": marcados_quais,
           "T2_gerados_5q": g, "T2_reais_5q": rr,
           "A4_5m_por_modelo": por_modelo, "A4_5m_por_voz": por_voz,
           "A4_5q_por_modelo": q5q,
           "portoes": portoes,
           "T3": {"dispara": t3},
           "T4": {"dispara": not t3}}
    with open(os.path.join(AQUI, "01-deteccao.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    # ---------------- ecra --------------------------------------------- #
    print(f"\n{'regra':8s} {'corpus':>12s} {'gerados 5Q':>12s} "
          f"{'reais 5Q':>10s}   T1   T2")
    for r in REGRAS:
        print(f"{r:8s} {corpus[r]['marcados']:4d}/{corpus[r]['n']:<5d} "
              f"{g[r]['marcados']:5d}/{g[r]['n']:<5d} "
              f"{rr[r]['marcados']:4d}/{rr[r]['n']:<4d}  "
              f"{'SIM' if portoes[r]['T1']['dispara'] else ' no':>4s} "
              f"{'SIM' if portoes[r]['T2']['dispara'] else ' no':>4s}   "
              f"-> {portoes[r]['tratamento_pre_escrito']}")
    print(f"\nramo `se` (reportado a parte): corpus "
          f"{corpus['_se']['marcados']}/{corpus['_se']['n']}, gerados "
          f"{g['_se']['marcados']}/48, reais {rr['_se']['marcados']}/24")
    print(f"`vosso` (o protocolo errou, e EP correcto): corpus "
          f"{corpus['_vosso']['marcados']}/{corpus['_vosso']['n']}")
    for r in REGRAS:
        if corpus[r]["exemplos"]:
            print(f"\n{r} no CORPUS ({corpus[r]['marcados']} poemas): "
                  f"{corpus[r]['exemplos'][:6]}")
            print(f"   poemas: {marcados_quais[r][:8]}")
        if g[r]["exemplos"]:
            print(f"{r} nos GERADOS: {g[r]['exemplos'][:6]}")
    print(f"\nT3 (a instrucao e desobedecida): "
          f"{'DISPARA' if t3 else 'nao dispara'}")
    print(f"\n5Q por modelo (3 vozes que falham): {q5q}")
    print(f"5M por modelo: {por_modelo}")
    print(f"5M por voz:    {por_voz}")
    print(f"\n-> {os.path.join(AQUI, '01-deteccao.json')}")


if __name__ == "__main__":
    main()
