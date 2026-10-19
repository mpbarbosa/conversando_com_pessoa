"""O portão **I7′** da [§2 do plano do serviço público](../docs/PRODUCAO.md):
o corpo de um poema não sai desta máquina.

## Porque é que o I7 foi reescrito

O portão **I7** da Fase 6 afirmava: «`GET /api/poema/{id}` recusa pedidos de
fora de `127.0.0.1`; o servidor **não escuta noutro interface sem sinalizador
explícito**». Com um túnel, o `cloudflared` corre **nesta** máquina e liga-se de
dentro a `127.0.0.1:8000`: o `bind` não muda, não há sinalizador nenhum, o
**I7 passa literalmente**, e o serviço está na internet. A asserção estava a
usar «escuta em `127.0.0.1`» como **medida** de «não é alcançável de fora», e o
túnel separa as duas.

**I7′** mede o que o I7 protegia: *nenhuma linha de corpo de nenhum poema do
corpus aparece em nenhuma resposta de nenhuma rota.* É o varrimento do portão
**I6** apontado ao **fio HTTP** em vez da base de dados.

## O que este ficheiro mede, e o que não pode medir

Mede o varrimento **contra a aplicação**, com o `TestClient`: todas as rotas que
o `criar_app` registe, em cenários escolhidos para serem o pior caso. Isto é a
metade do portão que se pode fixar por teste, e é a metade que apanha
regressões.

⚠️ **A outra metade do I7′ exige o túnel, e não existe ainda.** A asserção do
plano é «medido **de fora**, contra o URL público», e o URL público é o passo 6
(autenticação) sobre o passo 4 (unidades). Até lá o varrimento corre contra o
`uvicorn` e **não** contra o túnel — o que este ficheiro não exclui é um
intermediário a acrescentar corpo (não há nenhum no desenho) e um erro de
configuração do próprio túnel. Fica escrito em vez de o portão se dar por
cumprido: é o mesmo modo de falha que fez o I7 ser reescrito.

## Os três achados que este varrimento produziu

O primeiro rascunho deste ficheiro foi escrito a contar com uma passagem
trivial: a saída B não constrói o `GET /api/poema/{id}`, logo não havia por onde
sair. **Falhou em três sítios**, e os três estavam no fio por decisão
deliberada da Fase 6:

1. **Os fragmentos da tentativa plagiada.** O §4.4 manda a tentativa rejeitada
   ao fio para explicar porque é que o utilizador esperou 58 s em vez de 30 —
   e ela vai **em fluxo, à medida que é gerada**, logo sai antes de a guarda a
   poder reprovar. Medido aqui: **6 de 8 versos** do `poem_1104` no fio.
2. **O evento `turno` da tentativa rejeitada**, com o texto inteiro.
3. **`serial.verso_copiado`**, cujo comentário dizia «o verso **gerado** que
   copiou [...] sem o verso original» — verdade quando a cópia troca palavras,
   falso quando é à letra, e à letra é o caso em que o verso gerado **é** o
   original.

Nenhum dos três é um defeito da Fase 6: num servidor em `127.0.0.1` os três
mostram ao dono material que o dono já tem no disco. O que os torna defeitos é
o túnel, e é por isso que a correcção (`src/web/retencao.py`) é deste plano e
não daquela fase.
"""
from __future__ import annotations

import contextlib
import json

import pytest
from fastapi.testclient import TestClient

from src.corpus.build import load
from src.corpus.models import Voice
from src.web.app import ESTATICO, Servico, criar_app
from src.web.retencao import MIN_PALAVRAS, linhas_de_corpo, normalizar

from .test_perguntar import GeradorDeterminista
from .test_pipeline import GeradorFalso, _pipeline


class GeradorPlagiador(GeradorFalso):
    """O `GeradorFalso` com o que o `/api/estado` lhe pergunta.

    O varrimento toca em **todas** as rotas, e o `/api/estado` interroga o
    gerador sobre o Ollama. É andaime do duplo e não comportamento do servidor —
    o mesmo que o `_servico` do `test_perguntar.py` faz com o `reranker`.
    """

    def __init__(self, copiar_de: str):
        super().__init__(copiar_de)
        self.modelo = self.nome = "duplo"
        self.url_base = "http://127.0.0.1:11434"

    def disponivel(self) -> bool:
        return True

    def modelo_instalado(self) -> bool:
        return True

#: As rotas que este varrimento cobre. **Não é documentação: é o portão.** Uma
#: rota nova que não apareça aqui faz o
#: `test_i7_o_varrimento_cobre_todas_as_rotas` falhar, e é esse o mecanismo —
#: sem ele, o passo 9 da Fase 6 podia acrescentar o `GET /api/poema/{id}` e
#: este ficheiro continuava verde a varrer as três rotas antigas.
#:
#: ✅ **E funcionou, no passo seguinte.** O `GET /api/health` do passo 3 fez
#: este portão falhar no dia em que nasceu, antes de qualquer outro teste o
#: tocar. Não é hipótese: está medido uma vez.
ROTAS_COBERTAS = {
    ("GET", "/api/estado"),
    ("GET", "/api/health"),
    ("GET", "/api/vozes"),
    ("POST", "/api/perguntar"),
    # Do FastAPI, e não deste repositório — e vai ao fio como as outras. Não
    # leva corpo (leva o esquema das rotas), mas é varrida pela mesma razão
    # pela qual está nesta lista: o portão não distingue rotas minhas de rotas
    # da biblioteca, e uma que apareça numa actualização tem de aparecer aqui.
    ("GET", "/openapi.json"),
}


@pytest.fixture(scope="module")
def corpus():
    _, cs = load()
    return cs


@pytest.fixture(scope="module")
def corpo(corpus):
    return linhas_de_corpo(corpus)


@pytest.fixture(scope="module")
def chunks_caeiro(corpus):
    return [c for c in corpus if c.voice is Voice.CAEIRO][:8]


def _cadeias(v: object):
    """Cada cadeia de uma estrutura já desserializada, a qualquer profundidade."""
    if isinstance(v, str):
        yield v
    elif isinstance(v, dict):
        for x in v.values():
            yield from _cadeias(x)
    elif isinstance(v, list):
        for x in v:
            yield from _cadeias(x)


def _agulheiros(texto: str) -> list[str]:
    """O texto cru **e** cada cadeia de cada evento NDJSON, já desescapada.

    As duas coisas, porque nenhuma basta. O texto cru apanha o verso tal como
    viaja; não apanha um verso com `"` dentro, que o JSON escapa para `\\"`
    (e o corpus tem-nos: «"tenho a minha alma!"»). As cadeias desserializadas
    apanham esses; não apanham corpo que viaje fora de um evento válido.
    """
    fora = [texto]
    for ln in texto.split("\n"):
        ln = ln.strip()
        if not ln.startswith("{"):
            continue
        try:
            fora.extend(_cadeias(json.loads(ln)))
        except json.JSONDecodeError:
            continue
    return fora


def varrer(texto: str, corpo: frozenset[str]) -> list[str]:
    """As linhas de corpo que aparecem em `texto`. Vazio é o que o portão pede.

    ⚠️ **A primeira versão desta função não mordia, e passou a mutação.** Varria
    `texto.split("\n")` e comparava cada linha com o conjunto — barato, e
    errado no fio: o fio é **NDJSON**, onde a mudança de linha de um verso é o
    par de caracteres `\\n` dentro de uma cadeia JSON e não uma linha do
    corpo HTTP. Partido por `\n`, o fio inteiro de uma geração são 6 linhas,
    e um verso no meio de uma delas nunca era uma linha. Com a retenção
    desligada em `app.py`, as 8 asserções deste ficheiro continuaram **verdes**.
    Está escrito aqui porque é o terceiro defeito de instrumento que o
    `CONTROLO.md` §4 regista nesta casa, e o segundo neste portão.

    Agora varre por **subcadeia**, nos dois agulheiros do `_agulheiros`, e
    custa 19 ms por resposta — medido, com as 29 816 linhas protegidas sobre um
    agulheiro de 12 KB. Juntam-se com `\\x00` para que uma linha não case
    através da fronteira de dois agulheiros.
    """
    agulheiro = "\x00".join(normalizar(a) for a in _agulheiros(texto))
    return sorted(ln for ln in corpo if ln in agulheiro)


@contextlib.contextmanager
def _cliente(chunks, gerador):
    pipeline = _pipeline(chunks, gerador)
    pipeline.reranker = None
    with TestClient(criar_app(Servico(gerador=pipeline.gerador,
                                      pipeline=pipeline))) as c:
        yield c


def _fio(cliente, pergunta: str = "o que é a natureza?") -> str:
    """Tudo o que as rotas cobertas devolvem, num texto só."""
    partes = [cliente.get("/api/estado").text, cliente.get("/api/health").text,
              cliente.get("/api/vozes").text,
              cliente.get("/openapi.json").text]
    with cliente.stream("POST", "/api/perguntar",
                        json={"pergunta": pergunta, "voz": "caeiro"}) as r:
        partes.append(r.read().decode("utf-8"))
    return "\n".join(partes)


# --- o portão -------------------------------------------------------------- #

def test_i7_o_varrimento_cobre_todas_as_rotas(chunks_caeiro):
    """Se uma rota nascer e este ficheiro não a varrer, isto falha.

    O `mount` da página não é uma rota com método: entra como `Mount` e tem
    teste próprio (`test_i7_a_pagina_nao_leva_corpos`).
    """
    with _cliente(chunks_caeiro, GeradorDeterminista()) as cliente:
        rotas = {(m, r.path) for r in cliente.app.routes
                 for m in getattr(r, "methods", None) or ()
                 if m not in ("HEAD", "OPTIONS")}
    assert rotas == ROTAS_COBERTAS, (
        "o varrimento do I7′ deixou de cobrir as rotas da aplicação: "
        f"novas={rotas - ROTAS_COBERTAS} desaparecidas={ROTAS_COBERTAS - rotas}"
    )


def test_i7_nenhuma_rota_leva_corpo_na_resposta_aprovada(chunks_caeiro, corpo):
    """O caminho normal: a geração não plagia, e nada do corpus vai ao fio."""
    with _cliente(chunks_caeiro, GeradorDeterminista()) as cliente:
        acertos = varrer(_fio(cliente), corpo)
    assert acertos == [], f"corpo no fio: {acertos[:3]}"


def test_i7_nenhuma_rota_leva_corpo_na_tentativa_plagiada(chunks_caeiro, corpo):
    """**O achado 1.** Sem a `retencao`, são 6 versos do `poem_1104` no fio.

    O `GeradorFalso` copia o primeiro poema do contexto, que é o modo de falha
    observado a correr o chatbot (ver `CONTROLO.md`): a tentativa é reprovada
    pela guarda de plágio, e o §4.4 manda-a ao fio **de qualquer maneira** para
    o utilizador ver porque esperou. Em fluxo, sai antes de haver veredicto.
    """
    alvo = chunks_caeiro[0]
    with _cliente(chunks_caeiro, GeradorPlagiador(alvo.text)) as cliente:
        fio = _fio(cliente)
    acertos = varrer(fio, corpo)
    assert acertos == [], f"corpo no fio: {acertos[:3]}"


def test_i7_a_tentativa_rejeitada_continua_a_ir_ao_fio(chunks_caeiro):
    """A correcção retém **versos**, e não o evento: o §4.4 continua de pé.

    Sem esta asserção, a maneira mais fácil de passar o I7′ era deixar de
    mandar a tentativa rejeitada — e aí o utilizador voltava a esperar 58 s sem
    explicação, que é o defeito que o §4.4 existe para corrigir. O portão tem
    de proteger o corpo **e** a explicação.
    """
    alvo = chunks_caeiro[0]
    with _cliente(chunks_caeiro, GeradorPlagiador(alvo.text)) as cliente, \
            cliente.stream("POST", "/api/perguntar",
                           json={"pergunta": "o que é a natureza?",
                                 "voz": "caeiro"}) as r:
        eventos = [json.loads(ln) for ln in r.read().decode("utf-8").split("\n")
                   if ln.strip()]
    turnos = [e["turno"] for e in eventos if e["tipo"] == "turno"]
    assert len(turnos) == 2, "a tentativa rejeitada deixou de ir ao fio"
    assert turnos[0]["aprovado"] is False
    assert turnos[0]["plagio"]["plagiou"] is True, (
        "o veredicto de plágio tem de sobreviver à retenção: é o que explica "
        "a espera")
    assert turnos[0]["plagio"]["copiados"], (
        "a lista de versos copiados é o que o rodapé mostra; só o verso em si "
        "é que não pode ir")


def test_i7_nao_ha_rota_que_devolva_o_corpo_de_um_poema(chunks_caeiro):
    """Saída B: o passo 9 **não existe enquanto houver túnel** (§2 do plano).

    404 e não 403: a rota não está registada. É a decisão de desenho que torna
    o I7′ verdadeiro por construção em vez de por asserção — e a razão pela
    qual este teste olha para o 404 em vez de para um cabeçalho de origem.
    """
    with _cliente(chunks_caeiro, GeradorDeterminista()) as cliente:
        for caminho in ("/api/poema/poem_1104", "/api/poema/poem_1"):
            assert cliente.get(caminho).status_code == 404, caminho


def test_i7_a_pagina_nao_leva_corpos(corpo):
    """O `mount` em `/` serve **só** a pasta `estatico`, e ela não tem verso.

    Vale a pena medir e não presumir: um `index.html` com um poema de exemplo
    no corpo era um corpo publicado, e nenhum dos outros testes o veria.
    """
    for f in sorted(ESTATICO.iterdir()):
        if f.is_file():
            acertos = varrer(f.read_text(encoding="utf-8"), corpo)
            assert acertos == [], f"{f.name}: {acertos[:3]}"


# --- o instrumento, verificado a morder ------------------------------------ #

def test_i7_o_varrimento_morde(chunks_caeiro, corpo):
    """Um varrimento que nunca acerta é indistinguível de um que não varre.

    O `CONTROLO.md` §4 lista defeitos nos instrumentos desta casa — incluindo
    um portão que media uma geração já acabada e passava vazio. Aqui planta-se
    o que o portão procura e exige-se que ele o encontre.
    """
    versos = [ln for ln in chunks_caeiro[0].text.split("\n") if ln.strip()]
    solto = f'{{"tipo":"fragmento","texto":"x"}}\n{versos[0]}\nmais nada'
    assert varrer(solto, corpo) == [normalizar(versos[0])]

    # E o caso que a primeira versão desta função não via: o verso **dentro**
    # de uma cadeia JSON, que é a única forma em que ele viaja de verdade.
    no_fio = json.dumps({"tipo": "fragmento",
                         "texto": f"{versos[0]}\n{versos[1]}"},
                        ensure_ascii=False)
    assert varrer(no_fio, corpo) == sorted(
        {normalizar(versos[0]), normalizar(versos[1])})


def test_i7_o_varrimento_ignora_linhas_curtas_e_isso_esta_medido(corpus, corpo):
    """O limiar de `MIN_PALAVRAS`, e o que ele deixa de fora — por número.

    Uma linha de corpus de uma palavra (`'*'`, `'IV'`, `'Agora'`) não é um
    corpo de poema em nenhum sentido útil, e protegê-la fazia a retenção cortar
    fala comum. O limiar é 4 palavras, e o preço está contado: das 33 236 linhas
    distintas do corpus, 29 816 são protegidas e **3 420 não são** — números
    medidos neste corpus, nesta máquina, e que este teste prende para que uma
    mudança no limiar apareça como uma falha e não como um silêncio.
    """
    distintas = {normalizar(ln) for c in corpus for ln in c.text.split("\n")
                 if normalizar(ln)}
    assert MIN_PALAVRAS == 4
    assert len(distintas) == 33236
    assert len(corpo) == 29816
    assert len(distintas) - len(corpo) == 3420
    assert corpo <= distintas
    assert all(len(ln.split()) >= MIN_PALAVRAS for ln in corpo)
