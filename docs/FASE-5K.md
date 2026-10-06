# Fase 5K — Dar chão e escala ao critério de forma

**Passos 21 e 22** da tabela do [`CONTROLO.md`](CONTROLO.md) §6. Pré-registada em
2026-10-06, antes de qualquer medição do §4 existir.

---

## 1. Porque é que esta fase vem antes do passo 16

A [5J](FASE-5J-RELATORIO.md) deixou o 3b em suspenso e não o substituiu:

- a componente de **comprimento** do 3b está errada em três das quatro vozes, e
  **pior** no Campos e no ortónimo do que no Caeiro (§1.1 da 5J);
- a correcção descritiva — alargar o intervalo — **destrói a discriminação**:
  `[4,31]` dá 100% aos dois modelos contra 86% do poeta (§4.2);
- a razão é de **forma de instrumento**: a dispersão é propriedade de um
  **conjunto** e nenhum critério por amostra a mede (§4.3).

O **passo 16** — as outras três vozes com os dois modelos — ia usar o 3b. Correr
o 16 agora é reproduzir o defeito em escala maior, nas duas vozes onde ele é
maior. **É a sequência [5E](FASE-5E-RELATORIO.md) → [5F](FASE-5F-RELATORIO.md) →
[5G](FASE-5G-RELATORIO.md) outra vez: endireitar o instrumento, depois remedir.**

E o substituto que a 5J propõe — a distância entre a **distribuição** de
comprimentos de um braço e a do corpus — **está implementado e não está
calibrado**. Os números que ela publicou são `KS = 0,288` para o qwen e `0,347`
para o llama, e **nenhum dos dois é legível**: não se sabe quanto vale um KS
nesta escala, nem quanto dele é ruído de amostragem a n=30.

> **A lição da 5D, aplicada ao instrumento novo antes de o adoptar.** Um
> instrumento precisa de **validade** (5C), de **resolução** (5D) e de que o
> **original seja pontuado com ele** (5E). O KS da 5J tem a terceira por
> construção — mede contra o corpus. Esta fase mede-lhe as outras duas.

---

## 2. O que já está medido, e entra como dado

Da [5J](FASE-5J-RELATORIO.md), re-executável por
[`fase-5j/contar.py`](fase-5j/) e [`analisar.py`](fase-5j/):

| | n | mediana | dentro de 10–20 | KS ao Caeiro real |
|---|---|---|---|---|
| **Caeiro real** (pt, elegível) | 118 | 11,5 | 39% | — |
| **qwen2.5** (5H) | 30 | 13,5 | **83%** | **0,288** |
| **llama3.1** (5H) | 30 | 7,5 | **30%** | **0,347** |

Contagem de versos por `plagio._versos` sobre `parse_poem(...).body`, as duas
convenções que a 5J fixou. **Nada nesta fase gera amostras.**

---

## 3. Hipóteses e portões, escritos antes de medir

| | nome | dispara se | leitura, escrita agora |
|---|---|---|---|
| **K1** | **o critério tem resolução a n=30** | o KS dos **dois** braços excede o **percentil 95** do nulo «sub-amostra real contra o corpus» a n=30 | a distância distingue um braço de uma amostra genuína do poeta, e os números da 5J são legíveis como sinal |
| **K2** | **a escala é interpretável** | — (descritivo, sem limiar) | o KS entre **vozes reais** dá a magnitude de uma diferença formal entre dois poetas a sério. Situa os modelos nessa régua |
| **K3** | **o KS bate a conformidade ao intervalo** | AUC(KS) > AUC(conformidade monótona) nos **dois** braços, com IC95% do Δ a excluir 0 | é o argumento **empírico** para o passo 22, e não só o argumento de princípio da 5J §4.3 |
| **K4** | **a conformidade monótona é pior que a moeda ao ar** | AUC(conformidade monótona) **< 0,50** para o **qwen** | o instrumento antigo não é só fraco: está **invertido** onde o modelo excede a persona. Já previsto pela 5J §4.2 e aqui quantificado |
| **K5** | **inconclusivo por resolução** | o percentil 95 do nulo **excede** o KS dos dois braços | a n=30 o critério **não** tem resolução. Então o passo 16 não o pode usar com esse n, e o §6.2 diz o que fazer |

### 3.1 O nulo, e porque é ele e não uma fórmula

O valor crítico assintótico do KS a n=30 contra n=118 é
`1,36·√(1/30 + 1/118) ≈ 0,278`, o que poria o qwen (0,288) **à tangente**. Uma
decisão à tangente não se toma por aproximação assintótica sobre uma distribuição
discreta, muito atada e com cauda longa — as condições em que essa fórmula é
pior. Logo o nulo é **empírico**: 10 000 sub-amostras de 30 poemas reais,
**sem reposição**, cada uma medida contra o corpus completo, exactamente como os
braços são medidos.

### 3.2 O agrupamento, que desfavorece os braços e tem de entrar

As 30 amostras de cada braço vêm de **10 perguntas × 3 repetições**. São
**agrupadas**, logo o seu n **efectivo** é mais perto de 10 que de 30, enquanto as
sub-amostras reais são 30 poemas independentes. **O nulo a n=30 é portanto
optimista para os braços.**

Primário: nulo a **n=30**, que é o que replica a medição da 5J.
**Sensibilidade obrigatória:** nulo a **n=10** contra braços reduzidos a uma
repetição por pergunta (escolhida ao acaso, 10 000 vezes, e o KS médio).
**Um resultado que só sobreviva ao nulo a n=30 lê-se como «não mostrado».**

### 3.3 O desfecho do K3, posto como tarefa de detecção

A tarefa, igual para os dois instrumentos: **dado um conjunto de 30 poemas,
decidir se veio do Caeiro real ou do modelo M.** Positivos = 10 000
sub-amostras reais; negativos = reamostragens do braço (bootstrap de 30, com
reposição, dos 30 ensaios). Três detectores:

| | detector | como o 3b o usa |
|---|---|---|
| **D1** | conformidade ao intervalo, **monótona** (maior = mais Caeiro) | **é o 3b actual** |
| **D2** | `|conformidade − 0,39|` (dois lados) | a emenda mínima ao 3b |
| **D3** | **KS** ao corpus | o critério da 5J |

AUC por contagem directa de pares, IC95% por bootstrap de 2 000. O **K3 compara
D3 com D1**; o D2 entra para separar «o problema era a monotonia» de «o problema
era o escalar», que são prescrições diferentes para o passo 22.

### 3.4 O K4 já tem a sua direcção prevista, e isso é um risco

A 5J §4.2 mostrou que o intervalo premeia o qwen (83%) acima do poeta (39%). Logo
**eu já sei que o D1 vai estar invertido para o qwen** antes de o medir, e o K4
não é uma descoberta — é uma quantificação. Está escrito como portão só para
fixar o limiar (0,50) antes de ver o número, e lê-se como tal.

---

## 4. Desenho

### 4.1 Dados e definições

- **Corpus**: poemas autênticos por voz, `language == pt`, elegíveis pelo filtro
  de lacuna da [5J §4.3](FASE-5J.md), contados com `plagio._versos` sobre
  `.body`. Reutiliza [`fase-5j/01-contagem.json`](fase-5j/).
- **Braços**: `docs/fase-5h/01-cru.jsonl`, campos `braco` ∈ {Q, L} e `n_versos`.
- **Semente** `20261006`, `random.Random`. `B = 10 000` para nulos, `2 000` para
  IC de AUC.

### 4.2 K2 — a régua entre vozes

KS entre os conjuntos **reais** de cada par de vozes (caeiro, campos, reis,
ortonimo), com os n de cada uma. Dá a magnitude de uma diferença formal entre
dois poetas que existem. Reporta-se também o KS de cada braço ao corpus de
**cada** voz: se o llama estiver mais perto do Reis que do Caeiro, isso é uma
afirmação interpretável sobre o que ele escreve, e não um número solto.

### 4.3 K4 — a potência, que é o que o passo 16 precisa de saber

Para cada braço e para cada `n` em {10, 20, 30, 60, 120}: fracção de
reamostragens do braço cujo KS contra o corpus excede o percentil 95 do nulo
**ao mesmo n**. É a potência de detecção daquele desvio àquele n.

**O que isto decide:** o `n` por célula que o passo 16 precisa para que o critério
de forma diga alguma coisa nas quatro vozes. Se a n=30 a potência for baixa para
um desvio do tamanho do do qwen, o passo 16 tem de subir o n **ou** declarar que
não mede forma.

### 4.4 Estatística

Sem `scipy`, como desde a [Fase 3B](FASE-3B.md). KS de duas amostras reutilizado
de [`fase-5j/analisar.py`](fase-5j/analisar.py) — **o mesmo código, validado
nos três casos de sanidade lá** —, AUC por contagem de pares, bootstrap à mão com
`numpy`.

---

## 5. O que esta fase não faz

- **Não gera amostras** e não toca no Ollama.
- **Não repontua 3b à mão.** Os critérios qualitativos do 3b — verso livre, rima,
  imagem, ornamento — não são medidos aqui, e a prescrição do passo 22 é sobre a
  **cláusula de comprimento**, não sobre o resto da âncora.
- **Não decide o passo 16.** Dá-lhe o `n` e o instrumento; a corrida é dele.
- **Não mede as outras três vozes contra modelos** — não há amostras geradas de
  Reis, Campos ou ortónimo com os dois modelos. O K2 usa só os **corpora** reais.
- **Não revisita a decisão de troca de modelo.** O M3 da 5H continua condicionado.

---

## 6. Ameaças e leituras pré-escritas

### 6.1 O nulo tem um n fixo e os braços são agrupados

Está no §3.2 e é a ameaça principal. A mitigação é a sensibilidade obrigatória a
n=10, e a regra de leitura está escrita: sobreviver só ao nulo a n=30 **não
conta**.

### 6.2 Se o K5 disparar

Então a 5J propôs um substituto que não funciona ao n que o projecto usa, e as
duas saídas ficam escritas **antes** de eu saber qual é:

1. o passo 16 sobe o `n` até à potência que o K4 indicar, e a forma mede-se; ou
2. o `n` necessário é impraticável — mais de ~120 por célula a ~30 s por amostra
   são mais de uma hora por célula — e então **a forma por comprimento deixa de
   ser medível neste projecto**, o que é uma limitação a declarar e não um
   instrumento a adoptar.

**Em nenhum dos casos o intervalo antigo volta.** A 5J §1 mostrou que ele é
descritivamente falso nas três vozes, e isso não depende desta fase.

### 6.3 O KS não é sensível a tudo

O KS apanha a maior diferença entre funções de distribuição acumulada, e é
relativamente **surdo às caudas**. O Caeiro real tem cauda até 161 versos e os
braços param nos 17: é precisamente uma diferença de cauda, logo o KS
**sub-estima** a distância nesse ponto. Fica declarado que a escolha é
conservadora, e **não** vou trocar de métrica depois de ver o resultado — a 5J
§2 fixou o KS como pré-registado e trocá-lo agora seria escolher a métrica pelo
desfecho.

### 6.4 Comparo um instrumento com o seu substituto, e escrevi o substituto

O D3 é a proposta da 5J, que é minha, e o D1 é o instrumento que eu quero
retirar. O K3 é portanto um teste em que tenho uma direcção preferida. As
defesas: os três detectores correm na **mesma** tarefa, com os **mesmos**
positivos e negativos; o limiar do K4 está fixado aqui; e a tarefa de detecção
foi definida **antes** de qualquer AUC existir. O que não tenho é cegueira — é
tudo mecânico — e isso está dito na 5J §6.2.

---

## 7. Lista de verificação

```
[ ] A1  nulo empirico: 10k sub-amostras reais a n=30 e n=10 -> 01-nulo.json
[ ] B1  K1 os bracos contra o percentil 95, nos dois n
[ ] B2  K2 a regua entre vozes reais, e cada braco contra cada voz
[ ] B3  K3 AUC dos tres detectores na tarefa de deteccao, com IC
[ ] B4  K4 potencia por n em {10,20,30,60,120}
[ ] C1  portoes -> 03-resultados.json
[ ] C2  relatorio FASE-5K-RELATORIO.md
[ ] C3  CONTROLO.md: fase, passos 21 e 22, e o n que o passo 16 precisa
```

**Sessões paralelas:** verificado com `ListAgents` e `list_sessions` antes de
abrir a fase — **nenhuma outra sessão neste repositório**. Mesmo assim, `git add`
com ficheiros nomeados, pela razão registada na memória do projecto depois de um
`git add -A` de outra sessão ter apanhado um ficheiro meu em 2026-10-05.
