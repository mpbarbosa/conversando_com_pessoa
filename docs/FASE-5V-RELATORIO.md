# Fase 5V — relatório: o ortónimo não rima, e a persona manda-o rimar

**Protocolo:** [`FASE-5V.md`](FASE-5V.md), pré-registado em `e7efe7a`.
**Dados:** [`fase-5v/01-forma.json`](fase-5v/) ·
[`02-correccao.json`](fase-5v/) · [`03-rima-gerada.json`](fase-5v/)
**Produto:** nada entrou em `src/`. O §4.1 autoriza **pré-registar** uma
intervenção, não fazê-la.

---

## 0. Os portões

| | | |
|---|---|---|
| **V1** o detector de rima funciona | ❌ **não dispara** como pré-registado | **e o erro era meu**: atribuí ao Reis a instrução do ortónimo (§1) |
| **V1′** o mesmo, com o par certo | ✅ **dispara** | ortónimo **0,777** contra Reis **0,199**, nulo 0,239 |
| **V2** o detector de metro funciona | ✅ dispara | Reis 0,476 mais regular que Campos 0,357 |
| **V3** a forma distingue gerado de real | ✅ **dispara nos dois instrumentos** | e replica em dois conjuntos independentes |
| **V4** inútil | ❌ não dispara | — |

**É o primeiro instrumento mecânico desta sequência a discriminar nas três
vozes.** E, ao contrário da 5T e da 5U, não morreu por falta de eventos: cada
verso é uma observação, e são milhares.

---

## 1. O V1 não disparou porque eu troquei as vozes

O §1 do protocolo escreveu, há um *commit*: «o Reis manda *metro regular e
rima*». **Não manda.** O `src/voices.py`, que é anterior a esta fase:

| voz | o que a persona manda |
|---|---|
| **Reis** | «Ode breve. Estrofes curtas e regulares … **sem rima**.» |
| **ortónimo** | «**Metro regular e rima.** Quadras ou quintilhas.» |

Atribuí ao Reis a instrução do **ortónimo**. As odes de Ricardo Reis são verso
branco — e a persona di-lo correctamente. O par de calibração certo era
**ortónimo contra Reis**, e com ele o V1′ dispara com uma folga enorme.

**A premissa da correcção vem do `voices.py` e não do resultado**, que é a única
razão por que re-especificar o portão aqui não é ajustá-lo ao que eu queria.

---

## 2. E a chave de rima estava a contar repetição

Caeiro — verso livre — «rimava» a **0,6417**. A suspeita tinha mecanismo: dois
versos que acabam na **mesma palavra** dão a mesma chave, e Caeiro repete («uma
árvore é uma árvore») e Campos faz anáfora **por instrução**.

Excluindo os pares cuja última **palavra** coincide:

| voz | com repetição | **sem repetição** | nulo p99 | a persona manda |
|---|---|---|---|---|
| **ortónimo** | 0,8143 | **0,7769** | 0,2388 | «metro regular e **rima**» |
| **Campos** | 0,7063 | 0,4594 | 0,4094 | «irregular», anáfora |
| **Reis** | 0,3586 | **0,1992** | 0,2072 | «**sem rima**» |
| **Caeiro** | 0,6417 | **0,1583** | 0,2833 | verso livre |

**O Caeiro cai de 0,64 para 0,16 — abaixo do próprio nulo.** A «rima» dele era
repetição, toda. O Reis cai para **0,199**, também abaixo do seu nulo (0,207): o
Reis **não rima**, exactamente como a persona diz. E o ortónimo fica em
**0,777** contra um nulo de 0,239.

**As quatro vozes passam a concordar com as quatro poéticas.** Sem esta exclusão,
o instrumento media repetição e chamava-lhe rima.

---

## 3. O resultado: o ortónimo não rima, e devia

| voz | real | gerado 5U | **gerado 5M** | diferença | IC95 | AUC | **nulo do gerado** | acima do nulo? |
|---|---|---|---|---|---|---|---|---|
| **ortónimo** | **0,7769** | 0,3000 | **0,2167** | **+0,5603** | [+0,450, +0,659] | **0,780** | **0,2167** | **NÃO** |
| Reis | 0,1992 | 0,1000 | 0,1667 | +0,0325 | [−0,076, +0,135] | 0,516 | 0,2333 | NÃO |
| Campos | 0,4594 | 0,1000 | 0,2000 | +0,2594 | [+0,141, +0,374] | 0,630 | 0,3167 | NÃO |

**O ortónimo gerado rima a 0,2167 — que é exactamente o seu próprio nulo de
permutação (p99 = 0,2167).** Não rima *menos*: **não rima nada.** O que o
detector apanha nele é o que o acaso dá às terminações do português.

E a persona manda-o rimar, em três palavras explícitas, num `system` que a
[5U](FASE-5U-RELATORIO.md) mediu ter 340–388 *tokens*. **É a desobediência mais
clara que esta sequência encontrou a uma instrução de forma.**

### 3.1 E o Reis é o controlo positivo que dá crédito ao instrumento

A persona do Reis manda «**sem rima**». Um detector que funcione tem de achar
diferença no ortónimo e **não achar** no Reis:

> Reis: diferença **+0,0325**, IC [−0,076, +0,135] — **contém zero**, AUC
> **0,516**.

**Não há diferença onde não devia haver.** O instrumento não está a marcar «texto
gerado» em geral; está a marcar **rima ausente onde a poética a exige**. É o
controlo que a 5T teve de construir à parte, e que aqui vem de graça com o
desenho.

---

## 4. O metro: discrimina nas três, e revela compressão

| voz | real | gerado 5U | gerado 5M | AUC 5U | AUC 5M | direcção |
|---|---|---|---|---|---|---|
| Campos | **0,3566** | 0,5094 | 0,5165 | 0,729 | 0,740 | **gerado mais regular** |
| Reis | 0,4755 | 0,5269 | 0,6151 | 0,591 | 0,688 | gerado mais regular |
| ortónimo | **0,7572** | 0,6672 | 0,6712 | 0,639 | 0,632 | **real mais regular** |

Todas as diferenças do 5M excluem zero; no 5U, duas das três.

**E a leitura que interessa não é voz a voz, é a amplitude:**

| | amplitude entre as três vozes |
|---|---|
| **poeta** | **0,4006** (0,357 no Campos a 0,757 no ortónimo) |
| gerado 5M | **0,1547** |
| gerado 5U | 0,1578 |

**O poeta varia 2,6× mais do que o modelo.** O modelo converge para uma
regularidade média (0,52–0,67) em todas as vozes, enquanto o poeta vai do
versículo irregular do Campos à quadra metrificada do ortónimo. **A forma é onde
as vozes mais se distinguem umas das outras, e é onde o modelo as distingue
menos.**

Note-se a direcção: no Campos o modelo é **regular de mais** e no ortónimo
**irregular de mais** — os dois erros apontam para o meio. **Não é falta de
capacidade numa direcção; é regressão à média.**

---

## 5. O que isto decide

**Dá ao passo 34 a primeira causa medida.** A [5Q](FASE-5Q-RELATORIO.md)
atribuiu o seu AUC de 0,938–1,000 a «ortografia e forma de verso». Três fases
desmontaram a primeira metade ([5R](FASE-5R-RELATORIO.md),
[5T](FASE-5T-RELATORIO.md), [5U](FASE-5U-RELATORIO.md): 7 próclises e 1 marca
em 120 amostras). **Esta confirma a segunda.**

**E dá-lhe tamanho, que é o que falta às atribuições:**

| via | AUC mecânico | fase |
|---|---|---|
| **rima, no ortónimo** | **0,780** [0,724, 0,831] | esta |
| metro, no Campos | 0,740 | esta |
| metro, no ortónimo | 0,632 | esta |
| rima, no Reis | 0,516 — **e é o correcto** | esta |
| ortografia | sem eventos | 5R · 5U |
| gramática | sem sinal | 5T · 5U |

**0,780 não é 0,938.** A forma é o maior contribuinte mecânico encontrado e
**não fecha** o número da 5Q. Combinar rima e metro poderia aproximar-se — e
**não o fiz**, porque é exactamente o movimento que produziu o pior resultado
deste projecto: a [5C](FASE-5C.md) ajustou um combinador em amostra e viu o AUC
cair de **0,869 para 0,544** em dados retidos. Combinar pede validação retida e
é fase própria.

**Autoriza uma intervenção, e numa voz só.** Pelo §4.1, o V3 disparar autoriza
**pré-registar** uma intervenção de forma na voz onde disparou. O caso mais
informativo não é o Reis — como o §4.1 previa, com as vozes trocadas — mas o
**ortónimo**: a instrução existe, é explícita, e é ignorada por completo.

**Não autoriza mexer agora.** A [5I](FASE-5I-RELATORIO.md) mediu saldo líquido
**negativo** numa mudança de instrução, e nada aqui diz que *reforçar* a
instrução de rima a faz cumprir — só que a actual não é cumprida.

### O que fica na mesa

1. **O [passo 37](CONTROLO.md), novo: fazer o ortónimo rimar.** É a primeira
   intervenção desta sequência com um desfecho mecânico, barato e pré-medido —
   0,2167 contra 0,7769 — e com um controlo positivo embutido (o Reis não pode
   começar a rimar).
2. **Combinar rima e metro, com validação retida.** Pode levar a forma de 0,780
   para mais perto do 0,938. A 5C diz exactamente como falhar nisto.
3. **A amplitude entre vozes como desfecho próprio.** 0,4006 contra 0,1547 é uma
   medida de «o modelo diferencia as vozes?» que não existia, e aplica-se a
   qualquer intervenção futura.
4. **O esquema rimático** (ABAB contra AABB), que o §2.3 deixou de fora por o
   `stanzas` do *parse* não estar validado para isso.

> **A lição, e é a oitava sobre instrumentos.** Esta fase teve **dois** erros
> meus e os dois foram apanhados pelo mesmo mecanismo — o portão de calibração
> a correr **antes** do alvo.
>
> O primeiro foi de conteúdo: troquei as instruções de duas personas e construí
> o portão sobre a troca. O segundo foi de instrumento: a chave de rima contava
> **repetição**, e Caeiro «rimava» a 0,64 por repetir palavras. **Nenhum dos dois
> se veria olhando para o alvo**, porque ambos produziriam números plausíveis
> sobre texto gerado. Vêem-se olhando para o material cuja forma já se conhece
> por outra via — aqui, as quatro poéticas escritas em `voices.py` antes de a
> fase existir.
>
> **E a diferença entre esta fase e as duas anteriores não é o método: é a
> frequência.** A 5T e a 5U usaram o mesmo rigor e morreram com 7 eventos em 120
> amostras. Aqui cada verso conta, e por isso o mesmo rigor chega a uma
> conclusão. **Escolher onde medir é anterior a medir bem.**
