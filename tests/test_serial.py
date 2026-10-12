"""O portão do passo 2 da Fase 6: um campo novo no domínio é detectado.

O risco que isto cobre não é «o JSON sai mal» — isso dá erro e vê-se. É o
silencioso: alguém acrescenta um campo a `Turno` ou a `Veredicto`, o
serializador não o conhece, nada falha, e a interface passa a mostrar menos do
que o sistema sabe. Foi assim que o `Resposta.truncada` ficou **gravado e não
usado** até a Fase 5R o apanhar, com cinco amostras cortadas a meio da palavra
a chegarem à folha de julgamento.

A protecção é comparar `dataclasses.fields()` com o que o serializador
produziu, campo a campo:

- **campo escalar** — o seu valor tem de aparecer em algum sítio do JSON;
- **campo de contentor** — tem de estar declarado no `CONTENTORES` abaixo, que
  diz em que chave aterra;
- **campo que não vai** — tem de estar no `serial.OMITIDOS`, com motivo.

Um campo novo não está em nenhum dos três, logo falha.

⚠️ **O instrumento tem um limite declarado:** a verificação de um escalar é por
**presença do valor**, logo um campo novo de tipo `bool` pode passar por
coincidência — já há `ok`, `truncada`, `plagiou` e `aprovado` no fio, e `True`
aparece lá de qualquer maneira. Para escalares distintos (texto, tempos,
contagens) as instâncias abaixo usam valores únicos de propósito, e aí a
coincidência não acontece.
"""
from dataclasses import fields

from src.corpus.models import Chunk, Lang, Poem, Voice
from src.generation.base import Resposta
from src.guard import Veredicto
from src.lexico import Suspeita
from src.pipeline import Tentativa, Turno
from src.plagio import Analise, VersoCopiado
from src.roteador import Proposta
from src.voices import Persona
from src.web import serial

# --- instâncias com valores únicos, para a presença não ser coincidência ----

CHUNK = Chunk(poem_id="poem_9001", chunk_ix=3, text="corpo que não deve sair",
              indexed_text="Autor — Título\ncorpo que não deve sair",
              voice=Voice.CAEIRO, language=Lang.PT, n_words=4242)

CHUNK_B = Chunk(poem_id="poem_9002", chunk_ix=0, text="outro corpo",
                indexed_text="Outro — Outro\noutro corpo",
                voice=Voice.CAEIRO, language=Lang.PT, n_words=77)

RESPOSTA = Resposta(texto="As coisas são o que são.\nE nada mais.",
                    prefill_s=19.11, decode_s=11.22, prefill_tokens=1847,
                    decode_tokens=203, truncada=False)

SUSPEITA = Suspeita(palavra="inventoso", verso="um verso com inventoso dentro")

VEREDICTO = Veredicto(True, ("motivo-unico-aqui",),
                      "As coisas são o que são.\nE nada mais.",
                      (SUSPEITA,), ("construcao-proibida-unica",))

COPIADO = VersoCopiado(verso="verso gerado que copiou",
                       similaridade=0.8123, origem="verso real do contexto",
                       poema="poem_9001")

ANALISE = Analise(fracao_copiada=0.6412, n_versos=14, copiados=(COPIADO,),
                  max_similaridade=0.8911)

TENTATIVA = Tentativa(n=1, usados=(CHUNK,), resposta=RESPOSTA,
                      veredicto=VEREDICTO, plagio=ANALISE)

TURNO = Turno(pergunta="porque é que o fim do dia é melancólico?",
              voz=Voice.CAEIRO, idioma=Lang.PT,
              recuperados=(CHUNK, CHUNK_B), usados=(CHUNK,),
              resposta=RESPOSTA, veredicto=VEREDICTO, plagio=ANALISE,
              tentativas=1, recuperacao_ms=412.77, rerank_ms=2571.33,
              historico=(TENTATIVA,))

PROPOSTA = Proposta(voz=Voice.CAMPOS, bruto="a voz é: campos", segundos=0.53)

PERSONA = Persona(voz=Voice.CAEIRO, nome="Alberto Caeiro",
                  poetica="poetica que não vai ao fio",
                  forma="forma que não vai ao fio", idioma=Lang.PT)

POEMA = Poem(id="poem_9001", author="Alberto Caeiro", voice=Voice.CAEIRO,
             title="TÍTULO ÚNICO", body="corpo inteiro do poema",
             language=Lang.PT, stanzas=("corpo inteiro do poema",),
             n_words=4242, duplicate_of=None)

#: Campo de contentor → a chave em que aterra no fio.
#: Vive no teste e não no `serial.py` porque é andaime de verificação; o
#: `OMITIDOS` é que é uma afirmação sobre o produto.
CONTENTORES: dict[type, dict[str, str]] = {
    Veredicto: {"motivos": "motivos", "suspeitas": "suspeitas",
                "gramatica": "gramatica"},
    Analise: {"copiados": "copiados"},
    Tentativa: {"resposta": "resposta", "veredicto": "veredicto",
                "plagio": "plagio"},
    Turno: {"resposta": "resposta", "veredicto": "veredicto",
            "plagio": "plagio", "historico": "historico"},
}

CASOS = [
    (Chunk, CHUNK, serial.chunk),
    (Resposta, RESPOSTA, serial.resposta),
    (Suspeita, SUSPEITA, serial.suspeita),
    (Veredicto, VEREDICTO, serial.veredicto),
    (VersoCopiado, COPIADO, serial.verso_copiado),
    (Analise, ANALISE, serial.analise),
    (Tentativa, TENTATIVA, serial.tentativa),
    (Turno, TURNO, serial.turno),
    (Proposta, PROPOSTA, serial.proposta),
    (Persona, PERSONA, serial.persona),
    (Poem, POEMA, serial.poema),
]


def _escalares(obj) -> set:
    """Todos os valores escalares do JSON, a qualquer profundidade."""
    if isinstance(obj, dict):
        return {v for x in obj.values() for v in _escalares(x)}
    if isinstance(obj, (list, tuple)):
        return {v for x in obj for v in _escalares(x)}
    return {obj}


def _e_escalar(v) -> bool:
    return v is None or isinstance(v, (str, int, float, bool))


# --- o portão -------------------------------------------------------------- #

def test_cada_campo_do_dominio_esta_decidido():
    """Serializado, declarado contentor, ou omitido com motivo. Não há quarta."""
    faltam = []
    for tipo, inst, fn in CASOS:
        saida = fn(inst)
        valores = _escalares(saida)
        omitidos = serial.OMITIDOS.get(tipo, {})
        contentores = CONTENTORES.get(tipo, {})
        for f in fields(tipo):
            if f.name in omitidos or f.name in contentores:
                continue
            v = getattr(inst, f.name)
            if not _e_escalar(v):
                faltam.append(f"{tipo.__name__}.{f.name}: contentor não declarado")
            elif v not in valores:
                faltam.append(f"{tipo.__name__}.{f.name}: valor não está no fio")
    assert not faltam, (
        "campos do domínio que ninguém decidiu — serialize-os, declare-os "
        "em CONTENTORES, ou omita-os em serial.OMITIDOS com motivo:\n  "
        + "\n  ".join(faltam))


def test_contentores_declarados_aterram_mesmo():
    """Um contentor declarado tem de produzir a chave que diz produzir."""
    for tipo, inst, fn in CASOS:
        saida = fn(inst)
        for campo, chave in CONTENTORES.get(tipo, {}).items():
            assert chave in saida, f"{tipo.__name__}.{campo} → «{chave}» não existe"


def test_omitidos_nomeiam_campos_que_existem():
    """Apanha a entrada obsoleta: campo renomeado, omissão a apontar a nada."""
    for tipo, nomes in serial.OMITIDOS.items():
        reais = {f.name for f in fields(tipo)}
        fantasmas = set(nomes) - reais
        assert not fantasmas, f"{tipo.__name__}: {fantasmas} já não existem"


# --- as duas decisões que não são de formato ------------------------------- #

def test_corpo_de_poema_nao_vai_no_turno():
    """O §3.3: uma resposta leva 6 chunks, e nenhum leva verso de Pessoa."""
    import json
    fio = json.dumps(serial.turno(TURNO), ensure_ascii=False)
    assert CHUNK.text not in fio
    assert CHUNK.indexed_text not in fio
    assert CHUNK_B.text not in fio
    # O verso original de que o modelo copiou também é corpo de poema.
    assert COPIADO.origem not in fio
    # Mas o verso **gerado** que copiou vai, senão a rejeição não se explica.
    assert COPIADO.verso in fio


def test_o_poema_inteiro_so_sai_pelo_serializador_que_o_anuncia():
    assert POEMA.body in serial.poema(POEMA)["corpo"]


def test_derivados_vao_calculados_e_nao_sao_recalculaveis_por_engano():
    """`aprovado` decide se o pipeline repete. Não se recalcula no navegador."""
    d = serial.turno(TURNO)
    assert d["aprovado"] is TURNO.aprovado
    assert d["plagio"]["plagiou"] is ANALISE.plagiou
    assert d["resposta"]["total_s"] == RESPOSTA.total_s
    assert serial.proposta(PROPOSTA)["decidiu"] is True


def test_turno_inteiro_e_json_valido():
    """Ida-e-volta de um `Turno` sintético, que é o aceite do passo 2."""
    import json
    d = serial.turno(TURNO)
    volta = json.loads(json.dumps(d, ensure_ascii=False))
    assert volta == d
    assert volta["texto"] == TURNO.texto
    assert volta["voz"] == "caeiro"
    assert volta["idioma"] == "pt"
    assert volta["tentativas"] == 1
    assert len(volta["historico"]) == 1


def test_fontes_distinguem_usado_de_recuperado():
    """`montar` corta o contexto: há recuperados que nunca entraram no prompt."""
    fontes = serial.turno(TURNO)["fontes"]
    papeis = {f["poem_id"]: f["papel"] for f in fontes}
    assert papeis == {"poem_9001": "usado", "poem_9002": "recuperado"}


def test_proposta_sem_opiniao_vai_como_nula():
    """`voz is None` é um estado legítimo, e não se inventa uma voz."""
    d = serial.proposta(Proposta(voz=None, bruto="não sei", segundos=0.4))
    assert d["voz"] is None
    assert d["decidiu"] is False


def test_persona_nao_leva_o_system_prompt():
    d = serial.persona(PERSONA)
    assert d["nome"] == "Alberto Caeiro"
    assert PERSONA.poetica not in str(d)


# --- o detector verificado contra si mesmo --------------------------------- #

def test_o_detector_detecta_mesmo_um_campo_novo():
    """Meta-teste: o portão acima podia passar por não estar a olhar.

    Nesta casa um instrumento que nunca disparou não está validado — a Fase 5C
    rejeitou um detector cuja AUC caía de 0,869 para 0,544 em dados retidos, e
    a 5R apanhou um portão que contava como erro casos em que o detector estava
    certo. Logo: fabrica-se um `Resposta` com um campo a mais e confirma-se que
    o detector o **nomeia**.

    Não se faz isto editando o `src/`: o checkout é partilhado com outras
    sessões, e um campo de mentira no `generation/base.py`, por dez segundos
    que fosse, podia ser apanhado pelo `git add -A` de quem commita ao lado.
    """
    from dataclasses import field as dc_field
    from dataclasses import make_dataclass

    # Herda de `Resposta` em vez de a copiar: assim traz os campos **e** as
    # propriedades derivadas (`total_s`, `decode_tps`), que o serializador lê.
    RespostaMais = make_dataclass(
        "RespostaMais",
        [("campo_novo", str, dc_field(default="ninguem-me-serializou"))],
        bases=(Resposta,), frozen=True)

    inst = RespostaMais(**{f.name: getattr(RESPOSTA, f.name)
                           for f in fields(Resposta)})
    # O serializador real corre sobre ele: só lê atributos.
    valores = _escalares(serial.resposta(inst))
    nao_decididos = [
        f.name for f in fields(RespostaMais)
        if f.name not in serial.OMITIDOS.get(Resposta, {})
        and _e_escalar(getattr(inst, f.name))
        and getattr(inst, f.name) not in valores]

    assert nao_decididos == ["campo_novo"], (
        "o detector não apanhou o campo novo, logo o portão não vale")
