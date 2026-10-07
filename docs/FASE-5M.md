# Fase 5M — A forma das quatro vozes, nos dois modelos

**Passo 16**, na metade que está pronta. Pré-registada em 2026-10-07, antes de
qualquer amostra existir.

---

## 1. O que esta fase mede, e o que o passo 16 não pode medir ainda

O passo 16 pergunta se a troca de modelo que a [5H](FASE-5H-RELATORIO.md)
autorizou a **investigar** se mantém nas outras três vozes. Tem duas metades:

| metade | instrumento | estado |
|---|---|---|
| **forma** | KS ao corpus da voz, ao nível do **conjunto** | ✅ pronto e calibrado na [5K](FASE-5K-RELATORIO.md) |
| **conteúdo** | âncora **3a′** | ❌ **não existe para três das quatro vozes** |

### 1.1 Porque é que a metade do conteúdo está bloqueada

A âncora 3a′ da [5F](FASE-5F.md) §2 mede **«o poema acaba na coisa»** — a
assinatura deflacionária do Caeiro. **É inteiramente específica do Caeiro**, e
aplicá-la às outras vozes não é medir mal, é medir outra coisa:

- ao **ortónimo**, cujo modo é precisamente acabar **além** da coisa — mistério,
  alma, destino —, o 3a′ dá **0 por construção**. Seria uma anti-medida;
- ao **Reis** e ao **Campos**, mede ausência de uma assinatura que não é deles.

Logo o conteúdo das três vozes precisa de **uma âncora por voz, validada contra
os poemas reais dessa voz** — que é exactamente o percurso
[5E](FASE-5E-RELATORIO.md) → [5F](FASE-5F-RELATORIO.md), três vezes. Não é um
acréscimo a esta corrida; são fases de instrumentação, e entram como passo novo.

**Esta fase faz a metade da forma, que é mecânica, está calibrada, e testa uma
predição já registada.** A redução de âmbito está declarada aqui e não
descoberta no fim.

---

## 2. Uma correcção à 5K, medida antes de escrever este protocolo

A [5K §1.3](FASE-5K-RELATORIO.md) prescreveu **20 perguntas por célula**, a
partir de uma análise que reduzia cada braço a **uma repetição por pergunta** —
isto é, que tratava as 3 repetições como **perfeitamente correlacionadas**
(ICC = 1), o pior caso possível.

Medi a correlação intraclasse do número de versos dentro de pergunta, nos quatro
braços disponíveis:

| braço | ICC | IC95% (bootstrap sobre perguntas) | n efectivo |
|---|---|---|---|
| 5H qwen | **+0,066** | [−0,292; +0,426] | 16,2 – 30,0 |
| 5H llama | **−0,023** | [−0,339; +0,286] | 19,1 – 30,0 |
| 5I braço A | +0,122 | [−0,112; +0,362] | 17,4 – 30,0 |
| 5I braço B | +0,094 | [−0,206; +0,229] | 20,6 – 30,0 |

**O número de versos depende sobretudo da semente, não da pergunta.** Com
ICC ≈ 0,07 o n efectivo de 10×3 é ≈ **26**, e no **pior caso** do IC é **≈ 16** —
não 10. Pela curva de potência da 5K isso dá 100% no estimado e 55–100% no pior
caso, contra os 24% que a prescrição assumia.

**Consequência:** o desenho de **10 perguntas × 3 repetições** é adequado, e esta
fase usa-o — o que além disso a põe em **pé de igualdade exacto com a 5H**, cujas
células de Caeiro são reutilizadas em vez de regeradas.

**E corrige a leitura do K1 agrupado:** o «desvio do qwen não está demonstrado»
da 5K §1.2 vinha de supor ICC = 1. Ao n efectivo medido (≈26, p95 ≈ 0,21) os
0,288 do qwen ficam **acima** do nulo. A ressalva da 5K era conservadora a mais,
e o §4 desta fase passa a ler os dois limites em vez de um.

> **Registo de honestidade:** esta medição foi feita **antes** de escrever o
> protocolo mas **depois** de a 5K estar publicada, e beneficia-me — reduz o
> orçamento de 4 h para ~1,5 h e devolve-me um resultado que a 5K tinha posto em
> dúvida. Por isso o §4 não a usa para **substituir** a leitura conservadora:
> usa **as duas**, e o portão M5 exige que um resultado sobreviva ao pior caso.

---

## 3. Desenho

### 3.1 As células

| | perguntas | fonte |
|---|---|---|
| **caeiro** | `q01`–`q10` | **reutilizadas da [5H](FASE-5H-RELATORIO.md)** — mesmo banco, mesmo desenho, mesmas sementes |
| **campos** | `q11`–`q20` | geradas aqui |
| **reis** | `q21`–`q30` | geradas aqui |
| **ortonimo** | `q31`–`q40` | geradas aqui |

Banco: [`fase-1/08-perguntas.json`](fase-1/), o conjunto dourado desde a Fase 1,
10 perguntas por voz, etiquetadas e com proveniência. Verifiquei que as 10
perguntas de Caeiro da 5H são **exactamente** as do banco, logo a reutilização é
legítima.

**3 vozes × 2 modelos × 10 perguntas × 3 repetições = 180 amostras** a gerar
(~1,5 h a ~30 s), mais as 60 da 5H reaproveitadas = grelha completa de **4 × 2**.

### 3.2 Harness

O da 5H (`fase-5h/gerar_amostras.py`), adaptado só para iterar vozes: mesma
persona de serviço por voz, mesmas opções, mesmo esquema de sementes
(`SEMENTE_BASE + 100·r + i`), mesmo diário retomável `01-cru.jsonl`, e **a mesma
asserção byte a byte** que compara o prompt entre braços por `(voz, pergunta)` —
se diferir, aborta. Sementes: `SEMENTE_BASE = 20261007`.

**Só o modelo muda entre braços.** A voz muda entre células, e por isso as
comparações do §4 são sempre **dentro** de voz, excepto o M1 e o M4, que estão
escritos para o atravessar de propósito.

### 3.3 Medição

Mecânica e sem avaliador: `n_versos` por `plagio._versos`, KS ao corpus de cada
voz (poemas autênticos, pt, elegíveis — os de
[`fase-5j/01-contagem.json`](fase-5j/)), nulos por voz de
[`fase-5k`](fase-5k/), recalculados a **n=16** e **n=30**.

---

## 4. Portões

| | nome | dispara se | leitura, escrita agora |
|---|---|---|---|
| **M1** | **a predição da 5K** | KS(llama pedido Reis → corpus do Reis) **<** KS(llama pedido Caeiro → corpus do Caeiro) = 0,347 | o défice de forma do llama é **específico da voz**, e o custo da troca concentra-se no Caeiro. A predição está registada na [5K §2.2](FASE-5K-RELATORIO.md) **antes** desta corrida existir |
| **M2** | **algum braço acerta a forma da sua voz** | em ≥1 das 8 células, KS ao corpus da voz-alvo **≤** p95 do nulo dessa voz | há pelo menos uma voz em que um dos modelos reproduz a distribuição de comprimento. Se **nenhuma** disparar, o resultado da 5K generaliza: **nenhum modelo acerta a forma de nenhuma voz** |
| **M3** | **o custo de forma da troca é geral** | o llama tem KS **maior** que o qwen em **≥3 das 4** vozes | o M3 da 5H não era do Caeiro: trocar de modelo piora a forma em geral. Se o llama for pior **só** no Caeiro, a troca deixa de ter esse custo e a decisão muda |
| **M4** | **os modelos não modulam a forma por voz** | para um modelo, **≥3 das 4** células caem mais perto do **mesmo** corpus | o modelo escreve um comprimento só, independentemente da voz pedida — e então a «forma da voz» não é algo que a persona controle |
| **M5** | **não mostrado no pior caso** | um resultado do M1–M4 que sobreviva ao nulo a **n=30** e **não** ao de **n=16** | lê-se como «**não mostrado**», pela razão do §2: o IC do ICC é largo e o pior caso é que manda |

### 4.1 O que o M3 decide, e não decide

O M3 é sobre **forma**. A 5H mediu o **conteúdo** (3a′) e deu **+0,700 ao llama**
no Caeiro. Esta fase **não** mede conteúdo (§1.1), logo **não pode** concluir
sobre a troca de modelo — só sobre uma das duas metades do seu custo. Está escrito
antes de medir para não ser lido como mais do que é.

---

## 5. Ameaças

### 5.1 O corpus de cada voz é o que o RAG serve, e nada mais

«O Campos real» significa «os 245 poemas de Campos elegíveis deste corpus». Vale
para julgar **este** sistema e não é uma afirmação sobre a obra — igual à
ressalva da [5J §6.3](FASE-5J.md).

### 5.2 O ortónimo é 1055 poemas e um alvo difuso

O ortónimo do corpus inclui obra de toda a vida e em dois idiomas, com mediana de
9 versos e cauda até 226. É a voz com **mais** dados e provavelmente a menos
coerente formalmente. Um KS baixo ao ortónimo pode significar «acertou» ou
«acertou num alvo largo», e o nulo por voz (p95 = 0,222, o mais alto dos quatro)
já reflecte essa largura. Declarado agora.

### 5.3 A persona de serviço pode não pedir comprimento nenhum

Se a persona de uma voz não disser nada sobre extensão, o M4 pode disparar por
falta de instrução e não por incapacidade do modelo. **Verificação declarada:**
reportar, para cada voz, se a persona de serviço menciona comprimento — e se não
mencionar, o M4 lê-se como «a persona não o pede», não como «o modelo não o
sabe».

### 5.4 A surdez do KS às caudas, outra vez

Como na [5K §2.3](FASE-5K-RELATORIO.md): nenhum braço de 5H passou de 17 versos e
as vozes reais vão até 226. Os KS são **pisos**. Métrica mantida, por ser a
pré-registada.

---

## 6. Lista de verificação

```
[ ] A1  gerar 180 amostras (3 vozes × 2 modelos × 10 × 3) -> 01-cru.jsonl
[ ] A2  asserção byte a byte do prompt entre bracos, por (voz, pergunta)
[ ] A3  verificar se a persona de cada voz menciona comprimento (§5.3)
[ ] B1  KS de cada celula ao corpus da sua voz, nulos a n=16 e n=30
[ ] B2  M1 a predicao da 5K · M2 alguma celula acerta · M3 custo geral
[ ] B3  M4 os modelos modulam por voz? · M5 leitura no pior caso
[ ] C1  portoes -> 03-resultados.json
[ ] C2  relatorio FASE-5M-RELATORIO.md
[ ] C3  CONTROLO.md: fase, passo 16, a correccao a 5K e o passo novo do 3a'
```

**Sessões paralelas:** verificado antes de abrir — nenhuma outra sessão neste
repositório. `git add` com ficheiros nomeados. O Ollama foi arrancado por esta
sessão (estava fora) pelo caminho absoluto `~/.local/ollama/bin/ollama`.
