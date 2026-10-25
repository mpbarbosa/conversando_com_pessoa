"""Portão **I6** — `data/sessoes.db` não contém corpos de poemas.

O enunciado está no §7 da [Fase 6](../docs/FASE-6.md): «varrimento da base por
qualquer linha de corpo de qualquer poema do corpus: **zero** acertos». A razão
é de direitos e está no §3.3 — os 2083 ficheiros estão num repositório público
com os termos de uso do Arquivo Pessoa **não confirmados**, e uma base de
sessões com poemas lá dentro era um ficheiro novo com o mesmo problema, mais
fácil de partilhar por distracção.

## Porque é que este portão é fácil de passar sem o cumprir

A `fonte` guarda `poem_id` e `chunk_ix`, logo quem olhe para o esquema conclui
que não há corpos e vai para casa. **Há um caminho por onde entram:** o
`mensagem.texto` de um turno é o poema **gerado**, e o portão I7′ do
[`PRODUCAO.md`](../docs/PRODUCAO.md) §2.1 descobriu que numa cópia **à letra**
o verso gerado **é** o verso de Pessoa. Uma tentativa plagiada gravada em cru é
corpo de poema em disco.

É por isso que o `sessoes.py` grava o turno **já redigido** — o que foi ao fio,
depois do `redigir` — e não o `Turno` do domínio. Este ficheiro mede as duas
coisas: que a base fica limpa (o portão) e que o varrimento **morde** quando
ela não está (o instrumento). A segunda é a que falta na maior parte dos
portões desta casa, e o `CONTROLO.md` §4 regista três defeitos de instrumento
para provar que faz falta.
"""
from __future__ import annotations

import sqlite3

import pytest
from fastapi.testclient import TestClient

from src.web import serial
from src.web.app import Servico, criar_app
from src.web.retencao import normalizar
from src.web.sessoes import Arquivo

from .test_i7 import GeradorPlagiador, _sessao_do_fluxo, chunks_caeiro  # noqa: F401
from .test_i7 import corpo, corpus  # noqa: F401
from .test_pipeline import _pipeline

#: As tabelas que a base tem hoje. **Não é documentação: é o portão**, pela
#: mesma mecânica do `ROTAS_COBERTAS` do `test_i7.py`. O varrimento enumera o
#: `sqlite_master`, logo cobre uma tabela nova sem mudar de código — mas uma
#: tabela nova é uma decisão de direitos nova, e esta lista obriga a olhar para
#: ela em vez de a herdar em silêncio.
TABELAS = {"esquema_versao", "sessao", "mensagem", "turno_reg",
           "tentativa_reg", "fonte", "proposta_reg", "sqlite_sequence"}


def _tabelas(caminho: str) -> set[str]:
    c = sqlite3.connect(caminho)
    try:
        return {r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'")}
    finally:
        c.close()


def _texto_da_base(caminho: str) -> str:
    """Todo o texto de todas as colunas de todas as tabelas, num agulheiro.

    Enumera as tabelas pelo `sqlite_master` e as colunas pelo `row_factory`:
    uma coluna nova entra no varrimento sem ninguém se lembrar dela. O
    `\\x00` entre valores existe para que uma linha de corpo não case **através**
    da fronteira de dois valores — o mesmo cuidado que o `varrer` do
    `test_i7.py` tem entre agulheiros, e pela mesma razão.
    """
    c = sqlite3.connect(caminho)
    c.row_factory = sqlite3.Row
    try:
        valores: list[str] = []
        for tabela in sorted(_tabelas(caminho)):
            for linha in c.execute(f"SELECT * FROM {tabela}"):  # noqa: S608
                valores.extend(v for v in tuple(linha) if isinstance(v, str))
    finally:
        c.close()
    return "\x00".join(normalizar(v) for v in valores)


def varrer_base(caminho: str, corpo: frozenset[str]) -> list[str]:
    """As linhas de corpo que estão na base. Vazio é o que o portão pede."""
    agulheiro = _texto_da_base(caminho)
    return sorted(ln for ln in corpo if ln in agulheiro)


@pytest.fixture
def base(tmp_path):
    return str(tmp_path / "sessoes.db")


def _gerar_plagiando(chunks, base: str) -> tuple[str, str]:
    """Uma geração que copia o 1.º poema do contexto. Devolve `(fluxo, sid)`."""
    alvo = chunks[0]
    pipeline = _pipeline(chunks, GeradorPlagiador(alvo.text))
    pipeline.reranker = None
    servico = Servico(gerador=pipeline.gerador, pipeline=pipeline,
                      arquivo=Arquivo(base))
    with TestClient(criar_app(servico)) as cliente, \
            cliente.stream("POST", "/api/perguntar",
                           json={"pergunta": "o que é a natureza?",
                                 "voz": "caeiro"}) as r:
        fluxo = r.read().decode("utf-8")
    sid = _sessao_do_fluxo(fluxo)
    assert sid is not None, "a geração não gravou sessão nenhuma"
    return fluxo, sid


# --- o portão -------------------------------------------------------------- #

def test_i6_o_varrimento_cobre_todas_as_tabelas(base):
    """Uma tabela nova faz isto falhar, e é esse o mecanismo."""
    Arquivo(base).preparar()
    assert _tabelas(base) == TABELAS, (
        "o esquema mudou de tabelas e o portão I6 não foi reconsiderado: "
        f"novas={_tabelas(base) - TABELAS} desaparecidas={TABELAS - _tabelas(base)}")


def test_i6_a_base_nao_contem_corpos_de_poemas(chunks_caeiro, corpo, base):
    """O portão, no caso em que ele pode falhar: o gerador copiou à letra."""
    _gerar_plagiando(chunks_caeiro, base)
    acertos = varrer_base(base, corpo)
    assert acertos == [], f"corpo na base: {acertos[:3]}"


def test_i6_a_base_fica_com_a_tentativa_plagiada_registada(chunks_caeiro, base):
    """E não passa por **não gravar nada**, que era a maneira fácil.

    A 5Y é a razão da `tentativa_reg`: guardar só a resposta final contaminou
    nove fases emparelhadas. Um portão de direitos cumprido às custas desse
    registo trocava um defeito por outro, logo mede-se que a tentativa
    reprovada **está** lá — com o plágio assinalado e sem o verso.
    """
    _, sid = _gerar_plagiando(chunks_caeiro, base)
    sessao = Arquivo(base).ler_sessao(sid)
    assert sessao is not None
    turnos = [m["turno"] for m in sessao["mensagens"] if "turno" in m]
    assert turnos, "a geração não deixou turno nenhum"
    with sqlite3.connect(base) as c:
        tentativas = c.execute(
            "SELECT n, plagiou, fracao_copiada FROM tentativa_reg "
            "ORDER BY n").fetchall()
    assert tentativas, "nenhuma tentativa registada"
    assert any(t[1] for t in tentativas), (
        "o gerador copiou à letra e nenhuma tentativa ficou marcada como "
        "plágio: ou o registo perdeu-se, ou a guarda deixou de morder")
    assert turnos[0]["fontes"], "as fontes do turno não ficaram registadas"


def test_i6_a_tentativa_reprovada_nao_guarda_texto_nenhum(base):
    """**A protecção real da tentativa plagiada, e não é a retenção.**

    O verso copiado à letra vive no `historico[n].texto`, e o §3.2 do plano não
    lhe deu coluna: a `tentativa_reg` guarda `n`, os três ingredientes do
    veredicto, a fracção copiada e os motivos — **nenhum texto**. É isso que
    põe a tentativa reprovada fora do alcance do portão, e não o `redigir`.

    Medido ao escrever este ficheiro: numa geração que copia à letra, a 1.ª
    tentativa tem **6** linhas de corpo e a 2.ª zero, e o texto final (que a
    `mensagem` guarda) é limpo porque o `_repetir_sem` tirou os poemas do
    contexto. Logo a base passa o I6 **por omissão de coluna**, que é a
    protecção mais forte que há — não há o que redigir no que não se guarda.

    Este teste existe para que acrescentar `texto` à `tentativa_reg` deixe de
    ser uma linha de SQL distraída e passe a ser um teste vermelho.
    """
    Arquivo(base).preparar()
    c = sqlite3.connect(base)
    try:
        colunas = {r[1] for r in c.execute("PRAGMA table_info(tentativa_reg)")}
    finally:
        c.close()
    assert "texto" not in colunas, (
        "a `tentativa_reg` ganhou uma coluna de texto: é por ali que o verso "
        "copiado à letra entra na base, e o portão I6 passa a depender de "
        "alguém se lembrar de a redigir")
    assert colunas == {"id", "turno_id", "n", "veredicto_ok", "plagiou",
                       "truncada", "fracao_copiada", "motivos"}


def test_i6_o_varrimento_morde_se_a_base_tiver_corpo(chunks_caeiro, corpo, base):
    """**O instrumento.** Uma base com corpo tem de ser acusada.

    Sintético e declarado: grava-se um turno cujo `texto` **é** um poema do
    corpus. Nenhum caminho da aplicação produz isto hoje — o teste acima
    explica porquê —, e é precisamente por isso que o varrimento precisa de uma
    prova própria de que morde. Sem ela, os três testes anteriores podiam estar
    verdes por o varrimento não varrer nada, que é o defeito que o `varrer` do
    `test_i7.py` teve na primeira versão (verde com a retenção desligada).
    """
    alvo = chunks_caeiro[0]
    pipeline = _pipeline(chunks_caeiro, GeradorPlagiador(alvo.text))
    pipeline.reranker = None
    turno = pipeline.responder("o que é a natureza?", alvo.voice)
    publicado = serial.turno(turno)
    publicado["texto"] = alvo.text          # a mutação, e é só esta linha
    arquivo = Arquivo(base)
    sid = arquivo.criar_sessao(voz="caeiro", idioma="pt", modelo="duplo",
                               rerank=False, auto=False)
    arquivo.registar_turno(sid, publicado)
    acertos = varrer_base(base, corpo)
    assert acertos, ("o varrimento não acusou uma base com um poema do corpus "
                     "na coluna `mensagem.texto`, logo não está a medir o "
                     "portão I6")
