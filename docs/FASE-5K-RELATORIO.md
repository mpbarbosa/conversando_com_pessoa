# Fase 5K — relatório: o critério serve, e o desenho da 5H não lhe chega

**Protocolo:** [`FASE-5K.md`](FASE-5K.md), pré-registado em `bd48dca`.
**Dados:** [`fase-5k/01-nulo.json`](fase-5k/) · [`03-resultados.json`](fase-5k/)
**Não gerou amostras.** Tudo determinista sobre o corpus e as amostras da
[5H](FASE-5H-RELATORIO.md).

---

## 0. Os portões

| | | |
|---|---|---|
| **K1** resolução a n=30 | ✅ **dispara** | **e não dispara agrupado** — o qwen cai, e é o que importa (§1.2) |
| **K2** a escala é interpretável | ✅ dispara | e dá o achado da fase: **nenhum braço cabe em nenhuma voz** (§2) |
| **K3** o KS bate a conformidade | ✅ dispara | nos dois braços, com Δ a excluir 0 |
| **K4** a conformidade está invertida | ✅ dispara | **AUC = 0,000** para o qwen — não «fraca», *invertida* (§3.1) |
| **K5** inconclusivo por resolução | ❌ não dispara | o critério tem resolução; o que falta é **n** |

**Em uma frase.** O substituto que a 5J propôs **funciona** — distingue os dois
braços de uma amostra genuína do poeta, e bate o instrumento antigo nos dois —
**mas não ao n do desenho da 5H**: respeitado o agrupamento, o desvio do qwen
**não está demonstrado**. O passo 16 precisa de **20 perguntas por célula**, não
de 10.

---

## 1. K1 — o chão, e a metade do resultado que o agrupamento retira

### 1.1 O nulo empírico

10 000 sub-amostras de Caeiro real, **sem reposição**, cada uma medida contra o
corpus completo — exactamente como os braços são medidos:

| n | mediana | **p95** | p99 |
|---|---|---|---|
| 10 | 0,214 | **0,371** | 0,461 |
| 15 | 0,171 | **0,300** | 0,357 |
| 20 | 0,146 | **0,251** | 0,304 |
| 30 | 0,111 | **0,190** | 0,233 |
| 60 | 0,064 | **0,112** | 0,139 |

O §3.1 tinha escrito que o valor crítico assintótico a n=30 contra n=118 é
≈0,278 e que isso poria o qwen (0,288) à tangente. O nulo empírico dá **0,190** —
o assintótico era **conservador por 46%** nesta distribuição, discreta e de cauda
longa. Fez diferença ter medido: por 0,278 o qwen passaria a raspar, por 0,190
passa com folga.

### 1.2 E depois o agrupamento

| braço | KS a n=30 | percentil no nulo | KS agrupado a n=10 | percentil |
|---|---|---|---|---|
| **qwen2.5** | 0,288 | 99,9 — **acima** | 0,337 [0,288; 0,466] | **90,0 — abaixo do p95** |
| **llama3.1** | 0,347 | 100,0 — **acima** | 0,413 [0,348; 0,561] | 97,7 — **acima** |

As 30 amostras de cada braço são **10 perguntas × 3 repetições**, logo o n
efectivo está perto de 10 e não de 30, enquanto as sub-amostras reais são 30
poemas independentes. Reduzindo cada braço a uma repetição por pergunta (ao
acaso, 10 000 vezes), **o llama sobrevive e o qwen não**.

O §3.2 escreveu a regra antes de medir: **um resultado que só sobreviva ao nulo a
n=30 lê-se como «não mostrado»**. Aplica-se ao qwen. O desvio dele **não está
demonstrado** — o que não é o mesmo que estar ausente, e o percentil 90 diz que
é provável.

### 1.3 A potência diz o mesmo por outro caminho

| n | qwen2.5 | llama3.1 |
|---|---|---|
| **10** | **24%** | 63% |
| 12 | 43% | 100% |
| 15 | 55% | 100% |
| **20** | **100%** | **100%** |
| 30 | 100% | 100% |

A n=10 a potência para um desvio do tamanho do do qwen é **24%** — e é
exactamente por isso que o K1 agrupado falha. **Duas rotas independentes ao
mesmo sítio**, uma por nulo e outra por potência, que é a concordância que mais
vale num resultado de resolução.

**É o número accionável desta fase: 20 perguntas por célula.** O desenho de 10
perguntas, herdado desde a 5B, tem potência para desvios grandes (o do llama) e
não para desvios médios (o do qwen).

---

## 2. K2 — a régua, e o achado

### 2.1 Quanto vale um KS, em diferenças entre poetas que existem

| par de vozes **reais** | KS |
|---|---|
| caeiro – campos | **0,149** |
| caeiro – reis | 0,182 |
| caeiro – ortónimo | 0,266 |
| reis – ortónimo | 0,270 |
| campos – ortónimo | 0,277 |
| campos – reis | **0,317** |

Uma diferença formal genuína entre dois heterónimos vale entre **0,149 e 0,317**.
É a escala em que os números da 5J passam a ler-se:

| braço, contra o Caeiro | KS | |
|---|---|---|
| **qwen2.5** | **0,288** | dentro da gama entre-vozes — à distância a que **uma voz real está de outra** |
| **llama3.1** | **0,347** | **acima** do maior par real (campos–reis, 0,317) |

**Pedido o Caeiro, o llama fica mais longe do Caeiro do que quaisquer dois
heterónimos estão um do outro.** É a leitura que faltava ao «défice de forma» do
M3 da 5H: não é um desvio pequeno medido com uma régua errada — é um desvio maior
do que a diferença entre Campos e Reis.

### 2.2 E nenhum dos dois cabe em nenhuma voz

Com o nulo calculado **por voz** a n=30 (p95: caeiro 0,194 · campos 0,208 ·
reis 0,204 · ortónimo 0,222):

| | caeiro | campos | reis | ortónimo | mais perto | cabe em |
|---|---|---|---|---|---|---|
| **qwen2.5** | **0,288** | 0,396 | 0,396 | 0,452 | caeiro | **nenhuma** |
| **llama3.1** | 0,347 | 0,465 | **0,216** | 0,268 | **reis** | **nenhuma** |

**Nenhum dos dois perfis de comprimento cabe no intervalo de amostragem de
nenhum dos quatro heterónimos.** Não é só que erram o Caeiro: não acertam em
voz nenhuma.

E o llama está **mais perto do Reis** (0,216) do que do Caeiro (0,347), falhando
o Reis **por pouco** — p95 de 0,204. Nos quantis vê-se porquê: a metade de baixo
do llama (p25=6) coincide com a do Reis (6) e não com a do Caeiro (8).

| | p5 | p25 | p50 | p75 | p95 | max | >20 versos |
|---|---|---|---|---|---|---|---|
| caeiro | 3 | 8 | 11 | 18 | 40 | **161** | **19%** |
| reis | 3 | 6 | 10 | 13 | 27 | 104 | 10% |
| **llama3.1** | 4 | **6** | **7** | 10 | 14 | **15** | **0%** |
| **qwen2.5** | 8 | 11 | 13 | 16 | 17 | **17** | **0%** |

> **Uma predição para o passo 16, registada antes de ele correr.** Se o perfil de
> comprimento do llama é de ode breve, então **o llama deve sair melhor no Reis
> do que no Caeiro** — e o Reis é precisamente a voz cujo intervalo do 3b a
> [5J §1](FASE-5J-RELATORIO.md) encontrou **correcto** (73%, a única que passa).
> Fica escrito aqui para que o passo 16 a possa confirmar ou desmentir, em vez de
> a explicar depois.

### 2.3 O que a cauda mostra, e o KS não pune o suficiente

As duas vozes reais têm cauda longa — Caeiro até 161 versos, Reis até 104 — e
**nenhum dos braços passa de 17**. O §6.3 do protocolo declarou de antemão que o
KS é **surdo às caudas** e que por isso **sub-estima** esta distância. Mantém-se a
métrica pré-registada e registo que os 0,288 e 0,347 são **pisos**.

---

## 3. K3 e K4 — o instrumento antigo, medido na mesma tarefa

Tarefa: dado um conjunto de 30 poemas, dizer se é Caeiro real ou do modelo.
Positivos: 10 000 sub-amostras reais. Negativos: 10 000 reamostragens do braço.

| detector | qwen2.5 | llama3.1 |
|---|---|---|
| **D1** conformidade **monótona** — *é o 3b actual* | **0,000** | 0,784 |
| **D2** `|conformidade − 39%|` — a emenda de dois lados | **1,000** | **0,689** |
| **D3** **KS** ao corpus — o critério da 5J | **0,999** | **1,000** |
| Δ(D3 − D1), IC95% | +0,999 [0,998; 1,000] | +0,212 [0,194; 0,232] |

### 3.1 AUC = 0,000 não é «fraco», é invertido

O 3b actual, usado como está — maior conformidade = mais Caeiro —, ordena
**todas** as 10 000 reamostragens do qwen **acima de todas** as 10 000
sub-amostras reais. Zero pares certos em cem milhões.

A 5J §4.2 já tinha previsto a direcção (o intervalo premeia o qwen a 83% contra
os 39% do poeta) e o §3.4 desta fase declarou que o K4 seria **quantificação e
não descoberta**. O valor é o extremo possível.

### 3.2 E a emenda de dois lados não salva — troca de vítima

O D2 resolve o qwen (1,000) e **piora o llama** (0,689 contra os 0,784 do D1).
A razão é a mesma que a 5J §2.1 encontrou: **o llama tem quase a fracção certa
com a distribuição errada** — 30% dentro contra 39% do poeta. Olhada só pela
fracção, a amostra do llama **parece real**.

É o escalar da 5J a reaparecer, agora como falha de detector e já não como erro
de leitura meu. **Nenhuma das duas versões da conformidade funciona nos dois
braços; o KS funciona nos dois.**

> **Ressalva, registada junto dos números em `03-resultados.json`.** Os negativos
> são *bootstrap* dos **mesmos** 30 ensaios, não amostras novas do modelo, logo
> variam menos do que um braço fresco variaria: **uma AUC de 1,000 sobrestima a
> separação de um braço novo**. Mede a separação **deste** perfil de
> comprimentos. A inversão do D1 não depende disto — está nas medianas.

---

## 4. Desvios ao protocolo, declarados

1. **A grelha de potência perdeu o 120 e ganhou 12, 15 e 25.** O 120 é
   impossível: não se tira uma sub-amostra de 120 **sem reposição** de 118
   poemas, logo o nulo não existe a esse n — o §4.3 pré-registou um ponto que
   não podia ser calculado. E a grelha pré-registada deixava sem resolução
   exactamente a região onde a potência salta (10 → 20), que é a região da
   decisão. **Nenhum portão depende da grelha**: a potência do §4.3 é descritiva
   e sem limiar.
2. **O nulo por voz entrou no K2.** Sem ele, «o llama está mais perto do Reis»
   é uma ordenação sem escala e não diz se ele cabe no intervalo de amostragem
   de alguma voz. O K2 é descritivo e sem limiar, logo isto não mexe em portão
   nenhum — e é o que permite o §2.2.

---

## 5. O que isto autoriza, e o que não

**Autoriza o passo 22: retirar a cláusula de comprimento do 3b.** Agora com
argumento **empírico** e não só de princípio — AUC 0,000 no qwen, e a emenda de
dois lados a trocar de vítima. A [5J §4.3](FASE-5J-RELATORIO.md) tinha o
argumento conceptual; o §3 desta fase tem o número.

**Autoriza o passo 21: adoptar o KS ao corpus como critério de forma**, ao nível
do **conjunto** e não da amostra, com o nulo por voz como referência de leitura.
O instrumento está em [`fase-5j/analisar.py`](fase-5j/analisar.py) e a calibração
em [`fase-5k/01-nulo.json`](fase-5k/).

**Não autoriza correr o passo 16 com 10 perguntas.** Precisa de **20 por
célula** (§1.3). Com 4 vozes × 2 modelos × 20 perguntas × 3 repetições são 480
amostras a ~30 s — **~4 horas de geração** —, o que é uma decisão de orçamento a
tomar antes e não a descobrir no meio.

**Não autoriza dizer que o qwen desvia da forma do poeta.** O desvio dele **não
está demonstrado** com o agrupamento respeitado (§1.2). O do llama está.

**Não revisita a troca de modelo.** O M3 da 5H continua condicionado ao passo 16
— e o §2.2 dá-lhe agora uma **predição** a confirmar em vez de uma pergunta
aberta.

**Não mede os critérios qualitativos do 3b** — verso livre, rima, imagem,
ornamento. O passo 22 retira a cláusula de **comprimento**; o resto da âncora
fica intacto e não foi avaliado aqui.

### O que fica na mesa

1. **Passo 22, e é escrita de instrumento:** alterar a [Fase 5](FASE-5.md) §5.2
   nas quatro vozes. Mexe na âncora que sete fases usaram, logo pede o seu
   próprio pré-registo e uma nota de compatibilidade — as pontuações antigas de
   3b deixam de ser comparáveis com as novas.
2. **Passo 16 a 20 perguntas**, com a predição do §2.2 registada.
3. **Uma métrica sensível à cauda**, se a surdez do KS (§2.3) vier a importar: o
   que distingue o Caeiro é escrever ora 4 ora 161 versos, e é na cauda que isso
   vive. Não se troca a métrica agora — seria escolhê-la pelo desfecho —, mas
   fica nomeado.
4. **O nulo por voz a outros n**, se o passo 16 usar n diferente de 30.

> **A lição, e fecha a série dos instrumentos.** As quatro anteriores foram
> **validade** (5C), **resolução** (5D), **origem** (5E) e **forma** (5J). Esta é
> sobre **escala**: um número de distância sem um **chão** (quanto dá o ruído de
> amostragem) e sem uma **régua** (quanto vale uma diferença real) não é legível,
> e a 5J publicou dois desses números a achar que eram legíveis. Custou uma hora
> de computação dar-lhes um e outro, e o que mudou não foi o número — foi passar
> de «0,347 é mais que 0,288» para «0,347 é mais do que a distância entre Campos
> e Reis».
>
> E o corolário operacional, que é o mais caro: **o nulo assintótico era
> conservador por 46%** e o n efectivo de um desenho agrupado é o número de
> **agrupamentos**, não de amostras. As duas coisas apontam para medir o chão em
> vez de o estimar.
