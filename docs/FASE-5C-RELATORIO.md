# Fase 5C — relatório: o instrumento é rejeitado, e o corpus é que não dá

Protocolo em [`FASE-5C.md`](FASE-5C.md), pré-registado em `43af93b` **antes de
existir qualquer número de validação**.

---

## 1. O que se decidiu

**V1 falha, V3 falha, V4 passa. O FAS é rejeitado como desfecho.**

| portão | exigia | mediu | |
|---|---|---|---|
| **V1** validade discriminante | AUC retida ≥ 0,70 e p ≤ 0,05 | **AUC = 0,544**, IC95% [0,446; 0,629], p = 0,573 | **falha** |
| **V3** validade convergente | ρ(FAS, 3a) ≤ −0,25 nos dois avaliadores | **+0,015** (R1) e **+0,041** (R2) | **falha** |
| **V4** especificidade | \|ρ(FAS, n.º de versos)\| ≤ 0,35 | +0,010 | passa |

E o número que importa está no contraste entre duas linhas:

| | AUC |
|---|---|
| **in-sample** — lista derivada dos poemas que depois separa | **0,869** |
| **retida** — lista derivada de metade, medida na outra metade | **0,544** |

**0,869 contra 0,544.** Todo o sinal do piloto era sobreajustamento. Com 39
poemas de Caeiro na derivação e 40 palavras escolhidas por estarem ausentes
**nesses** 39 poemas, a lista está ajustada à metade de derivação e não
generaliza nada: 0,544 é moeda ao ar.

O protocolo §3 tinha escrito, antes de medir: «A AUC de 0,809 do piloto é
in-sample e está inflacionada — o número que conta é o retido, e ainda não
existe.» Existe agora, e mata o instrumento.

---

## 2. O diagnóstico: premissa certa, corpus pobre

Os portões falharam, e **não** houve tentativa de os reabrir. O que se fez a
seguir foi distinguir duas causas possíveis, porque a prescrição muda com a
resposta: o FAS falha por a premissa lexical estar errada, ou por não haver
Caeiro suficiente para a derivar?

### 2.1 A curva de aprendizagem diz que é fome de dados

AUC retida contra o número de poemas de Caeiro na derivação, com os retidos
sempre os mesmos 26:

| poemas na derivação | AUC retida | AUC in-sample |
|---|---|---|
| 10 | 0,566 | 0,916 |
| 20 | 0,512 | 0,878 |
| 30 | 0,591 | 0,849 |
| 40 | 0,589 | 0,812 |
| **52** | **0,635** | 0,828 |

A retida **sobe** com os dados e a in-sample **desce**: é a assinatura clássica
do sobreajustamento a diminuir. A premissa não está morta — está **faminta**. E a
0,635 com 52 poemas, chegar a 0,70 exigiria bastante mais Caeiro do que existe:
o corpus tem **119** poemas de Caeiro, dos quais 78 estão limpos de
contaminação, e são ~5800 *tokens*. Não há mais.

### 2.2 A ligação ao construto existe, e é V1 que a esconde

Com a lista derivada de **todos** os 78 poemas limpos — a melhor que este corpus
permite, e **sem retenção possível**, porque não sobra nada para validar:

| | ρ(FAS, 3a) |
|---|---|
| R1 | **−0,271** |
| R2 | **−0,300** |

Os dois **passam** o limiar de −0,25 que o V3 pré-registou, e com o sinal certo:
mais vocabulário de atribuição, menos poética. **A falha do V3 é consequência da
falha do V1, e não um achado independente sobre o construto.** A lista de 39
poemas é ruído, e com ruído a correlação é zero; a lista de 78 carrega sinal.

E é aqui que está o aperto que esta fase não consegue desfazer:

> Este corpus permite uma lista **validada e inútil** (39 poemas, AUC retida
> 0,544) ou uma lista **útil e não validada** (78 poemas, ρ ≈ −0,28 e nenhum
> dado retido). **Não permite as duas.**

### 2.3 Um controlo que valida o princípio do §11 da Fase 5

A mesma correlação, calculada com a lista do **Instrumento II da Fase 5B** — os
20 referentes tirados do texto da persona, e não do corpus:

| | ρ(FAS, 3a) |
|---|---|
| R1 | +0,099 |
| R2 | −0,080 |

Nenhuma relação. A lista **derivada do corpus** (ρ ≈ −0,28) é
mensuravelmente melhor que a lista **derivada do tratamento** (ρ ≈ 0), e isto é
a primeira confirmação empírica, neste projecto, do princípio que a Fase 5 §11
tinha escrito como argumento:

> «o que protege a medição não é a ordem temporal, é a **independência entre a
> regra e a quantidade medida**.»

Não protege só contra viés: **mede melhor**. Formulação da sessão da Fase 5, e
fica agora com um número a sustentá-la.

### 2.4 Uma atenuação que inflaciona a severidade do V3

O 3a tem **3 valores distintos** e 50 das 60 amostras no mesmo valor. Um ρ de
Spearman contra uma variável de três níveis é atenuado por construção, logo
−0,28 é um piso da associação verdadeira e não uma estimativa dela. O V3 foi
pré-registado contra um alvo que a própria saturação do 3a torna difícil de
atingir — e isso é mais um sintoma do problema que a Fase 5C existia para
resolver, não uma desculpa.

---

## 3. A resolução, que era o motivo de tudo isto

Propriedade declarada, nunca portão (§3.1 do protocolo), medida cegamente ao
braço:

| desfecho | valores distintos em 60 amostras | no valor modal | máximo |
|---|---|---|---|
| **3a** (Fase 5B) | **3** | 50 de 60 | 2 |
| **FAS** | **25** | 15 de 60 a zero | 0,4375 |

O FAS tem **8x mais resolução** que o 3a e um quarto do chão. **Resolvia o
problema da Fase 5B, e não serve — porque não está validado.** Um desfecho com
resolução e sem validade mede finamente alguma coisa que não se sabe qual é.

---

## 4. O que está proibido de concluir, e cumpre-se

O passo E1 do protocolo era aplicar o FAS aos 30 pares da Fase 5B, como
**estimativa exploratória para dimensionar uma Fase 5D** — nunca como decisão
sobre H5B (§7). Correu, e o resultado está em
[`fase-5c/01-validacao.json`](fase-5c/01-validacao.json).

**Está morto pela falha do V1, e não se interpreta.** O número existe no
ficheiro porque o script o calculou antes de os portões serem avaliados, e
apagá-lo seria pior que o declarar. Para ser explícito sobre o que não se lê: o Δ
aponta na direcção **contrária** a H5B, com 18 dos 28 pares discordantes a favor
do braço de controlo. **Isto não é evidência de nada.** Vem de um instrumento com
AUC retida de 0,544 — um instrumento que não distingue Caeiro real de ortónimo
real não pode distinguir dois prompts de Caeiro, e a direcção que ele aponta é
ruído com sinal.

**E não se recalcula o E1 com a lista dos 78.** Seria trocar o instrumento depois
de ver que o primeiro falhou, com o desfecho já escolhido depois de eu ter lido
as amostras — a pesca de instrumento que o §7 proibiu e que a Fase 5B recusou ao
seu próprio intervalo favorável. A estimativa para dimensionar a 5D tem de sair
de um instrumento validado, e ainda não há nenhum.

---

## 5. As ameaças do protocolo, revisitadas

- **Eu li as 60 amostras antes de desenhar o instrumento.** Continua a ser a
  ameaça principal, e esta fase não a testou — fechou antes, na validação.
- **O FAS é lexical e a poética não é.** O §2.2 mostra que a ligação existe
  (ρ ≈ −0,28) mas é modesta, e o §2.4 mostra que o 3a saturado a atenua. A
  questão fica aberta, não respondida.
- **A lista não é lematizada.** Com 39 poemas na derivação, é provável que a
  falta de lematização contribua para a instabilidade: `sonhar` entra, `sonho`
  e `sonhos` não, e qual das formas aparece nos 39 é sorte. Não foi isolado.
- **O contraste mistura três poéticas.** A variante só-ortónimo, sem portão, dá
  AUC retida **0,568** contra 0,544, e ρ(3a) de +0,039/+0,079 — igualmente
  inútil. As duas listas partilham 35 das 40 palavras, logo o contraste não era
  o problema.
- **39 poemas são poucos** e o IC95% da AUC retida é [0,446; 0,629]: contém 0,5
  com folga. O intervalo largo lê-se como intervalo largo, e lê-se assim.

---

## 6. Checklist

```
[x] A1  protocolo commitado antes de existir número de validação (43af93b)
[x] B1  partição 39/39 por semente fixa, 41 Caeiro contaminados excluídos
[x] B2  lista derivada só da metade de derivação; publicada inteira no JSON
[x] C1  V1: AUC retida 0,544, IC95% [0,446; 0,629], p=0,573 — **falha**
[x] C2  V3: ρ = +0,015 (R1) e +0,041 (R2) — **falha**
[x] C3  V4: ρ(n.º de versos) = +0,010 — passa
[x] D1  variante só-ortónimo: AUC 0,568, 35/40 palavras comuns — igual
[x] E1  calculado e **declarado nulo** pela falha do V1 (§4)
[x] F1  relatório
```

Fora do protocolo, e registado por ter aparecido pelo caminho: o diagnóstico do
§2, que localiza a falha na dimensão do corpus e não na premissa, e o controlo
do §2.3, que dá um número ao princípio do §11 da Fase 5.

---

## 7. O que isto autoriza, e o que não

**Não autoriza usar o FAS como desfecho**, nem como primário nem como
secundário. Fica em [`fase-5c/fas.py`](fase-5c/fas.py) com os números da sua
própria rejeição.

**Não autoriza uma Fase 5D sobre H5B.** Continua a faltar o instrumento, que era
o pré-requisito, e esta fase não o entregou.

**Não autoriza nenhuma leitura do Δ do §4.**

**Autoriza fechar a via lexical para esta voz, e com uma razão quantificada:**
78 poemas limpos e ~5800 *tokens* não bastam para derivar por log-odds uma lista
que generalize. A curva do §2.1 mostra a retida a subir — 0,512 → 0,635 — e a
chegar a 0,635 com 52 poemas, o que diz que o caminho é real e que este corpus
não o percorre. Quem o quiser percorrer precisa de mais Caeiro do que existe, e
isso não é uma tarefa de engenharia.

Isto fecha também, pela mesma razão, o **passo 4** da lista do `CONTROLO.md` — a
«sombra lexical» do §11 da Fase 5, que pedia exactamente esta regra de selecção
vinda de fora da amostra. A regra foi construída, foi validada, e a validação
reprovou-a por falta de corpus. O passo não fica pendente: fica **respondido**.

### A entrada da fase seguinte, e é mais simples do que esta

A via lexical era um desvio. **O construto que falta medir finamente já está
definido nas âncoras da Fase 5**, e em palavras exactas: a âncora de 1 diz
«sensorial na maior parte, com **uma** volta simbólica ou moral». A âncora
**conta voltas** — e depois joga fora a contagem, porque o 0 serve para uma volta
a mais que uma e para dez.

O desfecho em falta é portanto a contagem que a âncora já faz e descarta:

> **Número de voltas interpretativas por poema**, com «volta» definida pela
> âncora de 3a que já existe, julgada pelos dois avaliadores.

Três coisas recomendam-no acima de tudo o que esta fase tentou:

1. **Não precisa de corpus para ser derivado.** O construto vem da âncora, que
   está pré-registada desde a Fase 5 e nunca foi tocada.
2. **Os dados de validação já existem.** Os dois avaliadores da Fase 5B
   escreveram, por amostra, a razão que decidiu o 3a, e essas razões **citam as
   voltas uma a uma** — «a inexpressividade», «eco na minha alma», «presença sem
   perturbação». A concordância de uma contagem pode ser medida contra material
   que já está commitado.
3. **Valida-se contra os poemas reais**, que devem contar perto de zero voltas —
   e aí os 119 poemas de Caeiro bastam, porque se usam como **teste** e não como
   corpo de derivação. É a diferença que afundou o FAS.

O que isso pede, e esta fase não tem, é um protocolo próprio: a definição
operativa de «volta», o teste de concordância entre contadores, e a validação
contra Caeiro real **antes** de se aplicar a qualquer amostra gerada. Pela
terceira vez neste projecto, a ordem é essa.
