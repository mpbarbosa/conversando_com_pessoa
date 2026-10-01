# Fase 3 — Reranking: **medição inconclusiva**, não integrado

Executada em 2026-10-01. Passo 1 (latência) em
[`FASE-3-PASSO-1.md`](FASE-3-PASSO-1.md); Passos 2–4 aqui.

---

## Decisão

**O reranker não entra no sistema.** Não por ser mau, mas porque **a medição
não consegue decidir**, e integrar com base num número cujo sinal se inverte
seria pior que não integrar.

---

## 1. O que a qualidade parecia dizer

Gabarito ampliado para 291 candidatos, com o top-5 de cada reranker agrupado e
julgado antes de medir.

| sistema | nDCG@5 | Δ | apt@3 | latência |
|---|---|---|---|---|
| denso (e5), sem rerank | 0,638 | — | **95%** | — |
| MiniLM-L12 n=20 sem trunc | 0,616 | **−0,022** | 85% | 2,8 s |
| MiniLM-L12 n=10 sem trunc | 0,605 | −0,033 | 95% | 1,7 s |
| MiniLM-L12 n=20 trunc 120 | 0,656 | +0,018 | 95% | 1,5 s |
| bge-base n=20 trunc 256 | 0,647 | +0,009 | 90% | 7,0 s |
| bge-base n=10 sem trunc | 0,630 | −0,008 | 85% | 4,5 s |
| **bge-m3 n=8 trunc 256** | **0,726** | **+0,088** | 95% | 8,2 s |
| **bge-m3 n=8 trunc 120** | **0,712** | **+0,074** | 95% | **2,0 s** |

Duas coisas pareciam estabelecidas. O modelo que o Passo 1 quase desqualificou
por latência — o `bge-m3` de 568M — era o único a ganhar de forma clara. E
**truncar a 120 tokens mantinha quase todo o ganho a um quarto do custo**, o que
sugeria que a abertura do chunk carrega o tema e a cauda acrescenta ruído ao
cross-encoder.

---

## 2. O ganho é artefacto do pooling

O gabarito foi ampliado com os candidatos **destes rerankers**. Medido contra as
três versões do gabarito:

| gabarito | candidatos | denso | + rerank | Δ |
|---|---|---|---|---|
| original (só denso + BM25) | 176 | 0,719 | 0,671 | **−0,048** |
| + candidatos da fusão | 209 | 0,677 | 0,678 | +0,001 |
| ampliado (tudo) | 291 | 0,638 | 0,712 | **+0,074** |

**O sinal inverte-se conforme o gabarito.** No original o reranker é pior por
0,048; no ampliado é melhor por 0,074.

Nenhum dos dois é limpo:

- O **original** penaliza o reranker por construção: os documentos que ele
  promove nunca foram julgados, logo contam 0.
- O **ampliado** tem o top-5 de ambos os sistemas julgado, o que o torna mais
  defensável — mas o ideal cresceu de tal forma que o denso caiu de 0,719 para
  0,638 sem nada mudar no denso.

### O desempate: `apt@3` não vê diferença nenhuma

| gabarito | denso | + rerank | Δ |
|---|---|---|---|
| original | 95% | 95% | **0** |
| + fusão | 95% | 95% | **0** |
| ampliado | 95% | 95% | **0** |

`apt@3` é binário — «há uma resposta de nota 2 no top-3?» — e é muito menos
sensível ao crescimento do ideal. **Nos três gabaritos, com e sem reranker, a
resposta é a mesma: 95%.**

Logo o nDCG@5 está a medir **qual** das respostas certas aparece, não **se**
aparece.

---

## 3. É o mesmo tecto da Fase 2, e agora com duas confirmações

A Fase 2 mediu: o denso leva 40 documentos de nota 2 no top-5 somado de 20
perguntas, a fusão leva 39. Há 84 documentos de nota 2 no gabarito, **mediana de
4 por pergunta**, e o top-5 só leva cinco.

Num corpus com tantas respostas certas por pergunta, **reordenar troca respostas
boas por outras respostas boas**. A fusão falhou por isso; o reranker falha por
isso; e o `apt@3` constante a 95% nos dois casos é a assinatura do mesmo tecto.

Isto não é propriedade dos algoritmos: é propriedade do corpus, medida desde a
Fase 0 (67% dos candidatos agrupados eram aproveitáveis).

---

## 4. O que diz o protocolo, e o que faço

O Passo 4 da `FASE-3.md` dizia: «Se não passar: registar o resultado negativo e
**manter o código fora do sistema**. Um reranker desligado por omissão é dívida.»

**Cumprido.** `src/retrieval/rerank.py` fica no repositório, testado, e **fora do
caminho de execução** — não desligado por configuração.

Guardo-o em vez de o apagar porque o que o limita é mensurável e pode mudar:

| condição | efeito |
|---|---|
| julgar as 20 perguntas restantes | n=40 pode resolver o sinal |
| agrupar a top-10 em vez de top-5 | elimina a ambiguidade do gabarito |
| orçamento de contexto maior que 300 tokens | mais lugares no top-k, menos tecto |
| conjunto dourado com mais de um avaliador | o julgamento deixa de ser meu |

---

## 5. O que esta fase estabeleceu de útil, apesar de inconclusiva

**A latência não é o obstáculo.** O Passo 1 derivou ~19 s para um reranker de
568M sobre 20 candidatos; medido, 34,59 s — a estimativa estava optimista. Mas
com truncagem a 120 tokens e 8 candidatos, o mesmo modelo custa **2,0 s**, que
é irrelevante contra os ~30 s de geração. A fase reescreveu-se duas vezes por
causa da latência e no fim a latência não decidiu nada.

**Truncar melhora a qualidade, não só a velocidade.** O MiniLM passa de −0,022
para +0,018 ao truncar a 120 tokens. Contra-intuitivo e reproduzido em dois
modelos.

**O procedimento de pooling é o que impediu uma conclusão errada.** Sem agrupar
e julgar os 82 candidatos novos, eu teria medido −0,048 e concluído que o
reranker piora. Com eles, +0,074 e concluiria que melhora. Foi ver os dois que
mostrou que nenhum é de confiança.

**O MiniLM é mau em poesia portuguesa, e isso é mensurável num caso.** Dada a
pergunta «o que vês numa árvore?» e três candidatos, põe o poema das árvores em
**último**. Treinado em mMARCO — recuperação web traduzida — não transfere. É
consistente com os −0,022 que mediu, e está fixado num teste.

**E dei dois alarmes falsos sobre o bge-m3**, ambos por não olhar para os
números em bruto. Primeiro vi «0.000» num `print` arredondado de um caso de
brinquedo e suspeitei que não discriminava, pondo em dúvida todo o Passo 2.
Depois escrevi que a sigmoide «comprime tudo perto de zero», na ordem de 1e-3.
Ambos errados: a gama é [0,1] e usada toda — a resposta certa dá **0,77** contra
**1,6e-05** do candidato errado. Os 0,0091 que tinha observado eram de uma
pergunta em que nenhum dos 12 candidatos era correspondência forte.

---

## 6. Estado das fases de melhoria

| fase | resultado |
|---|---|
| **2 — busca híbrida** | negativo: +0,004, ruído; `apt@3` cai de 95% para 90% |
| **3 — reranking** | inconclusivo: sinal inverte-se com o gabarito; `apt@3` inalterado |

Duas tentativas de melhorar a recuperação, duas sem efeito demonstrável, e a
mesma causa medida nas duas. **A recuperação densa simples parece estar no tecto
do que este corpus permite a k=5.**

O caminho que resta não é melhorar o ranking: é **mudar o que se mede**. O
`apt@3` de 95% diz que o sistema já encontra quase sempre uma resposta apta. A
pergunta aberta desde o Passo 7 da Fase 1 continua a ser a que importa — **se o
modelo é a voz pedida quando não copia** — e nenhuma métrica de recuperação a
responde.
