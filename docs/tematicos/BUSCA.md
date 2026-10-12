# A busca: o denso serve, e o subsistema híbrido não entra

Documento temático, escrito em 2026-10-12, décimo primeiro da série. **Não é uma
fase**, e é reunião.

**Quatro módulos de `src/retrieval/` não estavam cobertos por nenhum temático** —
`fusion.py`, `search.py`, `index.py` e a parte do `lexical.py` que não é
*stopwords*. E a primeira coisa a dizer sobre eles é que **o caminho de produção
não os usa**:

```
src/cli.py:143    idx = Index.load(chunks, enc, meta["assinatura"])
```

**Produção carrega o índice denso e mais nada.** O `BuscaHibrida` existe, está
correcto, cita o artigo original — e **não serve**.

---

## 1. A Fase 2 chama-se «Busca híbrida: **resultado negativo**»

| sistema | nDCG@5 | apt@3 | latência |
|---|---|---|---|
| **denso (`multilingual-e5-base`)** | **0,677** | **95%** | 332 ms |
| BM25 | 0,464 | 65% | **4 ms** |
| RRF 1:1 | 0,670 | 90% | 389 ms |
| RRF 2:1 a favor do denso | **0,681** | 90% | 546 ms |
| RRF 1:2 a favor do BM25 | 0,580 | 85% | 706 ms |

> «A melhor fusão dá **+0,004** de nDCG@5, **ruído a n=20**, e o `apt@3` **cai de
> 95% para 90%** em todas as configurações. O critério do Passo 3 era «supera a
> melhor das duas listas isoladas»; **não supera**.»

E nenhuma profundidade de fusão ajuda: 5 → 0,616 · 10 → 0,640 · 20 → 0,670 ·
40 → 0,621.

**A fusão não entra no sistema. O denso sozinho mantém-se.**

### 1.1 E a hipótese que a motivava era boa

Não foi um palpite. O Passo 8 da Fase 1 mediu a condição em que o RRF costuma
ganhar:

> «a sobreposição entre o top-5 denso e o top-5 BM25 é de **mediana 1/5**, e
> **zero em 9 das 40 perguntas**. Duas listas que concordam tão pouco são o caso
> em que o RRF costuma dar mais.»

**A condição verificou-se e o ganho não apareceu.** É um resultado negativo com
hipótese declarada e medida, que é a forma mais útil de o ser.

---

## 2. O RRF, e porque se escolhe fundir por **ordem** e não por pontuação

O [`fusion.py`](../../src/retrieval/fusion.py) cita Cormack, Clarke & Buettcher
(SIGIR 2009):

```
score(d) = Σᵢ 1 / (k + rankᵢ(d))
```

E a razão de ser ordem e não pontuação é um número:

> «Combina *rankings* **sem normalizar pontuações**, que é o ponto: o cosseno do
> e5 anda em **0,80–0,86** e o BM25 em **5–11**. Não são comparáveis em escala, e
> **qualquer normalização seria uma invenção**.»

### 2.1 `k = 60`, e deliberadamente não afinado

> «O valor do artigo original, com uma década de validação. **Mantido sem o
> afinar**: o conjunto dourado tem **20 perguntas julgadas**, demasiado pouco
> para ajustar um parâmetro sem sobreajustar.»

**É a decisão que mais contrasta com o resto do projecto**, que mede tudo: aqui
mediu-se que **não se pode medir**, e manteve-se o valor publicado.

### 2.2 E a desduplicação é por **poema**, não por *chunk*

> «dois *chunks* do mesmo poema são a mesma resposta, e contá-los duas vezes
> dar-lhes-ia o dobro do peso na fusão.»

---

## 3. O índice: `numpy` em vez de FAISS, por aritmética

| | |
|---|---|
| 2290 *chunks* × 768 dimensões | **7,0 MB** |
| uma busca | produto matriz-vector de **1,8 M** operações |

> «O `IndexFlatIP` do FAISS faz **exactamente o mesmo cálculo** — força bruta —
> com uma dependência a mais. IVF e HNSW existem para milhões de vectores e aqui
> **só trariam perda de recall**.»

O `faiss-cpu` saiu do `requirements.txt` por isto, com o motivo escrito lá.

### 3.1 O manifesto, e o defeito que ele corrige

> «Os ids do índice são **posicionais**. O índice só é reutilizável acompanhado
> da **ordem dos documentos** a partir da qual foi construído — sem ela, o id *i*
> não aponta para nada. Era o defeito do `retriever.py` original: gravava o
> índice [sem ela].»

É a mesma classe de defeito que o [`DADOS.md`](DADOS.md) §5 descreve nos meus
próprios ficheiros de medição: **dados que só significam algo acompanhados da
convenção com que foram produzidos.**

---

## 4. Então para que serve o BM25, se não serve para buscar?

**Para o gabarito não nascer enviesado.** É a decisão que o
[`DADOS.md`](DADOS.md) §4.2 descreve, e vale repetir aqui porque é a resposta à
pergunta óbvia:

> «Escrita no Passo 8 da **Fase 1**, **antes** da Fase 2 que a tem como
> objectivo, por uma razão metodológica: o conjunto dourado precisa de **pooling
> imparcial**. Um gabarito construído só com candidatos do encoder denso ficaria
> **enviesado a favor dele**, e a Fase 2 existe para comparar os dois.»

**O BM25 foi escrito para ser um candidato honesto ao gabarito que depois o
reprovou.** Se tivesse sido escrito depois, a Fase 2 teria comparado o denso
contra um adversário cujos documentos ninguém julgou — e o resultado negativo não
valeria nada.

---

## 5. O que **entrou** foi a reordenação

O que a Fase 3B mediu e embarcou:

| configuração | nDCG@5 | Δ | IC95% | sinais | p | latência |
|---|---|---|---|---|---|---|
| base (denso) | 0,606 | — | — | — | — | — |
| **`bge-m3` n=8 trunc120** | **0,696** | **+0,090** | [+0,005, +0,171] | **+16/−4** | **0,012** | **2,6 s** |
| `bge-m3` n=20 trunc120 | 0,733 | +0,127 | [+0,031, +0,221] | +14/−5 | 0,064 | 8,4 s |

**Escolhido o n=8**, e a razão é latência contra um ganho que não se distingue:
«n=20 dá +0,124, mas a diferença é +0,033 com IC95% [−0,017, +0,081]».

E a fronteira do *pool* é o **top-20 do denso**, «e nunca mais de 20», porque «um
reranker que vá mais fundo volta a pontuar documentos **não julgados**, e o Δ
medido deixa de valer».

**O reranker está desligado por omissão** e ligado em `/rerank`: custa 2,6 s, e
«é a parcela que o utilizador paga por uma escolha que pode desligar».

Os dois achados de transferência desta parte — o reranker do MS MARCO como
controlo negativo, e truncar a melhorar a **qualidade** — estão no
[`TRANSFERENCIA.md`](TRANSFERENCIA.md) §2.

---

## 6. Resumo

1. **Produção carrega o índice denso e mais nada.** O `BuscaHibrida` existe e não
   serve.
2. **A Fase 2 é um resultado negativo declarado**: a melhor fusão dá **+0,004**,
   ruído a n=20, e o `apt@3` **cai** de 95% para 90% em todas as configurações.
3. **E a hipótese que a motivava era boa e verificou-se** — sobreposição mediana
   de 1/5 entre as duas listas — e o ganho não apareceu.
4. **O RRF funde por ordem e não por pontuação**, porque o cosseno anda em
   0,80–0,86 e o BM25 em 5–11, e normalizar «seria uma invenção».
5. **O `k=60` não foi afinado de propósito**: 20 perguntas julgadas não bastam.
   Mediu-se que não se podia medir.
6. **Não há FAISS por aritmética**: 7,0 MB e 1,8 M operações por busca.
7. **O BM25 sobrevive por uma razão que não é buscar**: foi escrito uma fase
   antes para que o gabarito que o reprovou não nascesse enviesado.
8. **O que entrou foi a reordenação**: +0,090 nDCG@5 por 2,6 s, desligada por
   omissão.

**Ficheiros:** [`src/retrieval/fusion.py`](../../src/retrieval/fusion.py) ·
[`src/retrieval/index.py`](../../src/retrieval/index.py) ·
[`src/retrieval/search.py`](../../src/retrieval/search.py) ·
[`src/retrieval/lexical.py`](../../src/retrieval/lexical.py) ·
[`FASE-2-RELATORIO.md`](../FASE-2-RELATORIO.md) ·
[`FASE-3B-RELATORIO.md`](../FASE-3B-RELATORIO.md).
