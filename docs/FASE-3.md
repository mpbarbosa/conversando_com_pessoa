# Fase 3 — Reordenação (rerank)

Protocolo de execução da Fase 3 de [`PLANO-RAG-LOCAL.md`](PLANO-RAG-LOCAL.md).

**Objectivo:** um cross-encoder reordena os candidatos da Fase 2, de top-20
para top-4.

**Pré-requisitos:** Fase 1 completa (chunks, índice, conjunto dourado) e Fase 2
completa (lista fundida a reordenar).

**Duração estimada no plano:** meio dia. **Revista: 1 dia**, pelas razões do §1.

---

## 1. Esta fase tem um problema de latência, e é grave

O plano original dizia «custa 1–3 s em CPU; medir se o ganho justifica a
latência». **Essa estimativa está errada por um factor de 6 a 20.**

Derivado das medições da Fase 0: o `bge-m3` (568M parâmetros) processou o
corpus de 324 244 tokens em 1807 s, ou seja **179 tokens/s em CPU** nesta
máquina. Um cross-encoder da mesma classe de tamanho tem custo por token
comparável.

| Candidatos | Tokens por par | Carga | Latência derivada |
|---|---|---|---|
| 20 | 170 (mediana dos chunks) | 3 400 | **~19 s** |
| 20 | 350 (chunks maiores) | 7 000 | **~39 s** |
| 8 | 170 | 1 360 | ~7,6 s |

Contra o orçamento medido na Fase 0 — **28 s de prefill + 16 s de decode = 44 s
por resposta** — acrescentar 19 s leva o total a 63 s, e 39 s leva-o a 83 s.
A Fase 0 classificou >90 s como inutilizável e <45 s como tolerável.

**Um reranker de 568M sobre 20 candidatos não cabe neste hardware.**

Estes números são **derivados, não medidos**: extrapolam o custo por token de
um bi-encoder para um cross-encoder. O Passo 1 desta fase existe para os
substituir por medição — e a extrapolação pode estar optimista, porque um
cross-encoder processa a consulta e o documento juntos em cada passagem.

---

## 2. Consequência: o espaço de desenho muda

Em vez de «qual o melhor reranker», a pergunta é **«existe um reranker que caiba
no orçamento e ainda melhore o ranking?»**. Três eixos para cortar custo:

### 2.1 Modelo mais pequeno

| Modelo | Params | Custo relativo a 568M |
|---|---|---|
| `BAAI/bge-reranker-v2-m3` | 568M | 1,0 — ~19 s / 20 cand. |
| `BAAI/bge-reranker-base` | 278M | ~0,5 — ~9 s |
| `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` | ~120M | ~0,2 — ~4 s |

O MiniLM multilingual é o candidato óbvio para CPU. **A qualidade em português
europeu é desconhecida** e tem de ser medida, não assumida — foi exactamente o
erro que cometi na bibliografia ao recomendar o Serafim sem verificar o
`max_seq_length`.

### 2.2 Menos candidatos

Reordenar top-8 em vez de top-20 corta o custo para 40%. O custo é o recall: se
o candidato certo está em 12º, nenhum reranker o traz. A Fase 2 tem de medir
`recall@8` para saber quanto se perde.

### 2.3 Truncar os chunks na reordenação

Pontuar apenas os primeiros ~120 tokens de cada chunk. Em poesia a abertura
carrega muito do tema, e a Fase 1 mediu mediana de 93 tokens por poema — a
maioria dos chunks não é truncada. Baixa o custo e o risco é pequeno.

---

## 3. Passos

### Passo 1 — Medir a latência real, antes de qualquer qualidade (2 h)

Nada mais nesta fase faz sentido antes disto.

```
para cada reranker candidato:
  para n_candidatos em (4, 8, 20):
    para truncagem em (120, 256, sem):
      medir latência de pontuação, mediana de 5 corridas, taskset -c 0-11
```

Mesma disciplina da Fase 0: máquina sossegada, corrida de aquecimento
descartada, temperatura registada, **e prompts distintos entre corridas** —
o defeito de cache de KV da Fase 0 não se aplica aqui, mas o princípio de
nunca medir a mesma entrada duas vezes mantém-se.

**Aceite:** uma tabela de latência real que substitua as estimativas do §1.
**Portão:** só passam ao Passo 2 as configurações com latência ≤ 6 s. Acima
disso, o total ultrapassa 50 s e a fase não é viável mesmo que a qualidade
melhore.

Se **nenhuma** configuração passar o portão, a Fase 3 termina aqui com
resultado negativo, e isso é um resultado legítimo.

### Passo 2 — Qualidade das configurações viáveis (3 h)

Só para as que passaram o portão de latência.

```
                              nDCG@5   apt@3   latência   total previsto
RRF sem rerank (Fase 2)          ?        ?        0 s        44 s
+ MiniLM-L12, top-8, trunc 120   ?        ?        ?          ?
+ bge-base, top-8, trunc 120     ?        ?        ?          ?
```

**Aceite:** `nDCG@5` melhora **e** o total previsto fica ≤ 50 s. As duas
condições, não uma.

### Passo 3 — Decisão explícita de troca (1 h)

A decisão não é binária. Registar a curva:

| configuração | ganho em nDCG@5 | custo em segundos | segundos por ponto de nDCG |
|---|---|---|---|

Se o rerank custar 5 s para ganhar 0,02 de nDCG@5, **não vale**. Se custar 4 s
para ganhar 0,10, vale. O limiar é um juízo e tem de ficar escrito, não
implícito.

### Passo 4 — Integração condicional (2 h)

Se passar: `src/retrieval/rerank.py`, activado por configuração e **desligável**.
A latência é visível no CLI (a Fase 1 Passo 9 já mostra os tempos), logo o
utilizador vê o que o rerank custa.

Se não passar: registar o resultado negativo em `FASE-3-RELATORIO.md` e
**manter o código fora do sistema**. Um reranker desligado por omissão é dívida.

---

## 4. Alternativas se o rerank não couber

Não são parte desta fase, mas ficam registadas para não se perder a ideia:

- **Rerank assíncrono**: responder com o top-4 da fusão e, em paralelo,
  reordenar para a pergunta seguinte. Só ajuda em conversa, não na primeira.
- **Rerank só quando a fusão está indecisa**: se os top-2 têm pontuações
  próximas, reordenar; senão, não. Custo médio muito menor.
- **Deixar o LLM escolher**: injectar 6 chunks e instruir o modelo a usar os
  que servem. Custa prefill (~4 s por chunk extra a 179 tok/s... não — custa
  prefill do gerador, medido na Fase 0 a ~21 tok/s, logo ~8 s por 170 tokens).
  Mais caro que um reranker leve. Provavelmente má ideia, mas mensurável.

A segunda é a mais promissora e é barata de testar.

---

## 5. Riscos

| Risco | Sinal | Resposta |
|---|---|---|
| Nenhum reranker cabe no orçamento | Passo 1 falha o portão | fase termina com resultado negativo; §4 fica como trabalho futuro |
| O reranker leve é mau em PT-PT | nDCG@5 piora | medir antes de integrar; é o erro que cometi com o Serafim |
| Ganho real mas marginal | +0,01 nDCG por 5 s | a §3 Passo 3 obriga a escrever a troca; não integrar por inércia |
| Truncar a 120 tokens perde sinal | ganho cai com truncagem | medir as três truncagens no Passo 1, não escolher a priori |

---

## 6. Checklist

```
[ ] 1  latência real medida: 3 rerankers x 3 n_candidatos x 3 truncagens
[ ] 2  estimativas do §1 substituídas por medição
[ ] 3  portão de latência aplicado (≤ 6 s)
[ ] 4  qualidade medida só nas configurações viáveis
[ ] 5  curva de troca escrita: segundos por ponto de nDCG
[ ] 6  decisão registada, incluindo se for negativa
[ ] 7  se integrado: desligável por configuração e latência visível no CLI
[ ] 8  se não integrado: código fora do sistema, não desligado por omissão
```
