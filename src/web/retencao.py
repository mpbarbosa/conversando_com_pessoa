"""A retenção de versos: o que impede o corpo de um poema de sair pelo fio.

Portão **I7′** do [plano do serviço público](../../docs/PRODUCAO.md) §2.

## Porque é que isto existe, e porque é que não é da Fase 6

A Fase 6 fechou o corpo dos poemas numa rota só — o `GET /api/poema/{id}` do
passo 9 — e protegeu-a com o portão **I7**: a rota recusa pedidos de fora de
`127.0.0.1`. Com o servidor a escutar só no *loopback*, isso bastava, e tudo o
mais que o fio leva é texto **gerado**.

Com um túnel deixa de bastar, e não por causa da rota: o `cloudflared` liga-se
de dentro a `127.0.0.1:8000`, o `bind` não muda, e o serviço está na internet
com o I7 a passar literalmente. A saída B resolve a rota — ela não é construída
enquanto houver túnel —, e o varrimento do `tests/test_i7.py` mostrou que havia
**três outras portas**, todas abertas de propósito pela Fase 6:

1. **Os fragmentos da tentativa plagiada.** O §4.4 manda a tentativa rejeitada
   ao fio para o utilizador saber porque esperou 58 s em vez de 30. Vai **em
   fluxo**, logo sai *antes* de a guarda de plágio poder reprovar: não há
   verificação a jusante que a possa apanhar, porque já saiu. Medido: 6 de 8
   versos do `poem_1104`.
2. **O evento `turno` da tentativa rejeitada**, com o texto inteiro.
3. **`serial.verso_copiado`.** O comentário dizia «o verso **gerado** que
   copiou [...] sem o verso original» — verdade quando a cópia troca palavras,
   e falso exactamente no caso em que importa: numa cópia à letra, o verso
   gerado **é** o original.

Nenhuma das três é um defeito da Fase 6. Num servidor em `127.0.0.1` as três
mostram ao dono material que ele já tem no disco. O que as torna defeitos é o
túnel — e por isso a correcção é deste plano e vive em `src/web/`, que é a
camada de transporte. **Nada em `src/pipeline.py`, `src/guard.py` ou
`src/generation/`:** um plano de publicação que precise de mexer na política
está mal desenhado (§9 do plano).

## A decisão: retém-se a **linha**, não o evento

A maneira mais fácil de passar o I7′ era deixar de mandar a tentativa rejeitada.
Isso desfazia o §4.4 e devolvia o utilizador aos 58 s sem explicação. Então o
que se retém é o **verso**, e o que fica é tudo o resto: `aprovado: false`, o
veredicto, a fracção copiada, a lista de versos copiados — com o campo `verso`
vazio quando o verso era o do corpus. A explicação sobrevive; o corpo não sai.
O `tests/test_i7.py` prende as duas metades, porque proteger uma à custa da
outra é regressão e não correcção.

## O limiar, e o seu preço — medido

Protegem-se as linhas de **4 palavras ou mais**. Das 33 236 linhas distintas do
corpus (já normalizadas), são 29 816; ficam **3 420** de fora, e são `*`, `IV`,
`Agora`, `A verdade`, `Nada, nada` — numeração, rubricas de cena e fala comum,
que não são corpo de poema em nenhum sentido útil e cuja protecção fazia a
retenção cortar texto gerado legítimo.

**O que isto custa em texto real, contado e não estimado.** Os 10 ficheiros
`01-cru.jsonl` das Fases 5B a 5Z têm **1 560** textos gerados nesta máquina,
com **16 866** linhas de 4+ palavras. A retenção acerta em **20** delas
(**0,119%**), em **12** dos 1 560 textos, e são **15 linhas distintas** de 6
poemas. Foram inspeccionadas uma a uma: **as 15 são versos de Pessoa** — «O
mistério das coisas, onde está ele?» (`poem_3452`), e 8 linhas seguidas do
`poem_3657` num texto só, que é um poema inteiro reproduzido. **Zero falsos
positivos em 1 560 textos reais.** A medição está no `CONTROLO.md`.

## O que esta retenção **não** é

Não é uma guarda de plágio, e não a substitui. Apanha a linha **igual**; uma
linha com uma palavra trocada passa-lhe ao lado e é da `guard.py`, que a mede
por fracção e reprova a tentativa. As duas têm alvos diferentes: a guarda
protege a qualidade da resposta, esta protege o corpus de ser publicado.

E **não garante o I7′ sozinha**. O que o garante é a cobertura: o varrimento do
`tests/test_i7.py` falha se nascer uma rota que não passe por aqui. A força do
emparelhamento não está na comparação — essa é exacta dos dois lados, e o teste
que a mede seria circular — está em o varrimento percorrer **todas** as rotas
que o `criar_app` registe. Foi assim que as três portas apareceram.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

#: Linhas com menos palavras do que isto não são protegidas. Ver o cabeçalho:
#: o limiar tem preço medido, e o `tests/test_i7.py` prende-o por número para
#: que mudá-lo apareça como falha e não como silêncio.
MIN_PALAVRAS = 4


def normalizar(linha: str) -> str:
    """A forma em que as duas pontas se comparam: espaços colapsados, minúsculas.

    `casefold` e não `lower` por causa do corpus em alemão e francês das peças
    de teatro. Não se tira pontuação de propósito: tirá-la fazia a retenção
    cortar paráfrases, que são da `guard.py` e não desta camada — e punha uma
    decisão de semelhança num sítio que tem de ser exacto para ser legível.
    """
    return " ".join(linha.split()).casefold()


def linhas_de_corpo(chunks: Iterable[Any]) -> frozenset[str]:
    """As linhas de corpo a proteger, normalizadas.

    Vem dos **chunks** e não dos `Poem`: o `corpus.jsonl` é a fronteira do
    sistema (`src/corpus/build.py`), e o `chunk.text` é o verso puro — o mesmo
    texto que vai ao prompt. Usar outra fonte era proteger um corpus e publicar
    outro.
    """
    return frozenset(
        n for c in chunks for ln in c.text.split("\n")
        if len(ln.split()) >= MIN_PALAVRAS and (n := normalizar(ln))
    )


class Retentor:
    """Filtro de fluxo por linha: come fragmentos, devolve o que pode sair.

    Tem de guardar a linha incompleta porque um fragmento do Ollama não acaba
    numa fronteira de linha: deixar passar `"O mistério das coi"` e depois
    `"sas, onde está ele?"` publicava o verso em duas prestações. É a mesma
    razão pela qual a `apresentacao.limpar_inicio` retém até haver uma linha
    completa — ali para o preâmbulo, aqui para o corpo.

    Uma instância por **tentativa**: o `reiniciar` existe porque a tentativa
    seguinte começa com o buffer vazio, e um resto de linha da anterior colado
    ao início da seguinte dava uma linha que nunca foi gerada.
    """

    def __init__(self, corpo: frozenset[str]):
        self._corpo = corpo
        self._buffer = ""
        #: Quantas linhas foram retidas nesta tentativa. Vai ao fio no evento
        #: `turno`, porque um texto com um buraco e sem explicação é pior do
        #: que um texto com um buraco e com ela.
        self.retidas = 0

    def alimentar(self, texto: str) -> str:
        """O que deste fragmento pode sair agora. Pode ser `""`, e isso é normal."""
        self._buffer += texto
        saida: list[str] = []
        while "\n" in self._buffer:
            linha, self._buffer = self._buffer.split("\n", 1)
            if normalizar(linha) in self._corpo:
                self.retidas += 1
            else:
                saida.append(f"{linha}\n")
        return "".join(saida)

    def esvaziar(self) -> str:
        """A última linha, que não trazia `\\n`. Chamado no fim de cada tentativa.

        Sem isto o último verso de cada resposta nunca saía — o modo de falha de
        qualquer buffer de linha, e silencioso, porque a resposta continua a
        parecer completa.
        """
        linha, self._buffer = self._buffer, ""
        if not linha:
            return ""
        if normalizar(linha) in self._corpo:
            self.retidas += 1
            return ""
        return linha

    def reiniciar(self) -> None:
        self._buffer = ""
        self.retidas = 0


def redigir(valor: Any, corpo: frozenset[str]) -> tuple[Any, int]:
    """Tira as linhas de corpo de uma estrutura já serializada. Devolve `(x, n)`.

    Percorre **tudo** em vez de uma lista de campos, e é deliberado: o `turno`
    do `serial.py` leva texto em `texto`, `resposta.texto`, `veredicto.texto`,
    `plagio.copiados[].verso`, `veredicto.suspeitas[].verso` e outra vez em cada
    entrada do `historico`. Uma lista de campos protegia os que eu me lembrei de
    escrever, e um campo novo no `serial.py` passava a publicar corpo sem que
    nada falhasse. Aqui, um campo novo nasce protegido.

    Uma cadeia de uma linha só que seja corpo fica `""` — é o caso do
    `verso_copiado.verso` numa cópia à letra, e é o achado 3 do cabeçalho.
    """
    if isinstance(valor, str):
        linhas = valor.split("\n")
        ficam = [ln for ln in linhas if normalizar(ln) not in corpo]
        return "\n".join(ficam), len(linhas) - len(ficam)
    if isinstance(valor, dict):
        n = 0
        d = {}
        for k, v in valor.items():
            d[k], m = redigir(v, corpo)
            n += m
        return d, n
    if isinstance(valor, list):
        n = 0
        xs = []
        for v in valor:
            x, m = redigir(v, corpo)
            xs.append(x)
            n += m
        return xs, n
    return valor, 0
