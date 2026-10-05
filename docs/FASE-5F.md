# Fase 5F — endireitar a régua: a âncora recalibrada, e a condição de a aceitar

Protocolo, **pré-registado antes de pontuar**. É o passo 9 da lista «[depois da
Fase 5](CONTROLO.md)», e a [Fase 5E](FASE-5E-RELATORIO.md) §8 autorizou-o — a
primeira autorização positiva desde a Fase 3B.

**Objectivo:** escrever uma âncora de 3a que premeie o Caeiro **real**, e
decidir por medição, em dados **retidos**, se ela o faz sem perder a
discriminação.

---

## 1. O que a 5E deixou, e o que esta fase tem de corrigir

A âncora de 3a, usada em cinco fases, dá a nota máxima a **3 de 20** poemas
autênticos de Caeiro, e **7 de 20** levam 0 dos dois avaliadores. Entre os
reprovados está «Vi que não há Natureza, / Que Natureza não existe».

O diagnóstico da 5E é preciso e é o que esta fase usa: **a âncora penaliza o
acto de filosofar**, e o Caeiro real filosofa constantemente. A definição do 0 —
«filosofa, interpreta, atribui significado oculto, personifica» — mede a
**presença** do movimento filosófico. Mas o que separa o Caeiro do ortónimo não é
filosofar ou não; os dois filosofam. É **para onde** o argumento vai.

> O Caeiro filosofa **para fechar a porta**: conclui que a coisa é só o que é.
> O ortónimo filosofa **para a abrir**: conclui em mistério, alma, destino.

A âncora nova mede a **direcção** em vez da presença. É a única mudança de
princípio, e tudo o resto segue dela.

---

## 2. A âncora recalibrada (3a′)

| 2 | 1 | 0 |
|---|---|---|
| o poema **acaba na coisa**: ou fica no visível de ponta a ponta, ou argumenta e o argumento **fecha a porta** — conclui que a coisa é só o que é | o poema fecha a porta mas deixa **uma** aberta: fica de pé uma afirmação de profundidade, de alma, de destino, ou uma lição que manda buscar além | o poema **acaba além da coisa**: mistério, alma, destino, verdade oculta, moral que manda buscar, ou a natureza a sentir pelo poeta |

### 2.1 Os casos difíceis, decididos antes de pontuar

A Fase 5D falhou porque a sua definição foi escrita pelos casos fáceis e
calou-se sobre a fronteira que decidia tudo. Estas seis regras são a correcção, e
nenhuma é inventada aqui: cada uma nomeia um caso que apareceu nas folhas das
fases 5B a 5E.

1. **Filosofar não é falta.** Um poema inteiramente argumentativo pode levar 2 se
   o argumento terminar na coisa. «Vi que não há Natureza… A Natureza é partes
   sem um todo» é um **2**.
2. **A tautologia deflacionária é a assinatura, não um defeito.** «As coisas são
   só o que são», «cada coisa só lembra o que é», «a borboleta é apenas
   borboleta» contam **para** o 2. *(Esta é a fronteira que partiu a Fase 5D ao
   meio — passo 8 da lista do `CONTROLO.md` — e fica aqui decidida.)*
3. **Atribuição negada não conta como atribuição.** «Não lhes atribuo significado
   oculto», «não busco na natureza uma moral» não abrem porta nenhuma.
4. **Atribuição posta e depois retirada conta como fechada.** «Se às vezes digo
   que as flores sorriem… não é porque eu julgue que há sorrisos nas flores» é
   retracção, e o poema é candidato a 2.
5. **Personificação posta e mantida abre a porta.** «A montanha sorri», «o riacho
   esquece a fonte» levam 0, salvo retracção pela regra 4.
6. **Moral: a direcção decide.** Mandar **aceitar o que é** fecha a porta («e eu
   aceito, e nem agradeço» — conta para 2); mandar **buscar além** abre-a
   («ensina-me a sonhar» — 0).

### 2.2 O que **não** muda

A escala continua **0/1/2** e o critério continua a ser a **poética** — não a
forma, que é o 3b, nem a resposta à pergunta, que é o 4. A âncora de 3b fica
intacta: esta fase não lhe toca.

E a âncora antiga **não é apagada**. Fica em [`FASE-5.md`](FASE-5.md) §5.1 como
está, porque é com ela que as Fases 5 e 5B foram medidas e reescrevê-la
tornaria aqueles relatórios ilegíveis.

---

## 3. Derivação e retenção, que é a lição da 5C

A âncora acima foi escrita **depois** de eu ler os 39 poemas reais de Caeiro das
folhas da 5D e da 5E. Não há como desfazer isso, e é por isso que esses 39
**não** validam nada aqui.

| | n | para que serve |
|---|---|---|
| **derivação** | 39 poemas reais já pontuados (5D + 5E) | escrever a âncora. Qualquer número sobre eles é **in-sample e inflacionado** |
| **retenção** | os **24** poemas elegíveis de Caeiro que sobram, **nunca lidos por mim** | **os portões correm aqui, e só aqui** |

A Fase 5C mediu o custo de confundir os dois: a AUC do FAS caía de **0,869
in-sample para 0,544 retida**. Esta fase não repete isso — e não há números
in-sample no relatório, nem como curiosidade, porque a tentação de os citar é o
que a 5C documentou.

---

## 4. A folha: 64 itens, três grupos, às cegas

| grupo | n | o que é |
|---|---|---|
| **R** | **24** | os poemas de Caeiro **retidos**, todos eles |
| **O** | 20 | poemas reais do ortónimo PT, não usados em nenhuma folha anterior |
| **G** | 20 | as 20 amostras da Fase 5B que nenhuma folha anterior usou |

Usam-se os **24** e não 20, porque o portão X1 é uma proporção sobre o grupo R e
cada poema vale 4 pontos percentuais.

Mesma elegibilidade das fases anteriores: 6 a 25 versos, numerais romanos
removidos, e os poemas de Caeiro recuperados para as perguntas da Fase 5B fora.

---

## 5. Os portões

Primário na **estimativa conjunta** — a média dos dois avaliadores por item —
que é a correcção prescrita pela 5D. Por avaliador corre em separado e
**relata-se, sem decidir**.

Estatística sem scipy: permutação (10000, semente 3), AUC por Mann-Whitney
normalizado com IC por bootstrap, κ ponderado linear.

| | portão | condição (nos 24 retidos) | o que decide |
|---|---|---|---|
| **X3** | **piso de concordância** | κ_lin ≥ **0,30** e concordância exacta ≥ **50%** | abaixo disto a média é ruído e nada se lê. Corre primeiro |
| **X2** | **a discriminação sobrevive** | AUC(ortónimo < Caeiro real) ≥ **0,70** e p ≤ 0,05 | a âncora nova **não** comprou simpatia pelo Caeiro à custa de pontuar tudo alto. Tem veto: sem isto, X1 não vale nada |
| **X1** | **a condição de aceitação** | mediana de 3a′ no Caeiro real ≥ **1** **e** ≥ **30%** dos 24 com **2** | a âncora premeia o original. **Autoriza substituí-la** como instrumento de regressão das fases seguintes |

**O 30% é o dobro do que a antiga deu** (15%, 3 de 20 na Fase 5E), e está fixado
antes de medir. Se sair entre 15% e 30%, a âncora melhorou e **não passa** — e
é isso que o número tem de significar para valer algo.

### 5.1 O que corre sem portão

- **O grupo G.** Se a âncora nova separar o gerado do real onde a antiga não
  separou (AUC 0,655, IC95% a conter 0,5 na 5E), é um ganho — mas a 5E já
  mostrou que n=20 não vê esta diferença, e pré-registar um portão sobre ela
  seria pedir o que não há potência para dar.
- **A comparação com a âncora antiga.** O marco é 15% e mediana 0,5, medidos na
  5E em **outros** 20 poemas. É uma comparação **entre amostras**, não dentro,
  e lê-se como tal.

---

## 6. Ameaças

- **A âncora foi escrita por mim depois de ler 39 poemas reais.** É a ameaça
  principal e a retenção do §3 é a defesa. Não é completa: o *princípio* da
  direcção veio de olhar para aqueles poemas, e se ele estiver ajustado a eles,
  os 24 retidos mostram-no.
- **Uma âncora pode ser frouxa em vez de certa.** É exactamente o que X2 vigia, e
  é a razão de ter veto sobre X1. Uma âncora que dê 2 a tudo passa X1 e falha
  X2.
- **Eu escrevi a âncora e sou um dos avaliadores.** R2 recebe-a sem saber que é
  nova, sem saber que houve uma antiga, e sem saber que há grupos.
- **Reconhecimento dos poemas canónicos.** A 5E desarmou-o em parte por
  evidência (o Caeiro real espalhou-se, e R2, sem viés, deu-lhe mediana mais
  alta que eu). Aqui a direcção do viés inverte-se: reconhecer um poema como
  Caeiro autêntico empurra-o **para cima**, e isso **favorece** X1. Fica
  declarado, e é a ameaça mais séria desta fase precisamente por favorecer a
  hipótese.
- **Os dois avaliadores são sessões do mesmo modelo.** Ressalva de sempre: o κ
  mede concordância, nunca correcção.
- **n=24.** Um poema vale 4 pontos percentuais em X1. Os IC vêm por bootstrap.

---

## 7. O que esta fase não faz

- **Não mede H5B**, nem nada por braço.
- **Não reescreve a Fase 5 nem a 5B.** A âncora antiga fica onde está (§2.2).
- **Não toca em `src/voices.py`.** A persona continua por medir; o que esta fase
  entrega é a régua para a medir.
- **Não recalibra as outras três vozes.** A âncora do Caeiro era a que estava
  sob suspeita, por ser a do único caso a 0,0.
- **Não mede 3b nem o critério 4.**

---

## 8. Checklist

```
[ ] A1  protocolo e âncora nova commitados antes de existir pontuação
[ ] B1  folha de 64 itens (24 R retidos + 20 O + 20 G), numerais removidos
[ ] B2  chave fechada; enquadramento de R2 verificado por fronteira de palavra
[ ] C1  R1 pontua com 3a′, com razão por item
[ ] C2  R2 pontua, cego ao desenho, aos grupos e à existência de âncora antiga
[ ] C3  as duas pontuações commitadas antes de a chave abrir
[ ] D1  X3 e X2 primeiro, na estimativa conjunta
[ ] D2  X1, com IC por bootstrap; por avaliador em separado, sem decidir
[ ] E1  relatório, sem um único número in-sample
```
