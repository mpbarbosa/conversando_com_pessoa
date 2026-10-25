"""O arquivo das sessões, e as duas rotas que o publicam. Passo 8 da Fase 6.

O portão **I6** — corpos de poemas — tem ficheiro próprio
([`test_i6.py`](test_i6.py)). Aqui está o resto: o esquema, as gravações, as
leituras, e as três decisões que são fáceis de desfazer sem ninguém notar —
as chaves estrangeiras ligadas por ligação, o `aceite` anulável do roteador, e
uma falha de gravação que **não** mata uma geração de 30 s.
"""
from __future__ import annotations

import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from src.web import serial
from src.web.app import Servico, criar_app
from src.web.sessoes import VERSAO, Arquivo, ErroDeEsquema, abrir

from .test_perguntar import GeradorDeterminista
from .test_pipeline import _pipeline
from .test_i7 import chunks_caeiro, corpus  # noqa: F401


@pytest.fixture
def base(tmp_path):
    return str(tmp_path / "sessoes.db")


@pytest.fixture
def arquivo(base):
    return Arquivo(base)


@pytest.fixture
def sessao(arquivo):
    return arquivo.criar_sessao(voz="caeiro", idioma="pt", modelo="duplo",
                                rerank=False, auto=True)


def _turno(chunks, gerador=None):
    """Um turno real, publicado como o fio o publica."""
    pipeline = _pipeline(chunks, gerador or GeradorDeterminista())
    pipeline.reranker = None
    return serial.turno(pipeline.responder("o que é a natureza?",
                                           chunks[0].voice))


# --- 1. o esquema ---------------------------------------------------------- #

def test_abrir_cria_o_ficheiro_e_a_versao(base):
    c = abrir(base)
    try:
        assert c.execute("SELECT versao FROM esquema_versao").fetchone()[0] == VERSAO
    finally:
        c.close()


def test_abrir_duas_vezes_nao_duplica_a_versao(base):
    """O `IF NOT EXISTS` do guião protege as tabelas; a versão é um `INSERT`."""
    abrir(base).close()
    c = abrir(base)
    try:
        assert c.execute("SELECT COUNT(*) FROM esquema_versao").fetchone()[0] == 1
    finally:
        c.close()


def test_uma_versao_diferente_levanta_em_vez_de_migrar(base):
    """A lição do manifesto do índice: «não dá erro — dá respostas erradas».

    Migrar às cegas uma base de outra versão era ler colunas que podem não
    significar o mesmo. Levanta, e diz as duas versões.
    """
    abrir(base).close()
    with sqlite3.connect(base) as c:
        c.execute("UPDATE esquema_versao SET versao = 99")
    with pytest.raises(ErroDeEsquema) as e:
        abrir(base)
    assert "99" in str(e.value) and str(VERSAO) in str(e.value)


def test_as_chaves_estrangeiras_estao_ligadas_na_ligacao(base):
    """**A decisão 3**, e é a que é fácil de desfazer sem notar.

    `PRAGMA foreign_keys` é de **ligação**: declarado no `esquema.sql`
    aplicava-se à ligação que correu o guião e a mais nenhuma, e as chaves
    ficavam declaradas e desligadas. Mede-se pela ligação, e mede-se a morder:
    uma mensagem de uma sessão inexistente tem de ser recusada.
    """
    c = abrir(base)
    try:
        assert c.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError):
            c.execute("INSERT INTO mensagem (sessao_id, ordem, papel, texto, "
                      "criada_em) VALUES ('nao-existe', 0, 'bot', 'x', 'y')")
    finally:
        c.close()


def test_o_pragma_nao_esta_no_ficheiro_de_esquema():
    """E que ninguém o «arrume» para lá, onde não faz nada."""
    from src.web.sessoes import ESQUEMA
    sql = ESQUEMA.read_text(encoding="utf-8")
    assert "PRAGMA foreign_keys" not in sql.upper().replace("-- ", "@@ ") or True
    activas = [ln for ln in sql.splitlines()
               if not ln.strip().startswith("--")
               and "PRAGMA" in ln.upper()]
    assert activas == [], f"pragma num guião de esquema não se aplica: {activas}"


# --- 2. gravar ------------------------------------------------------------- #

def test_criar_sessao_guarda_a_configuracao(arquivo):
    sid = arquivo.criar_sessao(voz="reis", idioma="pt", modelo="llama3.1:8b",
                               rerank=True, auto=False)
    s = arquivo.ler_sessao(sid)
    assert s["voz_inicial"] == "reis"
    assert s["modelo"] == "llama3.1:8b"
    assert s["rerank_ligado"] is True and s["auto_ligado"] is False


def test_as_mensagens_ficam_pela_ordem(arquivo, sessao):
    arquivo.registar_mensagem(sessao, "utilizador", "primeira")
    arquivo.registar_mensagem(sessao, "sistema", "voz trocada")
    arquivo.registar_mensagem(sessao, "utilizador", "segunda")
    ordens = [(m["ordem"], m["papel"]) for m in
              arquivo.ler_sessao(sessao)["mensagens"]]
    assert ordens == [(0, "utilizador"), (1, "sistema"), (2, "utilizador")]


def test_registar_turno_achata_o_turno(arquivo, sessao, chunks_caeiro):
    publicado = _turno(chunks_caeiro)
    arquivo.registar_turno(sessao, publicado)
    s = arquivo.ler_sessao(sessao)
    msg = s["mensagens"][-1]
    assert msg["papel"] == "bot" and msg["texto"] == publicado["texto"]
    t = msg["turno"]
    assert t["voz"] == publicado["voz"]
    assert t["aprovado"] == publicado["aprovado"]
    assert t["tentativas"] == publicado["tentativas"]
    assert t["prefill_s"] == publicado["resposta"]["prefill_s"]
    assert t["fracao_copiada"] == publicado["plagio"]["fracao_copiada"]


def test_as_fontes_guardam_ids_e_o_papel(arquivo, sessao, chunks_caeiro):
    """Ids, nunca corpos (§3.3) — e o `papel`, que não é redundante."""
    publicado = _turno(chunks_caeiro)
    arquivo.registar_turno(sessao, publicado)
    fontes = arquivo.ler_sessao(sessao)["mensagens"][-1]["turno"]["fontes"]
    assert fontes, "o turno não deixou fontes"
    assert {f["papel"] for f in fontes} <= {"usado", "recuperado"}
    assert all(isinstance(f["poem_id"], str) for f in fontes)
    assert [f["poem_id"] for f in fontes] == [
        f["poem_id"] for f in publicado["fontes"]]


def test_as_tentativas_ficam_todas(arquivo, sessao, chunks_caeiro):
    """A 5Y é a razão: guardar só a última contaminou nove fases."""
    publicado = _turno(chunks_caeiro)
    turno_id = arquivo.registar_turno(sessao, publicado)
    with sqlite3.connect(arquivo.caminho) as c:
        linhas = c.execute("SELECT n FROM tentativa_reg WHERE turno_id = ? "
                           "ORDER BY n", (turno_id,)).fetchall()
    assert [r[0] for r in linhas] == [t["n"] for t in publicado["historico"]]


def test_um_turno_meio_gravado_nao_fica(arquivo, sessao, chunks_caeiro):
    """Uma transacção só: `tentativa_reg` sem o pai é o registo que a 5Y
    queria e não teria. Força-se a falha com uma fonte sem `poem_id`."""
    publicado = _turno(chunks_caeiro)
    publicado["fontes"] = [{"poem_id": None, "chunk_ix": 0, "papel": "usado"}]
    with pytest.raises(sqlite3.IntegrityError):
        arquivo.registar_turno(sessao, publicado)
    s = arquivo.ler_sessao(sessao)
    assert [m for m in s["mensagens"] if m["papel"] == "bot"] == []
    with sqlite3.connect(arquivo.caminho) as c:
        assert c.execute("SELECT COUNT(*) FROM turno_reg").fetchone()[0] == 0
        assert c.execute("SELECT COUNT(*) FROM tentativa_reg").fetchone()[0] == 0


def test_o_aceite_do_roteador_e_nulo_quando_nao_houve_decisao(
        arquivo, sessao, chunks_caeiro):
    """§3.5, e a ressalva que eu acrescentei ao plano.

    `voz: None` é «o roteador não teve opinião». Guardar `aceite = 0` ali
    lia-se como «o utilizador recusou a proposta» — e estes dados existem
    **para** serem lidos como rótulos, logo um 0 falso é pior que um nulo.
    """
    publicado = _turno(chunks_caeiro)
    for proposta, esperado in (
            ({"voz": None, "bruto": "?", "segundos": 0.4, "decidiu": False}, None),
            ({"voz": publicado["voz"], "bruto": "caeiro", "segundos": 0.5,
              "decidiu": True}, 1),
            ({"voz": "reis", "bruto": "reis", "segundos": 0.5,
              "decidiu": True}, 0)):
        sid = arquivo.criar_sessao(voz="caeiro", idioma="pt", modelo="duplo",
                                   rerank=False, auto=True)
        turno_id = arquivo.registar_turno(sid, publicado, proposta)
        with sqlite3.connect(arquivo.caminho) as c:
            linha = c.execute("SELECT voz_proposta, voz_usada, aceite FROM "
                              "proposta_reg WHERE turno_id = ?",
                              (turno_id,)).fetchone()
        assert linha[2] == esperado, f"{proposta['voz']} → aceite {linha[2]}"


def test_sem_roteador_nao_ha_linha_de_proposta(arquivo, sessao, chunks_caeiro):
    turno_id = arquivo.registar_turno(sessao, _turno(chunks_caeiro))
    with sqlite3.connect(arquivo.caminho) as c:
        assert c.execute("SELECT COUNT(*) FROM proposta_reg WHERE turno_id = ?",
                         (turno_id,)).fetchone()[0] == 0


# --- 3. ler ---------------------------------------------------------------- #

def test_listar_traz_a_primeira_pergunta_e_a_contagem(arquivo, sessao):
    arquivo.registar_mensagem(sessao, "utilizador", "quem sou eu?")
    arquivo.registar_mensagem(sessao, "sistema", "voz trocada")
    s = arquivo.listar_sessoes()[0]
    assert s["primeira_pergunta"] == "quem sou eu?"
    assert s["n_mensagens"] == 2


def test_listar_nao_estoura_numa_sessao_sem_perguntas(arquivo, sessao):
    assert arquivo.listar_sessoes()[0]["primeira_pergunta"] is None


def test_ler_uma_sessao_que_nao_existe_devolve_none(arquivo):
    assert arquivo.ler_sessao("nao-existe") is None


def test_existe_separa_reabrir_de_abrir_outra(arquivo, sessao):
    assert arquivo.existe(sessao) is True
    assert arquivo.existe("nao-existe") is False


# --- 4. as rotas ----------------------------------------------------------- #

@pytest.fixture
def cliente(chunks_caeiro, base):
    pipeline = _pipeline(chunks_caeiro, GeradorDeterminista())
    pipeline.reranker = None
    servico = Servico(gerador=pipeline.gerador, pipeline=pipeline,
                      arquivo=Arquivo(base))
    with TestClient(criar_app(servico)) as c:
        yield c


def _perguntar(cliente, pergunta="o que é a natureza?", **extra):
    with cliente.stream("POST", "/api/perguntar",
                        json={"pergunta": pergunta, "voz": "caeiro", **extra}
                        ) as r:
        bruto = r.read().decode("utf-8")
    return [json.loads(ln) for ln in bruto.split("\n") if ln]


def test_o_primeiro_evento_do_fluxo_nomeia_a_sessao(cliente):
    eventos = _perguntar(cliente)
    assert eventos[0]["tipo"] == "sessao"
    assert eventos[0]["sessao_id"]


def test_a_segunda_pergunta_continua_a_mesma_sessao(cliente):
    sid = _perguntar(cliente)[0]["sessao_id"]
    eventos = _perguntar(cliente, "e o tempo?", sessao_id=sid)
    assert eventos[0]["sessao_id"] == sid
    corpo = cliente.get(f"/api/sessoes/{sid}").json()
    papeis = [m["papel"] for m in corpo["mensagens"]]
    assert papeis == ["utilizador", "bot", "utilizador", "bot"]


def test_uma_sessao_que_ja_nao_existe_abre_outra_e_di_lo(cliente):
    """Um id guardado de uma base apagada não é um erro do utilizador."""
    eventos = _perguntar(cliente, sessao_id="nao-existe")
    assert eventos[0]["tipo"] == "sessao"
    assert eventos[0]["sessao_id"] not in (None, "nao-existe")


def test_a_pergunta_fica_gravada_mesmo_sem_resposta(cliente, base):
    """A sessão abre **antes** de gerar: uma pergunta abortada foi feita.

    Um histórico que só guarda o que correu bem mente sobre o uso — e é o
    espelho da `tentativa_reg`, que existe porque guardar só o fim contaminou
    nove fases (5Y).
    """
    sid = _perguntar(cliente)[0]["sessao_id"]
    with sqlite3.connect(base) as c:
        n = c.execute("SELECT COUNT(*) FROM mensagem WHERE papel = "
                      "'utilizador' AND sessao_id = ?", (sid,)).fetchone()[0]
    assert n == 1


def test_a_rota_de_uma_sessao_desconhecida_da_404_com_remedio(cliente):
    r = cliente.get("/api/sessoes/nao-existe")
    assert r.status_code == 404
    assert r.json()["detail"]["erro"] == "sessao_desconhecida"
    assert "remedio" in r.json()["detail"]


def test_a_listagem_vem_da_mais_recente_para_a_mais_antiga(cliente):
    primeira = _perguntar(cliente, "a primeira")[0]["sessao_id"]
    segunda = _perguntar(cliente, "a segunda")[0]["sessao_id"]
    ids = [s["id"] for s in cliente.get("/api/sessoes").json()["sessoes"]]
    assert ids.index(segunda) < ids.index(primeira)


def test_um_turno_por_pergunta_e_nao_um_por_tentativa(cliente, base):
    """O evento `turno` sai por tentativa (§4.4); a gravação é do último.

    Sem isto, a contagem de perguntas do histórico passava a depender de
    quantas vezes o modelo plagiou.
    """
    _perguntar(cliente)
    with sqlite3.connect(base) as c:
        assert c.execute("SELECT COUNT(*) FROM turno_reg").fetchone()[0] == 1


# --- 5. falhar a gravar não mata a geração --------------------------------- #

def test_uma_falha_de_gravacao_nao_quebra_a_resposta(chunks_caeiro, tmp_path):
    """**A decisão 5.** Perder 30 s de resposta por causa do disco é pior.

    Aponta-se o arquivo a um caminho impossível — um ficheiro onde devia estar
    a pasta — e exige-se que o fluxo continue a dar um `turno` aprovado.
    """
    bloqueio = tmp_path / "ficheiro"
    bloqueio.write_text("não sou uma pasta")
    pipeline = _pipeline(chunks_caeiro, GeradorDeterminista())
    pipeline.reranker = None
    servico = Servico(gerador=pipeline.gerador, pipeline=pipeline,
                      arquivo=Arquivo(str(bloqueio / "sessoes.db")))
    with TestClient(criar_app(servico)) as cliente:
        eventos = _perguntar(cliente)
        assert eventos[0] == {"tipo": "sessao", "sessao_id": None}
        assert eventos[-1]["tipo"] == "turno"
        assert eventos[-1]["turno"]["aprovado"] is True
        # E a avaria fica à vista no sítio onde esta casa põe as avarias.
        componentes = {c["nome"]: c for c in
                       cliente.get("/api/estado").json()["componentes"]}
        assert componentes["sessoes"]["pronto"] is False
        assert "falhou" in componentes["sessoes"]["detalhe"]


def test_o_arquivo_em_baixo_nao_impede_de_perguntar(chunks_caeiro, tmp_path):
    """O `sessoes` não está em `EXIGIDOS`: sem histórico ainda há respostas."""
    bloqueio = tmp_path / "ficheiro"
    bloqueio.write_text("não sou uma pasta")
    pipeline = _pipeline(chunks_caeiro, GeradorDeterminista())
    pipeline.reranker = None
    servico = Servico(gerador=pipeline.gerador, pipeline=pipeline,
                      arquivo=Arquivo(str(bloqueio / "sessoes.db")))
    with TestClient(criar_app(servico)) as cliente:
        _perguntar(cliente)
        assert cliente.get("/api/estado").json()["pode_perguntar"] is True


def test_a_rota_de_listagem_responde_503_com_a_base_ilegivel(chunks_caeiro,
                                                             tmp_path):
    """Uma base ilegível é uma peça em baixo, não um 500 do serviço."""
    bloqueio = tmp_path / "ficheiro"
    bloqueio.write_text("não sou uma pasta")
    pipeline = _pipeline(chunks_caeiro, GeradorDeterminista())
    pipeline.reranker = None
    servico = Servico(gerador=pipeline.gerador, pipeline=pipeline,
                      arquivo=Arquivo(str(bloqueio / "sessoes.db")))
    with TestClient(criar_app(servico), raise_server_exceptions=False) as c:
        r = c.get("/api/sessoes")
    assert r.status_code == 503
    assert r.json()["detail"]["erro"] == "sessoes_indisponiveis"
