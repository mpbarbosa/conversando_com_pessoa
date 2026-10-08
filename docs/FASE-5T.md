# Fase 5T — A gramática que a persona manda e o modelo não faz

**Ataca o [passo 34](CONTROLO.md) pelo lado da geração.** Pré-registada em
2026-10-08, **antes de qualquer medição**. Não gera amostra nenhuma: corre sobre
dados já comprometidos.

---

## 1. A pergunta, e porque é esta

A [5Q](FASE-5Q-RELATORIO.md) mediu que em Campos, Reis e ortónimo **os dois
modelos** se entregam trivialmente (AUC 0,938–1,000), e nomeou a causa:
**competência de superfície em português europeu e em forma de verso**. A
[5R](FASE-5R-RELATORIO.md) fechou a via de **detectar** a parte **ortográfica**
com este corpus — não por defeito de desenho, mas porque as canónicas que
interessam aparecem 8, 7 e 2 vezes em 2083 poemas.

**Mas a ortografia não era a única metade.** A 5Q escreveu «ortografia **e
gramática**», e a gramática é outra coisa:

| | ortografia (5R) | gramática (esta fase) |
|---|---|---|
| unidade | a **forma** (`objecto`) | a **construção** (pronome antes do verbo) |
| observações no corpus | 8, 7, 2 — **unidades** | milhares de linhas |
| o que limitava | o tamanho do corpus | — por medir |

**E há uma circunstância que torna a pergunta mais do que instrumental:** as três
regras que vão a medição estão **escritas no `system` prompt**, em
[`src/voices.py`](../src/voices.py):

> «Colocação enclítica, **sempre**: «dói-me», «estende-se», nunca «me dói», «se
> estende». Usa «tu», não «você». Não uses gerúndio onde o português europeu usa
> «a» + infinitivo.»

Logo isto não mede só se o defeito é detectável. Mede **se a instrução é
obedecida** — e é essa a pergunta que decide por onde o passo 34 ataca.

> **E a guarda não tem nada disto.** `grep` por «proclise», «gerundio» e «voce»
> em [`src/guard.py`](../src/guard.py) dá **zero**. As três regras existem só na
> instrução, e nunca foram verificadas na saída.

---

## 2. Os três detectores, declarados antes de correr

### 2.1 Próclise (R-PRO)

Marca um pronome átono em posição em que o português europeu exige ênclise.

**Pronomes considerados: `me`, `te`, `lhe`, `lhes`.** `o`/`a`/`os`/`as` ficam
**fora** (artigos e preposições homógrafos) e `nos`/`vos` também (`nos` = `em` +
`os`). É um sacrifício deliberado de cobertura a favor da precisão, declarado
aqui e não depois.

**`se` vai num ramo separado e reportado à parte,** porque é também conjunção
(«se me vires»). No ramo do `se` exige-se que o *token* anterior não seja
fronteira de oração.

**Marca-se quando o *token* anterior não licencia próclise.** A lista de
licenciadores é de **gramática, não do corpus** — fixada aqui antes de qualquer
contagem:

- negação: `não`, `nunca`, `nada`, `ninguém`, `nem`, `jamais`, `nenhum(a)`
- subordinação e relativos: `que`, `quem`, `se`, `quando`, `onde`, `como`,
  `porque`, `cujo(a)`, `qual`, `quanto`, `enquanto`, `embora`, `caso`,
  `conforme`, `pois`, `segundo`
- advérbios e quantificadores de foco: `já`, `ainda`, `sempre`, `também`, `só`,
  `apenas`, `talvez`, `bem`, `mal`, `tudo`, `todo(s)`, `toda(s)`, `muito`,
  `pouco`, `tanto`, `mais`, `menos`, `antes`, `depois`, `até`, `logo`, `aqui`,
  `ali`, `lá`, `cá`, `hoje`, `ontem`, `amanhã`, `assim`, `onde`
- **qualquer preposição** (o infinitivo preposicionado leva próclise: «para se
  ver»)
- **fronteira de oração** — início de linha, `,`, `;`, `:`, `.`, `!`, `?`, `—`,
  `(`, `«` — conta como **não licenciador**, porque é aí que a próclise é
  inequivocamente brasileira

### 2.2 Gerúndio progressivo (R-GER)

`estar`/`andar`/`ir`/`ficar`/`continuar` conjugado, seguido (com no máximo **um**
*token* de intervalo) de uma forma em `-ndo`. **Só a perífrase**: o gerúndio solto
(«andando por aí») é português europeu correcto e **não** se marca.

### 2.3 «você» (R-VOC)

`você`/`vocês`/`vosso` como tratamento. A 5R já mediu `vocês` **2×** em Pessoa,
logo esta tem uma expectativa publicada antes de correr.

---

## 3. O desenho

**Nenhuma geração nova.** Três conjuntos, todos já no repositório:

| conjunto | n | o que é |
|---|---|---|
| corpus pt | **1906** poemas | o **nulo**: quanto é que o detector marca em Pessoa |
| [5Q](fase-5q/) `01-chave.json` | **48** gerados + **24** reais | o alvo, nas três vozes que falham, nos **dois** modelos |
| [5M](fase-5m/) `01-cru.jsonl` | **180** | 4 vozes × 2 modelos, para a leitura por voz |

Os 24 reais da 5Q são um **segundo nulo**, de 24 poemas que passaram pelo mesmo
funil de amostragem que os gerados — e é a comparação que não depende de o corpus
inteiro ser comparável a uma resposta de chatbot.

---

## 4. Portões

| | nome | dispara se | leitura, escrita agora |
|---|---|---|---|
| **T1** | **o detector é seguro** | marca **< 1%** dos 1906 poemas pt | a construção não é coisa que Pessoa faça, logo marcá-la não é marcar o poeta. É o mesmo limiar do R1 da [5R](FASE-5R.md) |
| **T2** | **o detector discrimina** | o limite inferior do IC de Wilson a 95% da taxa nos **48 gerados** da 5Q fica **acima** da taxa do corpus | o defeito existe e é mecanicamente alcançável — **onde o da 5R não era** |
| **T3** | **a instrução é desobedecida** | T1 **e** T2 disparam para ao menos uma das três regras | **a decisão da fase** (§4.1) |
| **T4** | **inútil** | nenhuma regra passa T1 **e** T2 | a gramática não é a parte alcançável dos 67% da 5Q, e o passo 34 vai à **forma**. Nada entra em `src/`, e declara-se a limitação com número |

### 4.1 A decisão, pré-escrita — e com dois precedentes do próprio código

O `src/guard.py` já tem **os dois tratamentos**, cada um com a sua medição:

| precedente | medido | tratamento |
|---|---|---|
| `lingua_errada` | **0,16%** no corpus (3 de 1906) | **rejeita** e regenera |
| `suspeitas` do `lexico` | não medido contra o corpus | **reporta e não rejeita** («rejeitar custa ~28 s») |

Logo, por regra, para cada detector que dispare T2:

| taxa no corpus (T1) | tratamento |
|---|---|
| **≤ 0,2%** — nível do `lingua_errada` | entra como **rejeição**, em `verificar` |
| **> 0,2% e < 1%** | entra como **aviso** em `suspeitas`, sem falhar o veredicto |
| **≥ 1%** | não entra (T1 não disparou) |

**O limiar de 0,2% não é escolhido agora para caber num número que eu já vi:** é
a taxa que o `lingua_errada` tem publicada desde a Fase 3, e é o único nível a
que este projecto já autorizou uma rejeição.

### 4.2 O que esta fase não decide

- **Não decide a forma de verso**, que é a outra metade dos 67% da 5Q.
- **Não reabre a ortografia.** A 5R fechou-a com uma razão estrutural.
- **Não corrige as personas** (passo 24). Se T3 disparar, o que isso diz é que
  reforçar a instrução é a via **fraca** — e a 5I já mediu que mexer na
  instrução deu saldo líquido **negativo** uma vez.
- **Não compara modelos para decidir.** A troca está feita na
  [5S](FASE-5S-RELATORIO.md). A leitura qwen/llama vai no relatório como
  descritiva.

---

## 5. Ameaças

### 5.1 Pessoa inverte, e a inversão poética parece próclise

É a objecção que a pendência do `CONTROLO.md` levantou ao desenho da sessão
paralela: «"se recua a mão" é português correcto, e o corpus está cheio de
inversões». **É exactamente por isso que o T1 corre no corpus inteiro e é um
portão de segurança, não uma verificação.** Se Pessoa o faz, o T1 não dispara e o
detector morre — e isso é um resultado, não um acidente.

### 5.2 Eu construí os licenciadores e podia construí-los a meu favor

Estão fixados no §2.1 **antes de contar**, e vêm de gramática. Se a lista
estiver incompleta, o T1 falha por excesso de marcações no corpus — isto é, o
erro de desenho **aparece no portão de segurança** em vez de se esconder.

### 5.3 O nulo do corpus não é comparável ao alvo

Um poema de Pessoa e uma resposta de chatbot diferem em comprimento e em registo.
Por isso há o **segundo nulo**: os 24 poemas **reais** da 5Q, que passaram pelo
mesmo funil. Se os dois nulos discordarem, é o da 5Q que manda, e o relatório
di-lo.

### 5.4 Posso não encontrar nada, e quero encontrar

O T4 existe para esse caso e tem uma leitura **útil** escrita: fecha a gramática
como via mecânica e manda o passo 34 à forma. A fase não precisa de achar o
defeito para valer.

---

## 6. Lista de verificação

```
[ ] A1  detectores escritos como o §2 os declara, sem olhar para dados
[ ] A2  T1: taxa nos 1906 poemas pt, por regra
[ ] A3  T2: taxa nos 48 gerados e nos 24 reais da 5Q, com IC de Wilson
[ ] A4  descritivo: por modelo e por voz, nos 180 da 5M
[ ] B1  portões, e a decisao do §4.1 accionada
[ ] C1  se autorizado: entra em src/guard.py com o tratamento que o §4.1 manda
[ ] C2  testes, e o ./pessoa responde
[ ] C3  relatorio FASE-5T-RELATORIO.md
[ ] C4  CONTROLO.md
```

**Sessões paralelas:** verificado antes de abrir (nenhuma neste repositório).
`git add` com ficheiros nomeados.
