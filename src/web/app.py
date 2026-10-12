"""A fronteira HTTP. Passo 3 da Fase 6: `GET /api/estado` e `GET /api/vozes`.

## O que este módulo não faz

**Não decide nada.** Não recupera, não monta prompt, não gera, não valida.
Isso é o passo 4, e chega lá pelo `Pipeline` — os mesmos objectos que o
`cli.py` e o `grafo.py` correm. Ver §0 do [plano](../../docs/FASE-6.md).

**Não carrega modelos à importação.** O `Servico` abaixo guarda referências e
constrói cada peça quando alguém a pede. Importar este módulo num teste tem de
custar milissegundos, senão o `pytest` paga o encoder — e o portão **I4** exige
que o `/api/estado` responda em menos de 100 ms **durante** uma geração.

## Porque é que o servidor escuta em 127.0.0.1 e isso não é um valor por omissão

A interface serve **corpos de poemas** (`GET /api/poema/{id}`, passo 9) de um
corpus que não está no repositório porque os termos de uso do Arquivo Pessoa
não estão confirmados — ver `data/README.md`. Expor isto à rede era publicar
esse material. A omissão é local, e mudá-la tem de ser explícito e ruidoso.
Portão **I7**.
"""
from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI

from ..corpus.models import VOZES_PRINCIPAIS, Lang
from ..generation.ollama import OllamaGenerator
from ..roteador import ROTEAVEIS
from ..voices import IDIOMA_UNICO, PERSONAS, idiomas_de
from . import serial
from .estado import (
    Componente,
    componente_corpus,
    componente_modelo,
    componente_ollama,
    diagnosticar_indice,
    manifesto_cru,
)

HOST = "127.0.0.1"
PORTA = 8000


class Servico:
    """O que o processo tem carregado, e o que ainda não.

    Existe para que o `/api/estado` possa responder «o encoder ainda não está
    carregado» sem o carregar para descobrir.
    """

    def __init__(self, gerador=None):
        self.gerador = gerador if gerador is not None else OllamaGenerator()
        #: Preenchidos pelo passo 4, quando alguém fizer a primeira pergunta.
        self.pipeline = None
        self.corpus = None          # (meta, chunks)
        self.roteador_aquecido = False

    # --- leituras baratas, que não provocam carregamento nenhum -----------

    @property
    def encoder_carregado(self) -> bool:
        return self.pipeline is not None

    @property
    def reranker_ligado(self) -> bool:
        return self.pipeline is not None and self.pipeline.reranker is not None

    def componentes(self) -> list[Componente]:
        """A prontidão por peça, na ordem em que o arranque as precisa."""
        ollama = componente_ollama(self.gerador)
        cs = [ollama, componente_modelo(self.gerador, ollama.pronto),
              componente_corpus()]
        cs.append(self._componente_indice())
        cs.append(Componente(
            "encoder", self.encoder_carregado,
            "carregado" if self.encoder_carregado
            else "ainda não carregado: carrega na 1.ª pergunta"))
        cs.append(Componente(
            "roteador", self.roteador_aquecido,
            "aquecido" if self.roteador_aquecido
            else "frio: a 1.ª proposta custa ~20 s de prefill",
            remedio=None if self.roteador_aquecido else "liga-se em /auto",
            custo_s=None if self.roteador_aquecido else 20.0))
        cs.append(Componente(
            "reranker", self.reranker_ligado,
            "ligado" if self.reranker_ligado
            else "desligado: +0,090 nDCG@5 por ~2,6 s, e é uma escolha",
            remedio=None if self.reranker_ligado else "liga-se em /rerank",
            custo_s=None if self.reranker_ligado else 2.6))
        return cs

    def _componente_indice(self) -> Componente:
        """O índice, e **qual** campo do manifesto falha quando falha.

        Sem o corpus carregado não há com que comparar a assinatura nem a
        ordem, e carregá-lo aqui era pagar na consulta de estado. Então
        declara-se o que se sabe — se os ficheiros existem — e diz-se que o
        resto só se sabe no arranque. É menos informação e é verdadeira.
        """
        if self.corpus is None:
            m, erro = manifesto_cru()
            if m is None:
                return Componente("indice", False, erro,
                                  remedio="constrói-se no arranque",
                                  custo_s=384.0)
            return Componente(
                "indice", False,
                f"em disco ({m.get('n_chunks')} chunks), ainda não verificado "
                f"contra o corpus",
                remedio="verifica-se no arranque")
        meta, chunks = self.corpus
        ok, detalhe = diagnosticar_indice(chunks, meta["assinatura"])
        return Componente("indice", ok, detalhe,
                          remedio=None if ok else "reconstrói-se no arranque",
                          custo_s=None if ok else 384.0)


def criar_app(servico: Servico | None = None) -> FastAPI:
    """Monta a aplicação. Recebe o `Servico` para os testes o poderem trocar."""
    app = FastAPI(title="PessoaBot", docs_url=None, redoc_url=None)
    app.state.servico = servico if servico is not None else Servico()

    @app.get("/api/estado")
    def estado() -> dict:
        """Prontidão por componente. **Não carrega nada** — ver o cabeçalho.

        `pronto` global é a conjunção do que é preciso para responder: Ollama,
        modelo, corpus e índice. O roteador e o reranker estão de fora de
        propósito — são escolhas, não requisitos, e tratá-los como requisito
        dizia «não pronto» a um sistema que responde perfeitamente.
        """
        cs = app.state.servico.componentes()
        exigidos = {"ollama", "modelo", "corpus", "indice"}
        return {
            "pronto": all(c.pronto for c in cs if c.nome in exigidos),
            "componentes": [asdict(c) for c in cs],
        }

    @app.get("/api/vozes")
    def vozes() -> dict:
        """As vozes com persona, e as combinações que **não** existem.

        A interface desactiva o impossível em vez de o corrigir depois (§4.6 do
        plano): o CLI muda a escolha do utilizador em silêncio com uma nota, e
        numa interface gráfica isso é pior que negá-la à partida.
        """
        itens = []
        for (voz, _lingua), p in PERSONAS.items():
            itens.append(serial.persona(p) | {
                "idiomas": [i.value for i in idiomas_de(voz)],
                "idioma_unico": (IDIOMA_UNICO[voz].value
                                 if voz in IDIOMA_UNICO else None),
                "roteavel": voz in ROTEAVEIS,
                "principal": voz in VOZES_PRINCIPAIS,
            })
        return {
            "vozes": itens,
            # O roteador só foi medido em português, logo propor em inglês era
            # propor fora do que foi medido.
            "roteador": {"idiomas": [Lang.PT.value], "acerto": 0.68,
                         "custo_s": 0.5,
                         "nota": "medido com o llama3.1 na Fase 5S; "
                                 "72% eram do qwen2.5"},
            "reranker": {"ganho_ndcg5": 0.090, "custo_s": 2.6,
                         "primeira_s": 4.8},
        }

    return app


app = criar_app()
