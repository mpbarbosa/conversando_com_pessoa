# Transferência neste projecto: é tudo, e nada foi treinado

Documento temático, escrito em 2026-10-12, sétimo da série. **Não é uma fase.**

**Não há *fine-tuning*, nenhum `LoRA`, nenhum conjunto de treino** — os únicos
`from_pretrained` em `src/` são tokenizadores e o `model.py`, que é código morto
marcado para remoção. **E ao mesmo tempo este projecto é quase todo
transferência:** cinco modelos pré-treinados, nenhum treinado aqui, todos a
servir um domínio que nenhum deles viu.

> **E os achados mais úteis desta linha são falhas de transferência medidas**,
> não sucessos. O §1 é o caso mais claro: um reranker do MS MARCO que põe o poema
> das árvores em último.

---

## 1. Os cinco, e para que foram treinados

| componente | modelo | treinado para | aplicado a |
|---|---|---|---|
| encoder | `intfloat/multilingual-e5-base` | recuperação multilingue | poesia de 1915 |
| reranker | **`BAAI/bge-reranker-v2-m3`** | reordenação multilingue | idem |
| *controlo negativo* | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` | **MS MARCO** — passagens web | idem |
| gerador | `llama3.1:8b-instruct-q4_K_M` | instrução geral | escrever em verso como Pessoa |
| ortografia | `aspell -d pt_PT` | português **pós-1990** | português **pré-1990** |

**Nenhum foi adaptado. Todos foram medidos.**

---

## 2. A falha mais clara: o reranker do MS MARCO

O `mmarco-mMiniLMv2` era o padrão «quando a latência parecia ser o
constrangimento». O [`rerank.py`](../../src/retrieval/rerank.py) di-lo assim:

> «É **mau em poesia portuguesa** e está medido: **+0,018**, e dada «o que vês
> numa árvore?» põe **o poema das árvores em último**. Fica como **controlo
> negativo**.»

O escolhido é o `bge-reranker-v2-m3`, com **+0,090 nDCG@5** por +2,6 s.

**Um modelo de *ranking* de passagens web transferiu quase nada para verso** — e
o projecto ficou com o mau **no código, como controlo**, em vez de o apagar. É a
mesma escolha que fez com o latim da Fase 0 e com o `_RE_PREAMBULO`: guardar o
caso que falha onde ele possa reprovar uma versão futura.

### 2.1 E a adaptação que melhorou a transferência foi **encurtar**

```python
TRUNCAR_TOKENS = 120
#: Truncar **melhora** a qualidade, não só a velocidade, e está reproduzido em
#: três truncagens e dois modelos: a n=20, 120 tokens dá +0,127 e 256 dá menos.
```

> «A abertura do *chunk* carrega o tema; a cauda acrescenta **ruído** ao
> cross-encoder.»

**É aproximar a entrada daquilo que o modelo viu no treino** — o MS MARCO são
passagens curtas — e o ganho é de **qualidade**, não só de tempo. Está
reproduzido em três truncagens e dois modelos, o que é mais do que a maioria dos
números deste projecto tem.

---

## 3. A transferência entre **épocas ortográficas** falha, com número

O `aspell` é pós-acordo de 1990 e o corpus é pré-1990. Medido no
[`lexico.py`](../../src/lexico.py):

> «vocabulário real de Pessoa que o `aspell` **rejeita**: **593 tipos (7,1%)**»

Foi isso que forçou o desenho de **duas autoridades** — corpus *e* dicionário —
em vez de uma, e foi o mesmo argumento que recusou o lematizador: **adequado ao
problema e treinado na língua errada** (ver
[`LEMATIZACAO.md`](LEMATIZACAO.md) §3).

**E a 5R mostrou que o corpus sozinho também não substitui:** as formas
canónicas que interessavam aparecem **8, 7 e 2** vezes em 2083 poemas. **Nenhuma
das duas autoridades transfere bem, e é por isso que são duas.**

---

## 4. O que transferiu foi **família**, não escala — e está medido duas vezes

É o achado mais interessante desta linha, e vem de duas fases independentes.

### 4.1 A 5N separou capacidade de família

| | salto | efeito em 3a′ | |
|---|---|---|---|
| **dentro** da família (qwen 3b → 7b) | **+145%** de parâmetros | +0,400 | **não significativo**, p=0,12 |
| **entre** famílias (qwen 7b → llama 8b) | **+5%** | **+0,700** | **p=0,0002** |

**Mais do dobro do efeito com 1/29 do aumento de parâmetros.** O que importou foi
a mistura de pré-treino, não o tamanho — e foi esse resultado que autorizou a
troca de modelo que está em produção.

### 4.2 E o roteador diz o mesmo por outro caminho

O 3B faz **42%** e o 7B **72%** na mesma tarefa de classificação, e a leitura
está escrita no [`roteador.py`](../../src/roteador.py):

> «o 3B a 42% contra o 7B a 72% diz o que a tarefa é — **conhecimento**, não
> padrão. **O 3B não sabe quem é Ricardo Reis.**»

**Duas medições, dois instrumentos, a mesma conclusão:** o que se transfere aqui
é conhecimento adquirido no pré-treino sobre um autor português, e isso não
escala com parâmetros dentro de uma família — muda com a família.

---

## 5. Duas armadilhas de API, e as defesas

### 5.1 O e5 exige prefixos, e sem eles falha **em silêncio**

> «O e5 **exige** `query: ` nas consultas e `passage: ` nos documentos. Sem eles
> funciona e devolve resultados **piores, sem avisar** — é a falha silenciosa
> clássica deste modelo.»

E a defesa não é uma asserção: são **dois métodos distintos**,
`encode_queries` e `encode_passages`, e **não há caminho para encodar texto sem
prefixo**. Uma convenção de transferência que não se pode esquecer porque não
existe a forma de a omitir.

### 5.2 E recomendei um modelo do artigo sem verificar

O `Serafim-335m-ir` era «o candidato preferencial» — e tem **`maxlen=128`**, que
**trunca ¼ dos poemas**. É a correcção 4 do [`CONTROLO.md`](../CONTROLO.md), e a
nota é minha: «Recomendei do artigo sem verificar».

**Uma métrica publicada num artigo é sobre o conjunto do artigo.** O que
transfere ou não transfere para 2083 poemas de 1915 não está lá escrito, e o
`maxlen` está — na ficha do modelo, a uma linha de distância.

---

## 6. Onde a transferência **não** chegou, e é o problema aberto

O [passo 34](../CONTROLO.md) é exactamente um limite de transferência, e três
vias de o contornar estão fechadas:

| via | fase | estado |
|---|---|---|
| detectar o defeito | 5R · 5T · 5U | fechada: 7 próclises e 1 marca em 120 amostras |
| instruir o modelo | 5V · 5W | fechada: a instrução existe, é ignorada, reforçá-la dá sinal negativo |
| mudar a descodificação | 5X · 5Z | sem efeito detectável, e a 0,9 degenera |

**O que sobra é afinação** — isto é, deixar de transferir e começar a treinar. E
está fora do que esta máquina faz em CPU, o que é uma conclusão de engenharia e
não de método.

---

## 7. Resumo

1. **Nada foi treinado**, e cinco modelos pré-treinados fazem todo o trabalho.
2. **O reranker do MS MARCO transferiu quase nada** — +0,018 contra +0,090 do
   `bge-m3` — e ficou no código **como controlo negativo**.
3. **A adaptação que funcionou foi encurtar a entrada** para 120 *tokens*, com
   ganho de **qualidade** reproduzido em três truncagens e dois modelos.
4. **O dicionário rejeita 7,1% do vocabulário de Pessoa**: transferir entre
   épocas ortográficas falha, e é por isso que há duas autoridades.
5. **O que transferiu foi família e não escala**: +145% de parâmetros dão +0,400
   n.s.; +5% com mudança de família dão +0,700 a p=0,0002.
6. **O e5 falha em silêncio sem prefixos**, e a defesa é arquitectural: não
   existe o caminho que permitiria esquecê-los.
7. **E o problema aberto do projecto é um limite de transferência** — três vias
   de o contornar sem treinar estão fechadas.

**Ficheiros:** [`src/retrieval/rerank.py`](../../src/retrieval/rerank.py) ·
[`src/retrieval/encoder.py`](../../src/retrieval/encoder.py) ·
[`src/lexico.py`](../../src/lexico.py) ·
[`src/roteador.py`](../../src/roteador.py) ·
[`FASE-5N-RELATORIO.md`](../FASE-5N-RELATORIO.md) ·
[`CONTROLO.md`](../CONTROLO.md) correcção 4.
