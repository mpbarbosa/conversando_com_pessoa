"""A fronteira HTTP. Passos 3 e 4 da Fase 6: estado, vozes e `/api/perguntar`.

## O que este módulo não faz

**Não decide nada.** Não recupera, não monta prompt, não gera, não valida.
Tudo isso chega pelo `Pipeline` — os mesmos objectos que o `cli.py` e o
`grafo.py` correm. Ver §0 do [plano](../../docs/FASE-6.md). O portão **I1** é o
que o prova: 20 perguntas fixas, gerador determinista, e o `Turno` que sai daqui
igual campo a campo ao do CLI e ao do grafo.

O que este ficheiro **acrescenta** ao pipeline é de transporte e de
concorrência, e não de política: traduzir para NDJSON (`serial.py`), atravessar
a fronteira síncrono/assíncrono (`fluxo.py`), reter o início do fluxo com a
**mesma** função que o CLI usa (`apresentacao.limpar_inicio`, portão **I2**) e
deixar passar **uma geração de cada vez** (§2.2).

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

## Porque é que o fluxo é NDJSON num POST, e não SSE

O `EventSource` do navegador só faz **GET**, e com GET a pergunta — texto que a
pessoa escreveu — viajava na *query string*, que fica no histórico do navegador
e nos registos de tudo o que esteja no caminho. Uma linha de JSON por evento num
POST em fluxo resolve-se numa chamada só, e cancela-se com `AbortController`.
Ver §1.3 do plano; o que se perde é a reconexão do `EventSource`, que não faz
falta porque a geração não é retomável.
"""
from __future__ import annotations

import asyncio
import json
import time
from dataclasses import asdict
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..apresentacao import limpar_inicio
from ..corpus.models import VOZES_PRINCIPAIS, Lang, Voice
from ..generation.ollama import OllamaGenerator
from ..roteador import ROTEAVEIS
from ..voices import IDIOMA_UNICO, PERSONAS, idiomas_de, persona
from . import serial
from .estado import (
    Componente,
    componente_corpus,
    componente_modelo,
    componente_ollama,
    diagnosticar_indice,
    manifesto_cru,
)
from .fluxo import em_fluxo

HOST = "127.0.0.1"
PORTA = 8000

#: O tipo do fluxo. Não é `application/json`: o corpo **não** é um documento
#: JSON, é uma sequência de documentos separados por `\n`, e dizer `json` fazia
#: um cliente ingénuo esperar pelo fim para desserializar — que é exactamente o
#: que o fluxo existe para evitar.
NDJSON = "application/x-ndjson"

#: Custo médio de uma resposta, para a estimativa do `409`. É o número do
#: `pipeline.py`: «1,21 gerações, ou ~34 s». É **média medida**, não promessa —
#: a Fase 0 mediu *throttling* térmico até 101 °C, e a repetição de ~21% dos
#: casos custa mais ~28 s.
SEGUNDOS_POR_RESPOSTA = 34.0


class Servico:
    """O que o processo tem carregado, e o que ainda não.

    Existe para que o `/api/estado` possa responder «o encoder ainda não está
    carregado» sem o carregar para descobrir.
    """

    def __init__(self, gerador=None, pipeline=None):
        self.gerador = gerador if gerador is not None else OllamaGenerator()
        #: `None` até alguém fazer a primeira pergunta. Os testes injectam-no
        #: já feito — é o que permite exercitar a API sem pagar o encoder.
        self.pipeline = pipeline
        self.corpus = None          # (meta, chunks)
        self.roteador_aquecido = False
        #: O reranker fica em cache **aqui** e não no pipeline: um pedido sem
        #: `rerank` desliga-o do pipeline, e desligar não pode significar
        #: recarregar 568M na próxima vez que alguém o peça.
        self._reranker = None
        #: §2.2: há um Ollama, um encoder e um reranker. Duas gerações em
        #: paralelo não dão duas respostas em 30 s — dão duas em 70 s, com os
        #: tempos do rodapé a mentir, porque `prefill_s` e `decode_s` vêm do
        #: Ollama e não sabem que estavam a competir.
        self.trinco = asyncio.Lock()
        #: Instante monótono do início da geração em curso, para a estimativa
        #: de espera do `409`. `None` quando não há nenhuma.
        self.inicio_geracao: float | None = None

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

    # --- o que custa, e por isso corre numa thread ------------------------

    def garantir_pipeline(self):
        """Constrói o `Pipeline` à primeira pergunta. **Bloqueante.**

        É o `_arrancar` do `cli.py` sem o `typer`: corpus, encoder, índice e o
        contador de tokens do **gerador** — e não do encoder, porque o qwen
        conta ~17% mais tokens em português e orçamentar com o do e5
        subestimava até 46%.

        ⚠️ **Isto é a única duplicação que o passo 4 faz**, e é consciente: o
        `_arrancar` mistura construção com mensagens no terminal, e extraí-lo
        obrigava a mexer no `cli.py`, que esta fase declarou não tocar (§6). O
        risco é divergirem os parâmetros — um `top_k` diferente aqui produzia
        respostas que **nenhuma medição deste repositório descreve** —, e a
        defesa é um teste em `tests/test_perguntar.py` que compara as duas
        chamadas a `Pipeline(...)`. Nenhuma das duas afina nada: as omissões do
        `Pipeline` são as que as Fases 0 a 5Y mediram.

        Chamar isto duas vezes é de graça: devolve o que já está construído.
        """
        if self.pipeline is not None:
            return self.pipeline
        import os

        from ..corpus.build import CAMINHO, build, load
        from ..pipeline import Pipeline
        from ..retrieval.encoder import Encoder
        from ..retrieval.index import Index
        from ..tokens import GERADOR, contador

        if not os.path.exists(CAMINHO):
            build()
        meta, chunks = load()
        self.corpus = (meta, chunks)
        enc = Encoder()
        idx = Index.load(chunks, enc, meta["assinatura"])
        if idx is None:
            idx = Index.load_or_build(chunks, enc, meta["assinatura"])
        n_tok = contador(GERADOR)
        self.pipeline = Pipeline(idx, enc, self.gerador, n_tok)
        return self.pipeline

    def reranker_para(self, ligado: bool):
        """O reranker a usar nesta pergunta, carregando-o se for a 1.ª vez.

        **Bloqueante**: são 568M, e a 1.ª reordenação custa ~4,8 s contra os
        ~2,6 s das seguintes — medido, e não se resolve com aquecimento (ver
        `retrieval/rerank.py`). Quem não pede não paga nada disto.
        """
        if not ligado:
            return None
        if self._reranker is None:
            from ..retrieval.rerank import padrao
            self._reranker = padrao()
        return self._reranker

    def rotear(self, pergunta: str):
        """A proposta do roteador. **Bloqueante**, e nunca levanta.

        Marca o roteador como aquecido porque é isso que uma chamada faz: põe o
        prefixo dos 331 tokens do `SYSTEM` em cache no Ollama. A primeira custa
        ~20 s e as seguintes ~0,5 s (Fase 4, Passo A4b), e o `/api/estado`
        deixa de dizer «frio» quando já não está.
        """
        from ..roteador import rotear

        p = rotear(pergunta, self.gerador)
        self.roteador_aquecido = True
        return p

    def espera_estimada_s(self) -> float:
        """Quanto falta da geração em curso, pela média medida.

        É uma **estimativa** e a interface tem de a mostrar como tal: a
        repetição de ~21% dos casos acrescenta ~28 s que isto não sabe prever.
        """
        if self.inicio_geracao is None:
            return 0.0
        decorrido = time.monotonic() - self.inicio_geracao
        return max(0.0, SEGUNDOS_POR_RESPOSTA - decorrido)


class Pedido(BaseModel):
    """O corpo do `POST /api/perguntar`.

    **Não é um modelo do domínio.** O §1.4 do plano recusa declarar `Turno` e
    companhia em `pydantic` porque isso criava duas definições da mesma coisa;
    isto é o oposto — a entrada do fio, que não existe em sítio nenhum do
    domínio e cujo trabalho é rejeitar lixo antes de chegar ao `Pipeline`.

    Uma `voz` ou um `idioma` fora dos enums dá `422` sem o pipeline ser tocado.
    """

    pergunta: str = Field(min_length=1)
    voz: Voice = Voice.ORTONIMO
    idioma: Lang = Lang.PT
    #: +0,090 nDCG@5 por ~2,6 s (Fase 3B). É uma troca, logo é uma escolha.
    rerank: bool = False
    #: O roteador propõe a voz. 68% de acerto medido na 5S, ~0,5 s a quente.
    auto: bool = False


def _linha(evento: dict[str, Any]) -> bytes:
    """Um evento, uma linha. `ensure_ascii=False` porque o conteúdo é verso."""
    return (json.dumps(evento, ensure_ascii=False) + "\n").encode("utf-8")


def _verificar_combinacao(p: Pedido) -> None:
    """Recusa as combinações impossíveis em vez de as corrigir (§4.6).

    O CLI corrige em silêncio com uma nota: `/pt` com `/search` volta a inglês,
    porque Alexander Search tem **1 poema em português entre 52**. Numa
    interface, mudar a escolha de alguém depois de ele a fazer é pior que
    lha negar antes — e a API é a fronteira onde isso se decide, porque o
    `/api/vozes` já publica exactamente estes limites (`idiomas`,
    `idioma_unico`, `roteavel`) para a página poder desactivar o impossível.

    As duas regras vêm das **mesmas constantes** que o CLI lê (`IDIOMA_UNICO`,
    `idiomas_de`, `ROTEAVEIS`), e não de uma cópia da lógica dele: uma segunda
    tabela do que é possível divergia da primeira em silêncio.
    """
    disponiveis = idiomas_de(p.voz)
    if p.idioma not in disponiveis:
        unica = IDIOMA_UNICO.get(p.voz)
        motivo = (f"{persona(p.voz, unica).nome} escreve em {unica.value}"
                  if unica is not None
                  else f"esta voz só tem persona em "
                       f"{', '.join(i.value for i in disponiveis) or 'nenhuma língua'}")
        raise HTTPException(422, detail={
            "erro": "combinacao_impossivel",
            "campo": "idioma",
            "mensagem": f"{p.voz.value} em {p.idioma.value}: {motivo}",
            "idiomas": [i.value for i in disponiveis],
        })
    if p.auto and p.idioma is not Lang.PT:
        raise HTTPException(422, detail={
            "erro": "combinacao_impossivel",
            "campo": "auto",
            "mensagem": "o roteador só foi medido em português",
            "idiomas": [Lang.PT.value],
        })


async def _eventos(servico: Servico, p: Pedido):
    """O fluxo, evento a evento. Quem chama já tomou o trinco; aqui liberta-se.

    A libertação é no `finally` **deste** gerador e não no fim do manipulador:
    o corpo de um `StreamingResponse` corre depois de o manipulador devolver, e
    libertar lá deixava o trinco aberto durante toda a geração.

    Quatro tipos de evento, e a ordem é a do tempo:

    - `proposta` — só com `auto`, antes de gerar: a voz que o roteador propôs e
      o que custou. A geração arranca logo (§4.5: não se paga latência por uma
      caixa de diálogo), e é o cliente que aborta se quiser outra voz.
    - `fragmento` — texto à medida que chega, já **sem** o início que a
      `limpar_inicio` descasca.
    - `turno` — o `Turno` serializado, no fim de **cada** tentativa. Quando não
      está aprovado segue-se outra ronda de fragmentos: o utilizador vê a
      tentativa a ser rejeitada em vez de esperar 58 s sem explicação (§4.4).
    - `erro` — porque quando a geração falha o estado HTTP já foi 200. Um fluxo
      que morre calado é indistinguível de um que acabou.
    """
    try:
        pipeline = await asyncio.to_thread(servico.garantir_pipeline)
        voz, idioma = p.voz, p.idioma
        if p.auto:
            proposta = await asyncio.to_thread(servico.rotear, p.pergunta)
            # `voz is None` é «não sei», e mantém-se a voz corrente: inventar
            # uma era pior. Vai ao fio como tal, com `decidiu: false`.
            if proposta.decidiu:
                voz = proposta.voz
            yield _linha({"tipo": "proposta",
                          "proposta": serial.proposta(proposta),
                          "voz": serial.voz(voz)})
        pipeline.reranker = await asyncio.to_thread(servico.reranker_para,
                                                    p.rerank)

        # A retenção do início, com a **mesma** função que o CLI chama (portão
        # I2). Uma segunda implementação — num `app.js`, por exemplo — era uma
        # segunda política de apresentação a divergir em silêncio.
        buffer: list[str] = []
        a_reter = True
        async for item in em_fluxo(
                lambda: pipeline.responder_em_fluxo(p.pergunta, voz, idioma)):
            if isinstance(item, str):
                if a_reter:
                    buffer.append(item)
                    retido, a_reter = limpar_inicio("".join(buffer), p.pergunta)
                    if a_reter:
                        buffer = [retido] if retido else []
                        continue
                    buffer, item = [], retido
                yield _linha({"tipo": "fragmento", "texto": item})
                continue
            yield _linha({"tipo": "turno", "turno": serial.turno(item)})
            # A tentativa seguinte volta a reter. O CLI **não** faz isto — o
            # `a_reter` dele não é reposto entre tentativas —, logo um eco na
            # 2.ª tentativa chega ao terminal dele. Aqui não chega, porque o
            # portão I2 é sobre o fluxo inteiro e não sobre a 1.ª tentativa.
            buffer, a_reter = [], True
    except Exception as e:  # vai ao fio como evento `erro`; ver o docstring
        yield _linha({"tipo": "erro", "erro": type(e).__name__,
                      "mensagem": str(e)})
    finally:
        # Também no caminho do cancelamento (`CancelledError` não é `Exception`
        # e passa ao lado do `except`): abortar liberta o trinco.
        servico.inicio_geracao = None
        servico.trinco.release()


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

    @app.post("/api/perguntar")
    async def perguntar(pedido: Pedido) -> StreamingResponse:
        """Uma pergunta, um fluxo de NDJSON. **Uma geração de cada vez** (§2.2).

        O trinco é tomado **aqui** e não dentro do fluxo, porque é aqui que
        ainda se pode responder com um estado: depois de o `StreamingResponse`
        começar, o `200` já foi. O segundo pedido concorrente recebe `409` com
        o tempo que falta — a interface desactiva o botão e di-lo. Não é uma
        limitação a esconder: é a verdade do hardware que a Fase 0 mediu a
        fazer *throttling* térmico até 101 °C.

        ⚠️ O trinco é um `asyncio.Lock`, logo é **por processo**. Não protege
        contra um `gerar_amostras.py` de uma fase a falar com o mesmo Ollama, e
        esse é o modo de falha caro: o campo `segundos` do `01-cru.jsonl` da
        fase fica ininterpretável. O interbloqueio entre processos é o
        **passo 7** (sentinela em ficheiro, portão **I8**); até lá, não correr o
        servidor com uma medição a decorrer é disciplina e não mecanismo.
        """
        servico: Servico = app.state.servico
        _verificar_combinacao(pedido)
        # Entre este `locked()` e o `acquire()` não há `await` nenhum, logo
        # nada mais corre no laço pelo meio: um `acquire()` sobre um trinco
        # livre devolve sem suspender. É o que torna a verificação atómica, e
        # é por isso que não se mete código aqui.
        if servico.trinco.locked():
            raise HTTPException(409, detail={
                "erro": "ocupado",
                "mensagem": "há uma geração em curso; há um Ollama, um encoder "
                            "e um reranker, e duas gerações em paralelo não dão "
                            "duas respostas em 30 s — dão duas em 70 s",
                "espera_estimada_s": servico.espera_estimada_s(),
            })
        await servico.trinco.acquire()
        servico.inicio_geracao = time.monotonic()
        return StreamingResponse(_eventos(servico, pedido),
                                 media_type=NDJSON)

    return app


app = criar_app()
