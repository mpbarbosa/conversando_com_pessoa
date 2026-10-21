"""O portão I3 da Fase 6: a interface não diz pronto o que não está.

Dois riscos, e só o segundo é óbvio.

O óbvio: o `/api/estado` mente, e a página mostra-se pronta com o Ollama em
baixo. Testa-se com um gerador falso.

O que não é óbvio, e é o que este ficheiro gasta mais linhas a cobrir: o
diagnóstico do índice (`src/web/estado.py`) **reimplementa** a comparação do
`Index.load`, porque o `Index.load` devolve `None` e não diz qual dos cinco
campos falhou — e «índice desactualizado» manda reconstruir 6,4 minutos sem
dizer o que mudou. Duas versões da mesma regra divergem; a defesa é o teste de
paridade abaixo, na disciplina do `tests/test_grafo.py`.

E um terceiro, que é de desempenho mas tem consequência de honestidade:
consultar o estado **não pode carregar nada**. Se carregasse, o `/api/estado`
deixava de responder durante uma geração, que é o que o portão I4 exige — e a
interface ficava sem o único canal que tem para dizer «estou viva» nos 19 s de
prefill.
"""
from __future__ import annotations

import json

import numpy as np
import pytest
from fastapi.testclient import TestClient

from src.corpus.models import Chunk, Lang, Voice
from src.generation.ollama import MODELO
from src.retrieval.index import Index, Manifesto
from src.tokens import ENCODER
from src.web.app import Servico, criar_app
from src.web.estado import diagnosticar_indice

# --- duplos ----------------------------------------------------------------- #


class GeradorFalso:
    """Um Ollama de mentira, com os dois estados que o CLI já distingue."""

    def __init__(self, vivo: bool = True, instalado: bool = True,
                 modelo: str = MODELO):
        self._vivo, self._instalado = vivo, instalado
        self.modelo = modelo
        self.url_base = "http://127.0.0.1:11434"
        self.nome = modelo

    def disponivel(self) -> bool:
        return self._vivo

    def modelo_instalado(self) -> bool:
        return self._instalado


def _cliente(gerador=None) -> TestClient:
    return TestClient(criar_app(Servico(gerador or GeradorFalso())))


def _comp(corpo: dict, nome: str) -> dict:
    return next(c for c in corpo["componentes"] if c["nome"] == nome)


CHUNKS = [
    Chunk("poem_1", 0, "verso um", "A — T\nverso um", Voice.CAEIRO, Lang.PT, 2),
    Chunk("poem_2", 0, "verso dois", "A — T\nverso dois", Voice.CAEIRO, Lang.PT, 2),
]
ASSINATURA = "assinatura-de-teste"


def _escrever_indice(tmp_path, *, encoder=ENCODER, assinatura=ASSINATURA,
                     chunks=None, dim=4, ids=None, n_chunks=None, extra=None):
    """Escreve um índice em disco, com os campos que o teste quiser torcer.

    `extra` acrescenta chaves que o `Manifesto` não tem. É o caso que a
    paridade não cobria: o `Index.load` recusa-o no `Manifesto(**m)` e o
    diagnóstico, que lia por chave, aceitava-o.
    """
    chunks = CHUNKS if chunks is None else chunks
    caminho = str(tmp_path / "index")
    m = Manifesto(
        encoder=encoder, dim=dim, assinatura=assinatura,
        n_chunks=len(chunks) if n_chunks is None else n_chunks,
        chunk_ids=([[c.poem_id, c.chunk_ix] for c in chunks]
                   if ids is None else ids))
    bruto = dict(m.__dict__)
    if extra:
        bruto.update(extra)
    np.save(f"{caminho}.npy", np.zeros((len(chunks), dim), dtype="float32"))
    with open(f"{caminho}.manifest.json", "w", encoding="utf-8") as f:
        json.dump(bruto, f)
    return caminho


# --- I3: o estado é honesto ------------------------------------------------- #

def test_ollama_em_baixo_aparece_com_o_comando_que_o_resolve():
    r = _cliente(GeradorFalso(vivo=False)).get("/api/estado")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["pronto"] is False
    o = _comp(corpo, "ollama")
    assert o["pronto"] is False
    assert o["remedio"] == "ollama serve"


def test_modelo_nao_instalado_traz_o_pull():
    corpo = _cliente(GeradorFalso(instalado=False)).get("/api/estado").json()
    m = _comp(corpo, "modelo")
    assert m["pronto"] is False
    assert m["remedio"] == f"ollama pull {MODELO}"


def test_sem_ollama_o_modelo_fica_indeterminado_e_nao_falso():
    """Uma causa, uma linha vermelha.

    Com o Ollama em baixo não se **sabe** se o modelo está instalado, e dizer
    «não instalado» era inventar um segundo problema a partir do primeiro.
    """
    corpo = _cliente(GeradorFalso(vivo=False, instalado=True)).get(
        "/api/estado").json()
    m = _comp(corpo, "modelo")
    assert m["pronto"] is False
    assert "indeterminado" in m["detalhe"]
    assert m["remedio"] is None


def test_roteador_e_reranker_nao_contam_para_pronto():
    """São escolhas, não requisitos.

    Tratá-los como requisito dizia «não pronto» a um sistema que responde
    perfeitamente — e empurrava o utilizador para pagar 20 s e 2,6 s que a
    medição diz serem opcionais.
    """
    corpo = _cliente().get("/api/estado").json()
    assert _comp(corpo, "roteador")["pronto"] is False
    assert _comp(corpo, "reranker")["pronto"] is False
    exigidos = {"ollama", "modelo", "corpus", "indice"}
    assert corpo["pronto"] == all(
        c["pronto"] for c in corpo["componentes"] if c["nome"] in exigidos)


def test_o_custo_das_esperas_vai_declarado():
    """§4.2: as quatro esperas, com o número à frente e não uma surpresa."""
    corpo = _cliente().get("/api/estado").json()
    assert _comp(corpo, "roteador")["custo_s"] == 20.0
    assert _comp(corpo, "reranker")["custo_s"] == 2.6


# --- I3: o diagnóstico do índice nomeia o campo ----------------------------- #

@pytest.mark.parametrize("torcer,esperado", [
    ({"encoder": "outro/encoder"}, "encoder"),
    ({"assinatura": "outra"}, "corpus mudou"),
    ({"n_chunks": 99}, "contagem"),
    ({"ids": [["poem_2", 0], ["poem_1", 0]]}, "ordem"),
    # O campo a mais **nomeia-se**, porque é o único que não dá erro em lado
    # nenhum: o índice até funcionava, e o que o recusa é o `Manifesto(**m)` do
    # `Index.load`. Dizer «desactualizado» mandava reconstruir 6,4 min sem
    # dizer que basta reescrever o manifesto.
    ({"extra": {"versao": 2}}, "campo a mais"),
])
def test_diz_qual_campo_do_manifesto_divergiu(tmp_path, torcer, esperado):
    caminho = _escrever_indice(tmp_path, **torcer)
    ok, detalhe = diagnosticar_indice(CHUNKS, ASSINATURA, caminho=caminho)
    assert ok is False
    assert esperado in detalhe


def test_indice_ausente_e_ilegivel_distinguem_se(tmp_path):
    ok, detalhe = diagnosticar_indice(CHUNKS, ASSINATURA,
                                      caminho=str(tmp_path / "nada"))
    assert ok is False and "ausente" in detalhe

    caminho = _escrever_indice(tmp_path)
    with open(f"{caminho}.manifest.json", "w", encoding="utf-8") as f:
        f.write("{isto não é json")
    ok, detalhe = diagnosticar_indice(CHUNKS, ASSINATURA, caminho=caminho)
    assert ok is False and "ilegível" in detalhe


def test_indice_bom_e_aceito_e_diz_o_que_tem(tmp_path):
    caminho = _escrever_indice(tmp_path)
    ok, detalhe = diagnosticar_indice(CHUNKS, ASSINATURA, caminho=caminho)
    assert ok is True
    assert "2 chunks" in detalhe and ENCODER in detalhe


# --- a paridade, que é o que autoriza a duplicação ------------------------- #

class EncoderFalso:
    """Só o que o `Index.load` usa: o nome. Não carrega modelo nenhum."""

    def __init__(self, nome: str = ENCODER):
        self.nome = nome


@pytest.mark.parametrize("torcer", [
    {},
    {"encoder": "outro/encoder"},
    {"assinatura": "outra"},
    {"n_chunks": 99},
    {"ids": [["poem_2", 0], ["poem_1", 0]]},
    {"dim": 7},
    # Acrescentado depois de a divergência ser medida, e não imaginada: com o
    # diagnóstico a ler o manifesto por chave, ele dizia `True` e o
    # `Index.load` devolvia `None`. Ver `docs/twowayflow/manifesto-decisao.md`
    # §4, e o `_como_manifesto` que o fecha.
    {"extra": {"versao": 2}},
])
def test_paridade_com_o_index_load(tmp_path, torcer):
    """O diagnóstico aceita exactamente quando o `Index.load` carrega.

    É o teste que torna a duplicação aceitável. Se divergirem, falha — e o que
    falha é o diagnóstico, não o `Index.load`: a decisão de produção é dele.
    """
    caminho = _escrever_indice(tmp_path, **torcer)
    # O `dim` torcido tem de bater no `.npy` para o caso ser o da forma, e não
    # o do manifesto: escreve-se o vector com a forma certa e o `dim` errado.
    if "dim" in torcer:
        np.save(f"{caminho}.npy", np.zeros((len(CHUNKS), 4), dtype="float32"))

    meu_ok, _ = diagnosticar_indice(CHUNKS, ASSINATURA, caminho=caminho)
    dele = Index.load(CHUNKS, EncoderFalso(), ASSINATURA, caminho=caminho)
    assert meu_ok is (dele is not None), (
        f"divergência com o Index.load em {torcer or 'caso bom'}")


def test_o_diagnostico_compara_contra_o_encoder_que_o_sistema_usa():
    """A ressalva declarada no cabeçalho do `estado.py`, fixada.

    O diagnóstico compara com a constante `tokens.ENCODER` para não instanciar
    um `SentenceTransformer`. Isso só é correcto enquanto `Encoder()` por
    omissão tiver esse nome — e é por isso que está aqui, e não num comentário.
    """
    import inspect

    from src.retrieval.encoder import Encoder
    assert inspect.signature(Encoder).parameters["nome"].default == ENCODER


# --- consultar o estado não carrega nada ----------------------------------- #

def test_api_estado_nao_instancia_o_encoder(monkeypatch):
    """Se carregasse, o `/api/estado` calava-se durante uma geração (I4)."""
    import src.retrieval.encoder as mod

    def proibido(*a, **k):
        raise AssertionError("o /api/estado carregou o encoder")

    monkeypatch.setattr(mod, "Encoder", proibido)
    assert _cliente().get("/api/estado").status_code == 200


def test_api_estado_nao_carrega_o_corpus(monkeypatch):
    import src.corpus.build as mod

    def proibido(*a, **k):
        raise AssertionError("o /api/estado carregou o corpus")

    monkeypatch.setattr(mod, "load", proibido)
    assert _cliente().get("/api/estado").status_code == 200


# --- /api/vozes ------------------------------------------------------------- #

def test_vozes_lista_as_personas_com_as_linguas_que_existem():
    corpo = _cliente().get("/api/vozes").json()
    nomes = {v["nome"] for v in corpo["vozes"]}
    assert "Alberto Caeiro" in nomes
    assert "Álvaro de Campos" in nomes


def test_search_vem_marcado_como_lingua_unica():
    """Tem 1 poema em português entre 52: servi-lo em PT era servi-lo do que não é."""
    corpo = _cliente().get("/api/vozes").json()
    search = [v for v in corpo["vozes"] if v["voz"] == "search"]
    assert search, "o Alexander Search não aparece"
    assert all(v["idioma_unico"] == "en" for v in search)
    assert all(v["roteavel"] is False for v in search)


def test_o_roteador_so_e_oferecido_em_portugues():
    corpo = _cliente().get("/api/vozes").json()
    assert corpo["roteador"]["idiomas"] == ["pt"]
    assert corpo["roteador"]["acerto"] == 0.68


def test_vozes_nao_leva_o_system_prompt():
    """O texto da persona é o `system`; a interface mostra o nome."""
    bruto = _cliente().get("/api/vozes").text
    assert "Vês as coisas como elas são" not in bruto
