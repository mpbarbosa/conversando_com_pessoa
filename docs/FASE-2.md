# Fase 2 — Busca híbrida

Protocolo de execução da Fase 2 de [`PLANO-RAG-LOCAL.md`](PLANO-RAG-LOCAL.md).

**Objectivo:** juntar à recuperação densa uma recuperação **lexical** (BM25) e
fundir as duas listas por RRF, para apanhar o que o embedding dilui.

**Pré-requisito:** Fase 1 completa, incluindo o conjunto dourado do Passo 8.
Sem ele não há como saber se a fusão melhorou — e esta fase existe
exclusivamente para melhorar um número.

**Duração:** 1 dia.

---

## 1. Por que esta fase existe

O problema nomeado na §2 do plano: **similaridade semântica é o objectivo
errado para poesia**. O embedding de «AS ILHAS AFORTUNADAS» captura imagética
marítima e registo arcaico; a pergunta «o que é a saudade?» não se parece com
isso vectorialmente, mesmo sendo o poema certo.

Em poesia as palavras exactas pesam: «Tejo», «tabacaria», «Lídia», «Neera»,
«alcatifa». São nomes próprios e termos raros — exactamente onde o BM25 ganha
e o denso perde.

Evidência do corpus: a Fase 0 mostrou que o `all-MiniLM-L6-v2` monolíngue dava
**0/13** no conjunto de fumo. Não medimos ainda quanto um BM25 puro daria. **É
a primeira coisa a medir nesta fase**, e pode ser humilhante: a literatura
(BEIR, §3.1 da bibliografia) mostra que o BM25 é linha de base robusta fora do
domínio de treino, e poesia portuguesa de 1915 é o caso extremo disso.

---

## 2. O problema específico: ortografia

Pessoa escreveu antes do acordo de 1911 e os manuscritos têm variação. O corpus
mostra, medido na Fase 1 Passo 2:

| Forma | Variante no corpus |
|---|---|
| `coisa` | `cousa` |
| `pelo` | `p'lo` |
| `para o` | `prò` |
| `dourou` | `doirou` |
| `umbela` | `umbrela` |
| `Panteão` | `Pantéon` |

BM25 é lexical: `cousa` e `coisa` são tokens distintos e não casam. Isto
**não** é um problema teórico — foi observado nos pares de variantes
detectados no Passo 2 da Fase 1.

### Decisão: normalizar, não lematizar

**Não usar stemmer.** O Snowball português reduz `cousa`→`cous` e
`coisa`→`cois`: continua a não casar, e destrói terminações que em verso
carregam rima. Stemming resolve flexão, não ortografia histórica.

Em vez disso, uma camada de **normalização ortográfica explícita**, aplicada aos
dois lados (documento e consulta):

1. minúsculas, remoção de pontuação, colapso de espaços
2. expansão de elisões: `p'lo`→`pelo`, `prò`→`para o`, `d'água`→`de água`
3. tabela de equivalências históricas, povoada a partir do corpus
4. **sem** remoção de acentos — em português o acento distingue palavras
   (`e`/`é`, `a`/`à`, `pode`/`pôde`)

A tabela do ponto 3 tem de ser **construída a partir do corpus**, não de
memória. Procedimento no §4.

### Stopwords

Remover stopwords portuguesas do índice BM25, **mas não as mais frequentes em
verso**: `não`, `nada`, `tudo`, `nunca`, `sem`, `só` são palavras-chave em
Pessoa, não ruído. A lista tem de ser revista à mão, não importada.

---

## 3. Arquitectura

```
src/retrieval/
├── encoder.py       # (Fase 1) e5 com prefixos
├── index.py         # (Fase 1) numpy + manifesto
├── lexical.py       # NOVO: BM25 sobre os chunks
├── normalize.py     # NOVO: normalização ortográfica
├── fusion.py        # NOVO: RRF
└── search.py        # (Fase 1, alterado) orquestra denso + lexical + fusão
```

### RRF

```python
def rrf(listas: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    """Reciprocal Rank Fusion (Cormack, Clarke & Buettcher, SIGIR 2009).

    score(d) = sum_i 1 / (k + rank_i(d))

    Combina rankings sem normalizar pontuações — que é o ponto: a pontuação
    de cosseno do e5 e a do BM25 não são comparáveis em escala.
    """
```

`k=60` é o valor do artigo original. **Mantê-lo até haver medição que justifique
mudá-lo** — é um parâmetro com uma década de validação e o nosso conjunto
dourado tem 40–60 perguntas, demasiado pequeno para o afinar sem sobreajustar.

### Pesos

RRF puro trata as duas listas como iguais. Se a medição mostrar que uma domina,
usar RRF ponderado: `w_denso / (k + rank)` e `w_lex / (k + rank)`. **Só com
evidência**, e com os pesos registados no `config.py`.

---

## 4. Passos

### Passo 1 — Linha de base lexical nua (2 h)

Antes de fundir, medir o BM25 **sozinho** no conjunto dourado. Com e sem
normalização ortográfica, para isolar o efeito dessa camada.

```
            nDCG@5   apt@3
denso (e5)    ?        ?     <- da Fase 1
BM25 cru      ?        ?
BM25 normal.  ?        ?
```

**Aceite:** a normalização ortográfica melhora o BM25. Se não melhorar,
**remover a camada** em vez de a manter por parecer certa.

### Passo 2 — Tabela de equivalências a partir do corpus (3 h)

Procedimento, não intuição:

1. Construir o vocabulário completo (19 965 tipos, medido)
2. Para cada par de tipos com distância de edição ≤ 2 e frequência ≥ 2,
   listar os candidatos a equivalência
3. **Filtrar à mão** — `cousa`/`coisa` sim, `mar`/`mal` não
4. Gravar em `data/equivalencias.tsv`, versionado e inspeccionável

O ponto 3 é trabalho humano e não deve ser automatizado: distância de edição
pequena junta palavras distintas com a mesma facilidade com que junta variantes.

### Passo 3 — Fusão e medição (3 h)

```
                       nDCG@5   apt@3   latência
denso                     ?        ?        ?
BM25                      ?        ?        ?
RRF(denso, BM25)          ?        ?        ?
```

**Aceite:** `nDCG@5` da fusão supera a melhor das duas listas isoladas. Se não
superar, **reverter e registar o resultado negativo** — uma fase que não
melhora um número não entra no sistema.

### Passo 4 — Latência (1 h)

BM25 com `rank_bm25` é Python puro sobre ~2 800 chunks: deve ser < 50 ms, isto
é, irrelevante face aos 28 s de prefill medidos na Fase 0. **Verificar, não
assumir** — `rank_bm25` pontua todos os documentos a cada consulta.

Se for lento, a alternativa é um índice invertido próprio com acumulação
esparsa; mas a esta escala é improvável ser preciso.

---

## 5. Riscos

| Risco | Sinal | Resposta |
|---|---|---|
| BM25 bate o denso sozinho | nDCG@5 do BM25 > e5 | não é problema — é informação. Reponderar a fusão a favor do lexical |
| A fusão não melhora nada | nDCG@5 igual ou pior | reverter; registar. O denso e o lexical podem estar a errar nas mesmas perguntas |
| Tabela de equivalências com falsos positivos | recall sobe e precisão cai | filtro humano no Passo 2; tabela versionada para auditoria |
| Sobreajuste ao conjunto dourado | tudo melhora e nada melhora na prática | não afinar `k` nem pesos com 40–60 perguntas; manter os valores da literatura |

---

## 6. Checklist

```
[ ] 1  normalize.py com expansão de elisões, sem remoção de acentos
[ ] 2  lista de stopwords revista à mão (manter «não», «nada», «tudo», «nunca»)
[ ] 3  lexical.py com BM25 sobre os chunks
[ ] 4  BM25 nu medido no conjunto dourado, com e sem normalização
[ ] 5  data/equivalencias.tsv construído do corpus e filtrado à mão
[ ] 6  fusion.py com RRF, k=60
[ ] 7  tabela comparativa: denso / BM25 / RRF em nDCG@5 e apt@3
[ ] 8  latência do BM25 verificada (< 100 ms)
[ ] 9  decisão registada, incluindo se for negativa
```
