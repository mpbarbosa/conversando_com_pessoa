# Fase 5R — relatório: o detector não passa, e a razão é o tamanho do corpus

**Protocolo:** [`FASE-5R.md`](FASE-5R.md), pré-registado em `181e202`.
**Dados:** [`fase-5r/01-derivacao.json`](fase-5r/)

---

## 0. Os portões

| | | |
|---|---|---|
| **R1** falsos positivos < 1% | ❌ **não dispara** | **2,18%** na metade retida |
| **R2** recall ≥ 50% do alvo ortográfico | ❌ **não dispara** | **42%** (5 de 12) |
| **R3** sem regressão | ✅ dispara | **238** testes, e o `./pessoa` responde |
| **R4** inútil por cobertura | ❌ não dispara | a derivação dá 2013 variantes, não menos de 50 |

**Pelo §4, o detector não entra no `src/`.** Entrou o **passo 30** — a rejeição da
truncatura —, que não tinha portão e é um defeito inequívoco (§3).

---

## 1. Porque é que o R1 falhou, e não é o que parece

A derivação da metade A marcou **21 poemas de 963** na metade B (2,18%). Mas ao
olhar para **quais** formas, a leitura inverte-se: a razão entre a frequência da
forma canónica e da variante, no corpus inteiro, separa-as em dois grupos.

| forma marcada | canónica | f(canónica) | f(variante) | razão | |
|---|---|---|---|---|---|
| `ha` | `há` | 698 | 2 | **349×** | gralha da fonte |
| `es` | `és` | 134 | 1 | **134×** | gralha da fonte |
| `silencio` | `silêncio` | 93 | 1 | **93×** | gralha da fonte |
| `musica` | `música` | 62 | 1 | 62× | gralha da fonte |
| `magoa` | `mágoa` | 62 | 1 | 62× | gralha da fonte |
| `forca` | `força` | 48 | 1 | 48× | gralha da fonte |
| … | | | | | |
| `fabrica` | `fábrica` | 4 | 1 | 4× | **homografia real** |
| `andamos` | `andámos` | 3 | 1 | 3× | **homografia real** |
| **`avô`** | **`avó`** | **4** | **2** | **2×** | **homografia real** |
| `helahoho` | `helahôhô` | 2 | 11 | 0,2× | **homografia real** |

**Nove das 19 formas marcadas são gralhas da transcrição do Arquivo Pessoa** —
`há` escrito 698 vezes e `ha` duas. Marcá-las é **correcto**: são erros
ortográficos, mesmo dentro do corpus.

**E sete são homografia genuína.** O caso que decide é `avô`/`avó`: avô e avó são
**palavras diferentes** que diferem só no diacrítico, e a classe C gera uma da
outra. Marcar `avô` porque o corpus tem `avó` é um falso positivo verdadeiro.

**Logo o meu R1 contava as duas coisas como erro**, e a métrica era grossa de
mais. A razão canónica:variante é o que as separa.

---

## 2. A correcção, declarada como posterior — e não salva

O protocolo tinha já a constante **20×** (na cláusula tolerante do §2, posta por
causa do `silencio`). Apliquei-a **uniformemente** em vez de só a esse ramo, e
medi o compromisso:

| razão mínima | variantes | **falsos positivos em B** | **recall no alvo** | reais da 5Q marcados |
|---|---|---|---|---|
| 5× | 807 | 2,18% | 33% | 1 de 24 |
| 10× | 397 | 1,45% | 17% | 0 |
| **20×** | **212** | **0,73%** ✅ | **17%** ❌ | **0** |
| 30× | 152 | 0,52% | 17% | 0 |
| 50× | 91 | 0,31% | 17% | 0 |

**Não há limiar em que os dois portões passem.** A 20× os falsos positivos ficam
em 0,73% — abaixo do 1% e na ordem do `lingua_errada` (0,16%) — e o recall cai a
17%.

### 2.1 E a razão é estrutural: o corpus é pequeno

As formas que eu precisava de apanhar têm **canónicas raras**:

| defeito observado | canónica | ocorrências no corpus |
|---|---|---|
| `objeto` | `objecto` | **8** |
| `tênue` | `ténue` | **7** |
| `elétricas` | `eléctricas` | **2** |

**Exigir uma razão de 20× a uma canónica que aparece 8 vezes é impossível.** E
baixar a razão para as apanhar traz de volta os falsos positivos, porque as
homografias reais (`avô`/`avó`, 2×/4×) vivem precisamente nessa zona de
frequência.

**O limite não é do método; é de 2083 poemas.** Com um léxico externo de
português europeu pré-1990 o problema desapareceria — e isso é uma dependência
nova, de outra natureza.

### 2.2 O que o detector *teria* apanhado, para o registo

A 20× marca 3 dos 48 itens gerados da 5Q e **zero dos 24 poemas reais**:
`silencio` (qwen, ortónimo), `veem` e `ve` (llama). A 5×, marca 5 e acerta
também `objeto`, `tênue` e `elétricas`/`elétricos` — ao preço de 2,18% de falsos
positivos e de um poema real marcado.

**Precisão perfeita nos reais da 5Q, cobertura de 6%.** Não é nada, e não é o que
o R2 pedia.

---

## 3. O que entrou: o passo 30

`Turno.aprovado` era `veredicto limpo e sem plágio` e **não olhava para a
truncatura**, apesar de o campo `resposta.truncada` ser gravado desde a Fase 1 a
partir de `done_reason == "length"`. Consequência medida: na
[5Q](FASE-5Q-RELATORIO.md), **cinco de 48** amostras chegaram à folha de
julgamento cortadas **a meio da palavra** — «não alcan», «sua pass», «que
ninguém l».

A correcção é de duas linhas em [`src/pipeline.py`](../src/pipeline.py):

1. `aprovado` passa a exigir `not self.resposta.truncada` — e é `aprovado` que o
   `responder_em_fluxo`, o caminho do CLI, usa para repetir;
2. a condição de repetição do `responder` passa a `not a.plagiou and not
   r.truncada`, para os dois caminhos concordarem.

Mais um teste. **238 testes passam** (eram 237) e o `./pessoa` responde.

**O custo**: rejeitar e regenerar custa ~30 s. Na 5Q foram 5 em 48 (10%) e na 5H
1 em 60 (1,7%); a ~10% das respostas, o custo esperado é **~3 s por pergunta**. O
limite de tentativas fica como está (2), logo no pior caso o utilizador recebe
uma resposta truncada em vez de esperar indefinidamente.

---

## 4. Correcções a afirmações minhas da 5Q

Ao consultar o corpus **antes** de começar, três razões que citei na
[5Q](FASE-5Q-RELATORIO.md) revelaram-se erradas:

| forma | eu escrevi | o corpus |
|---|---|---|
| `rastro` (Q44) | «brasileiro» | **7×** em Pessoa (`rasto` 9×) |
| `vocês` (Q24) | «brasileiro» | **2×** |
| `concreto` (Q48) | «brasileiro» | **1×** |

**O meu ouvido para «o que é brasileiro» erra uma em três.** Os juízos da 5Q não
mudam — identifiquei esses três itens como gerados por **outras** razões no mesmo
item (truncatura em Q24 e Q62, imagem decorativa em Q48) —, mas as razões
escritas estão corrigidas aqui.

E o rótulo, que o §1.1 do protocolo já corrigia: **`objeto` e `elétrico` não são
brasileirismos**, são a grafia europeia correcta desde 1990. O que se mede é
distância à ortografia **do corpus**.

---

## 5. O que isto autoriza, e o que não

**Não autoriza o detector.** Os dois portões falharam e a correcção posterior não
os salva. Nada foi escrito em `data/`.

**Não autoriza a lista à mão**, que era a tentação e que o §1 do protocolo
antecipou. As onze formas que eu vi incluem três que estão em Pessoa; uma lista
feita delas teria 27% de erro embutido.

**Autoriza declarar a limitação com um número:** a via mecânica derivada de 2083
poemas dá **ou** um detector seguro com 6% de cobertura, **ou** um detector com
33% de cobertura e 2,18% de falsos positivos. Nenhum dos dois serve, e a causa é
o tamanho do corpus — não o método.

**E deixa uma observação do produto a correr.** A guarda lexical de
[`src/lexico.py`](../src/lexico.py) **já reporta** palavras desconhecidas: na
corrida de verificação desta fase apanhou «afite». **Reporta e não rejeita** — é o
mesmo padrão da truncatura antes do passo 30. Mas aqui rejeitar é arriscado:
Pessoa inventa palavras, e medir esse falso positivo é uma fase própria.

### O que fica na mesa

1. **Um léxico externo de português europeu pré-1990** — a única coisa que
   resolve o §2.1. É uma dependência nova e tem de ser avaliada como tal
   (tamanho, licença, cobertura de ortografia antiga).
2. **Rejeitar as palavras desconhecidas da guarda lexical**, com a medição de
   falsos positivos contra o corpus que a truncatura não precisou de ter.
3. **O detector a 20×, como aviso e não como rejeição.** A 0,73% de falsos
   positivos e zero reais marcados, é seguro o suficiente para **mostrar** ao
   utilizador — o mesmo tratamento que a guarda lexical já tem. Não foi feito
   porque o protocolo não o pré-registou, e passa a passo próprio.

> **A lição, e é a oitava.** Esta é sobre **o que uma validação retida mede de
> facto**. Eu parti o corpus em dois para evitar a circularidade da 5C, e a métrica
> que construí contava como erro nove casos em que o detector estava **certo** —
> gralhas da fonte. A validação retida protegeu-me da circularidade e não me
> protegeu de medir a coisa errada, que é exactamente o que a
> [5M §4](FASE-5M-RELATORIO.md) já tinha dito sobre portões.
>
> **E a conclusão que sobra é a mais útil:** o obstáculo não era o desenho, era
> ter 2083 poemas. Isso só se vê depois de ter construído o detector e medido os
> dois lados do compromisso — e é um resultado que fecha uma via em vez de a
> deixar em aberto.
