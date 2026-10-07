# Fase 5M — relatório: o custo de forma da troca é só do Caeiro

**Protocolo:** [`FASE-5M.md`](FASE-5M.md), pré-registado em `ce241d1`.
**Dados:** [`fase-5m/01-cru.jsonl`](fase-5m/) (180 amostras geradas) ·
[`03-resultados.json`](fase-5m/) · Caeiro reutilizado da
[5H](FASE-5H-RELATORIO.md).

---

## 0. Os portões

| | | |
|---|---|---|
| **M1** a predição da 5K | ✅ **dispara** | e com margem: 0,196 contra 0,347 |
| **M2** alguma célula acerta a forma da sua voz | ✅ **dispara** | **`reis/L`** — a primeira da sequência inteira |
| **M3** o custo de forma da troca é geral | ❌ **não dispara** | o llama é pior **só no Caeiro** e melhor nas outras três. **Muda a decisão** |
| **M4** os modelos não modulam por voz | ❌ não dispara | e disparava por um **desempate de 7,6×10⁻⁵** — ver o §4 |
| **M5** não mostrado no nulo estrito | ✅ dispara | `campos/L` passa só o nulo fraco. E o portão tinha a **direcção invertida** (§5.1) |

**Em uma frase.** A predição que a 5K registou antes desta corrida existir
**confirma-se**, e com ela cai a leitura que a 5H tinha deixado: **o défice de
forma do llama3.1 é específico do Caeiro**. Nas outras três vozes o llama está
**mais perto** do poeta que o qwen2.5, e no Reis **reproduz-lhe a distribuição**.

---

## 1. A grelha completa, 4 vozes × 2 modelos

KS ao corpus da voz pedida, contra o p95 do nulo dessa voz:

| célula | mediana | **KS à voz pedida** | p95@30 | p95@16 | mais perto de | acerta |
|---|---|---|---|---|---|---|
| **reis/L** | 10,0 | **0,196** | 0,207 | 0,292 | **reis** | ✅ **sim** |
| campos/L | 14,5 | 0,280 | 0,216 | 0,304 | caeiro | não |
| caeiro/Q | 13,5 | 0,288 | 0,197 | 0,286 | caeiro | não |
| campos/Q | 15,0 | 0,314 | 0,216 | 0,304 | campos | não |
| ortonimo/L | 9,5 | 0,329 | 0,218 | 0,298 | caeiro | não |
| caeiro/L | 7,5 | 0,347 | 0,197 | 0,286 | reis | não |
| ortonimo/Q | 12,0 | 0,375 | 0,218 | 0,298 | reis | não |
| reis/Q | 12,0 | 0,376 | 0,207 | 0,292 | caeiro | não |

**`reis/L` é a única célula dentro do nulo da sua voz no teste estrito** — 0,196
contra um p95 de 0,207 — e é **a primeira vez em toda a sequência que um par
(modelo, voz) reproduz a distribuição de comprimento do poeta**. A 5K tinha
concluído que «nenhum braço cabe no intervalo de voz nenhuma»; era verdade das
células de Caeiro, e deixa de ser verdade com as outras vozes medidas.

`campos/L` (0,280) passa o nulo **fraco** e não o estrito: lê-se como **não
mostrado** (§5.1).

---

## 2. M1 — a predição da 5K confirma-se

A [5K §2.2](FASE-5K-RELATORIO.md) registou, **antes de esta corrida existir**:

> «o llama deve sair melhor no Reis do que no Caeiro, porque o seu perfil de
> comprimento está mais perto do Reis (KS 0,216) do que do Caeiro (0,347)»

| | KS à voz pedida |
|---|---|
| llama **pedido Caeiro** | **0,3475** |
| llama **pedido Reis** | **0,1956** |

**Confirmada**, e o valor do Caeiro remedido nesta grelha coincide com o
publicado pela 5K até à terceira decimal (0,3475 contra 0,347) — são as mesmas 60
amostras da 5H, logo é uma verificação de consistência do encanamento e não um
resultado novo.

---

## 3. M3 — o custo de forma é do Caeiro, e isso muda a decisão da 5H

| voz | KS qwen | KS llama | Δ (llama − qwen) | pior |
|---|---|---|---|---|
| **caeiro** | **0,288** | 0,347 | **+0,059** | **llama** |
| campos | 0,314 | **0,280** | −0,034 | qwen |
| **reis** | 0,376 | **0,196** | **−0,180** | qwen |
| ortonimo | 0,375 | **0,329** | −0,047 | qwen |

**O llama é pior em 1 de 4.** O portão pedia ≥3 para o custo ser geral, e a
leitura pré-escrita no §4 dizia: *«Se o llama for pior só no Caeiro, a troca
deixa de ter esse custo e a decisão muda.»* É o caso.

O **M3 da 5H** — «o llama escreve poemas demasiado curtos» — foi medido **só no
Caeiro** e generalizado implicitamente ao condicionar a troca. **Não
generaliza:** fora do Caeiro o llama está mais perto do poeta nas três vozes, e
no Reis bate o qwen por **0,180**, que é mais do que a distância entre o Caeiro e
o Campos reais (0,149).

### 3.1 O mecanismo: o qwen obedece a uma persona errada

As personas mandam os quatro intervalos que a [5L](FASE-5L.md) invalidou
(§5.3 do protocolo). Medindo a **obediência** a essa instrução:

| voz | a persona manda | **poeta** | qwen | llama |
|---|---|---|---|---|
| caeiro | 10–20 | 39% | **83%** | 30% |
| campos | 15–30 | 32% | **53%** | 50% |
| reis | ≤12 | 73% | 73% | 57% |
| ortonimo | 12–20 | 25% | **57%** | 43% |

E o erro da mediana contra o poeta:

| voz | poeta | qwen | llama |
|---|---|---|---|
| caeiro | 11,5 | +2,0 | **+4,0** |
| campos | 14,0 | +1,0 | **+0,5** |
| reis | 10,0 | +2,0 | **+0,0** |
| ortonimo | 9,0 | +3,0 | **+0,5** |

**O qwen obedece mais à persona do que o poeta obedece a si mesmo em três das
quatro vozes, e a obediência custa-lhe fidelidade.** O llama desobedece e acerta
a mediana real em três de quatro — no Reis **exactamente** —, falhando só no
Caeiro, onde escreve curto a mais.

Isto dá ao **passo 24** (corrigir as personas) uma predição: a correcção deve
beneficiar sobretudo o **qwen**, que é o modelo que segue a instrução. Fica
registada aqui, antes de esse passo existir.

---

## 4. M4 — não dispara, e disparava por um desempate de 7,6×10⁻⁵

O portão pré-registado media modulação por «≥3 de 4 células caem mais perto do
mesmo corpus». **Na primeira corrida disparou para o llama (3/4 no Caeiro) e o
disparo era um artefacto:**

Em `reis/L`, o KS ao Caeiro é **0,195480** e ao Reis **0,195556** — uma diferença
de **7,6×10⁻⁵**, e o `min()` resolvia-a pela ordem do dicionário, atribuindo a
célula ao Caeiro. Resolvido o empate **a favor da voz pedida** — a escolha
conservadora *contra* o portão disparar —, o llama fica em 2/4 e **o M4 não
dispara**.

**Dois defeitos do portão, e não do mundo:**

1. **O corpus do Caeiro é um atractor.** É o mais disperso dos quatro (1 a 161
   versos, p25=8, p90=28) e fica no meio da gama, logo minimiza o KS de muitas
   amostras por largura e não por semelhança. Aparece como «mais perto» em 3 das
   8 células.
2. **«Corpus mais próximo» não é modulação.** A medida directa — *muda a
   distribuição com a voz pedida?* — diz o **contrário** do portão:

| modelo | amplitude das medianas | KS médio entre os seus próprios braços |
|---|---|---|
| qwen2.5 | 3,0 | 0,306 |
| **llama3.1** | **7,0** | **0,344** |

**O llama modula a forma por voz mais do que o qwen**, que escreve 12–15 versos
seja a voz qual for. A medida directa é **descritiva e posterior** — está
declarada como tal e não substitui o portão —, mas onde as duas discordam a
discordância é o resultado: **o portão estava mal operacionalizado**, e a sua
leitura pré-escrita («o modelo escreve um comprimento só») não se sustenta.

---

## 5. Correcções a este protocolo, feitas depois de medir

### 5.1 O M5 tinha a direcção invertida

Escrevi o M5 a pensar em afirmações de **desvio** (`KS > p95`), onde o nulo de
n=16 é o teste **estrito** porque tem o p95 mais **alto**. Mas o **M2 é uma
afirmação de ajuste** (`KS ≤ p95`), e aí a direcção **inverte-se**: o teste
estrito é o de **n=30**, que tem o p95 mais **baixo**.

Consequência: uma célula que passa só a n=16 é a **fraca** e não a forte. Com a
direcção certa, `reis/L` ajusta-se aos **dois** nulos e `campos/L` só ao fraco,
logo é `campos/L` que se lê como **não mostrado**.

O erro não muda nenhum número; muda qual das duas células conta.

### 5.2 O desempate do M4

Está no §4. O `min()` sobre valores arredondados resolvia empates pela ordem do
dicionário.

---

## 6. O que isto autoriza, e o que não

**Autoriza retirar a condição de forma que o M3 da 5H pôs à troca de modelo.**
O custo existe e é **do Caeiro**: fora dele a troca **melhora** a forma, e no
Reis melhora-a até ao ponto de a reproduzir.

**Não autoriza decidir a troca.** Esta fase mede **forma**. O conteúdo das outras
três vozes **não pode ser medido** com o instrumento que existe — a âncora 3a′ é
do Caeiro (§1.1 do protocolo) — e é o **passo 25**. A 5H deu +0,700 ao llama em
conteúdo **no Caeiro**; nas outras vozes não há número e esta fase não o produz.

**Não autoriza dizer que o llama «acerta o Reis».** Acerta-lhe a **distribuição
de comprimento**, que é uma propriedade formal entre várias. Rima, estrofe,
dicção e sintaxe latinizante não foram medidas aqui.

**Não autoriza concluir nada sobre modulação a partir do M4.** O portão estava
mal operacionalizado (§4) e a medida directa aponta ao contrário, mas é
posterior.

**E convida a desconfiar de `ortonimo`.** As duas células do ortónimo são as
piores da grelha (0,329 e 0,375) e a §5.2 do protocolo já avisava que são 1055
poemas e um alvo largo. O p95 do nulo dele é o mais alto dos quatro (0,218) e
mesmo assim nenhum braço se aproxima.

### O que fica na mesa

1. **Passo 24, com a predição do §3.1**: corrigir as personas deve beneficiar
   sobretudo o **qwen**. É a primeira vez que esse passo tem uma predição
   direccional antes de correr.
2. **Passo 25**, que é o que bloqueia a decisão da troca: uma âncora 3a′ por voz.
3. **O Reis como voz de demonstração.** Se há um par (modelo, voz) cuja forma
   está certa, é `llama3.1` + Reis. Para o produto, isso é utilizável hoje.
4. **Um portão de modulação bem operacionalizado**, se a pergunta do M4 importar:
   compara os braços de um modelo **entre si**, não contra corpora alheios.

> **A lição, e é sobre portões e não sobre instrumentos.** As cinco lições
> anteriores foram sobre o instrumento — validade, resolução, origem, forma,
> escala. Esta é sobre a **operacionalização do portão**: o M4 estava escrito com
> um proxy («corpus mais próximo») para a coisa que queria medir («muda com a
> voz?»), e o proxy tinha um atractor e um empate. **Um portão pré-registado
> protege contra escolher o resultado; não protege contra medir a coisa errada**
> — e a diferença só aparece quando se mede também a coisa directa, que foi o que
> salvou esta célula.
