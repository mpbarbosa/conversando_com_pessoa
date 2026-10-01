# Relatório da Fase 3B — a reordenação entra, e o que a desbloqueou foi o gabarito

Executada em 2026-10-01. Protocolo em [`FASE-3B.md`](FASE-3B.md).

**Decisão: integrado.** `bge-reranker-v2-m3`, 8 candidatos, truncados a 120
tokens: **+0,090 de nDCG@5** por **2,6 s**, ligado em `/rerank` e desligado por
omissão.

A Fase 3 mediu este mesmo modelo e não conseguiu decidir. Não mudou o modelo nem
a máquina: mudou o **instrumento**.

---

## 1. O que estava a impedir a decisão

A Fase 3 mediu o mesmo reranker contra três gabaritos e obteve três respostas —
−0,048, +0,001 e +0,074 — porque **um poema não julgado conta 0** e o pool
crescia com cada sistema testado.

A correcção: um reranker sobre o top-20 do denso só pode promover documentos
desse top-20. Julgando-o **por inteiro**, o pool passa a ser definido pela
recuperação, que não muda, e deixa de depender de quem o construiu.

Custou **142 julgamentos**, e o gabarito passou de 291 para **433**, com 125
documentos de nota 2. Distribuição dos 142: **49 zeros, 52 uns, 41 dois**.

---

## 2. As quatro predições, confrontadas

Escritas no §3 do protocolo **antes** de medir.

| | predição | medido | |
|---|---|---|---|
| 1 | denso cai para 0,55–0,62; ~40 notas 2 novas (29%) | **0,606** e **41 notas 2 (29%)** | ✅ |
| 2 | oráculo@20 mantém-se acima de 0,90 | **0,980** — *subiu* de 0,956 | ✅ |
| 3 | bge-m3 trunc120 fica entre +0,03 e +0,09 | **+0,090** a n=8; **+0,127** a n=20 | ✅ no limite / ❌ por cima |
| 4 | `apt@3` fica em 95% e não discrimina | **95%** em todas menos uma | ✅ |

A predição 2 merece nota: esperava que o crescimento do ideal e o das notas 2 no
top-20 se cancelassem. Não se cancelaram — **o oráculo subiu e o denso desceu**,
e a folga passou de 0,316 para **0,374**. Fechar o pool tornou o argumento para
reordenar mais forte, não mais fraco.

---

## 3. A medição no pool fechado

| configuração | nDCG@5 | Δ | IC95% do Δ | sinais | p | apt@3 | latência |
|---|---|---|---|---|---|---|---|
| denso | 0,606 | — | — | — | — | 95% | — |
| **bge-m3 n=8 trunc120** | **0,696** | **+0,090** | [+0,005, +0,171] | **+16/−4** | **0,012** | 95% | **2,6 s** |
| bge-m3 n=12 trunc120 | 0,710 | +0,103 | [+0,020, +0,185] | +15/−5 | 0,041 | 95% | 3,7 s |
| bge-m3 n=20 trunc80 | 0,730 | +0,124 | [+0,027, +0,218] | +15/−5 | 0,041 | 95% | 4,7 s |
| bge-m3 n=16 trunc120 | 0,738 | +0,132 | — | — | — | 95% | 6,3 s |
| bge-m3 n=20 trunc120 | 0,733 | +0,127 | [+0,031, +0,221] | +14/−5 | 0,064 | 95% | 8,4 s |
| bge-m3 n=8 trunc256 | 0,678 | +0,072 | — | — | — | 95% | 5,4 s |
| bge-base n=20 trunc120 | 0,604 | −0,002 | — | — | — | **85%** | 1,9 s |
| MiniLM n=20 trunc120 | 0,624 | +0,018 | — | — | — | 95% | 0,6 s |
| **oráculo@20** | **0,980** | +0,374 | — | — | — | — | — |

O MiniLM entrou como **controlo negativo** e portou-se como tal: +0,018, o
menor ganho de todos. Se o pool fechado o tivesse mostrado a ganhar, era o pool
que estava errado.

### 3.1 Porque a mais barata, e não a de melhor Δ

**Nenhuma das configurações se distingue das outras.** Emparelhado:

| comparação | Δ | IC95% | sinais | p |
|---|---|---|---|---|
| n=20 trunc80 − n=8 trunc120 | +0,033 | [−0,017, +0,081] | +12/−5 | 0,14 |
| n=20 trunc80 − n=12 trunc120 | +0,020 | [−0,023, +0,064] | +8/−7 | 1,00 |
| n=20 trunc120 − n=20 trunc80 | +0,003 | [−0,019, +0,029] | +4/−6 | 0,75 |

Escolher a de cima por mais 0,033 que a medição não distingue de zero, pagando
mais 2 s, seria exactamente o erro que a Fase 2 evitou ao rejeitar +0,004 **por
ser ruído a n=20**. E a n=8 é também a que tem o sinal mais forte — 16 das 20
perguntas melhoram — e a mais barata. Não há troca a fazer.

### 3.2 O que os +0,090 valem, e o que não valem

O que está estabelecido é o **sinal**: 16 de 20 perguntas melhoram, p=0,012. A
**magnitude é incerta** — o IC95% vai de +0,005 a +0,171, e com n=20 perguntas
não dá para apertar.

Captura **24% dos 0,374** que o oráculo@20 mostra estarem no top-20. Três
quartos da folga continuam por reclamar.

E o `apt@3` fica em 95%, como em todas as medições desde a Fase 2: este reranker
muda **qual** das respostas certas aparece primeiro, não **se** aparece. A
leitura da Fase 3 — «o nDCG@5 mede qual das respostas certas aparece» — mantém-se
verdadeira; o que mudou é que agora isso vale +0,090 com o pool fechado, em vez
de um número que dependia do gabarito.

---

## 4. O que só apareceu a correr o CLI

O banco dizia 2,57 s. A primeira reordenação real custou **4,8 s**, porque no
banco descartei uma chamada de aquecimento e medi o caso quente — o mesmo erro
que cometi com o roteador na Fase 4, duas vezes na mesma sessão.

**Tentei eliminar o custo único e não consegui**, e as duas primeiras
explicações que dei estavam erradas:

1. «Aqueci com um par de duas palavras; é a forma do lote.» Aqueci com a forma
   real — 8 pares de 120 tokens — e continuou a custar 4,5 s.
2. «É contenção com o Ollama a carregar o gerador.» Medido em isolamento, sem
   Ollama nenhum, o efeito mantém-se.

A terceira medição encontrou a causa:

| | 1.ª reordenação | seguintes |
|---|---|---|
| isolado, sem aquecer | 4,77 s | 2,5 s |
| isolado, aquecido | **2,56 s** | 2,5 s |
| **com o e5 carregado antes, aquecido** | **4,56 s** | 2,5 s |
| no CLI, que tem sempre o e5 carregado | 4,8 s | 2,5 s |

**O aquecimento funciona em isolamento e não funciona no processo real.** Com o
encoder e5 residente — que é sempre o caso — a primeira reordenação volta a
custar 4,5 s.

O aquecimento foi **removido**: custava ~4 s de arranque e não tirava os 2,3 s
da primeira pergunta. Um componente que não faz o que diz é dívida. O custo
único passou a ser **anunciado** no `/rerank`, e há um teste que falha se
alguém voltar a acrescentar um aquecimento sem voltar a medir.

---

## 5. Integração

- `/rerank` liga, `/sem-rerank` desliga, `--rerank` arranca ligado.
- **Desligado por omissão**, porque 2,6 s num total de ~30 s é uma troca, e uma
  troca é do utilizador. Não é dívida de configuração: o Δ está medido e o custo
  está à vista.
- O modelo de 568M só é carregado quando alguém liga a reordenação.
- O rodapé mostra a reordenação **em parcela própria**, separada da recuperação:

```
  44 ms recuperação · 5.0 s reordenação · 12.8 s até ao 1.º verso · 7.7s prefill …
```

- `N_RERANK = 8` e a profundidade nunca passa de 20, porque **20 é a fronteira
  do pool fechado**. Um reranker mais fundo volta a pontuar documentos não
  julgados e o Δ medido deixa de valer.

237 testes a passar.

---

## 6. Checklist do protocolo

```
[x] 1  folha dos 142 candidatos gerada, por id, sem revelar ranking
[x] 2  142 julgados com a rubrica da Fase 1 Passo 8
[x] 3  gabarito em 433 julgamentos, top-20 denso completamente coberto
[x] 4  denso (0,606) e oráculo@20 (0,980) remedidos no pool fechado
[x] 5  rerankers remedidos; Δ sobre pool que nenhum ajudou a construir
[x] 6  as quatro predições confrontadas uma a uma (§2)
[x] 7  decisão pelo critério do Passo 3: Δ≥+0,03, ≤6 s, apt@3 não desce
[x] 8  integrado, com a latência à vista e desligado por omissão
```

### O que continua em falta

- **O avaliador é um só, e sou eu.** A Fase 3 §4 nomeou-o, a 3B não o resolveu, e
  os 433 julgamentos são todos do mesmo juízo. É a limitação maior que resta
  sobre toda a medição de recuperação deste projecto.
- **n=20 perguntas.** Chega para estabelecer o sinal, não a magnitude. As outras
  20 perguntas do conjunto continuam sem julgamento.
- **Três quartos da folga do oráculo.** +0,090 de +0,374.
- **E a pergunta que nenhuma destas fases responde:** se a voz gerada é a voz
  pedida. Quatro fases mediram recuperação; o produto é verso.

### Observado pelo caminho

`poem_224` aparece no top-20 do denso para `q11` e o seu texto é **mojibake**
(«O que hรก รฉ pouca gente para dar por isso»). É o poema com mojibake que o
`models.py` já nomeia. Julgado 0, e fica registado: há texto corrompido
indexado e recuperável.
