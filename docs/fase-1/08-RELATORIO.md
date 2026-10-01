# Fase 1 / Passo 8 — conjunto dourado

Construído em 2026-10-01. **Este é o instrumento que autoriza ou veta as Fases 2
e 3**, que existem exclusivamente para melhorar um número.

---

## Linha de base

| recuperador | nDCG@5 | apt@3 |
|---|---|---|
| **denso (`multilingual-e5-base`)** | **0,719** | **95%** |
| BM25 (`rank_bm25`, stopwords revistas à mão) | 0,488 | 65% |

`apt@3 = 95%` significa que em 19 de 20 perguntas há um poema de nota 2 no
top-3. A sobreposição entre os dois recuperadores é de **mediana 1/5**, e **zero
em 9 das 40 perguntas** — vêem coisas muito diferentes, o que dá margem real à
fusão da Fase 2.

---

## 1. O desenho, e porque não é o do plano

A §6.1 do plano especificava «40–60 perguntas, cada uma com 1–3 poemas
esperados» e recall@k. **Inválido neste corpus**, como a Fase 0 mostrou: Pessoa
escreveu dezenas de quadras sobre cada tema.

O que foi feito:

| | |
|---|---|
| perguntas | **40** (10 por voz), das quais 13 vêm do conjunto de fumo da Fase 0 |
| julgadas | **20** (5 por voz) |
| candidatos | **176** julgados |
| escala | 0 / 1 / 2 |
| candidatos | pooling TREC: top-5 do denso **e** do BM25, deduplicado por grupo, ordenado por id |
| métricas | **nDCG@5** (usa a graduação) e apt@3 |

### A nota 1 mais estrita

Na Fase 0 fui permissivo e a métrica saturou: o `util@3` deu 9/10 até ao
controlo inglês, porque o corpus é tematicamente tão uniforme que «adjacente» é
quase sempre verdade. Aqui `1` significa **«serviria se nada melhor houvesse»**.

Efeito: 68% dos candidatos têm nota ≥1 aqui, contra 67% na Fase 0 — mas a
distribuição mudou de forma, com 33% de nota 2 contra 23% antes. A métrica
discrimina.

### BM25 escrito fora da sua fase

`src/retrieval/lexical.py` pertence à Fase 2, e foi escrito aqui por uma razão
metodológica: **um gabarito construído só com candidatos do denso ficaria
enviesado a favor dele**, e a Fase 2 existe para comparar os dois. A
normalização ortográfica da Fase 2 não está lá.

---

## 2. Consciência de grupos

A deduplicação do Passo 2 marcou 21 poemas como duplicados, e o `poem_1000` —
gabarito de uma pergunta do conjunto de fumo — passou a não-representante de
`poem_629`. O gabarito resolve o grupo: procurar por qualquer membro dá a mesma
nota. Há um teste para isso.

---

## 3. O achado: 7 de 12 gabaritos do fumo não entraram no pool

Verificação que não estava planeada e que mudou a leitura dos resultados.

| pergunta | gabarito | posição no denso | no BM25 | leitura |
|---|---|---|---|---|
| q31 | `poem_100` | **6** | 125 | pool raso |
| q03 | `poem_2566` | **7** | 98 | pool raso |
| q05 | `poem_1000` | **9** | 22 | pool raso |
| q32 | `poem_1046` | 17 | 145 | fronteira |
| q12 | `poem_163` *(Tabacaria)* | **37** | 34 | **falha real** |
| q33 | `poem_1440` | **79** | 244 | **falha real** |
| q34 | `poem_116` | **172** | >300 | **falha real** |

Duas conclusões opostas, e as duas verdadeiras:

**O pool de top-5 era demasiado raso.** Três gabaritos estavam entre a 6.ª e a
9.ª posição do denso. Top-10 teria apanhado quatro dos sete.

**Mas há falhas genuínas.** A *Tabacaria* em 37.º para «sinto que não sou
ninguém e ao mesmo tempo que carrego tudo o que poderia ter sido» é mau: é o
poema mais óbvio do corpus para esse tema, e abre com «Não sou nada. Nunca serei
nada. Não posso querer ser nada. À parte isso, tenho em mim todos os sonhos do
mundo.» O `poem_116` em 172.º é pior.

**E, em todos os sete casos, o pool continha um poema de nota 2.** A recuperação
encontrou sempre algo apto, mesmo falhando o gabarito nomeado. Isso valida o
desenho de relevância graduada — e explica porque o `apt@3` é 95% enquanto o
nDCG@5 é 0,719: o sistema acha quase sempre *algo* bom, raramente *o melhor*.

### Reparação

Os sete gabaritos foram acrescentados ao julgamento, todos reconfirmados como
nota 2. Juntar documentos relevantes conhecidos ao pool é prática padrão: um
ideal incompleto inflaciona o nDCG.

---

## 4. Limitação metodológica, documentada no teste

**Enviesamento de pooling.** O gabarito foi construído a partir do denso e do
BM25, e ambos são avaliados sobre um gabarito que ajudaram a criar. Um sistema
terceiro — o reranker da Fase 3, ou a fusão da Fase 2 se mudar a ordem — pode
trazer documentos relevantes nunca julgados, que contam **0** por omissão.

**Procedimento obrigatório** ao avaliar um sistema novo: agrupar também o seu
top-5, julgar os candidatos novos, e só então comparar. Está escrito no topo de
`tests/test_retrieval_gold.py`, onde quem for fazer a Fase 2 o vai ler.

---

## 5. Outras limitações

| | |
|---|---|
| **Avaliador único** | eu, e o mesmo que escreveu as perguntas. Não é medição intersubjectiva |
| **20 de 40 julgadas** | as outras 20 estão no pool e na folha, prontas a julgar |
| **Pool de top-5** | demasiado raso, como a §3 mostrou. Top-10 na próxima ronda |
| **Não mede voz nem verso** | só recuperação. A pergunta aberta do Passo 7 — se o modelo é a voz pedida quando não copia — precisa de avaliação de geração às cegas, que isto não é |

---

## 6. O que fica autorizado

| | |
|---|---|
| **Fase 2** (busca híbrida) | ✅ tem contra o que medir: denso 0,719 · BM25 0,488 · sobreposição 1/5 |
| **Fase 3** Passos 2–4 (rerank) | ✅ tem contra o que medir, e já sabe a latência (Passo 1 feito) |

A Fase 2 arranca com uma hipótese forte: duas listas que concordam em 1 de 5
posições são o caso em que RRF costuma dar mais.

---

## 7. Próximos passos deste conjunto

```
[ ] julgar as 20 perguntas restantes (q06-q10, q16-q20, q26-q30, q36-q40)
[ ] repetir o pooling com top-10 em vez de top-5
[ ] investigar as 3 falhas reais, chunk a chunk (a hipótese do chunking foi refutada)
[ ] avaliação de geração às cegas, com RAG, para a pergunta da voz
```

### A hipótese do chunking: testada e **refutada**

Escrevi acima, na primeira versão deste relatório, que a *Tabacaria* em 37.º
apontava para poemas longos serem penalizados pelo chunking, por os seus chunks
ficarem diluídos. **Testei e está errado.**

Entre os poemas de nota 2, posição mediana no ranking:

| | posição mediana |
|---|---|
| 1 chunk (n=52) | **4,0** |
| mais de 1 chunk (n=5) | **4,0** |

Sem efeito. E o poema mais partido de todos — `poem_135`, *Ode Marítima*, **43
chunks, 9704 palavras** — está em **1.º lugar**. O `poem_2459` (*Ode Triunfal*,
10 chunks) em 2.º.

Tentei então uma segunda hipótese: que o encoder favorece vectores concentrados,
logo poemas curtos. Comparei o comprimento dos poemas por nota (nota 2: mediana
56 palavras; nota 0: 112). **Teste inválido:** a nota é o *meu julgamento*, não a
posição no ranking, logo isso mede o meu gosto por poemas curtos e não o
enviesamento do encoder. O teste certo já estava feito e não mostra efeito.

**A Tabacaria em 37.º fica sem explicação.** Não tenho hipótese que sobreviva à
medição, e inventar uma seria pior que registar a ignorância. É a primeira coisa
a investigar na próxima ronda, e o caminho provável é olhar chunk a chunk: qual
dos 8 chunks da *Tabacaria* pontua melhor, e porquê não o primeiro, que abre com
«Não sou nada. Nunca serei nada.»
