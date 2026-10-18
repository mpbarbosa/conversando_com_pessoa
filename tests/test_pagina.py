"""A página do passo 5, e o que dela se consegue verificar sem um navegador.

Não há aqui um motor de JavaScript, logo estes testes **não** provam que a
página desenha bem. Provam o que é verificável de fora e tem consequência
medida, que é uma lista curta e deliberada:

1. **O vocabulário de eventos é um só.** O `app.py` declara `TIPOS_DE_EVENTO` e
   o `app.js` declara `EVENTOS`. Se divergirem, o navegador recebe o fluxo
   inteiro e desenha um ecrã vazio — **sem erro nenhum**, que é o parente
   próximo do «índice velho não dá erro: dá respostas erradas» do
   `src/retrieval/index.py`.
2. **A página não decide nada** (§0): não limpa o início do fluxo, não
   recalcula `aprovado`, não interpreta o texto como marcação.
3. **A página não vai à rede** — nem por tipos de letra, nem por CSS, nem por
   bibliotecas. O servidor é local e serve um corpus cujos termos de uso não
   estão confirmados (§4.9).
4. **Os ficheiros são servidos**, e as rotas da API não foram engolidas pelo
   `mount` em `/`.

⚠️ O que fica **por** verificar e não se finge verificado: a tipografia, o
contraste AA, a tentativa rejeitada a ficar recolhida no lugar, e o cronómetro
a contar. Isso vê-se com os olhos, e foi visto uma vez com o Ollama a sério — o
que não é um teste de regressão. O portão **I2** é verificado onde pode ser, no
fluxo da API (`tests/test_perguntar.py`).
"""
from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from src.web.app import ESTATICO, TIPOS_DE_EVENTO, Servico, criar_app

HTML = (ESTATICO / "index.html").read_text(encoding="utf-8")
JS = (ESTATICO / "app.js").read_text(encoding="utf-8")
CSS = (ESTATICO / "estilo.css").read_text(encoding="utf-8")


def _sem_comentarios(fonte: str) -> str:
    """O código sem a prosa, porque estes testes são sobre o que corre.

    Os ficheiros desta pasta explicam-se por extenso, e um comentário a dizer
    «nada de `innerHTML`» fazia falhar o teste que procura `innerHTML`. O
    `(?<!:)` protege `http://` e `https://` dentro de cadeias: sem ele, cortar
    de `//` até ao fim da linha escondia exactamente o que o teste da rede
    procura.
    """
    fonte = re.sub(r"/\*.*?\*/", "", fonte, flags=re.S)
    fonte = re.sub(r"<!--.*?-->", "", fonte, flags=re.S)
    return re.sub(r"(?<!:)//.*", "", fonte)


#: As três fontes sem prosa. O `JS` cru fica disponível para quando o que
#: interessa é a declaração e não o comportamento (a lista `EVENTOS`).
CODIGO_JS = _sem_comentarios(JS)
CODIGO_HTML = _sem_comentarios(HTML)
CODIGO_CSS = _sem_comentarios(CSS)


@pytest.fixture
def cliente():
    with TestClient(criar_app(Servico(gerador=_GeradorMudo()))) as c:
        yield c


class _GeradorMudo:
    """O mínimo que o `/api/estado` pergunta. Não gera nada."""

    modelo = "nenhum"
    url_base = "http://127.0.0.1:11434"

    def disponivel(self) -> bool:
        return False

    def modelo_instalado(self) -> bool:
        return False


# --- 1. um vocabulário de eventos, não dois ------------------------------- #

def test_os_tipos_de_evento_do_cliente_e_do_servidor_sao_os_mesmos():
    """O modo de falha que não dá erro: o fluxo chega e o ecrã fica vazio.

    O `app.js` declara `EVENTOS` em vez de espalhar cadeias por um `switch`
    precisamente para isto ser comparável de fora.
    """
    m = re.search(r"const EVENTOS = \[([^\]]*)\]", JS)
    assert m, "o `app.js` deixou de declarar a lista `EVENTOS`"
    do_cliente = tuple(re.findall(r'"([a-z]+)"', m.group(1)))
    assert sorted(do_cliente) == sorted(TIPOS_DE_EVENTO), (
        f"cliente {do_cliente} contra servidor {TIPOS_DE_EVENTO}")


@pytest.mark.parametrize("tipo", TIPOS_DE_EVENTO)
def test_cada_tipo_de_evento_e_tratado_no_cliente(tipo):
    """Declarar não é tratar: cada tipo tem de ter um ramo que o leia.

    Sem isto, acrescentar um tipo à lista dos dois lados dava a paridade acima
    por satisfeita com a página a ignorar o evento novo.
    """
    assert f'e.tipo === "{tipo}"' in JS or f'"{tipo}"' in JS
    assert re.search(rf'tipo === "{tipo}"', JS), (
        f"o `app.js` declara «{tipo}» e não tem ramo que o trate")


# --- 2. a página não decide nada (§0) ------------------------------------- #

def test_a_pagina_nao_reimplementa_a_limpeza_do_inicio_do_fluxo():
    """Portão I2, do lado do cliente: a retenção é do servidor, e é uma só.

    O passo 1 extraiu a `limpar_inicio` para `src/apresentacao.py` justamente
    para não haver uma segunda. Se alguma destas palavras aparecer no
    `app.js`, há política de apresentação no navegador.
    """
    for proibido in ("remover_preambulo", "removerPreambulo", "preambulo",
                     "remover_eco", "removerEco", "Aqui está um poema"):
        assert proibido not in CODIGO_JS, (
            f"«{proibido}» no `app.js`: a limpeza do início voltou ao cliente")


def test_a_pagina_nao_recalcula_o_que_o_fio_ja_decidiu():
    """`aprovado` é uma regra do domínio que a Fase 5R corrigiu.

    O `serial.py` manda-a calculada de propósito. Recalculá-la aqui — «ok e
    não plagiou e não truncada» — punha uma segunda política de decisão no
    navegador, e seria ela a decidir o que o utilizador vê.
    """
    assert "turno.aprovado" in JS, "a página deixou de usar o `aprovado` do fio"
    # O sinal de um recálculo: as três condições juntas numa expressão.
    assert not re.search(r"veredicto\.ok\s*&&", CODIGO_JS), (
        "«aprovado» recalculado")
    assert not re.search(r"!\s*\w+\.plagio\.plagiou\s*&&", CODIGO_JS), (
        "«aprovado» recalculado")


def test_o_verso_entra_no_dom_como_texto_e_nunca_como_marcacao():
    """§4.8.1: nenhum motor de Markdown, e nada de `innerHTML`.

    As quebras de linha são semânticas num poema. E um verso que chegasse ao
    DOM por `innerHTML` era marcação a ser interpretada — com texto que um
    modelo gerou a partir de um contexto, o que é a definição do problema.
    """
    assert "innerHTML" not in CODIGO_JS
    assert "insertAdjacentHTML" not in CODIGO_JS
    assert "textContent" in CODIGO_JS
    for motor in ("marked", "markdown", "showdown", "remark"):
        assert motor not in CODIGO_JS.lower()
    # A decisão é inútil sem o CSS que a suporta.
    assert "white-space: pre-wrap" in CSS


def test_a_pagina_nao_corrige_combinacoes_impossiveis_e_desactiva_as():
    """§4.6: corrigir a escolha de alguém depois de ele a fazer é pior.

    Os limites vêm do `/api/vozes` — `idiomas`, `idioma_unico`, `roteavel` —,
    que é a mesma fonte que o `app.py` usa para recusar com 422.
    """
    assert "idioma_unico" in JS and "idiomas.includes" in JS
    assert "disabled" in JS
    assert "title" in JS, "o motivo tem de ir como legenda, não só a opacidade"


# --- 3. a página não vai à rede ------------------------------------------- #

@pytest.mark.parametrize("ficheiro,texto", [
    ("index.html", None), ("app.js", None), ("estilo.css", None)])
def test_nenhum_ficheiro_pede_nada_a_um_servidor_de_fora(ficheiro, texto):
    """§4.9: o servidor é local e serve corpos de poemas. Nada sai, nada entra.

    Um tipo de letra do Google numa página que serve este corpus mandava para
    fora, em cada visita, a informação de que ela foi aberta.
    """
    conteudo = {"index.html": CODIGO_HTML, "app.js": CODIGO_JS,
                "estilo.css": CODIGO_CSS}[ficheiro]
    for fora in ("http://", "https://", "fonts.googleapis",
                 "unpkg", "jsdelivr", "cdnjs"):
        assert fora not in conteudo, f"{ficheiro} aponta para fora: {fora}"


def test_nao_ha_passo_de_compilacao():
    """§1.1: um `index.html`, um `app.js`, um `estilo.css`, servidos como ficheiros."""
    nomes = sorted(p.name for p in ESTATICO.iterdir() if p.is_file())
    assert nomes == ["app.js", "estilo.css", "index.html"]
    assert "import " not in CODIGO_JS and "require(" not in CODIGO_JS


# --- 4. os ficheiros são servidos, e a API não foi engolida --------------- #

def test_a_raiz_serve_a_pagina(cliente):
    r = cliente.get("/")
    assert r.status_code == 200
    assert "Conversando com Pessoa" in r.text
    assert "text/html" in r.headers["content-type"]


@pytest.mark.parametrize("caminho,tipo", [
    ("/app.js", "javascript"),
    ("/estilo.css", "css"),
])
def test_os_outros_dois_ficheiros_tambem(cliente, caminho, tipo):
    r = cliente.get(caminho)
    assert r.status_code == 200
    assert tipo in r.headers["content-type"]


def test_o_mount_na_raiz_nao_engoliu_as_rotas_da_api(cliente):
    """O `mount` em `/` casa com qualquer caminho; o que decide é a ordem.

    Registá-lo antes das rotas dava um 404 numa rota que existe, que é das
    falhas mais difíceis de ler. Este teste é o que fixa a ordem.
    """
    assert cliente.get("/api/estado").status_code == 200
    assert cliente.get("/api/vozes").status_code == 200
    # E o 422 do `Pedido` continua a ser do manipulador, não do estático.
    assert cliente.post("/api/perguntar", json={"pergunta": ""}
                        ).status_code == 422


def test_a_pagina_declara_que_nao_ha_memoria_entre_perguntas():
    """§3.6, que o plano nomeia como o maior risco de UX desta fase.

    Uma caixa de conversa promete memória e o `Pipeline` não recebe histórico.
    A decisão foi mostrar o histórico e **não** o alimentar, dizendo-o — uma
    propriedade declarada e permanente, como o rodapé dos tempos.
    """
    assert "Cada pergunta é independente" in HTML


def test_a_pagina_mostra_a_prontidao_por_componente_e_nao_um_booleano():
    """§4.2: quatro esperas, e uma página em branco durante 6,4 min é uma avaria.

    O índice a construir é ~6,4 min, e o `/api/estado` devolve a lista por
    componente com remédio e custo precisamente para a página poder mostrá-la.
    """
    assert 'id="componentes"' in HTML
    assert "/api/estado" in JS
    for campo in ("remedio", "custo_s", "componentes"):
        assert campo in JS, f"a página ignora o campo «{campo}» do estado"


# --- o defeito que só aparece a correr ------------------------------------ #

def test_pode_perguntar_e_verdade_antes_da_primeira_pergunta(cliente):
    """A regressão que a página do passo 5 revelou, fixada no servidor.

    `pronto` é **falso por construção** antes da 1.ª pergunta: o índice só se
    verifica quando há corpus carregado, e o corpus só se carrega ao perguntar.
    Com o botão governado pelo `pronto`, a única acção que resolve o que falta
    nunca podia ser feita — a página arrancava permanentemente trancada.

    Aqui o Ollama está em baixo, logo `pode_perguntar` é falso **por esse**
    motivo; o teste abaixo é o que fixa o caso bom.
    """
    corpo = cliente.get("/api/estado").json()
    assert corpo["pronto"] is False
    assert corpo["pode_perguntar"] is False     # o Ollama do duplo está em baixo


def test_o_indice_por_verificar_nao_impede_de_perguntar():
    """Com o Ollama de pé e o índice ainda por verificar, pergunta-se.

    É o caso exacto do arranque: `pronto` falso, `pode_perguntar` verdadeiro.
    """
    class Vivo:
        modelo = "qualquer"
        url_base = "http://127.0.0.1:11434"

        def disponivel(self):
            return True

        def modelo_instalado(self):
            return True

    with TestClient(criar_app(Servico(gerador=Vivo()))) as c:
        corpo = c.get("/api/estado").json()
    indice = next(x for x in corpo["componentes"] if x["nome"] == "indice")
    assert indice["pronto"] is False, "o pressuposto do teste caiu"
    assert corpo["pronto"] is False
    assert corpo["pode_perguntar"] is True, (
        "o arranque voltou a trancar a 1.ª pergunta")


def test_a_pagina_governa_o_botao_pelo_pode_perguntar(cliente):
    """E a página tem de ler esse campo, não o `pronto`."""
    assert "pode_perguntar" in CODIGO_JS
    assert not re.search(r"!\s*corpo\.pronto", CODIGO_JS), (
        "o botão voltou a ser governado pelo `pronto`")


def test_uma_escolha_desligada_nao_aparece_como_falha(cliente):
    """O reranker desligado é uma troca por fazer, não uma avaria.

    O servidor diz quais são requisitos (`exigido`); a página não repete a
    lista.
    """
    corpo = cliente.get("/api/estado").json()
    por_nome = {c["nome"]: c for c in corpo["componentes"]}
    assert por_nome["reranker"]["exigido"] is False
    assert por_nome["roteador"]["exigido"] is False
    for nome in ("ollama", "modelo", "corpus", "indice"):
        assert por_nome[nome]["exigido"] is True
    assert "c.exigido" in CODIGO_JS, "a página ignora o campo `exigido`"


# --- §2.3: cancelar, do lado do cliente (passo 6) ------------------------- #

def test_o_botao_de_cancelar_existe_e_nasce_escondido():
    """Só aparece enquanto gera: um «cancelar» inerte ensina que não funciona.

    O `hidden` no HTML é o estado inicial, e o `trancar()` é quem o liga e
    desliga — no mesmo sítio onde tranca o «Perguntar» e a caixa de texto, para
    os três não poderem discordar.
    """
    assert re.search(r'id="cancelar"[^>]*\shidden', CODIGO_HTML), (
        "o botão de cancelar não nasce escondido")
    assert re.search(r'type="button"[^>]*id="cancelar"', CODIGO_HTML), (
        "um botão sem `type` dentro de um `form` submete: cancelar passava a "
        "perguntar outra vez")
    assert re.search(r'\$\("#cancelar"\)\.hidden\s*=', CODIGO_JS), (
        "nada liga e desliga o botão")


def test_o_abortcontroller_chega_ao_fetch():
    """O modo de falha silencioso deste passo, e é o pior de todos.

    Um `AbortController` criado, um botão a chamar-lhe `abort()` e o `signal`
    esquecido no `fetch`: a página fica com o botão certo, o `abort` não dá
    erro nenhum, o fluxo continua a chegar e **o Ollama nunca sabe**. Fica
    exactamente igual a funcionar.
    """
    assert "new AbortController()" in CODIGO_JS
    assert re.search(r"signal:\s*\w+\.signal", CODIGO_JS), (
        "o `fetch` não leva o `signal`: o `abort` não aborta nada")
    assert ".abort()" in CODIGO_JS


def test_o_controlador_e_um_por_geracao():
    """Um controlador abortado fica abortado para sempre.

    Reutilizá-lo fazia o `fetch` seguinte rebentar antes de sair, com um
    `AbortError` que a página ia ler como «o servidor não respondeu».
    """
    corpo = re.search(r"async function perguntar\(.*?\n}\n", CODIGO_JS,
                      flags=re.S)
    assert corpo, "a função `perguntar` mudou de forma"
    assert "new AbortController()" in corpo.group(0), (
        "o controlador deixou de ser criado por geração")


def test_cancelar_nao_apaga_o_que_ja_apareceu_no_ecra():
    """É verso que o modelo escreveu, e parar não é desfazer.

    A mesma decisão do §4.4 para a tentativa rejeitada: fica no lugar, com o
    motivo. O que o `cancelado()` faz é escrever «interrompido depois de …» —
    e nada mais.
    """
    corpo = re.search(r"\n    cancelado\(\) \{.*?\n    \},", CODIGO_JS,
                      flags=re.S)
    assert corpo, "a página deixou de ter um estado `cancelado`"
    for destrutivo in ("remove()", "replaceChildren", "textContent = \"\";"):
        assert destrutivo not in corpo.group(0).replace(
            'fase.textContent = "";', ""), (
            f"o `cancelado()` apaga o ecrã com `{destrutivo}`")
    assert "interrompido" in corpo.group(0)
