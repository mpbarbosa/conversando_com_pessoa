# As *stopwords* neste projecto

Documento temático, escrito em 2026-10-12, companheiro do
[`TOKENIZACAO.md`](TOKENIZACAO.md). **Não é uma fase**: não tem protocolo nem
portões. Reúne o que as fases decidiram e mediram sobre *stopwords*, e cada
número vem de um ficheiro citado ou de uma medição feita contra o corpus ao
escrever.

---

## 1. O essencial: há **três** listas, e só **uma** remove

É a confusão que este documento existe para desfazer. «Remoção de *stopwords*»
descreve **um** dos três usos.

| ficheiro | lista | n | o que faz |
|---|---|---|---|
| [`retrieval/lexical.py`](../../src/retrieval/lexical.py) | `STOPWORDS` | **84** | **remove**, para o BM25 |
| [`guard.py`](../../src/guard.py) | `_STOPWORDS[PT]` / `[EN]` | **34** / **49** | **detecta** a língua da resposta |
| [`corpus/parse.py`](../../src/corpus/parse.py) | `_PT` / `_EN` | **31** / **24** | **classifica** a língua do poema |

As duas últimas **não removem nada**. Contam palavras funcionais para decidir em
que língua um texto está — é o uso inverso, porque ali as *stopwords* são o
**sinal** e não o ruído.

### 1.1 E a prova está na diferença entre duas delas

Medido ao escrever este documento:

```
guard-PT ∩ lexical  = 32 palavras
guard-PT  −  lexical = {'mais', 'não'}
```

**As duas palavras que a lista de remoção deliberadamente exclui são exactamente
as que a lista de detecção deliberadamente inclui.** O comentário do
`lexical.py` diz porquê:

> «Deliberadamente ausentes: «não», «nada», «tudo», «nunca», «sem», «só», «mais»
> — em Pessoa são palavras-chave, não ruído. **«Não sou nada» é a abertura da
> Tabacaria.**»

Mesma palavra, dois papéis opostos, e os dois corretos. **É por isto que as
listas não se unificam.**

---

## 2. A remoção, no BM25

Uma linha, no fim do `tokenizar`:

```python
return [p for p in t.split() if p not in STOPWORDS and len(p) > 1]
```

Precede-a a normalização ortográfica da Fase 2 — e **a ordem importa**: as
elisões expandem-se **antes** de a pontuação sair, senão `p'ra` reduz-se ao
*token* `ra`, que é lixo, e `cousa` nunca casa com `coisa`.

O filtro `len(p) > 1` apanha o resto: letras soltas da elisão e iniciais.

### 2.1 Quanto remove, medido nos 2290 *chunks*

| | |
|---|---|
| palavras medianas por *chunk* | **70 → 42** |
| removido | **41%** |
| *chunks* que ficam **sem termos** | **0** (0,00%) |

A classe `IndiceLexical` prevê o caso de ficarem vazios — «*chunks* que ficam sem
termos depois das *stopwords* quebrariam o BM25» — e mantém-nos fora da máscara
com um *token* sentinela `"\x00"`. **Medido agora: a defesa nunca dispara neste
corpus.** É código que existe por precaução e não por observação, e vale dizê-lo.

### 2.2 O efeito nas consultas é o que se vê melhor

```
tokenizar("o que é a natureza?")        -> ['natureza']
tokenizar("Não sou nada. Nunca serei nada.") -> ['não','sou','nada','nunca','serei','nada']
```

A primeira colapsa a um termo. A segunda **sobrevive inteira** — e é esse o ponto
da lista revista à mão: num corpus em que «não», «nada» e «nunca» são o assunto,
removê-las apagaria o poema.

### 2.3 Porque é que a lista é uma *string* e não uma lista de literais

Está escrita como `"""a o as os …""".split()`. O `ruff` quer o contrário
(`SIM905`) e **aplicá-lo fez dano medido**: transformou as três listas em
literais de ~500 caracteres numa linha só, levando com elas o comentário que
explica as ausências deliberadas. A regra está desligada no
[`pyproject.toml`](../../pyproject.toml) com esse motivo escrito.

> **Uma lista de *stopwords* é uma decisão editorial, não dados.** O formato que
> a mantém legível e anotável vale mais que a convenção do linter.

---

## 3. A detecção, na guarda — e o instrumento que media a coisa errada

É a parte que custou mais a acertar, e a história está no `CONTROLO.md`
(correcção 12).

A guarda rejeitava respostas com fracção de *stopwords* abaixo de **0,12**. A
correr o chatbot, à pergunta «qual é o futuro de portugal?», rejeitou isto por
«idioma improvável (fracção pt 0,077)», custando 38 s de nova geração:

> os passos ecoam / silêncio envolve / vogais cantam / pés descalços ligam terra
> ar / brotam esperanças / raízes aprofundam

**É português inequívoco.** O que lá não há são palavras funcionais: o registo é
telegráfico.

**E o primeiro diagnóstico — «o limiar está alto» — estava errado.** Contra o
corpus, 0,12 rejeita **3 de 1906** poemas portugueses (**0,16%**), e um desses
três é francês. Os poemas reais têm mediana **0,385** e p5 **0,267**.

> **O limiar estava bem posto. O instrumento é que media registo e chamava-lhe
> língua.**

### 3.1 A correcção: três perguntas, em ordem de custo

| | pergunta | o que a sustenta |
|---|---|---|
| 1 | há *stopwords* em abundância? | mediana 0,385 (pt) e 0,375 (en); resolve **99,8%** dos casos sem subprocessos |
| 2 | outra língua pontua mais que a pedida? | pt dá 0,385 na própria e 0,048 na alheia. Em **2058** poemas, **zero** pontuam mais na língua errada |
| 3 | o dicionário reconhece o vocabulário? | **a única que não depende do registo** |

A terceira é a que separa o caso telegráfico do latim, e é a única que o faz:

| | dicionário pt |
|---|---|
| verso telegráfico (o caso observado) | **1,000** |
| latim (a falha da Fase 0) | **0,043** |
| poemas reais | p1 **0,857** |

`MIN_FRACAO_DICIONARIO = 0,50` fica no meio dessa lacuna, com folga deliberada
porque o dicionário é pós-acordo de 1990 e rejeita **7,1%** do vocabulário real
de Pessoa.

### 3.2 E o teste relativo sozinho não bastava — provou-o um teste que já existia

Escrevi a versão relativa (pergunta 2), ela passou no meu próprio caso de latim,
e **reprovou no do repositório**: o latim de `tests/test_guard.py` contém `se`,
que é *stopword* portuguesa, logo pontua 0,040 em pt contra 0,000 em inglês e
**passaria**.

**Uma amostra inventada por mim concordou comigo; a amostra observada na Fase 0
não.** É o argumento mais forte deste projecto a favor de guardar os casos reais
em testes.

### 3.3 A lista inglesa inclui arcaísmos, de propósito

`thy`, `thou`, `thee`, `doth`, `hath`. Pessoa foi educado em Durban e publicou
os *35 Sonnets* em 1918; **sem elas, um poema à maneira dos sonetos pontuaria
baixo na língua em que foi escrito.** A lista de *stopwords* tem de descrever o
inglês **deste** autor, não o inglês de 2026.

### 3.4 Sem autoridade sobre a língua, a guarda é inerte

`Lang.INDETERMINADO` existe para poemas curtos demais para classificar, e
`_STOPWORDS` **não o cobre**. Antes da correcção, `fracao_lingua` caía
silenciosamente no português e a guarda dava **quatro poemas reais** por língua
errada — `poem_3516`, `poem_3525`, `poem_4281`, `poem_4372`, entre eles
«Iniguais pertencemos.»

A correcção é uma linha no `lingua_errada`:

```python
if esperada not in _STOPWORDS:
    return False
```

**«Não sei» não pode virar «está errado».** E a ressalva simétrica está no outro
extremo: quando não há dicionário, volta-se ao limiar absoluto e **rejeita-se** —
porque «não sei» também não pode virar «está bem» sem perder a guarda contra o
latim, que é o modo de falha que ela existe para apanhar.

Medido depois: **0 falsos positivos em 2058 poemas reais**, e apanha os três
modos de falha (latim, inglês quando se pediu português, e o inverso).

---

## 4. A classificação, no *parse*

A terceira lista decide a língua de cada poema do corpus, por maioria simples:

```python
pt = sum(1 for p in palavras if p in _PT) / len(palavras)
en = sum(1 for p in palavras if p in _EN) / len(palavras)
```

Empate ou texto sem palavras → `Lang.INDETERMINADO`. É deliberadamente a mais
pequena das três listas (31 e 24): o trabalho é separar duas línguas muito
distantes, e um classificador mais fino não compraria nada.

**E esta lista tem consequências a jusante que não são óbvias**: é ela que
decide o que entra no índice por idioma, o que a guarda espera, e quais os 1906
poemas portugueses contra os quais todas as fases calibraram instrumentos.

---

## 5. Onde as *stopwords* **não** entraram, e porquê

| | |
|---|---|
| **no encoder denso** | o `e5` é um modelo de frase; retirar palavras funcionais estragaria o que ele aprendeu a representar |
| **no prompt do gerador** | o modelo recebe **verso puro**. O `text` do *chunk* não leva nem metadados nem filtros |
| **nos instrumentos de forma** | a rima, o metro e a próclise contam versos e terminações; remover palavras funcionais apagaria precisamente a próclise |

---

## 6. Resumo

1. **Três listas, um só uso de remoção.** As outras duas usam *stopwords* como
   **sinal** de língua, não como ruído.
2. **`guard-PT − lexical = {'mais', 'não'}`** — a mesma palavra é ruído para o
   BM25 e sinal para a detecção de língua, e as duas leituras estão certas.
3. **A remoção corta 41%** das palavras dos *chunks* e nunca deixa um *chunk*
   vazio neste corpus.
4. **O limiar de língua estava bem posto e o instrumento errado.** Uma fracção de
   *stopwords* mede **registo**, e verso telegráfico é português a 1,000 de
   dicionário e 0,077 de *stopwords*.
5. **Nunca se devolve «está errado» quando a resposta é «não sei»** — e, no outro
   extremo, nunca «está bem».
6. **A lista é uma decisão editorial**, e o formato que a mantém anotável vale
   mais que a convenção do linter.

**Ficheiros:** [`src/retrieval/lexical.py`](../../src/retrieval/lexical.py) ·
[`src/guard.py`](../../src/guard.py) ·
[`src/corpus/parse.py`](../../src/corpus/parse.py) ·
[`CONTROLO.md`](../CONTROLO.md) correcção 12 e a secção da guarda de idioma.
