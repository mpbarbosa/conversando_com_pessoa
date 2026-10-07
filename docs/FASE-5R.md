# Fase 5R — Um detector de superfície derivado do corpus

**Passos 29 e 30.** Pré-registada em 2026-10-07. **É uma fase de produto:** o
entregável é código em `src/guard.py`, não um relatório.

---

## 1. O que a 5Q deixou, e o que não se pode fazer com isso

A [5Q §3](FASE-5Q-RELATORIO.md) mediu que **32 de 48 itens gerados (67%)** têm um
defeito de superfície, e que a guarda `brasileirismos()` — uma lista fixa de 14
palavras da Fase 0 — **não apanha nenhuma das onze formas** que eu observei.

**A correcção óbvia é a errada.** Escrever à mão uma lista com as onze formas que
vi é derivar o instrumento dos dados que o motivaram, que é a falha da
[5C](FASE-5C-RELATORIO.md) — a AUC que caiu de 0,869 in-sample para 0,544 retida.

E já há prova disso nesta fase, antes de começar: **três das razões que eu citei
na 5Q estão erradas**, e descobri-o ao consultar o corpus:

| forma | eu escrevi | o corpus diz |
|---|---|---|
| `rastro` | «brasileiro» | aparece **7 vezes** em Pessoa (`rasto` 9) |
| `vocês` | «brasileiro» | aparece **2 vezes** |
| `concreto` | «brasileiro» | aparece **1 vez** |

**O meu ouvido para o que é «brasileiro» erra uma em três.** A regra tem de vir do
corpus.

### 1.1 E o rótulo também estava errado

`objeto` e `elétrico` **não são brasileirismos**: são a grafia **europeia
correcta** desde o Acordo de 1990. O corpus é Pessoa pré-1990 e escreve
`objecto`, `eléctrico`. Logo o que o detector mede **não é «brasileiro contra
europeu»**, é **«fora da ortografia do corpus»** — e para um pastiche de Pessoa é
isso que interessa. O rótulo novo é esse.

---

## 2. As três classes, e porque são só três

Derivadas por **transformação mecânica** de cada forma do vocabulário do corpus
(19 681 formas, 219 151 ocorrências), e não por lista:

| | classe | transformação | exemplo |
|---|---|---|---|
| **A** | consoante muda reduzida | remover `c`/`p` antes de `t`/`ç` | `objecto` → `objeto` |
| **B** | acento omitido | remover os diacríticos | `silêncio` → `silencio` |
| **C** | acento substituído | trocar o diacrítico na mesma vogal | `ténue` → `tênue` |

**A regra de marcação**, para uma variante `v` derivada de uma forma canónica
`c`:

> marca-se `v` se **`freq(c) ≥ 2` e `freq(v) = 0`**, ou se
> **`freq(c) ≥ 20` e `freq(v) ≤ 1`**

A segunda cláusula existe por um caso medido: `silêncio` aparece **93 vezes** e
`silencio` **uma** — quase certamente um erro da transcrição do Arquivo Pessoa. A
regra de ausência absoluta deixava passar um defeito de 93 contra 1 por causa de
uma gralha na fonte.

**E as colisões excluem-se por construção:** `facto` → `fato`, mas `fato` existe
no corpus (9 ocorrências, é um fato de vestir), logo `fato` **não** se marca. São
5 colisões no total, duas delas de poemas em inglês (`act`/`at`, `wept`/`wet`).

### 2.1 O que fica de fora, e declarado

**As formas lexicais e sintácticas não são deriváveis** e **não entram**:
`rastro`, `vocês`, `embaixo`, `em uma`. Para umas o corpus diz que não são
defeito (§1); para as outras não há transformação mecânica que as gere. Entrar
com elas era voltar à lista à mão.

**E os acentos que o corpus não tem não se inventam:** `árduo` não aparece no
corpus **nem na forma acentuada**, logo `arduo` não é derivável e não se marca,
apesar de eu o ter visto. O detector apanha o que o corpus sabe, e nada mais.

---

## 3. A validação, e porque tem de ser retida

**Derivar do corpus e medir falsos positivos no corpus é circular:** a regra diz
«a variante está ausente do corpus», logo corrida sobre o corpus marca zero por
construção. É o mesmo erro que a [5C](FASE-5C-RELATORIO.md) cometeu com a AUC
in-sample.

**Logo a validação parte o corpus em dois:**

1. derivar a lista de variantes marcadas **só da metade A** (semente declarada);
2. correr o detector sobre o **texto da metade B**;
3. **cada marca em B é um falso positivo** — uma forma que a metade A não tinha e
   que Pessoa usa de facto.

E o **recall** mede-se nos **48 itens gerados da 5Q**, que não participam na
derivação de forma nenhuma.

---

## 4. Portões

| | nome | dispara se | leitura, escrita agora |
|---|---|---|---|
| **R1** | **os falsos positivos são aceitáveis** | derivado da metade A, a fracção de poemas da metade B marcados é **< 1%** | o detector não acusa Pessoa. O precedente é o `lingua_errada`, que rejeita **3 de 1906 (0,16%)** — ver o `CONTROLO.md` §4 |
| **R2** | **apanha o que havia para apanhar** | marca **≥50%** dos itens da 5Q cujo defeito citado é **ortográfico** (as classes A, B, C) | vale a pena entrar. Note-se que o alvo são os defeitos **ortográficos**, não os 67% — a gramática e o léxico não são deste detector |
| **R3** | **não há regressão** | os **237** testes passam com o detector dentro, e o `./pessoa` responde | é de produto: se quebrar o caminho de execução, não entra |
| **R4** | **inútil por cobertura** | o R2 falha **e** a derivação produz menos de 50 variantes | então a via mecânica não dá, e a prescrição é **declarar a limitação**, não cair na lista à mão |

### 4.1 O que entra no `src/`, se os portões passarem

1. **O detector**, como função nova em `src/guard.py`, com a lista derivada
   **gravada em dados** (`data/`) e não em código — para ser re-derivável quando
   o corpus mudar.
2. **A rejeição da truncatura** (passo 30): o campo `truncada` é **gravado e não
   usado**, e cinco itens cortados a meio da **palavra** chegaram à folha da 5Q.
3. **Testes** para as duas coisas.

**Se o R1 falhar, nada entra.** Um detector que acusa Pessoa é pior do que não
ter detector, porque rejeita e regenera respostas boas — e a Fase 0 já pagou esse
preço uma vez, com a guarda de idioma que «media registo, não língua»
(`CONTROLO.md` §4, correcção 12).

---

## 5. Ameaças

### 5.1 O corpus é a única autoridade, e tem gralhas

O `silencio` com uma ocorrência prova que a transcrição do Arquivo Pessoa tem
erros. A regra do §2 tolera um; não tolera dois. **Um defeito que apareça duas
vezes na fonte passa a ser «ortografia do corpus»** e deixa de ser marcado. Não
tenho como corrigir isso sem uma segunda fonte, e declaro-o.

### 5.2 O detector é específico de Pessoa e não de português

Marcar `objeto` é correcto **para este produto** e seria errado em qualquer outro
contexto, porque é a grafia oficial desde 2009. O nome da função tem de dizer
isso — não é `brasileirismos`, é ortografia **do corpus**.

### 5.3 Os poemas em inglês

O corpus tem 152 poemas em inglês e eles entram no vocabulário: as colisões
`act`/`at` e `wept`/`wet` vêm de lá. A derivação restringe-se a
`language == pt`, e isso fica medido no relatório (quantas variantes mudam).

### 5.4 A rejeição da truncatura custa tempo

Rejeitar e regenerar custa ~30 s por ocorrência. Na 5Q foram 5 em 48 (10%), e na
5H 1 em 60. **A um décimo das respostas, o custo esperado é ~3 s por pergunta** —
reporto-o no relatório e deixo o limite de tentativas como está.

---

## 6. Lista de verificação

```
[x] A1  tres classes derivadas: 2013 variantes (B 1284, C 649, A 80)
[x] B1  R1 NAO dispara: 2,18% na metade B. Mas 9 das 19 formas eram GRALHAS da
        transcricao (`ha` 2x contra `ha` acentuado 698x): o portao contava como
        erro casos em que o detector estava certo
[x] B2  R2 NAO dispara: 42% (5 de 12)
[x] C1  o detector NAO entra (os dois portoes falharam). Entrou o passo 30:
        a truncatura reprova o turno, em src/pipeline.py, com teste
[x] C2  R3 dispara: 238 testes (eram 237) e o ./pessoa responde
[x] C3  relatorio FASE-5R-RELATORIO.md
[x] C4  CONTROLO.md: passo 29 fechado com a limitacao, 30 feito, 31-33 novos
```

**A correccao posterior, declarada, nao salva os portoes:** aplicando a razao de
20x uniformemente (constante que o §2 ja tinha), os falsos positivos caem a
**0,73%** — passa — e o recall fica em **17%** — falha. **Nao ha limiar em que os
dois passem**, e a causa e o **tamanho do corpus**: `objecto` aparece 8 vezes.

**Sessões paralelas:** verificado antes de abrir. `git add` com ficheiros
nomeados.
