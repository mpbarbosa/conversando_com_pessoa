# Conjuntos de dados heterogéneos neste projecto

Documento temático, escrito em 2026-10-12, sexto da série. **Não é uma fase.**

**É o tema onde este projecto tem mais história — e onde cometi o erro mais
grosseiro de todos**, que foi tratar 152 poemas de Pessoa como ruído a filtrar.

Há **três** famílias de dados aqui, e cada uma é heterogénea por sua conta: o
corpus, o material de avaliação, e — a que menos se vê — **os dados de medição
que o próprio projecto produziu**.

---

## 1. O corpus: 2083 ficheiros que não são um conjunto

Medido ao escrever:

| | |
|---|---|
| ficheiros | **2083** |
| línguas | `pt` **1926** · `en` **153** · indeterminado **4** |
| vozes | ortónimo 1298 · Campos 324 · Reis 252 · Caeiro 120 · Search 52 · outro 31 · Soares 6 |
| cadeias de autor a apontar para 7 vozes | **19** |

**A razão entre a voz maior e a menor servida é de 18:1** (1298 contra 120 do
Caeiro) — e o Caeiro é a voz que o projecto mediu mais e serve melhor. O
desequilíbrio é dado de entrada, não escolha.

### 1.1 E o ficheiro não é de confiança

As três coisas que o [`parse.py`](../../src/corpus/parse.py) tem de absorver
antes de haver dados:

| | |
|---|---|
| **mojibake** | `_chave` decompõe acentos, deita fora não-ASCII e **corta lixo de codificação à cabeça**. O `_AUTORES` tem `'lvaro de campos'` como chave a sério, para quando o `Á` se perde |
| **título repetido no corpo** | em **82%** dos ficheiros, e removê-lo apagava 3 poemas cujo título **é** o poema — «Vou atirar uma bomba ao destino.» |
| **língua por maioria** | `_PT`/`_EN` de 31 e 24 palavras, empate → `INDETERMINADO`. Ver [`STOPWORDS.md`](STOPWORDS.md) §4 |

---

## 2. O erro: 152 poemas ingleses tratados como ruído

Apontado pelo **proprietário do repositório** em 2026-10-01, e estava em três
lugares do código ao mesmo tempo:

| onde | dizia | passa a |
|---|---|---|
| `dedupe.py` | a duplicação por tradução é «resolvida pelo filtro de idioma» | **não são marcados**; a autoria da `NAVAL ODE` não está estabelecida aqui |
| `lexico.py` | o inglês «contaminaria» o vocabulário de referência | a referência é PT **porque avalia respostas em PT** |
| `index.py` | `idioma=PT` resolve a duplicação | `idioma=PT` **porque a resposta é em português** — preferência de consulta, não juízo sobre o corpus |

**Pessoa foi educado em Durban, em inglês. Os *35 Sonnets*, o *Antinous* e as
*Inscriptions* são dele. E Alexander Search é um heterónimo que escrevia em
inglês**, com 52 poemas neste corpus.

> **Nenhuma das três linhas mudou de comportamento. As três mudaram de
> justificação.** O filtro continua lá e faz o mesmo; o que estava errado era a
> razão escrita ao lado, e uma razão errada propaga-se — foi ela que me deixou
> escrever «ruído» três vezes sem estranhar.

### 2.1 E o que fica em falta está declarado e não resolvido

| voz | poemas | estado |
|---|---|---|
| Alexander Search | 52 em inglês | **sem persona; o sistema não o serve** |
| Charles Robert Anon | 9 em inglês | idem |
| ortónimo em inglês | 92 (*Sonnets*, *Inscriptions*) | **inacessível** com `idioma=PT` |

São **153 poemas** — 7,3% do corpus — que existem no índice e nunca chegam a uma
resposta. O `voices.py` já tem personas inglesas para o ortónimo e para o Search;
o que falta é o caminho de consulta.

---

## 3. A deduplicação: três mecanismos distintos, e um indetectável

O [`dedupe.py`](../../src/corpus/dedupe.py) teve o desenho **mudado por
medição**, e as três conclusões estão no seu cabeçalho:

| | |
|---|---|
| **duplicados exactos** | **3 pares, não 1.** A contagem em bruto dizia 1; normalizar o corpo limpo revela os outros dois |
| **variantes** | ~12 pares: esboços («ODE MARCIAL»), revisões («D. FERNANDO»/«GLÁDIO»), transcrições divergentes («umbrela»/«umbela») e **contenção** — `poem_12` tem 26 versos, **todos** presentes nos 47 do `poem_619` |
| **tradução** | **não detectável por similaridade**: *ODE MARÍTIMA*/*NAVAL ODE* dá similaridade de verso **0,000**, e a inglesa é parcial (1094 palavras contra as do original) |

**E a métrica foi rejeitada por medição:**

> «O Jaccard de n-gramas de palavra **não serve**: pequenas diferenças
> palavra-a-palavra destroem a sobreposição sem mudar o poema. A métrica usada é
> ao **nível do verso**, normalizada pelo **poema mais curto**, que é onde as
> variantes de facto se parecem.»

A normalização pelo mais curto é o que torna a **contenção** visível: um
fragmento dentro de um poema maior tem sobreposição 1,00 do lado do fragmento e
0,55 do lado do todo.

---

## 4. A avaliação: duas decisões que vêm da diversidade das fontes

### 4.1 Relevância graduada, porque o gabarito único era inválido

O plano especificava «1–3 poemas esperados» por pergunta. A Fase 0 mostrou-o
inválido **neste** corpus, e com um caso:

> para «ofereço-lhe o meu afecto e ela nem repara» o encoder devolveu «Entreguei-te
> o coração, / E que tratos tu lhe deste!» — **casamento igualmente bom, contado
> como erro**.

Pessoa escreveu dezenas de quadras sobre cada tema. Daí **2 = responde bem, 1 =
aproveitável, 0 = não serve**, e nDCG@5 como métrica principal
([`avaliacao.py`](../../src/avaliacao.py)).

### 4.2 *Pooling* imparcial, garantido pela **ordem** em que o código foi escrito

É a decisão mais subtil desta linha, e está no cabeçalho do
[`lexical.py`](../../src/retrieval/lexical.py):

> «Escrita no Passo 8 da **Fase 1**, **antes** da Fase 2 que a tem como
> objectivo, por uma razão metodológica: o conjunto dourado precisa de **pooling
> imparcial**. Um gabarito construído só com candidatos do encoder denso ficaria
> **enviesado a favor dele**, e a Fase 2 existe para comparar os dois.»

**O BM25 foi escrito uma fase antes de ser preciso, para que o gabarito não
nascesse a favor do método que ele ia julgar.** E a fronteira do *pool* fechado é
o **top-20** do denso, com `N_RERANK = 8` e nunca mais de 20 — porque «um
reranker que vá mais fundo volta a pontuar documentos não julgados, e o Δ medido
deixa de valer».

---

## 5. A família que menos se vê: os dados que o projecto produziu

Nove fases emparelhadas deixaram nove `01-cru.jsonl`. **E o esquema derivou** —
medido ao escrever este documento, e não documentado em sítio nenhum:

| fases | campos | campos de texto |
|---|---|---|
| 5B · 5G | 26 | `texto`, `texto_cru` |
| 5H · 5I · 5M · 5N | 27 | `texto`, `texto_cru` |
| **5U · 5W** | **18** | `texto_cru`, **`texto_limpo`** |
| 5X | 20 | `texto_cru`, `texto_limpo` |
| **5Z** | 25 | + **`primeira_texto`** |

Renomeei `texto` para `texto_limpo` a meio da sequência e deixei cair nove
campos, e a auditoria da [5Y](../FASE-5Y-RELATORIO.md) teve de lidar com as duas
convenções ao mesmo tempo.

**E foi neste terreno — reutilizar dados entre fases — que apareceram os dois
defeitos mais caros do projecto:**

| | |
|---|---|
| **o tokenizador trocado entre fases** | a 5W com o e5 e a 5X com o do gerador: **18 de 20 prompts diferentes**, e eu li a diferença como «chão de ruído», publicando um número que depois retirei ([correcção 33](../CONTROLO.md)) |
| **a repetição a re-recuperar** | o `_repetir_sem` troca o contexto quando o modelo plagia, logo braços que repetiram têm prompts diferentes: **7% a 40% das células** contaminadas, fase a fase ([5Y](../FASE-5Y-RELATORIO.md)) |

> **Reutilizar dados entre fases é barato e não é grátis.** As duas vezes que
> este projecto pagou caro por um erro de medição, pagou aqui — e nos dois casos
> o defeito não estava nos dados: estava em eu assumir que dois conjuntos
> produzidos em momentos diferentes eram comparáveis.

### 5.1 E há uma família que se manteve sã

Os julgamentos cegos — `01-itens.md` (folha embaralhada), `01-chave.json`
(selada) e `02-pontuacoes.json` — atravessaram **três avaliadores em duas
sessões** sem problema de esquema, porque a chave é um `id` opaco e a folha nunca
leva metadados. **A convenção que não derivou foi a que foi desenhada para
esconder informação**, e não a que foi desenhada para a guardar toda.

---

## 6. Resumo

1. **2083 ficheiros, 3 línguas, 7 vozes, 19 cadeias de autor**, e 18:1 entre a
   voz maior e o Caeiro.
2. **Tratei os 153 poemas ingleses como ruído**, em três lugares do código. As
   três linhas mudaram de **justificação** e nenhuma de comportamento — e uma
   razão errada propaga-se.
3. **153 poemas (7,3%) continuam inacessíveis**: Search, Anon e o ortónimo
   inglês. Declarado, não resolvido.
4. **A deduplicação distingue três mecanismos** e admite que a tradução não é
   detectável — e rejeitou o Jaccard por medição, a favor de similaridade de
   verso normalizada pelo poema mais curto.
5. **A relevância é graduada porque o gabarito único era inválido**, com um caso
   observado a prová-lo.
6. **O BM25 foi escrito uma fase antes de ser preciso**, para o *pooling* não
   nascer enviesado a favor do método que ia julgar.
7. **O esquema dos meus próprios dados derivou** de 27 para 18 campos a meio da
   sequência — e foi a reutilização entre fases que produziu os dois defeitos
   mais caros do projecto.

**Ficheiros:** [`src/corpus/parse.py`](../../src/corpus/parse.py) ·
[`src/corpus/dedupe.py`](../../src/corpus/dedupe.py) ·
[`src/retrieval/lexical.py`](../../src/retrieval/lexical.py) ·
[`src/avaliacao.py`](../../src/avaliacao.py) ·
[`CONTROLO.md`](../CONTROLO.md) §«Correcção: a obra em inglês não é
contaminação» e correcção 33.
