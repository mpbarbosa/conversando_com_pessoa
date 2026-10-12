# A lematização neste projecto: não houve

Documento temático, escrito em 2026-10-12, terceiro da série depois do
[`TOKENIZACAO.md`](TOKENIZACAO.md) e do [`STOPWORDS.md`](STOPWORDS.md). **Não é
uma fase.**

**E a resposta curta é que este projecto não lematiza nem faz *stemming*, em
sítio nenhum.** Verificado antes de escrever:

```
grep -rniE "lemmatiz|lematiz|stemm|snowball|rslp|spacy|nltk|simplemma" src/ tests/
```

dá **zero** ocorrências de uso — só as quatro passagens que **explicam a
ausência**. E o `requirements.txt` tem sete dependências de produção, nenhuma
delas morfológica.

Isto não é uma omissão. É uma **decisão nomeada na Fase 2, com um custo que
apareceu medido na Fase 5C**, e é essa a história que falta num sítio só.

---

## 1. A decisão: «normalizar, não lematizar»

É o título de uma secção da [`FASE-2.md`](../FASE-2.md), e o problema que ela
resolvia era real e observado: o BM25 é lexical, logo `cousa` e `coisa` são
*tokens* distintos e não casam.

| forma | variante no corpus |
|---|---|
| `coisa` | `cousa` |
| `pelo` | `p'lo` |
| `para o` | `prò` |
| `dourou` | `doirou` |
| `Panteão` | `Pantéon` |

**O *stemmer* foi considerado e recusado com dois argumentos, e os dois estão
certos:**

> «O Snowball português reduz `cousa`→`cous` e `coisa`→`cois`: **continua a não
> casar**, e **destrói terminações que em verso carregam rima**. *Stemming*
> resolve flexão, não ortografia histórica.»

O primeiro argumento é decisivo por si: o problema era **ortográfico**, e um
lematizador trata **flexão**. Aplicar a ferramenta errada não tinha resolvido o
caso que motivou a fase.

Em vez dele entrou normalização ortográfica explícita, com uma regra que é o
oposto do que um lematizador faria: **sem remoção de acentos**, porque em
português o acento distingue palavras — `e`/`é`, `a`/`à`, `pode`/`pôde`.

### 1.1 E a tabela saiu muito mais pequena do que a fase previa

O [`normalize.py`](../../src/retrieval/normalize.py) foi construído **a partir do
corpus**, e o que ficou de fora importa tanto como o que entrou:

| entra | |
|---|---|
| **elisões** | 245 ocorrências em 80 formas — e `p'ra` (59) e `p’ra` (36) usam apóstrofos diferentes (U+0027 e U+2019), que o BM25 reduzia ambos ao *token* **`ra`** |
| **alternância `ou`/`oi`** | 13 pares reais da época: `coisa`/`cousa` (387/39), `ouro`/`oiro`, `loura`/`loira`, `papoila`/`papoula` |

| fica de fora | porquê |
|---|---|
| **todos os pares distinguidos por acento** | o meu gerador de candidatos usou «acento» como sinal de equivalência **apesar de a fase o proibir**, e propôs fundir `pais`/`país`, `bebe`/`bebé`, `faca`/`faça`, `seria`/`séria` — **palavras diferentes** |
| `facto`/`fato` | em português europeu são palavras diferentes: um facto e um fato |
| **lematização** | o argumento do §1 |

**Dos 11 candidatos com razão de frequência extrema, 8 eram palavras distintas
ou infinitivos com clítico** (`esquecê-lo`, `deixá-lo`). Os 3 restantes —
`duvida`, `gloria`, `angustia` — são plausivelmente gralhas, mas **nos três a
forma sem acento é também um verbo válido**: 8 ocorrências em 229 mil palavras,
«risco de correcção real por ganho nulo».

---

## 2. Onde a ausência custou: a Fase 5C

A [5C](../FASE-5C-RELATORIO.md) derivou do corpus uma lista de 40 palavras para
medir «atribuição de sentido», e declarou a ameaça **antes** de correr:

> «A lista **não é lematizada**. `sonhar` está na lista e `sonho`, `sonhos`,
> `sonhava` não, salvo se entrarem por mérito próprio. Sem lematizador garantido
> no ambiente, as formas de superfície são o que há, e isto **reduz a
> sensibilidade — nunca infla**.»

A fase correu e **falhou na validação retida**: AUC de **0,869 em amostra** para
**0,544** em dados retidos. É o pior resultado deste projecto, e o relatório
nomeia a lematização entre as causas prováveis:

> «Com 39 poemas na derivação, é provável que a falta de lematização contribua
> para a instabilidade: `sonhar` entra, `sonho` e `sonhos` não, e **qual das
> formas aparece nos 39 é sorte**. **Não foi isolado.**»

**Duas coisas a dizer com precisão, porque é tentador dizer mais:**

1. A ameaça foi declarada antes e a direcção prevista estava certa — perda de
   sensibilidade, não inflação.
2. **A contribuição nunca foi isolada.** O relatório di-lo, e eu repito-o aqui:
   não se sabe quanto do colapso de 0,869 para 0,544 é falta de lematização e
   quanto é 39 poemas serem poucos. A variante com outro contraste deu 0,568 —
   «igualmente inútil» —, o que mostra que o contraste **não** era o problema,
   mas não mostra que a lematização fosse.

---

## 3. Onde a ausência custa hoje, em produção

O [`lexico.py`](../../src/lexico.py) usa o corpus como autoridade ortográfica, e
tem a limitação escrita:

> «**Flexões ausentes do corpus dão falsos positivos.** O corpus tem 216 mil
> palavras e não cobre todas as formas das palavras que contém: `reflecte` está
> lá, **`reflectem` não**. `reflectem` é português europeu pré-acordo correcto,
> ausente por acaso, e o dicionário moderno rejeita-o — logo é sinalizado
> indevidamente. Com **16 085 tipos** de referência, cada flexão em falta é um
> falso positivo potencial.»

**E a frase seguinte é a avaliação honesta da alternativa:**

> «não há correcção barata: **um lematizador português resolveria parte, mas
> introduziria os seus próprios erros sobre grafia de 1915**.»

É o argumento que decide, e é diferente do da Fase 2. Ali a ferramenta era
**inadequada ao problema**; aqui seria adequada e **treinada na língua errada**.
Um lematizador de português moderno sobre um corpus pré-acordo de 1990 traz os
seus próprios falsos positivos, e trocar erros conhecidos por erros desconhecidos
não é um negócio.

**O que o projecto fez em vez disso:** a guarda lexical **reporta e não
rejeita**, porque uma palavra inventada não estraga um poema e rejeitar custa
~28 s. É a mesma escolha que a truncatura **não** teve (essa rejeita, desde o
passo 30) — e a diferença é que ali há defeito inequívoco e aqui há dúvida.

---

## 4. E há um sítio onde lematizar teria destruído um resultado

Este é o fecho da história, e não era previsível em 2026-10-01.

A Fase 2 recusou o *stemmer* dizendo que ele «destrói terminações que **em verso
carregam rima**». Na altura era um argumento de princípio: **não existia nenhum
instrumento de rima neste projecto.**

Dez fases depois, a [5V](../FASE-5V-RELATORIO.md) construiu um — e ele é
**exactamente** uma função da terminação:

```python
def chave_letra(verso: str) -> str | None:
    """Chave consoante a partir da penúltima **vogal-letra**."""
```

É a chave que mediu o achado mais forte dessa linha: o ortónimo real rima a
**0,8367** e o gerado a **0,3833**, que é o seu próprio nulo de permutação. Com
`cansada` e `nada` reduzidas a `cans` e `nad`, a chave não existe e o achado não
aparece.

> **Uma decisão de pré-processamento é uma decisão sobre que perguntas se poderão
> fazer depois.** A Fase 2 protegeu, por um argumento de poética, um instrumento
> que só seria construído dez fases mais tarde. Não foi previsão — foi recusar
> destruir informação que não se estava a usar.

### 4.1 E dois instrumentos mais que vão na direcção contrária

| instrumento | o que faz com a morfologia |
|---|---|
| [5R](../FASE-5R-RELATORIO.md), detector ortográfico | **gera** variantes de superfície a partir da canónica (`objecto`→`objeto`) — é lematização ao contrário |
| [5T](../FASE-5T-RELATORIO.md), próclise por atracção | precisa do pronome clítico **e** do hífen de ênclise; reduzir `dói-me` a um lema apaga a construção |
| `plagio.py` | compara versos normalizados só por minúsculas, pontuação e espaços (`_norm`) — deliberadamente de superfície, porque o plágio a detectar é cópia quase literal |

---

## 5. Resumo

1. **Não há lematização nem *stemming* neste projecto**, em sítio nenhum, e
   nenhuma dependência morfológica está instalada.
2. **Foi decisão nomeada na Fase 2**, com dois argumentos corretos: o *stemmer*
   resolve flexão e o problema era ortografia (`cous`/`cois` continuam a não
   casar), e destruiria terminações que carregam rima.
3. **O substituto foi normalização ortográfica construída do corpus** — elisões
   e `ou`/`oi` —, deliberadamente **sem** remoção de acentos.
4. **A ausência tem custo medido**: na [5C](../FASE-5C-RELATORIO.md) é nomeada
   entre as causas prováveis de a AUC cair de 0,869 para 0,544 em dados retidos
   — e **não foi isolada**, o que é parte da afirmação.
5. **Em produção o custo é o falso positivo da guarda lexical** (`reflecte` está
   no corpus, `reflectem` não), e a alternativa foi recusada por um argumento
   diferente: um lematizador moderno traria os seus próprios erros sobre grafia
   de 1915.
6. **E a recusa protegeu, sem o saber, o instrumento de rima da 5V**, que é uma
   função da terminação que um *stemmer* teria apagado.

**Ficheiros:** [`src/retrieval/normalize.py`](../../src/retrieval/normalize.py) ·
[`src/retrieval/lexical.py`](../../src/retrieval/lexical.py) ·
[`src/lexico.py`](../../src/lexico.py) ·
[`FASE-2.md`](../FASE-2.md) §«Decisão: normalizar, não lematizar» ·
[`FASE-5C-RELATORIO.md`](../FASE-5C-RELATORIO.md) §5.
