# Correcção à Fase 4 — os centróides levavam o nome do heterónimo

Medido em 2026-10-03, dois dias depois de a Fase 4 ser dada por concluída.

**O defeito foi encontrado por outra sessão** a portar este desenho para a Fase
5, e confirmado no código antes de ser registado.

---

## 1. O defeito

`index.py:61` constrói o índice sobre `Chunk.indexed_text`, que **por desenho**
leva «Autor — Título» à cabeça (`chunk.py:23`):

```
indexed_text: 'Fernando Pessoa — Quarto: AS ILHAS AFORTUNADAS\n\nQue voz vem no som das ondas...'
text        : 'Que voz vem no som das ondas...'
```

Os Passos A1 e A1c usaram `idx.vectores` para os centróides e
`encode_queries(c.text)` para as consultas. O centróide tem portanto uma
componente ao longo do **nome do heterónimo** que nenhuma consulta de verso puro
pode igualar. O sinal discriminativo disponível à consulta fica diluído, e a
exactidão sai **subestimada**.

### 1.1 Eram dois defeitos empilhados, e só um é defeito

O segundo já estava declarado por mim em `bench_roteador_b.py` — a assimetria
`query:`/`passage:` do e5 — sem que eu o ligasse ao A1c. Três variantes separam
as causas, com o mesmo conjunto de teste e a semente 4 do A1c:

| variante | centróides | perguntas | poemas | probe perg. | probe poem. |
|---|---|---|---|---|---|
| **`original`** (publicado) | `encode_passages(indexed_text)` | **45%** | **42%** | 45% | 46% |
| **`sem_nome`** | `encode_passages(text)` | **68%** | **64%** | 60% | 61% |
| `sem_nome_nem_assimetria` | `encode_queries(text)` | 30% | 69% | 48% | 78% |

A terceira variante mostra que **a assimetria não era defeito, era o uso
correcto**: com centróides de `encode_queries`, os poemas sobem a 69% mas as
perguntas caem a 30%. É o e5 a funcionar como foi desenhado — consulta
compara-se contra passagem. Para rotear perguntas, a variante certa é a
`sem_nome`.

**O defeito era só o nome, e valia 23 pontos em perguntas e 22 em poemas.**

---

## 2. O que isto corrige

### 2.1 A afirmação está refutada

A Fase 4 afirmou, e eu repeti-o em três documentos:

> O espaço do e5 **não separa estas vozes**.

**Falso.** Separa-as a **68%** em perguntas e **64%** em poemas. A afirmação
apoiava-se nos 42–46% do A1c e nos 45% do A1, e os dois números vêm do mesmo
instrumento contaminado.

O que se mantém do A1c é a conclusão **relativa**, e ela sobrevive por inteiro:
poemas usados como consulta roteiam **tão bem como perguntas** (64% contra 68%,
antes 42% contra 45%). A hipótese do registo continua refutada — não é a
travessia de pergunta-para-verso que falha. Só não é verdade que o espaço seja
cego às vozes.

### 2.2 A decisão fica em dúvida, e eu disse primeiro que não ficava

Ao reportar o defeito escrevi que «a decisão aguenta-se, a afirmação não». **A
primeira metade estava errada**, e a aritmética é simples:

| | contra o publicado | contra o corrigido |
|---|---|---|
| roteador LLM (7B) | 72% | 72% |
| melhor embedding em perguntas | 45% | **68%** |
| vantagem do LLM | **+27 pontos** | **+4 pontos** |
| custo do LLM | 1,2 s/pergunta + ~20 s de aquecimento | o mesmo |
| custo do centróide | microssegundos | o mesmo |

**+4 pontos a n=40 não se distinguem de zero.** É o mesmo critério com que a
Fase 3B escolheu a configuração mais barata de reranker, e aplicado aqui diz:
**o roteador LLM não está estabelecido como melhor que um centróide corrigido.**
O ónus inverte-se.

Não se segue que o roteador deva sair, e falta medição para decidir — ver §4.

### 2.3 O «colapso no Caeiro» era artefacto

A Fase 4 reportou que 17 dos 22 erros do centróide apontavam para o Caeiro, a
voz **mais pequena**, e construí uma secção a explicar isso.

| | exactidão | erros, por voz prevista |
|---|---|---|
| `original` · perguntas | 45% | **caeiro 19**, campos 3 |
| `sem_nome` · perguntas | 68% | **ortonimo 12**, caeiro 1 |
| `original` · poemas | 42% | campos 34, caeiro 12 |
| `sem_nome` · poemas | 64% | campos 18, ortonimo 7, caeiro 3, reis 1 |

**Dezanove erros a apontar para o Caeiro passam a um.** E o atractor que resta é
o **ortónimo** — a classe maior, com 1230 chunks de treino —, que é o
comportamento banal que a tabela de riscos da Fase 4 previu e que eu registei
como não observado. O nome estava a produzir o inverso.

### 2.4 Mas a medição que eu usei para explicar sobrevive

A coerência interna, recalculada sem o nome:

| voz | n | com nome | sem nome |
|---|---|---|---|
| caeiro | 107 | 0,9341 | 0,9299 |
| campos | 435 | 0,9382 | 0,9304 |
| reis | 226 | 0,9387 | 0,9301 |
| ortonimo | 1230 | 0,9359 | 0,9281 |

As quatro continuam **iguais entre si** (0,928–0,930). Logo a observação «as
quatro vozes têm coerência interna igual, portanto o colapso não vem de
dispersão de classe» **não era artefacto**.

**O artefacto era o facto que ela explicava.** Fica uma medição correcta, uma
inferência válida a partir dela, e um fenómeno que não existe. É um modo de
falha diferente de «o número estava errado», e mais difícil de apanhar: a
explicação era boa, e nada nela avisava que o que explicava era um artefacto do
instrumento.

---

## 2.5 Cinco das oito linhas da tabela, e três ficam sem número

A tabela do `src/roteador.py` e do §1.1 do relatório tem oito linhas. **Cinco
usam `idx.vectores`** e partilham o defeito; duas foram remedidas e três não:

| linha | publicado | estado |
|---|---|---|
| centróide de embedding | 45% | **remedido: 68%** |
| regressão logística (probe) | 42% | **remedido: 60%** |
| vizinho mais próximo | 52,5% | contaminado, **não remedido** |
| voto@20 sobre o top-20 | 50% | contaminado, **não remedido** |
| centróide centrado | 32% | contaminado, **não remedido** |
| BM25 | 45% | limpo — é lexical |
| qwen2.5:7b / 3b | 72% / 42% | limpo — não toca no índice |

As três não remedidas não têm número válido em nenhum sentido: não se sabe se
sobem como as outras duas. **A frase «nenhum método de embedding passa dos
52,5%» não era contexto da afirmação refutada — era ela própria refutada**, e é
a premissa de que a escolha do roteador dependia.

Os valores publicados **ficam na tabela como foram medidos**, com a contaminação
declarada ao lado. É o padrão desta casa: preservar o publicado e declarar a
correcção, não trocar números em silêncio.

---

## 3. O que não muda

- **O 3B contra o 7B.** 42% contra 72% é sobre o juiz LLM e não toca nos
  centróides.
- **O conjunto adversarial e a ablação de indícios** (92% de vozes aceitáveis;
  72% → 70%). São medições do roteador LLM, sem embedding envolvido.
- **A ordenação entre variantes de embedding** da tabela do A1/A1b. Todas usaram
  `idx.vectores` e partilham o handicap, logo a comparação entre elas mantém-se
  — o que mudou é o nível de todas.
- **O roteador em serviço.** `src/roteador.py` usa o LLM e continua a funcionar
  como medido; o que está em dúvida é se é a escolha certa, não se faz o que diz.
- **E o 3B contra o 7B como argumento.** «É uma tarefa de conhecimento, não de
  padrão» compara dois LLMs, nenhum dos quais toca em `idx.vectores`. A
  inferência sobrevive inteira e **não leva ressalva** — corrigi-la a mais seria
  tão errado como não corrigir o resto.

---

## 4. O que decidiria, e que não foi medido

A comparação 68% contra 72% é **só no conjunto benigno** — as 40 perguntas
escritas para cada voz. Falta ao centróide exactamente o que dá robustez ao
roteador LLM, e a observação é de quem encontrou o defeito:

1. **O conjunto adversarial** (12 perguntas sem voz em mente, etiqueta por
   conjunto de vozes aceitáveis). O LLM fez 92%.
2. **A ablação de indícios** (15 substantivos-assinatura removidos). O LLM
   aguentou 72% → 70%.

Um centróide depende de superfície lexical, e é plausível que seja precisamente
aí que desabe — o que faria do roteador LLM a escolha certa por uma razão que
nunca foi medida, em vez de pela razão errada que eu publiquei. **É isto que
decide, e custa minutos.**

Contra, e também não medido: o centróide poupa os ~20 s de aquecimento a frio e
não exige o 7B carregado. A 68% com microssegundos pode ser a escolha certa
mesmo sendo ligeiramente pior.

---

## 4.1 E um segundo confundidor, que eu declarei a menos

Veio da mesma troca, e do achado que a sessão paralela fez no seu próprio juiz:
as descrições de voz que o juiz lê **derivam das personas do gerador**, logo um
poema escrito para casar com a persona casa com a descrição, e o juiz premeia a
imitação. Na Fase 5 isso foi medido e **domina**: o juiz dá 65% aos poemas
gerados e **45%** a Pessoa autêntico.

A Fase 4 tem o mesmo laço, numa forma mais fraca e que eu não declarei por
inteiro. O §5 do protocolo diz que **as perguntas e as etiquetas** são da mesma
pessoa. Mas o `SYSTEM` do roteador também é meu, e saiu das mesmas personas —
logo **três** coisas partilham autor:

| | |
|---|---|
| o conjunto de 40 perguntas | escrito por mim, 10 por voz |
| as etiquetas de voz | minhas |
| as descrições que o roteador-juiz lê | minhas, derivadas das personas |

**Consequência:** os 72% e os 92% do conjunto adversarial medem concordância
**dentro de uma cabeça só**. Não é o mesmo vício da Fase 5 — as perguntas de um
utilizador real não são escritas para casar com as descrições, enquanto os
poemas gerados são —, mas as perguntas *do conjunto dourado* foram escritas por
quem escreveu as descrições, e isso basta para inflacionar.

A **ablação de indícios** (72% → 70%) é a única das minhas medições que ataca
isto, e ataca pouco: remove substantivos-assinatura, não a concepção partilhada
de cada voz.

**O que quebraria o laço**, e não foi feito: descrições derivadas do **corpus** —
estatísticas de forma, como comprimento de verso, rima, anáfora — em vez das
personas; ou um conjunto de perguntas rotulado por outra pessoa.

O princípio geral é o que a Fase 5 acabou por registar, e aplica-se às três
defesas desta casa: **a protecção não é a ordem temporal, é a independência
entre a regra e a quantidade medida.** Pré-registar uma regra que olha para o
que vai medir só documenta o vício com data.

---

## 4.2 A correcção replicou-se noutra sessão

A Fase 5 mediu o centróide `sem_nome` em **40** poemas reais e obteve **62%**;
esta remedição obteve **64%** em **80**, com outro conjunto, outra semente e
noutra sessão. E o contrário também fecha: a variante `com_nome` dá **45%** em
reais, dentro dos 42–46% que a Fase 4 publicou — **o instrumento contaminado
reproduz o número contaminado**, que é a confirmação de que o diagnóstico do
defeito estava certo.

---

## 5. Como reproduzir

```bash
.venv/bin/python docs/fase-4/bench_centroides_remedidos.py   # as três variantes
.venv/bin/python docs/fase-4/bench_centroides_confusao.py    # confusão e coerência
```

Dados em [`08-centroides-remedidos.json`](08-centroides-remedidos.json) e
[`08b-confusao-remedida.json`](08b-confusao-remedida.json). A segunda corrida
guarda as codificações em `.npy` no scratchpad, para não repetir os ~5 min de
encoder.

---

## 6. A lição de processo

O defeito esteve dois dias num documento que se diz medido, em três ficheiros,
e sobreviveu a eu escrever noutro ficheiro do mesmo repositório — o
`bench_roteador_b.py` — a frase «a ressalva do probe é a assimetria do e5:
treina-se em vectores `passage:` e aplica-se a vectores `query:`». Tinha metade
do problema escrito pela minha mão e não liguei as duas pontas.

O que o encontrou foi **outra sessão a reutilizar o desenho para outro fim**. Ler
um instrumento para o portar obriga a perguntar o que ele mede de facto, e foi
isso que falhou quando eu o escrevi e passou quando outro o leu.
