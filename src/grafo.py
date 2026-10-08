"""O mesmo pipeline, declarado como um grafo de estado (LangGraph).

## Por que isto existe, e por que não é reescrita

`pipeline.py` já é um **grafo cíclico com arestas condicionais**, escrito à mão
num `for`: recuperar → montar → gerar → verificar → (se plagiou e ainda há
tentativa) repetir sem os poemas copiados → gerar. O que este módulo faz é
**declarar essa máquina** em vez de a executar implicitamente, usando
`langgraph.graph.StateGraph`.

🔴 **Nenhum componente medido foi tocado.** A recuperação é a mesma
(`Pipeline.recuperar`, índice denso + reranker opcional), o prompt é o mesmo
(`generation.prompt.montar`), a guarda é a mesma (`guard.verificar`), o detector
de plágio é o mesmo (`plagio.analisar`) e a política de repetição é a mesma
(`Pipeline._repetir_sem`). ⇒ **os números da avaliação continuam a valer**, por
construção: o grafo chama exactamente as mesmas funções, pela mesma ordem.
Se algum dia divergirem, `tests/test_grafo.py` falha — é um teste de paridade
contra `Pipeline.responder`, resposta a resposta.

## O que o grafo acrescenta ao `for`

1. **A política fica legível como diagrama**, não como fluxo de controlo. A
   aresta condicional `verificar → repetir | END` é a regra de aceitação, e
   passa a ser um objecto inspeccionável (`grafo.get_graph().draw_ascii()`).
2. **Pontos de observação por nó.** Cada passo é um evento, e `stream()` devolve
   o estado a cada transição — útil para ver *onde* os ~34 s se gastam sem
   instrumentar o corpo das funções.
3. **O ciclo é explícito.** O limite de tentativas deixa de ser `range(...)` e
   passa a ser uma condição de saída declarada, que é o que ele sempre foi.

## O que o grafo NÃO acrescenta

Nem agente, nem ferramentas, nem decisão do modelo sobre o seu próprio caminho.
**O caminho é determinado por regras**, como antes. Chamar isto de «agente»
seria vender o que não há — ver `docs/CONTROLO.md`.

⚠️ **Dependência:** `langgraph`. O `requirements.txt` já declarou `langchain` uma
vez, em 2026-10-01, **usado em zero linhas**, e foi removido por isso. Esta
entrada é diferente — há um teste que falha sem ela —, mas a lição fica: uma
dependência declarada e não exercida é dívida, não capacidade.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, TypedDict

from langgraph.graph import END, START, StateGraph

from .corpus.models import Chunk, Lang, Voice
from .generation.base import Resposta
from .generation.prompt import Prompt, montar
from .guard import Veredicto, verificar
from .pipeline import MAX_TENTATIVAS, Pipeline, Turno
from .plagio import REFORCO, REFORCO_EN, Analise, analisar
from .voices import persona


class Estado(TypedDict, total=False):
    """O estado que viaja entre os nós.

    É deliberadamente o conjunto mínimo que o `Turno` precisa no fim: o grafo
    não guarda nada que a resposta final não use.
    """

    pergunta: str
    voz: Voice
    idioma: Lang
    max_tentativas: int

    recuperados: tuple[Chunk, ...]
    recuperacao_ms: float
    rerank_ms: float | None

    prompt: Prompt
    user: str
    #: Tudo o que já foi **mostrado ao modelo** neste turno, não só o contexto da
    #: tentativa corrente — tirar um poema do prompt não torna aceitável
    #: devolvê-lo ao utilizador.
    mostrados: tuple[Chunk, ...]

    tentativa: int
    resposta: Resposta
    veredicto: Veredicto
    plagio: Analise


def _no_recuperar(pipeline: Pipeline) -> Callable[[Estado], Estado]:
    def recuperar(e: Estado) -> Estado:
        chunks, ms, ms_rr = pipeline.recuperar(e["pergunta"], e["voz"],
                                               e.get("idioma", Lang.PT))
        return {"recuperados": tuple(chunks), "recuperacao_ms": ms,
                "rerank_ms": ms_rr}
    return recuperar


def _no_montar(pipeline: Pipeline) -> Callable[[Estado], Estado]:
    def montar_no(e: Estado) -> Estado:
        idioma = e.get("idioma", Lang.PT)
        p = montar(e["pergunta"], list(e["recuperados"]),
                   persona(e["voz"], idioma), pipeline.n_tokens)
        return {"prompt": p, "user": p.user, "mostrados": p.chunks_usados,
                "tentativa": 0}
    return montar_no


def _no_gerar(pipeline: Pipeline) -> Callable[[Estado], Estado]:
    def gerar(e: Estado) -> Estado:
        r = pipeline.gerador.gerar(e["prompt"].system, e["user"])
        return {"resposta": r, "tentativa": e["tentativa"] + 1}
    return gerar


def _no_verificar() -> Callable[[Estado], Estado]:
    def verificar_no(e: Estado) -> Estado:
        idioma = e.get("idioma", Lang.PT)
        v = verificar(e["resposta"].texto, pergunta=e["pergunta"],
                      idioma=idioma)
        a = analisar(v.texto, tuple(e["mostrados"]))
        return {"veredicto": v, "plagio": a}
    return verificar_no


def _no_repetir(pipeline: Pipeline) -> Callable[[Estado], Estado]:
    """Prepara a repetição **sem os poemas de que o modelo copiou**.

    Delega em `Pipeline._repetir_sem`, que é onde a decisão está medida e
    documentada. O nó acrescenta só o reforço correctivo e a contabilidade do
    que já foi mostrado.
    """
    def repetir(e: Estado) -> Estado:
        idioma = e.get("idioma", Lang.PT)
        copiados = {x.poema for x in e["plagio"].copiados}
        p = pipeline._repetir_sem(e["pergunta"], e["voz"], idioma,
                                  list(e["recuperados"]), copiados,
                                  e["prompt"])
        mostrados = list(e["mostrados"])
        mostrados.extend(c for c in p.chunks_usados if c not in mostrados)
        # Reforço correctivo: refere-se a uma tentativa concreta, logo não pode
        # viver no prefixo em cache como a regra preventiva.
        reforco = REFORCO if idioma is Lang.PT else REFORCO_EN
        return {"prompt": p, "user": p.user + reforco,
                "mostrados": tuple(mostrados)}
    return repetir


def _decidir(e: Estado) -> str:
    """A regra de aceitação, agora como aresta e não como `if` no meio do laço.

    Sai quando a resposta serve **ou** quando as tentativas acabaram — a mesma
    condição do `pipeline.responder`, incluindo a truncatura (`done_reason ==
    "length"`), que entrou na Fase 5R porque cinco de 48 amostras chegaram
    cortadas a meio da palavra.
    """
    serve = not e["plagio"].plagiou and not e["resposta"].truncada
    if serve or e["tentativa"] >= e.get("max_tentativas", MAX_TENTATIVAS):
        return "fim"
    return "repetir"


def construir(pipeline: Pipeline):
    """Devolve o grafo compilado para um `Pipeline` já montado.

    O `Pipeline` continua a ser o dono dos componentes (índice, encoder,
    gerador, reranker); o grafo só os orquestra.
    """
    g = StateGraph(Estado)
    g.add_node("recuperar", _no_recuperar(pipeline))
    g.add_node("montar", _no_montar(pipeline))
    g.add_node("gerar", _no_gerar(pipeline))
    g.add_node("verificar", _no_verificar())
    g.add_node("repetir", _no_repetir(pipeline))

    g.add_edge(START, "recuperar")
    g.add_edge("recuperar", "montar")
    g.add_edge("montar", "gerar")
    g.add_edge("gerar", "verificar")
    g.add_conditional_edges("verificar", _decidir,
                            {"repetir": "repetir", "fim": END})
    g.add_edge("repetir", "gerar")
    return g.compile()


@dataclass(frozen=True)
class PipelineGrafo:
    """Adaptador com o mesmo contrato de `Pipeline.responder`.

    Existe para que o CLI, os testes e qualquer chamador possam trocar um pelo
    outro sem saber qual está a correr — e para que o teste de paridade possa
    comparar os dois lado a lado.
    """

    pipeline: Pipeline
    grafo: Any

    @classmethod
    def de(cls, pipeline: Pipeline) -> "PipelineGrafo":
        return cls(pipeline=pipeline, grafo=construir(pipeline))

    def responder(self, pergunta: str, voz: Voice, idioma: Lang = Lang.PT,
                  max_tentativas: int = MAX_TENTATIVAS) -> Turno:
        inicial: Estado = {"pergunta": pergunta, "voz": voz, "idioma": idioma,
                           "max_tentativas": max_tentativas}
        # `recursion_limit` tem de acomodar o ciclo: 4 nós + 2 por repetição,
        # com folga. Sem isto, um `max_tentativas` alto rebenta no limite
        # omisso do LangGraph (25) em vez de parar pela nossa regra.
        limite = 10 + 4 * max_tentativas
        f: Estado = self.grafo.invoke(inicial, {"recursion_limit": limite})
        return Turno(
            pergunta=f["pergunta"], voz=f["voz"], idioma=f["idioma"],
            recuperados=tuple(f["recuperados"]),
            usados=f["prompt"].chunks_usados,
            resposta=f["resposta"], veredicto=f["veredicto"],
            plagio=f["plagio"], tentativas=f["tentativa"],
            recuperacao_ms=f["recuperacao_ms"], rerank_ms=f["rerank_ms"],
        )

    def diagrama(self) -> str:
        """A política de repetição desenhada — o que o `for` não sabia mostrar.

        Mermaid e não ASCII de propósito: `draw_ascii()` exige `grandalf`, uma
        dependência a mais para desenhar; `draw_mermaid()` é pura e o resultado
        renderiza no README e no GitHub.
        """
        return self.grafo.get_graph().draw_mermaid()
