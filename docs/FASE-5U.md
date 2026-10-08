# Fase 5U — A instrução de língua faz alguma coisa?

**[Passo 35](CONTROLO.md), aberto pela [5T](FASE-5T-RELATORIO.md).** Pré-registada
em 2026-10-08, **antes de existir qualquer amostra**.

---

## 1. Porque esta pergunta tem de ser feita antes das outras

A [5T](FASE-5T-RELATORIO.md) mediu que, à régua da próclise por atracção, os
modelos estão **na taxa do poeta** (0,052–0,062 contra 0,045) e usam o gerúndio
progressivo **menos** que ele (2 em 48 contra 101 em 1926). Isso tem duas
explicações opostas e a fase não podia escolher entre elas:

| | se for assim | consequência para o passo 34 |
|---|---|---|
| **a instrução sustenta a superfície** | `REGRAS_LINGUA` está a fazer o trabalho | instruir **funciona** em superfície, e vale pré-registar uma instrução de **forma** |
| **a instrução é decoração** | os modelos escrevem assim de qualquer maneira | instruir **não funciona**, e o passo 34 precisa de outro mecanismo |

**E há um precedente medido, no mesmo ficheiro.** O `REGRAS_NAO_COPIAR` tem na
sua docstring o efeito que foi medido em 24 respostas reais: **sem ele, a
resposta mediana copia 82% dos seus versos do contexto** (Caeiro 93%, ortónimo
100%). Logo neste projecto já se sabe que **um bloco do `system` pode ser
decisivo** — e sabe-se porque foi medido.

**O `REGRAS_LINGUA` nunca o foi.** Está em produção desde a Fase 0, escrito a
partir da observação de que os três modelos de então faziam «colocação
proclítica sistemática».

### 1.1 E o bloco é exactamente um, e tem quatro regras

Verificado no `system_prompt()` montado, não de memória:

> «Escreves em português europeu, na **ortografia anterior ao acordo de 1990**.
> **Colocação enclítica, sempre** … Usa **«tu», não «você»**. **Não uses
> gerúndio** onde o português europeu usa «a» + infinitivo.»

**E as quatro têm leitura mecânica, três delas construídas na 5T:**

| regra | instrumento | medido em |
|---|---|---|
| ortografia pré-1990 | o detector da [5R](FASE-5R-RELATORIO.md) a **20×** | 0,73% de falsos positivos, **zero** poemas reais marcados |
| ênclise | próclise por **atracção** | [5T §1.3](FASE-5T-RELATORIO.md): poeta 0,045 |
| «tu» não «você» | `guard.tratamento_indevido` | [5T §3](FASE-5T-RELATORIO.md): corpus 0,21% |
| sem gerúndio | perífrase progressiva | [5T §2](FASE-5T-RELATORIO.md): corpus 5,24% |

> **E uma correcção a caminho.** A docstring do `INTERDICOES` diz que é «usada
> **na instrução** e na guarda de saída». `grep` dá `guard.py` e `cli.py` e mais
> nada: **não vai ao prompt**. Importa aqui porque define o que esta ablação
> remove — e o que remove é **todo** o tratamento de língua no `system`.

---

## 2. O desenho: ablação emparelhada de um bloco

**Dois braços, prompt idêntico menos o bloco:**

| braço | `system` |
|---|---|
| **C** (completo) | como está em produção |
| **A** (ablado) | igual, **sem** `REGRAS_LINGUA[Lang.PT]` |

**3 vozes × 10 perguntas × 2 repetições × 2 braços = 120 amostras.** As três
vozes são as que falham ([5Q](FASE-5Q-RELATORIO.md)): Campos, Reis, ortónimo. As
perguntas são as mesmas do banco dourado que a 5M usou (`q11`–`q40`), e o
harness é o da [5M](fase-5m/) adaptado — mesmas sementes, mesmo diário
retomável, mesmo modelo de serviço (`llama3.1:8b`, desde a [5S](FASE-5S-RELATORIO.md)).

**A ablação faz-se por substituição do `persona` que o `Pipeline` importa**, e
não mexendo em `src/`. Fica assim garantido que **só** o bloco muda.

### 2.1 Lê-se o texto cru, e não o limpo

A guarda **corrige** brasileirismos antes de devolver o texto
(`corrigir_brasileirismos`). Medir no texto limpo mediria a guarda e não o
modelo. **Toda a leitura é sobre `resposta.texto`**, o cru.

### 2.2 O emparelhamento é por célula, não por token

Mesma semente nos dois braços, mas **o prompt difere**, logo a cadeia de
amostragem diverge e os textos não são comparáveis palavra a palavra. O par é
`(voz, pergunta, repetição)`, e é a esse nível que a diferença é calculada. O n
efectivo é o **número de agrupamentos** — 30 por braço —, pela lição do
[5K](FASE-5K-RELATORIO.md).

---

## 3. Portões

| | nome | dispara se | leitura, escrita agora |
|---|---|---|---|
| **U1** | **a regra sustenta a ênclise** | o IC95 por *bootstrap* emparelhado da diferença (A − C) na proporção de próclise **exclui zero**, com A > C | o bloco faz trabalho na gramática |
| **U1′** | **e o efeito é «sistemático»** no sentido da Fase 0 | a proporção do braço **A** passa de **0,15** | três vezes a taxa do poeta (0,045) e fora de todos os intervalos que a 5T mediu |
| **U2** | **a regra sustenta a ortografia** | o IC95 emparelhado da diferença na fracção de itens marcados pelo detector da 5R a 20× **exclui zero**, com A > C | o bloco faz trabalho na ortografia — que é a metade que a 5R não conseguiu **detectar** mas consegue **medir** a 0,73% |
| **U3** | **a regra é decoração** | **nem U1 nem U2** disparam | o bloco não faz trabalho medível. Então a superfície das três vozes **não é alcançável por instrução**, e o passo 34 precisa de outro mecanismo |
| **U4** | — | descritivo, sem portão | «você», gerúndio, `e_verso`, fracção do dicionário, plágio, truncatura, latência |

### 3.1 A decisão, pré-escrita

| | decisão |
|---|---|
| **U1 ou U2 dispara** | o bloco é **portante**. Duas consequências: (a) o [passo 24](CONTROLO.md) **não pode** mexer nas personas sem remedir a língua, porque mexe num texto que faz trabalho; (b) instruir **move** a superfície, logo fica autorizado **pré-registar** uma instrução de **forma** para o passo 34 — com o aviso da [5I](FASE-5I-RELATORIO.md), que mediu saldo líquido **negativo** numa mudança de instrução |
| **U3 dispara** | o bloco é **decoração**, e o passo 34 **não se resolve no prompt**. O que fica autorizado é a via que não passa por instruir: constrangimento na descodificação, ou afinação, ou aceitar que o produto serve **uma** voz. **Remover o bloco não entra nesta fase** — é intervenção e pede pré-registo próprio, mesmo que saia de graça |

### 3.2 O que esta fase não decide

- **Não decide qual das quatro regras.** É uma ablação de **bloco**, de
  propósito: é o teste decisivo mais barato. Uma ablação por regra custa quatro
  vezes isto e **só vale a pena se o U1 ou o U2 disparar**.
- **Não mede voz nem conteúdo.** A âncora 3a′ é do Caeiro e estas são as outras
  três ([passo 25](CONTROLO.md)). Nada aqui é julgado às cegas, porque nada aqui
  é julgado: os quatro instrumentos são mecânicos.
- **Não remove nada de `src/`**, com uma excepção que é de comentário: a
  docstring do `INTERDICOES` diz que vai à instrução e não vai.

---

## 4. Ameaças

### 4.1 Uma ablação de bloco confunde quatro regras

Assumido e declarado. Se o resultado for nulo, **não exonera nenhuma das
quatro individualmente** — exonera o bloco como um todo, que é a unidade em que
ele existe no prompt e a unidade em que o passo 24 lhe mexeria.

### 4.2 Remover texto do `system` muda o número de tokens

O bloco são ~70 tokens de um `system` de ~310. Removê-lo encurta o prefixo, o
que muda o prefill mas **não** o conteúdo da pergunta nem do contexto — o
`ORCAMENTO_USER` é sobre a mensagem do utilizador e não é tocado. A latência vai
no U4 como descritivo, para o registo.

### 4.3 Os instrumentos são meus e três são da fase anterior

A próclise por atracção, o gerúndio e o «você» foram construídos na 5T, e a 5T
mediu-os **no corpus** antes de os apontar a qualquer coisa — 2,65%, 5,24% e
0,21%. É a única razão por que servem aqui. O detector da 5R a 20× tem a sua
própria medição retida (0,73%, zero reais marcados).

### 4.4 Eu quero que o bloco seja portante

Porque isso deixava o passo 34 com uma via barata. O U3 tem a leitura escrita e
**não** é «tentar instruir melhor»: é dizer que instruir não chega. E a 5I já
mediu uma mudança de instrução com saldo **negativo**, logo a expectativa
honesta não é optimista.

---

## 5. Lista de verificação

```
[x] A1  120 geradas (3 vozes x 10 perguntas x 2 repeticoes x 2 bracos)
[x] A2  asserido: o `system` difere em 300 caracteres nas tres vozes, e sao o
        bloco. Verificado antes de gerar E a cada celula
[x] A3  os quatro instrumentos, no texto CRU
[x] A7  SENSIBILIDADE posterior e declarada: a regua pre-registada licenciava
        qualquer preposicao a distancia, o que e permissivo de mais. Encontrado
        a ler «Em cada instante te vejo» no braco A
[x] B1  U1 nao dispara (A 0,0000 contra C 0,0408) · U1' nao · U2 nao (UM item
        marcado em 120) · U3 DISPARA
[x] B2  decisao do §3.1 accionada: U3 -> nada e removido. **Mas dispara no
        chao**: 2 ocorrencias de proclise e 1 marca ortografica no braco de
        base. Ausencia de prova nao e prova de ausencia
[x] C1  relatorio FASE-5U-RELATORIO.md
[x] C2  a docstring do INTERDICOES corrigida
[x] C3  CONTROLO.md
```

**Sessões paralelas:** verificado antes de abrir. `git add` com ficheiros
nomeados.
