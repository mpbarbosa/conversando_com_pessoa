# Fase 1 / Passo 5 — orçamento de prompt

Medido em 2026-10-01 com `qwen2.5:7b-instruct-q4_K_M`, `threads=10`,
`taskset -c 0-11`, persona de Caeiro (313 tokens), `num_predict=150`.

## Medições válidas

Mediana de repetições. «Frio» = prefixo de sistema invalidado por nonce no
início; «quente» = sistema em cache, pergunta e contexto novos.

| poemas | user tok | prefill frio | prefill quente | decode | **1ª pergunta** | **seguintes** |
|---|---|---|---|---|---|---|
| 1 | 168 | 31,4 s | **10,7 s** | 23,1 s | 39,6 s | **33,7 s** |
| 2 | 398 | 41,6 s | 30,6 s | 24,3 s | 65,9 s | **54,9 s** |
| 3 | 448 | 45,0 s | **27,7 s** | 26,0 s | 67,8 s | **53,7 s** |
| 5 | 531 | ~47 s † | — | ~23 s | ~70 s | — |

† duas repetições apenas; a corrida foi interrompida.

Referência do orçamento (Fase 0 §7.1): alvo < 20 s · **tolerável < 45 s** ·
inutilizável > 90 s.

## O que se conclui, e o que não

**Robusto:** `n=1` cabe no orçamento (33,7 s a quente). `n≥2` não cabe
(~54 s).

**Não robusto:** a diferença entre 2 e 3 poemas. O `n=2` deu prefill quente
**maior** que o `n=3` (30,6 s contra 27,7 s) com **menos** tokens (398 contra
448). Isso é impossível e localiza o chão de ruído: as duas configurações são
indistinguíveis. Não afirmar que uma é melhor.

**Ganho do cache de prefixo:** 20,7 s em `n=1`, 17,3 s em `n=3`. Compatível com
os 313 tokens da persona a ~16 tok/s, que é o que se esperava.

**Taxa efectiva a quente:** ~16 tok/s de prefill (168 tok em 10,7 s; 448 tok em
27,7 s). A Fase 0 mediu 21,5 tok/s a frio; a diferença é plausivelmente térmica,
dado o estado da máquina após horas de carga.

**Decode:** 5,8–5,9 tok/s, abaixo dos 6,7 tok/s da Fase 0. Mesma causa provável.

## Medições descartadas

**`n=2` com `num_predict=110`:** o prefill quente da primeira repetição deu
**0,19 s** — cache completo do prompt inteiro, porque o bloco anterior já tinha
enviado o mesmo par (mesmo `n`, mesma pergunta, mesmo sistema). Perguntas
distintas por bloco resolveriam.

Foi a **quarta vez nesta sessão** que o cache de prefixo invalidou um desenho de
medição meu:

| # | Onde | Erro |
|---|---|---|
| 1 | Benchmark da Fase 0 | mesmo prompt repetido; prefill reportado a 25 625 tok/s |
| 2 | 1ª tentativa deste orçamento | variei só a pergunta; «frio» e «quente» mediam o mesmo |
| 3 | 2ª tentativa | nonce no **fim** do sistema; não invalida nada (2,42 s contra 16,7 s com o nonce no início) |
| 4 | Medição de `n=2` | mesmo par (n, pergunta) em dois blocos |

A lição operacional: num servidor com cache de prefixo, **cada medição precisa
de uma entrada que nunca foi enviada**, e a variação tem de estar no início do
que se quer medir a frio.

## Decisão

**`ORCAMENTO_USER = 300` tokens.**

Derivação da taxa medida a quente (~16 tok/s de prefill) e do decode medido
(~23 s para 150 tokens):

| orçamento | prefill quente previsto | total previsto |
|---|---|---|
| 260 | 16,3 s | 39,3 s ✅ |
| **300** | **18,8 s** | **41,8 s** ✅ |
| 320 | 20,0 s | 43,0 s ✅ limite |
| 400 | 25,0 s | 48,0 s ❌ |

300 tokens deixam ~243 para contexto depois do cabeçalho, rodapé e reserva — o
que dá **1 a 2 poemas** conforme o comprimento, já que a mediana de um chunk é
126 tokens do qwen.

É uma escolha por orçamento, não por contagem fixa: um poema curto deixa espaço
para um segundo, um longo ocupa tudo. Melhor que fixar «2 poemas» e ter a
latência a variar com o que a recuperação trouxer.

### A consequência desagradável

Com 1 a 2 poemas de contexto, **a qualidade da recuperação passa a importar
mais, não menos**: não há redundância que cubra uma escolha má. Isso reforça a
prioridade do conjunto dourado (Passo 8) e da busca híbrida (Fase 2) — que
deixam de ser melhorias e passam a ser necessários.

O argumento a favor é o achado da Fase 0: 67% dos candidatos agrupados eram
tematicamente aproveitáveis, o que torna plausível que um poema apto baste para
fundamentar a voz. Plausível, não demonstrado.

### O que fica por medir

- `num_predict` menor: 110 em vez de 150 deve poupar ~4–5 s, mas a medição foi
  contaminada. A repetir com perguntas distintas por bloco.
- Pausa de arrefecimento maior: a 45–60 s a máquina não volta ao estado inicial
  depois de horas de carga, e as taxas medidas aqui são ~25% abaixo das da
  Fase 0.
