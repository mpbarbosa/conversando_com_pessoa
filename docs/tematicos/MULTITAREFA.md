# Multi-tarefa neste projecto: um modelo, duas tarefas opostas, e o custo medido

Documento temático, escrito em 2026-10-12, nono da série. **Não é uma fase.**
Companheiro do [`TRANSFERENCIA.md`](TRANSFERENCIA.md).

**Não há aprendizagem multi-tarefa** — não há treino nenhum. **Mas há uso
multi-tarefa de um modelo único, e o custo da partilha tem um número exacto:
72% → 68%.** Saiu de uma fase inteira, a [5S](../FASE-5S-RELATORIO.md), e é a
parte desta linha que vale.

---

## 1. O gerador e o roteador partilham a instância

Duas linhas, que a 5S encontrou com `grep`:

```
src/generation/ollama.py:41   MODELO = "llama3.1:8b-instruct-q4_K_M"
src/cli.py:372                s = aquecer(pipeline.gerador)
```

O `rotear(pergunta, gerador)` recebe um `Generator` por parâmetro, e o CLI
passa-lhe **o do pipeline**.

### 1.1 E as duas tarefas são o problema oposto uma da outra

| | gerador | roteador |
|---|---|---|
| tarefa | escrever verso | classificar voz |
| `temperature` | **0,9** | **0,0** |
| porquê | medido às cegas na Fase 0, para verso | «a mesma pergunta não pode dar vozes diferentes em duas sessões» |

O [`roteador.py`](../../src/roteador.py) já tinha a distinção escrita — «o
gerador usa 0,9… um classificador é outra coisa». **O que não estava escrito é
que partilhavam o modelo:**

> «Partilharem o modelo é um **acidente da ligação**, não uma escolha.»
> — [`FASE-5S.md`](../FASE-5S.md) §1

---

## 2. O custo, medido **antes** de mudar a constante

A 5S ia trocar `MODELO` por causa do poeta, e percebeu que isso mudaria
**silenciosamente** o roteador — cujos 72% tinham sido medidos na Fase 4 com o
qwen. Correu o bench daquela fase **sem o alterar**, nas mesmas 40 perguntas
etiquetadas:

| roteador | certos | exactidão | caeiro | campos | **reis** | ortónimo |
|---|---|---|---|---|---|---|
| `qwen2.5:7b` (Fase 4) | 29/40 | **72%** | 0,7 | 0,9 | 0,5 | 0,8 |
| `llama3.1:8b` (5S) | 27/40 | **68%** | 0,5 | 0,7 | **0,9** | 0,6 |

**Duas perguntas em 40** — e o §5.1 do protocolo escreveu, **antes de medir**,
que «uma diferença de uma ou duas perguntas não se lê como diferença», fixando o
limiar em 0,65 para não fingir precisão que 40 itens não dão.

**E o custo é baixo por desenho**, não por sorte: a Fase 4 decidira que **o
roteador propõe e não decide**, porque a 72% uma em quatro iria à voz errada. Uma
proposta que o utilizador vê e corrige com uma tecla não é o mesmo que uma
decisão silenciosa.

### 2.1 A partilha passou de acidente a decisão, e está fixada por teste

```
tests/test_generation.py:196
def test_o_modelo_de_servico_e_o_llama_e_o_roteador_partilha_o():
```

O teste afirma **duas** coisas: a constante, e que `OllamaGenerator().modelo` é a
mesma constante — isto é, **que a partilha é deliberada**. Se alguém separar os
dois modelos, é ali que se vê que a partilha foi medida.

---

## 3. A tensão clássica do multi-tarefa apareceu, e tem nome

**Os dois modelos são complementares.** O llama faz **0,9 no Reis** contra 0,5 do
qwen e é pior nas outras três, e os seus erros têm direcção: `caeiro`→`reis`
quatro vezes, `ortonimo`→`campos` quatro. **Sobre-roteia para o Reis.**

**O *optimum* de cada tarefa é um modelo diferente** — e é exactamente o
compromisso que a aprendizagem multi-tarefa existe para gerir, aqui sem treino
para o gerir.

O híbrido está **costeado e não feito**: poeta llama, roteador qwen, ao preço de
**dois modelos de ~5 GB em memória** e possível recarga por pergunta no `/auto`.
Vale 4 pontos de exactidão **numa proposta**, e o §5.2 da 5S diz o que medir
primeiro.

> **E a afinidade llama–Reis chegou a ser o achado confirmado por três
> instrumentos independentes** — a distribuição de comprimento (5M), a predição
> registada (5K) e este roteamento (5S). **A auditoria da
> [5Y](../FASE-5Y-RELATORIO.md) derrubou a primeira perna**, e ficaram duas. O
> roteamento é uma delas.

---

## 4. Duas outras partilhas de objecto, e uma vazou

O mesmo padrão — **um objecto a servir duas tarefas** — aparece duas vezes mais,
com resultados opostos:

| | as duas tarefas | resultado |
|---|---|---|
| **`Chunk`** | `text` vai ao **prompt** (verso puro); `indexed_text` vai ao **índice** (com «Autor — Título» à cabeça) | ❌ **vazou** |
| **encoder e5** | `encode_queries` e `encode_passages` | ✅ **não vazou** |

**O vazamento do `Chunk` custou ~23 pontos.** Cinco das oito linhas da tabela de
roteamento usavam *embeddings* de `indexed_text`, enquanto as consultas são verso
puro — **os centróides carregavam o nome do heterónimo**. Corrigido, o centróide
sobe de 45% para **68%** e a vantagem do LLM cai de +27 para **+4 pontos**, que a
n=40 não se distinguem de zero. Ver
[`ENTIDADES.md`](ENTIDADES.md) §5.

**O e5 não vazou, e por desenho:** são dois **métodos** distintos, e «não há
caminho para encodar texto sem prefixo, logo não há como esquecer».

> **A diferença é instrutiva: o mesmo padrão falhou onde a separação era um
> campo e funcionou onde era uma assinatura de função.** Dois campos do mesmo
> objecto confundem-se em silêncio; dois métodos não se confundem, porque
> chamar o errado é visível na linha que o chama.

---

## 5. E uma terceira tarefa que o mesmo modelo faz sem o saber

O `interpretar` do roteador trata «pessoa» como ortónimo «porque é o nome que o
CLI usa no comando (`/pessoa`)» — enquanto a **guarda** trata a mesma cadeia como
**quebra de persona**.

**A mesma palavra, duas tarefas, duas leituras opostas, e as duas certas:** na
saída é uma falha, na escolha de voz é a intenção. É o mesmo padrão das
*stopwords* que são ruído para o BM25 e sinal para a detecção de língua
([`STOPWORDS.md`](STOPWORDS.md) §1.1).

---

## 6. Resumo

1. **Não há aprendizagem multi-tarefa**, porque não há treino — mas há **uso
   multi-tarefa de um modelo único**.
2. **As duas tarefas são opostas**: verso a `temperature=0,9` e classificação a
   `0,0`, e partilhavam o modelo **por acidente da ligação**.
3. **O custo foi medido antes de mexer na constante partilhada**: **72% → 68%**,
   duas perguntas em 40, com o limiar escrito antes.
4. **E é baixo por desenho**: o roteador **propõe e não decide**, decisão da
   Fase 4.
5. **A partilha passou de acidente a decisão**, fixada por um teste que afirma a
   constante **e** a partilha.
6. **O *optimum* de cada tarefa é um modelo diferente** — llama 0,9 no Reis, qwen
   melhor nas outras três — e o híbrido está costeado em dois modelos de ~5 GB.
7. **O mesmo padrão vazou no `Chunk` e não vazou no encoder**: dois campos
   confundem-se em silêncio, duas assinaturas de função não.

**Ficheiros:** [`src/generation/ollama.py`](../../src/generation/ollama.py) ·
[`src/roteador.py`](../../src/roteador.py) ·
[`src/cli.py`](../../src/cli.py) ·
[`FASE-5S.md`](../FASE-5S.md) §1 e §5.2 ·
[`FASE-5S-RELATORIO.md`](../FASE-5S-RELATORIO.md) §1.
