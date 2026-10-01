"""Orquestração: recuperar -> montar -> gerar -> guardar -> repetir se preciso.

## Por que há repetição, e por que é rara

Medido em 24 respostas reais (ver `docs/fase-1/07-RELATORIO-PLAGIO.md`):

| | sem a regra preventiva | com a regra no `system` |
|---|---|---|
| mediana de versos copiados | **82%** | **0%** |
| respostas acima de 20% | 16/24 (67%) | 3/24 (12%) |

A regra preventiva (`REGRAS_NAO_COPIAR` em `voices.py`) faz quase todo o
trabalho, e custa zero por pergunta porque vive no prefixo em cache. A repetição
com reforço é rede de segurança: dispara em ~21% dos casos e corrigiu 3 de 3.

Custo médio esperado: 1,21 gerações, ou ~34 s.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterator, Sequence

from .corpus.models import Chunk, Lang, Voice
from .generation.base import Generator, Resposta
from .generation.prompt import montar
from .guard import Veredicto, verificar
from .plagio import REFORCO, REFORCO_EN, Analise, analisar
from .retrieval.encoder import Encoder
from .retrieval.index import Index
from .voices import persona

TOP_K = 6
MAX_TENTATIVAS = 2


@dataclass(frozen=True)
class Turno:
    pergunta: str
    voz: Voice
    idioma: Lang
    recuperados: tuple[Chunk, ...]
    usados: tuple[Chunk, ...]
    resposta: Resposta
    veredicto: Veredicto
    plagio: Analise
    tentativas: int
    recuperacao_ms: float

    @property
    def texto(self) -> str:
        return self.veredicto.texto

    @property
    def aprovado(self) -> bool:
        return bool(self.veredicto) and not self.plagio.plagiou

    def fontes(self) -> str:
        return ", ".join(f"{c.poem_id}" for c in self.usados)


class Pipeline:
    def __init__(self, index: Index, encoder: Encoder, gerador: Generator,
                 n_tokens: Callable[[str], int], top_k: int = TOP_K):
        self.index = index
        self.encoder = encoder
        self.gerador = gerador
        self.n_tokens = n_tokens
        self.top_k = top_k

    def recuperar(self, pergunta: str, voz: Voice,
                  idioma: Lang = Lang.PT) -> tuple[list[Chunk], float]:
        import time
        t0 = time.perf_counter()
        qv = self.encoder.encode_queries([pergunta])[0]
        res = self.index.search(qv, top_k=self.top_k, voz=voz, idioma=idioma)
        return [c for c, _ in res], (time.perf_counter() - t0) * 1000

    def _repetir_sem(self, pergunta: str, voz: Voice, idioma: Lang,
                     recuperados: list[Chunk], copiados: set[str],
                     prompt_anterior):
        """Prepara a repetição **sem os poemas de que o modelo copiou**.

        Observado a correr o chatbot, à pergunta «você conhece o senhor fernando
        pessoa?»: a primeira tentativa copiou 9 de 14 versos do `poem_1164`, um
        deles à letra, por substituição de palavras — `Natureza`→`Silêncio`,
        `brisa`→`luz`, `perceber`→`escutar`. A repetição, com o mesmo contexto,
        voltou **ao mesmo poema**: 5 de 14 versos, máximo 0,82. Duas rejeições,
        ~80 s, e o utilizador interrompeu.

        O `REFORCO` já diz «não o reescrevas trocando uma palavra», e o modelo
        ignorou-o. Pedir melhor comportamento sobre o mesmo contexto é pedir ao
        modelo que resista ao que lhe foi posto à frente; tirar o poema do
        contexto **remove a ocasião**.

        Não é só encolher: `montar` corta o contexto quando o orçamento acaba,
        logo deixar um poema de fora deixa entrar o seguinte da recuperação. O
        modelo recebe material novo, não menos material.

        Se não sobrar nenhum poema, mantém-se o contexto original — sem contexto
        a resposta perde o fundamento, e um reforço textual é melhor que nada.
        """
        restantes = [c for c in recuperados if c.poem_id not in copiados]
        if not restantes:
            return prompt_anterior
        return montar(pergunta, restantes, persona(voz, idioma), self.n_tokens)

    def responder(self, pergunta: str, voz: Voice, idioma: Lang = Lang.PT,
                  max_tentativas: int = MAX_TENTATIVAS) -> Turno:
        recuperados, ms = self.recuperar(pergunta, voz, idioma)
        p = montar(pergunta, recuperados, persona(voz, idioma), self.n_tokens)

        # Os versos são comparados contra **tudo o que já foi mostrado** neste
        # turno, e não só contra o contexto da tentativa corrente: tirar um
        # poema do prompt não torna aceitável devolvê-lo ao utilizador.
        mostrados: list[Chunk] = list(p.chunks_usados)
        user = p.user
        for tentativa in range(1, max_tentativas + 1):
            r = self.gerador.gerar(p.system, user)
            v = verificar(r.texto, pergunta=pergunta, idioma=idioma)
            a = analisar(v.texto, tuple(mostrados))
            if not a.plagiou or tentativa == max_tentativas:
                return Turno(pergunta, voz, idioma, tuple(recuperados),
                             p.chunks_usados, r, v, a, tentativa, ms)
            p = self._repetir_sem(pergunta, voz, idioma, recuperados,
                                  {x.poema for x in a.copiados}, p)
            mostrados.extend(c for c in p.chunks_usados if c not in mostrados)
            # Reforço corrective: refere-se a uma tentativa concreta, logo não
            # pode viver no prefixo em cache como a regra preventiva.
            user = p.user + (REFORCO if idioma is Lang.PT else REFORCO_EN)
        raise AssertionError("inalcançável")

    def responder_em_fluxo(self, pergunta: str, voz: Voice,
                           idioma: Lang = Lang.PT,
                           max_tentativas: int = MAX_TENTATIVAS
                           ) -> Iterator[str | Turno]:
        """Como `responder`, mas emite fragmentos à medida que chegam.

        Emite `str` para cada fragmento e um `Turno` no fim de **cada**
        tentativa. Se o `Turno` não estiver aprovado e houver tentativas, segue-
        se outra ronda de fragmentos — o utilizador vê a primeira tentativa a
        aparecer e depois a ser substituída, o que é mais honesto que esconder
        os ~28 s que a repetição custa.
        """
        import time
        recuperados, ms = self.recuperar(pergunta, voz, idioma)
        p = montar(pergunta, recuperados, persona(voz, idioma), self.n_tokens)

        mostrados: list[Chunk] = list(p.chunks_usados)
        user = p.user
        for tentativa in range(1, max_tentativas + 1):
            partes: list[str] = []
            resposta: Resposta | None = None
            for item in self.gerador.gerar_em_fluxo(p.system, user):
                if isinstance(item, str):
                    partes.append(item)
                    yield item
                else:
                    resposta = item
            assert resposta is not None
            v = verificar(resposta.texto, pergunta=pergunta, idioma=idioma)
            a = analisar(v.texto, tuple(mostrados))
            turno = Turno(pergunta, voz, idioma, tuple(recuperados),
                          p.chunks_usados, resposta, v, a, tentativa, ms)
            yield turno
            if turno.aprovado or tentativa == max_tentativas:
                return
            p = self._repetir_sem(pergunta, voz, idioma, recuperados,
                                  {x.poema for x in a.copiados}, p)
            mostrados.extend(c for c in p.chunks_usados if c not in mostrados)
            # `REFORCO_EN` existia e nunca era usado: este caminho — o que o CLI
            # corre — não tinha o ramo de língua, logo uma sessão em inglês
            # recebia o reforço em português.
            user = p.user + (REFORCO if idioma is Lang.PT else REFORCO_EN)
