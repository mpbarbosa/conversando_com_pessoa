# Fase 5F — relatório: a âncora passa os três portões, e a régua endireitada vê o que a torta não via

Protocolo em [`FASE-5F.md`](FASE-5F.md), pré-registado em `a3cf872` **antes de
existir qualquer pontuação**. As duas pontuações foram commitadas em `9f022f0`
**antes de a chave ser aberta**.

**Não há um único número in-sample neste relatório.** Todos os portões correm
sobre os **24 poemas retidos** que eu nunca li.

---

## 1. O que se decidiu

**Os três portões passam. A âncora recalibrada é aceite.**

| | portão | exigia | medido (estimativa conjunta, 24 retidos) | |
|---|---|---|---|---|
| **X3** | piso de concordância | κ_lin ≥ 0,30 · exacta ≥ 50% | **κ_lin 0,620** · **68,8%** | **passa** |
| **X2** | a discriminação sobrevive | AUC(ortónimo < real) ≥ 0,70 · p ≤ 0,05 | **0,913** · IC95% [0,816; 0,985] · **p=0,0001** | **passa** |
| **X1** | a condição de aceitação | mediana ≥ 1 · **≥ 30%** com 2 | mediana **2,0** · **16 de 24** = **67%** · IC95% [0,458; 0,833] | **passa** |

E os três avaliadores possíveis — R1, R2 e a média — passam os três portões cada
um por si. Não há leitura alternativa.

### 1.1 O contraste com a âncora antiga

| | âncora antiga (Fase 5E) | âncora recalibrada |
|---|---|---|
| poemas autênticos com nota máxima | **15%** (3 de 20) | **67%** (16 de 24) |
| mediana no Caeiro real | 0,5 | **2,0** |
| AUC(ortónimo < Caeiro real) | 0,811 | **0,913** |

**A discriminação não foi comprada: melhorou.** Era o modo de falha que o X2
existia para apanhar — uma âncora frouxa que dá 2 a tudo passa X1 e perde a
separação — e o número foi na direcção contrária. A âncora nova premeia o
original **e** reconhece melhor o que não é Caeiro.

A comparação da primeira linha é **entre amostras** — 20 poemas na 5E, 24 outros
aqui — e lê-se como tal. A segunda e a terceira também. Nenhuma é um teste
emparelhado.

---

## 2. O resultado que não era portão, e é o maior desta fase

O §5.1 do protocolo registou o grupo das amostras geradas **sem portão**, com
esta justificação escrita antes de medir: a Fase 5E tinha dado AUC(gerado <
real) de 0,655 com IC95% a conter 0,5, e «pré-registar um portão sobre ela seria
pedir o que não há potência para dar».

Saiu assim:

| | AUC(gerado < real) | p |
|---|---|---|
| âncora **antiga** (Fase 5E) | 0,655 | 0,112 |
| âncora **recalibrada** | **0,851** | **0,0003** |

**A pergunta aberta desde a Fase 5 tem resposta: o Caeiro gerado é pior que o
Caeiro real, e mede-se.** Médias de 0,675 contra 1,604 na escala de 0 a 2, e
**nenhuma das 20 amostras geradas atingiu 2,0** na estimativa conjunta — as
melhores pararam em 1,5, abaixo do valor **modal** do grupo autêntico.

E o que isto diz sobre as cinco fases anteriores é preciso: **a incapacidade da
âncora antiga de distinguir autêntico de gerado era um artefacto do
instrumento**, não um facto sobre o modelo. Quando o instrumento dá 0 a 85% do
original, não lhe sobra escala para separar o original da imitação. Endireitada
a régua, a separação aparece e é forte.

**O que isto não é:** um portão. Foi pré-registado sem portão, e por uma razão
que continua válida — n=20 contra 24. Um resultado forte onde a potência era
reconhecidamente baixa pede **replicação**, e é a primeira coisa que a lista do
`CONTROLO.md` passa a ter.

---

## 3. Como a âncora nova funciona, nos casos que a decidem

A mudança de princípio foi uma só: medir a **direcção** do movimento em vez da
sua **presença**. Os três poemas retidos que a âncora nova continua a reprovar
mostram que ela não se tornou cega:

| | | |
|---|---|---|
| `poem_3436` | 0 nos dois | «a verdade está nelas e em mim / **e na nossa comum divindade**» — acaba além da coisa |
| `poem_3421` | 0 nos dois | «têm **o mesmo sorriso antigo**… para ver se elas **falavam**» — personificação posta e mantida |
| `poem_2587` | 0 / 1 | «Também sei fazer conjecturas» — e faz a conjectura a sério: ninfa na planta, alma no homem |

As três reprovações são defensáveis pela letra da âncora, e nenhuma é arbitrária.

E do outro lado, o que a âncora antiga reprovava e esta premeia:

| | |
|---|---|
| `poem_1108` (Fase 5E) | «Vi que não há Natureza, / Que Natureza não existe» — a antiga deu **0**, por filosofar |
| `poem_1011` | «para além da realidade imediata não há nada», e a luz apaga-se |
| `poem_364` | «não preciso de raciocínio onde tenho espáduas» |
| `poem_2578` | «amo as árvores por serem árvores, sem o meu pensamento» |
| `poem_1182` | pergunta se a flor tem beleza e fecha: «têm cor e forma e existência apenas» |

É o mesmo movimento em todos: argumenta, e **fecha a porta**.

---

## 4. A divergência entre avaliadores, e o que ela custou

R2 foi substancialmente mais generoso: médias de **1,08 contra 0,73** na folha
inteira, e 30 notas máximas contra as minhas 16. O κ_lin de 0,620 passa o piso
com folga, mas **a discordância máxima foi de 2 pontos**, e isso aconteceu em
**4 dos 64** itens — um 0 contra um 2:

| | grupo | |
|---|---|---|
| X19 | gerado | `B31` |
| X26 | gerado | `B40` |
| X32 | **real** | `poem_3518` |
| X62 | ortónimo | `poem_1765` |

**Não mudou nenhum veredicto**, e é a razão pela qual a correcção da Fase 5D
importou: os portões correram sobre a estimativa conjunta, e por avaliador
chegam ao mesmo sítio. Na 5D, uma divergência desta ordem partiu o veredicto ao
meio porque os portões corriam por avaliador.

Mas fica registado como fragilidade real: uma âncora em que dois leitores
divergem dois pontos em 6% dos itens não está apertada, e a fonte da divergência
é a generosidade de R2 com as amostras **geradas** — 8 delas com 2 contra zero
minhas. Se alguém quiser usar esta âncora para medir diferenças pequenas entre
prompts, precisa de a apertar nesse ponto, e o §7 diz onde.

---

## 5. Ameaças, revisitadas

- **A ameaça principal favorecia a hipótese, e está declarada desde o protocolo
  §6:** reconhecer um poema como Caeiro autêntico empurra-o para cima, o que
  **ajuda** X1. Inverteu de sinal em relação à 5E, onde o viés trabalhava contra
  W. Três coisas limitam o dano, e nenhuma o elimina: os 24 retidos são poemas
  que eu nunca li; **R2 não viu nenhuma fase anterior** e deu ao grupo autêntico
  uma fracção de 2 **mais alta** que eu (79% contra 67%), logo X1 não depende do
  meu reconhecimento; e X2, que o reconhecimento não ajuda, melhorou.
- **Eu escrevi a âncora e sou um dos avaliadores.** É a fragilidade estrutural
  desta fase e a retenção é a única defesa. Uma repetição por dois avaliadores
  que não a escreveram seria mais forte, e não existe aqui.
- **A âncora é generosa por omissão.** Declarei-o no meu ficheiro de pontuação
  antes da chave, a propósito do X21 — um poema carnal de ponta a ponta que não
  toca em mistério, alma nem destino e por isso satisfaz um critério que mede a
  **direcção** da atribuição de sentido. Um poema que não atribui nada passa sem
  mérito. O X2 não apanha isto, porque o ortónimo raramente escreve assim.
- **n=24.** Um poema vale 4 pontos percentuais em X1, e o IC95% da fracção é
  [0,458; 0,833] — largo, mas inteiramente acima do limiar de 0,30 e do marco de
  0,15 da âncora antiga.
- **Os dois avaliadores são sessões do mesmo modelo.** A ressalva de sempre: o κ
  mede concordância, nunca correcção.

---

## 6. Checklist

```
[x] A1  protocolo e âncora commitados antes de existir pontuação (a3cf872)
[x] B1  folha de 64 itens (24 R retidos + 20 O + 20 G), numerais removidos
[x] B2  chave fechada; enquadramento de R2 verificado por fronteira de palavra
[x] C1  R1 pontuou com 3a', com razão por item e o caso-limite declarado
[x] C2  R2 pontuou, cego ao desenho, aos grupos e à existência de âncora antiga
[x] C3  as duas pontuações commitadas antes de a chave abrir (9f022f0)
[x] D1  X3 e X2 primeiro, na conjunta — **passam**
[x] D2  X1 com IC por bootstrap — **passa**; por avaliador em separado, e os
        três chegam ao mesmo veredicto
[x] E1  relatório, sem um único número in-sample
```

---

## 7. O que isto autoriza, e o que não

**Autoriza substituir a âncora de 3a do Caeiro** pela do §2 do protocolo, como
instrumento das fases seguintes. É a segunda autorização positiva desta
sequência, e a primeira que entrega um instrumento em vez de o rejeitar.

**Não autoriza reescrever a Fase 5 nem a 5B.** A âncora antiga fica em
[`FASE-5.md`](FASE-5.md) §5.1 como está, porque é com ela que aquelas fases
foram medidas, e o G2 da Fase 5 sobrevive por ter sido uma comparação
emparelhada (ver [5E §4](FASE-5E-RELATORIO.md)).

**Não autoriza tratar o resultado do §2 como estabelecido.** Foi
pré-registado sem portão e pede replicação, com portão, em amostras novas.

**Não autoriza tocar em `src/voices.py`.** A persona do Caeiro **continua por
medir** — é o que esta sequência toda nunca conseguiu fazer — e agora há com que
a medir.

### O que a cadeia das seis fases deixa

A 5B não pôde medir por saturação. A 5C falhou a construir um desfecho por falta
de corpus. A 5D construiu um com resolução e apontou a âncora. A 5E mediu a
âncora e encontrou-a a reprovar o original em 85% dos casos. **A 5F endireitou-a
e, com ela endireitada, a diferença que cinco fases não viram aparece de
imediato.**

O que fica na mesa, em ordem:

1. **Repetir a Fase 5B com a âncora nova.** O harness, os dois braços e a regra
   de reescrita estão escritos e verificados desde a 5B; o que faltava era a
   régua. O desfecho tem agora mediana 2,0 no original e 0,75 no gerado, logo há
   folga para medir uma intervenção em qualquer das direcções — que é
   exactamente o que o G4 da 5B não teve.
2. **Replicar o §2 com portão.**
3. **Apertar a âncora onde R2 divergiu de mim**: as amostras geradas em que ele
   deu 2 e eu 0. A fronteira está identificada e é pequena.
