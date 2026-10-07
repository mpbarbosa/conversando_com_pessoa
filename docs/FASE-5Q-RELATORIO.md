# Fase 5Q — relatório: o sistema funciona no Caeiro e falha nas outras três

**Protocolo:** [`FASE-5Q.md`](FASE-5Q.md), pré-registado em `92cc4f0`.
**Dados:** [`fase-5q/02-juizos.json`](fase-5q/) (às cegas, commitados antes da
chave) · [`03-resultados.json`](fase-5q/)

---

## 0. Os portões

| | | |
|---|---|---|
| **Q1** o instrumento tem resolução | ✅ **dispara** | **AUC 0,988** — e o problema é ter **demasiada** |
| **Q2** o llama está mais perto do poeta | ❌ **não dispara** | as médias são **idênticas**: 1,42 e 1,42 |
| **Q3** e está nas três vozes | ❌ não dispara | 1 de 3 |
| **Q4** inconclusivo | ✅ **dispara** | o IC inclui 0 |

**Pelo compromisso do §4 do protocolo, escrito antes de medir: o Q4 disparou,
logo nada entra no `src/`. A troca não é aplicada.**

E o resultado por trás do nulo é maior do que a pergunta que a fase fez: **nas
três vozes que faltavam, os dois modelos são trivialmente distinguíveis de
Pessoa autêntico.** O sucesso do Caeiro não é representativo.

---

## 1. Q1 — resolução a mais, não a menos

| | AUC(real > gerado) |
|---|---|
| pooled, 24 reais contra 48 gerados | **0,988** |
| só com os 20 reais **sem** marca editorial | **0,988** |

Identifiquei Pessoa autêntico quase sem erro. **A fuga editorial que declarei ao
commitar os juízos — `[acordando?]`, `[que]`, `(tua)`, `minhaOde` — era
imaterial:** só 4 dos 24 reais a tinham, a média deles é 4,00 contra 3,95 dos
outros, e **a AUC sem eles é idêntica à três decimais**. Tê-los-ia chamado reais
pela voz de qualquer maneira.

**Mas uma AUC de 0,988 não é um instrumento bom: é um instrumento sem espaço.**
Com os dois braços encostados ao chão, não há onde uma diferença entre eles
apareça — que é exactamente o que o Q2 encontrou.

> **É o espelho do problema da [5O](FASE-5O-RELATORIO.md), outra vez.** Ali o 3a′
> saturou no **tecto** (78% dos itens no máximo) e a AUC(real > llama) deu 0,526
> por falta de espaço em cima. Aqui satura no **chão**: 0,988 por falta de espaço
> em baixo. **O mesmo instrumento, nas duas pontas, pela mesma razão** — e o
> diagnóstico é o da 5D: um desfecho sem variância não separa nada.

---

## 2. Q2 e Q3 — não há diferença entre os modelos

| | AUC(real > …) | média do juízo |
|---|---|---|
| `qwen2.5:7b` | 0,978 | **1,42** |
| `llama3.1:8b` | 0,998 | **1,42** |
| Δ | **+0,020** · IC95% **[−0,005; +0,065]** | |

**As médias são iguais às duas decimais.** O Δ da AUC é +0,020 a favor do qwen e
o intervalo cruza zero.

Por voz:

| voz | AUC qwen | AUC llama | Δ | média Q | média L | **média real** |
|---|---|---|---|---|---|---|
| campos | **1,000** | 0,984 | −0,016 | 1,12 | 1,62 | **3,88** |
| reis | 0,938 | **1,000** | +0,062 | 1,75 | 1,50 | **4,00** |
| ortonimo | 1,000 | 1,000 | 0,000 | 1,38 | 1,12 | **4,00** |

Uma voz a favor de cada modelo e um empate. **Nenhuma AUC desce abaixo de
0,938** — em nenhuma das três vozes, com nenhum dos dois modelos, houve um
poema que eu tomasse por Pessoa com alguma convicção.

---

## 3. O achado: o gargalo é de superfície, não de conteúdo

A fase perguntava por **conteúdo** e a resposta veio de outro lado. Contando os
defeitos concretos que eu citei como razão nos 48 itens gerados:

| defeito | n | qwen | llama |
|---|---|---|---|
| erro de gramática ou concordância | **20** | 14 | 6 |
| grafia brasileira | **10** | 3 | 7 |
| palavra que não existe / incoerência | 7 | 7 | 0 |
| **truncado a meio** | 5 | 0 | **5** |
| palavra estrangeira (espanhol, inglês) | 2 | 2 | 0 |

**32 dos 48 itens gerados (67%) têm pelo menos um defeito de superfície
citado** — qwen 20 de 24, llama 12 de 24.

E é isto que explica o nulo do Q2: **a tarefa de detecção é decidida pelo
primeiro defeito de superfície que aparece.** Um `requefú`, um `Tudo else`, um
`amanece`, um verso cortado a meio da palavra — qualquer um basta, e nenhuma
subtileza de conteúdo chega a pesar. Os dois modelos têm defeitos em abundância,
em proporções diferentes mas com o mesmo efeito.

### 3.1 E explica o contraste com o Caeiro

| | AUC(real > llama) |
|---|---|
| **Caeiro** ([5O](FASE-5O-RELATORIO.md)) | **0,526** |
| campos · reis · ortonimo (esta fase) | 0,984 · 1,000 · 1,000 |

O Caeiro é a voz **mais fácil de imitar**: verso livre curto, dicção plana,
frases declarativas. Há pouca superfície onde errar. O **Reis** exige sintaxe
latinizante e medida alternada; o **ortónimo** exige metro regular e rima; o
**Campos** exige o versículo longo sustentado. São competências **formais**, e é
nelas que os dois modelos se entregam.

**Logo o sucesso do Caeiro, que seis fases mediram, não generaliza — e a razão
não é a que o passo 25 supunha.**

### 3.2 Três das cinco classes já têm guarda, e ela não as apanha

`src/guard.py` tem `brasileirismos()`, `lingua_errada()` e o harness grava
`truncada`. Testei a guarda contra **as formas que eu realmente vi**:

```
objeto · rastro · concreto · elétricas · tênue · embaixo
vocês · em uma · eletricos · arduo · silencio
```

**A guarda não apanha nenhuma das onze.** É uma lista fixa de 14 palavras
derivada na Fase 0, e os defeitos reais são de outra natureza:

- **ortográficos**, do Acordo de 1990 — `elétrica`/`eléctrica`,
  `objeto`/`objecto`, `tênue`/`ténue`. O corpus é Pessoa pré-1990 e usa as formas
  com consoante muda;
- **acentuação em falta** — `arduo`, `silencio`: não são brasileirismos, são
  erros;
- **lexicais e sintácticos** — `rastro`/`rasto`, `embaixo`/`em baixo`,
  `em uma`/`numa`, `vocês`.

E a **truncatura** é gravada e **não é rejeitada**: cinco itens cortados a meio
da palavra chegaram à folha.

---

## 4. A correcção ao meu próprio §4

O protocolo escreveu: «**Se o Q4 disparar**, nada entra — e a prescrição é
acrescentar as repetições que sobram da 5M». **A primeira metade cumpre-se e a
segunda está errada.**

A prescrição supunha que um nulo seria **falta de potência**. Não é: as médias
são **idênticas** (1,42 e 1,42) e as três AUCs estão entre 0,938 e 1,000, isto é,
**encostadas ao limite da escala**. Acrescentar 144 juízos estreitaria o intervalo
em torno de um Δ que é zero, num sítio onde não há espaço para ser outra coisa.

**É um problema de resolução e não de potência**, e a prescrição certa é a do §5
— mudar o que se mede, não medir mais do mesmo.

---

## 5. O que isto autoriza, e o que não

**Não autoriza a troca de modelo.** O Q4 disparou e o compromisso do §4 era
explícito. **E a razão do bloqueio mudou:** o passo 25 bloqueava por se temer que
o llama fosse **pior** nas outras vozes. Isso está agora medido e **é falso** — não
é pior, é igual. O que bloqueia é que **o instrumento não resolve nenhum dos dois
ali**, porque ambos estão muito abaixo do chão.

**Não autoriza dizer que os modelos são equivalentes.** Diz que são
indistinguíveis **nesta tarefa**, que satura. No Caeiro, onde há espaço, a
diferença é grande e replicada (+0,667).

**Autoriza — e é o que importa — reorientar o problema.** Em três das quatro
vozes o sistema não produz texto que passe por português de Portugal em verso. A
escolha de modelo é, nessas vozes, uma discussão sobre o segundo decimal de algo
que falha no primeiro.

**E não autoriza aplicar uma guarda nova sem a medir.** A correcção óbvia —
alargar a lista de interdições — é exactamente o que a pendência do
[`CONTROLO.md`](CONTROLO.md) avisa: «pede medição contra os 2083 poemas antes de
entrar, como o `lingua_errada` teve (0,12 rejeita 3 de 1906)». Uma lista escrita
à mão a partir dos onze casos que eu vi é a mesma falha da 5C: derivar o
instrumento dos dados que o motivaram.

### O que fica na mesa, reordenado por esta fase

1. **Um detector de superfície derivado do corpus**, e não da minha lista. A regra
   tem a forma «a contraparte europeia aparece nos 2083 poemas e a brasileira
   não», que é verificável e não vem da minha impressão. **É o próximo passo**, é
   de **produto**, e é mensurável: a taxa de falsos positivos contra o corpus, e
   quantos dos 48 itens desta fase apanharia.
2. **Rejeitar a truncatura na guarda.** Está gravada e não é usada; cinco itens
   cortados a meio da palavra chegaram à folha desta fase.
3. **A troca de modelo**, que deixa de estar bloqueada por falta de evidência
   contra e passa a estar à espera de um instrumento com resolução — ou de uma
   decisão de produto tomada com a evidência do Caeiro, que é forte.
4. **O passo 25** perde a urgência: uma âncora de conteúdo por voz não ajuda
   enquanto 67% das amostras se entregarem pela ortografia.

> **A lição, e é a sétima da série dos instrumentos.** As seis anteriores foram
> validade, resolução, origem, forma, escala e operacionalização do portão. Esta
> é sobre **onde o instrumento está apontado**: perguntei por conteúdo e a
> resposta chegou de uma camada abaixo, porque a detecção é decidida pelo defeito
> mais grosseiro presente. **Medir o andar de cima só faz sentido quando o de
> baixo está de pé** — e seis fases mediram conteúdo no Caeiro, que é a única voz
> onde o de baixo está de pé.
