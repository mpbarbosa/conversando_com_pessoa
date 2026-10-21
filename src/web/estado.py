"""Prontidão por componente, e sem pagar por perguntar.

## Porque é que isto existe antes de haver geração

A interface tem **quatro** esperas e só uma é por pergunta (§4.2 do plano): o
`corpus.jsonl` a construir (~40 s), o **índice a construir (~6,4 min)**, o
roteador a aquecer (~20 s) e o reranker de 568M a carregar. Todas já
surpreenderam alguém no terminal, e uma página em branco durante 6 minutos é
indistinguível de uma avaria.

Daí o `GET /api/estado` devolver a lista de componentes em vez de um booleano.
E daí cada componente trazer um **remédio**: a falha mais provável de todas é o
Ollama em baixo, e o CLI já responde a isso com o comando a correr
(`ollama serve`) em vez de um traço de pilha.

## A regra: perguntar o estado não carrega nada

`Encoder()` instancia um `SentenceTransformer` no construtor, e o reranker tem
568M. Se consultar o estado os carregasse, a interface pagava no primeiro
`GET` o que devia pagar quando alguém faz uma pergunta — e o `/api/estado` é
precisamente o que tem de responder **durante** uma geração (portão I4).

Logo tudo aqui é barato: existência de ficheiros, duas chamadas HTTP ao Ollama
com *timeout*, e leitura de um JSON. O estado do encoder, do roteador e do
reranker é lido do objecto de serviço — «já foi carregado?» —, nunca
provocado.

## O diagnóstico do manifesto, e porque é duplicação deliberada

`Index.load` devolve `None` e **não diz porquê**: são cinco verificações e uma
só saída. Para o portão **I3** isso não chega — «índice ausente ou
desactualizado» manda reconstruir 6,4 minutos sem dizer o que mudou, quando a
resposta é uma de cinco e está toda no manifesto.

Este módulo reimplementa a comparação, e isso é um risco conhecido: duas
versões da mesma regra divergem. A defesa **não** é cuidado, é um teste de
paridade — `tests/test_app.py` verifica que este diagnóstico diz «aceita»
exactamente quando o `Index.load` devolve um índice, e «recusa» exactamente
quando ele devolve `None`. É a disciplina do `tests/test_grafo.py` aplicada
aqui.

O sítio melhor para isto era um `Index.porque_recusou()` no próprio
`index.py`. Não vai lá porque a Fase 6 declarou que não mexe em `src/` fora de
`src/web/` — e o `index.py` está no caminho que sete fases mediram. Fica
nomeado como mudança a fazer de propósito, não de passagem.

⚠️ **Uma ressalva medida:** a comparação do encoder é contra a constante
`tokens.ENCODER`, não contra `Encoder().nome`, para não instanciar o modelo. As
duas são iguais quando o encoder é construído por omissão, que é o que o
`cli.py` faz — e há um teste a fixar isso. Um `Encoder(nome=...)` diferente
tornava este diagnóstico errado, e em silêncio.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, fields

from ..corpus.build import CAMINHO as CAMINHO_CORPUS
from ..retrieval.index import CAMINHO as CAMINHO_INDICE
from ..retrieval.index import Manifesto
from ..tokens import ENCODER


@dataclass(frozen=True)
class Componente:
    """Uma peça do sistema, e o que fazer quando não está pronta."""

    nome: str
    pronto: bool
    detalhe: str
    #: Comando ou acção que resolve. `None` quando não há nada a fazer senão
    #: esperar (um carregamento em curso) ou quando está pronto.
    remedio: str | None = None
    #: O que custa quando não está pronto e alguém o pede. Em segundos, e
    #: medido — é o que a interface mostra antes de o utilizador escolher.
    custo_s: float | None = None


def manifesto_cru(caminho: str = CAMINHO_INDICE) -> tuple[dict | None, str]:
    """Lê o manifesto do disco. Devolve `(dados, motivo_se_falhou)`."""
    npy, man = f"{caminho}.npy", f"{caminho}.manifest.json"
    if not os.path.exists(npy) or not os.path.exists(man):
        return None, "ausente: não há índice em disco"
    try:
        with open(man, encoding="utf-8") as f:
            return json.load(f), ""
    except (OSError, json.JSONDecodeError) as e:
        return None, f"ilegível: {e}"


def _como_manifesto(bruto: object) -> Manifesto | str:
    """O `Manifesto`, ou a razão por que não é um. É a 2.ª saída do `Index.load`.

    Existe porque ler o manifesto **por chave** não era a mesma verificação que
    o `Index.load` faz. Ele constrói um `Manifesto(**m)`, logo recusa tanto o
    campo a menos como o campo **a mais** — ambos `TypeError` —, e o
    diagnóstico, que procurava as chaves que queria e ignorava as outras,
    aceitava um manifesto que a produção recusa.

    **O lado optimista era o errado.** O `/api/estado` dava o índice por pronto,
    o portão I3 ficava satisfeito, e a pergunta seguinte reconstruía 6,4 min —
    a interface a afirmar saúde sobre a peça prestes a custar a maior espera do
    sistema. E era alcançável: o `copiar_artefactos` leva o manifesto do
    checkout de trabalho para o do serviço, o `recuar` leva o código para uma
    etiqueta anterior, e o `manifesto_aceite` — a verificação que o portão D6
    corre **antes** do reinício — chama este diagnóstico.

    Medido em `docs/twowayflow/manifesto-decisao.md` §4, e prendido pelo caso
    `{"extra": ...}` do `test_paridade_com_o_index_load`.

    Devolve o `Manifesto` ou a mensagem, em vez de levantar: quem chama tem de
    responder ao `/api/estado` sempre, e uma excepção aqui rebentava o único
    canal que a interface tem para dizer o que está mal.
    """
    try:
        return Manifesto(**bruto)  # type: ignore[arg-type]
    except TypeError:
        pass
    nomes = {f.name for f in fields(Manifesto)}
    if not isinstance(bruto, dict):
        return (f"manifesto não é um objecto: é {type(bruto).__name__}")
    sobram = sorted(set(bruto) - nomes)
    faltam = sorted(nomes - set(bruto))
    # «campo a mais» primeiro, e nomeado: é o caso que não dá erro nenhum em
    # lado nenhum — o índice até funcionaria — e por isso o que mais precisa de
    # ser dito. O remédio é reconstruir, que é o que o `Index.load` já faz.
    partes = []
    if sobram:
        partes.append(f"campo a mais: {sobram} — o `Index.load` recusa-o")
    if faltam:
        partes.append(f"sem o campo {faltam}")
    return "manifesto com forma errada: " + "; ".join(partes or ["razão desconhecida"])


def diagnosticar_indice(chunks, assinatura: str, *,
                        encoder: str = ENCODER,
                        caminho: str = CAMINHO_INDICE) -> tuple[bool, str]:
    """Diz se o índice em disco é de confiança e, se não for, **qual** campo falha.

    A ordem das verificações é a do `Index.load`, de propósito: é o que faz o
    teste de paridade comparar a mesma decisão e não uma parecida.
    """
    bruto, erro = manifesto_cru(caminho)
    if bruto is None:
        return False, erro
    m = _como_manifesto(bruto)
    if isinstance(m, str):
        return False, m
    if m.encoder != encoder:
        return False, (f"encoder diferente: o índice é de «{m.encoder}», "
                       f"o sistema usa «{encoder}»")
    if m.assinatura != assinatura:
        return False, ("corpus mudou: a assinatura do `corpus.jsonl` não é "
                       "a que gerou o índice")
    if m.n_chunks != len(chunks):
        return False, (f"contagem diferente: o índice tem {m.n_chunks} "
                       f"chunks, o corpus tem {len(chunks)}")
    esperado = [[c.poem_id, c.chunk_ix] for c in chunks]
    if m.chunk_ids != esperado:
        return False, ("ordem dos documentos mudou: os ids do índice são "
                       "posicionais, logo a ordem é parte da chave")
    # A forma dos vectores é a última verificação do `Index.load`, e a
    # única que obriga a tocar no `.npy`. O `mmap_mode="r"` lê o cabeçalho
    # e deixa os 7,0 MB em disco — perguntar o estado não carrega nada.
    import numpy as np
    forma = np.load(f"{caminho}.npy", mmap_mode="r").shape
    if forma != (len(chunks), m.dim):
        return False, (f"forma dos vectores: {forma}, esperado "
                       f"{(len(chunks), m.dim)}")
    return True, (f"{m.n_chunks} chunks · {m.encoder} · dim {m.dim}")


def componente_ollama(gerador) -> Componente:
    """O Ollama responde? É a falha mais provável de todas."""
    if not gerador.disponivel():
        return Componente(
            "ollama", False, f"não responde em {gerador.url_base}",
            remedio="ollama serve")
    return Componente("ollama", True, gerador.url_base)


def componente_modelo(gerador, ollama_pronto: bool) -> Componente:
    """O modelo está instalado? Só se pergunta com o Ollama de pé.

    Sem esta condição, um Ollama em baixo produzia **duas** linhas vermelhas
    para uma causa só, e a segunda era falsa: não se sabe se o modelo está
    instalado quando não há quem responda.
    """
    if not ollama_pronto:
        return Componente("modelo", False,
                          f"indeterminado: sem o Ollama não se sabe "
                          f"(«{gerador.modelo}»)")
    if not gerador.modelo_instalado():
        return Componente("modelo", False, f"«{gerador.modelo}» não instalado",
                           remedio=f"ollama pull {gerador.modelo}")
    return Componente("modelo", True, gerador.modelo)


def componente_corpus(caminho: str = CAMINHO_CORPUS) -> Componente:
    """O `corpus.jsonl` é a fronteira do sistema: sem ele não há nada a jusante."""
    if not os.path.exists(caminho):
        return Componente("corpus", False, f"{caminho} não existe",
                          remedio="constrói-se no arranque, dos 2083 .txt",
                          custo_s=40.0)
    return Componente("corpus", True, caminho)
