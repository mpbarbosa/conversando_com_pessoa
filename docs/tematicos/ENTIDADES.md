# Entidades nomeadas neste projecto

Documento temático, escrito em 2026-10-12, quarto da série depois do
[`TOKENIZACAO.md`](TOKENIZACAO.md), do [`STOPWORDS.md`](STOPWORDS.md) e do
[`LEMATIZACAO.md`](LEMATIZACAO.md). **Não é uma fase.**

**Não há NER no sentido habitual** — nenhum `spacy`, `stanza`, `flair` ou `nltk`,
e nenhum modelo de etiquetagem de entidades. Verificado antes de escrever, e as
sete dependências de produção não incluem nenhum.

**Mas há um problema de entidade nomeada no centro deste projecto**, e é mais
difícil que o habitual: as entidades são **heterónimos**, e três dos seus nomes
são palavras comuns em português.

> «em português `pessoa` é palavra comum, `reis` são reis e `campos` são campos —
> e Caeiro escreve sobre os campos constantemente.»
> — [`src/guard.py`](../../src/guard.py)

E **este documento traz uma medição nova**, que fiz ao escrevê-lo e que nunca
tinha sido feita: o detector de nomes **rejeita 1,61% dos poemas autênticos**,
dez vezes a taxa da guarda de idioma. O §4 mostra porquê, e **13 dos 31 casos são
falsos positivos de um tipo que o projecto já tinha diagnosticado noutro
instrumento.**

---

## 1. Dois sistemas, dois problemas opostos

| | onde | o problema |
|---|---|---|
| **resolução** | [`corpus/parse.py`](../../src/corpus/parse.py) | dada uma cadeia de autor no ficheiro, **que entidade é** |
| **detecção** | [`guard.py`](../../src/guard.py) | dado um poema gerado, **há ali um nome que não devia estar** |

O primeiro é mundo fechado e resolve-se com uma tabela. O segundo é o difícil, e
é onde está o trabalho.

---

## 2. Resolução: 19 entradas, e a ortografia do ficheiro não é de confiança

O `_AUTORES` mapeia cadeia → `(nome canónico, Voice)`. Dezanove entradas para
**sete** vozes, porque a mesma entidade aparece escrita de várias maneiras:

| `Voice` | entradas |
|---|---|
| `outro` | 12 |
| `campos` | **2** |
| `ortonimo`, `reis`, `caeiro`, `search`, `soares` | 1 cada |

**As duas do Campos são a parte interessante:**

```
'alvaro de campos'  -> ('Álvaro de Campos', Voice.CAMPOS)
'lvaro de campos'   -> ('Álvaro de Campos', Voice.CAMPOS)
```

A segunda não é um erro de escrita meu: é uma chave **para *mojibake***. Quando
o `Á` se perde na codificação, o que resta é `lvaro`, e a entrada existe para o
apanhar.

A normalização que precede a consulta faz quatro coisas, e cada uma apanha um
defeito observado no corpus:

```python
_chave('Álvaro de Campos')    -> 'alvaro de campos'
_chave('ALVARO DE CAMPOS')    -> 'alvaro de campos'
_chave('Ãlvaro de Campos')    -> 'alvaro de campos'   # mojibake
_chave('  Fernando   Pessoa ')-> 'fernando pessoa'
```

Decompõe acentos e deita fora os combinantes, remove o que não é ASCII nem
alfabético, **corta lixo de codificação à cabeça** (`re.sub(r"^[^A-Za-z]+", "")`)
e colapsa espaços.

> **A tabela é pequena porque o mundo é fechado.** Um `NER` estatístico aqui não
> teria nada a ganhar: há sete entidades, conhecem-se todas, e o problema real
> não é descobri-las — é a codificação do ficheiro.

---

## 3. Detecção: três sinais, porque um não chega

O modo de falha é observado, não imaginado. Da Fase 0:

> «(este poema não é do Reis, mas da minha voz...)», «Reis, na minha voz»,
> «Álvaro suspira em espírito de fuga».

**A primeira versão procurava «Pessoa», «Reis» e «Campos» sem distinguir
maiúsculas, e isso é um gerador de falsos positivos.** A correcção tem três
sinais:

### 3.1 Dois níveis de nome

```python
_NOMES_INEQUIVOCOS = ("Álvaro de Campos", "Alberto Caeiro", "Ricardo Reis",
                      "Fernando Pessoa", "Bernardo Soares", "Álvaro",
                      "Caeiro", "Soares")
_NOMES_AMBIGUOS    = ("Reis", "Campos", "Pessoa")
```

Os inequívocos «nunca aparecem inocentemente num poema português». Os ambíguos
coincidem com palavras comuns e **só contam com linguagem meta à volta**.

### 3.2 A maiúscula, que é um sinal e não um detalhe

Os inequívocos são procurados com `re.I`; **os ambíguos não**. A diferença é
deliberada e é o terceiro sinal: `Reis` conta, `reis` não. É o que separa «Olho
os campos, Neera» — que é Reis a sério — de «este poema é do Campos».

### 3.3 E a desambiguação do mais específico

```python
# «Álvaro de Campos» já implica «Álvaro»: manter só o mais específico
```

Sem isto, um poema que diga «Álvaro de Campos» seria reportado três vezes
(`Álvaro de Campos`, `Álvaro`, e `Campos` se houvesse meta). É resolução de
sobreposição de menções, e é a mesma operação que um `NER` faz ao escolher o
*span* mais longo.

---

## 4. A medição que faltava: o detector rejeita 1,61% dos poemas autênticos

Este projecto exige de cada guarda que ela seja medida contra o corpus — foi
assim que o `lingua_errada` ficou com os seus 0,16% (3 de 1906). **Ao
`_nomes_indevidos` isso nunca foi feito.** Fiz agora, nos 1926 poemas
portugueses:

| | n | % |
|---|---|---|
| **marcados** | **31** | **1,61%** |
| — só por nome de heterónimo | 17 | 0,88% |
| — só por **linguagem meta** | **13** | **0,67%** |
| — ambos | 1 | |

**É dez vezes a taxa da guarda de idioma, e esta guarda rejeita** — o motivo
entra em `motivos` e faz `ok=False`.

### 4.1 Os 17 do nome são verdadeiros positivos por desenho, e desconfortáveis

```
poem_212   «(Álvaro de Campos, nascido no Algarve, educado por um tio-avô,»
poem_1104  «Desembrulhar-me e ser eu, não Alberto Caeiro,»
```

O primeiro é a nota biográfica de Pessoa sobre Campos. O segundo é **Pessoa a
nomear Caeiro dentro de um poema, como poesia**. A guarda rejeitaria os dois, e
está a fazer o que lhe mandaram: numa **resposta gerada**, nomear o heterónimo é
quebra de persona. Mas o preço é que 17 poemas autênticos não passariam.

### 4.2 Os 13 da linguagem meta são falsos positivos, e do tipo que o projecto já conhece

O que o `_RE_META` apanhou no corpus real:

| padrão | poemas |
|---|---|
| `estes versos` | **7** |
| `a minha voz` / `da minha voz` / `minha voz` | **7** |

E os casos são inequívocos:

```
poem_163   «A caligrafia rápida destes versos,»
poem_1068  «A alma da minha voz?»
```

**Nenhum dos dois é meta-comentário.** São poemas a falar da sua própria
caligrafia e da sua própria voz — que é *assunto* de poesia, não um chatbot a
explicar-se. O `_RE_META` existe para apanhar «este poema não é do Reis, mas da
minha voz», e apanha também qualquer poema cujo tema seja a voz.

> **É exactamente o defeito do `lingua_errada`, noutro instrumento.** Ali a
> fracção de *stopwords* media **registo** e chamava-lhe **língua**; aqui o
> `_RE_META` mede **auto-referência** e chama-lhe **meta-comentário**. A lição
> está escrita no [`CONTROLO.md`](../CONTROLO.md) correcção 12 desde a Fase 3, e
> este instrumento não foi medido contra ela.

**E a consequência prática é maior do que parece**, porque a linguagem meta é
também o **portão** dos nomes ambíguos (§3.1): um poema sobre «a minha voz» que
mencione `Campos` é rejeitado duas vezes pelo mesmo erro.

**Isto não entra em `src/` agora.** É um achado de documento, sem protocolo e sem
portão — e a disciplina deste projecto diz que uma alteração a uma guarda se
pré-registra. Fica no [`CONTROLO.md`](../CONTROLO.md) como passo.

---

## 5. Onde o nome da entidade **vazou** e estragou uma medição

É a história mais cara desta linha, e está no
[`src/roteador.py`](../../src/roteador.py).

Cinco das oito linhas da tabela de roteamento usavam `idx.vectores`, que são
*embeddings* de `Chunk.indexed_text` — e esse leva **«Autor — Título» à cabeça**,
enquanto as consultas são verso puro. **Os centróides carregavam o nome do
heterónimo.**

| | antes | depois da correcção |
|---|---|---|
| centróide, perguntas | 45% | **68%** |
| centróide, poemas | 42% | **64%** |
| vantagem do LLM (72%) | +27 pontos | **+4 pontos** |

**E a frase que estava publicada — «nenhum método de *embedding* passa dos
52,5%, o espaço não separa estas vozes» — foi refutada pela própria correcção.**
A +4 pontos com n=40, o roteador LLM **não está estabelecido** como melhor que um
centróide corrigido.

> **O nome da entidade estava do lado do índice e não do lado da consulta, e isso
> subestimou um método em ~23 pontos.** É o caso mais claro deste projecto de uma
> entidade nomeada a contaminar uma medição — e nota-se que o defeito não era
> reconhecer mal a entidade: era **ter o nome lá**.

Três das cinco linhas afectadas **não foram re-medidas**, e os seus números não
valem em nenhum sentido.

---

## 6. E um sítio onde o nome é deliberadamente aceite

O `interpretar` do roteador lê a palavra que o modelo devolveu, e tem uma
cláusula que é normalização de entidade:

```python
if "pessoa" in t or "ortónimo" in t:
    return Voice.ORTONIMO
```

«Pessoa» vale como ortónimo porque é o nome que o CLI usa no comando
(`/pessoa`). **A mesma cadeia que a guarda trata como quebra de persona, o
roteador trata como nome válido da voz** — e as duas leituras estão certas,
porque os contextos são opostos: na saída é uma falha, na escolha de voz é a
intenção.

E a função devolve `None` em vez de palpitar: «nas 92 chamadas medidas o modelo
nunca deixou de incluir a palavra — mas um dia deixará, e aí o resultado é
`None`, não um palpite».

---

## 7. Resumo

1. **Não há NER estatístico**, e não faria falta: o mundo é fechado com sete
   entidades conhecidas.
2. **O problema difícil é a ambiguidade**: `Reis`, `Campos` e `Pessoa` são
   palavras comuns em português, e a solução são **três sinais** — dois níveis de
   nome, a maiúscula, e um portão de linguagem meta.
3. **A resolução de autores é uma tabela de 19 entradas para 7 vozes**, e a
   redundância existe para *mojibake*: `'lvaro de campos'` é uma chave a sério.
4. **Medido agora, e é novo: o detector rejeita 1,61% dos poemas autênticos** —
   dez vezes a guarda de idioma. 17 por nomear um heterónimo (verdadeiro
   positivo por desenho) e **13 por linguagem meta, que são falsos positivos**.
5. **E são o mesmo defeito do `lingua_errada`**: o `_RE_META` mede
   auto-referência e chama-lhe meta-comentário, como a fracção de *stopwords*
   media registo e chamava-lhe língua. «A alma da minha voz?» é poesia.
6. **O nome da entidade vazou para os centróides do roteador** e subestimou um
   método em **~23 pontos**, refutando uma frase publicada.

**Ficheiros:** [`src/guard.py`](../../src/guard.py) ·
[`src/corpus/parse.py`](../../src/corpus/parse.py) ·
[`src/roteador.py`](../../src/roteador.py) ·
[`CONTROLO.md`](../CONTROLO.md) correcção 12.
