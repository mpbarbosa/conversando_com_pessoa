# Fase 5J — A âncora de forma é real?

**Passo 19 da tabela do [`CONTROLO.md`](CONTROLO.md) §6**, que a 5I deixou como «o
passo que importa mais». Pré-registada em 2026-10-05, antes de qualquer das
medições do §4 existir.

---

## 1. A pergunta, em uma linha

O critério **3b** dá a nota máxima a um poema cujo número de versos caia num
intervalo fixado **por voz** — Caeiro 10–20, Campos 15–30, Reis ≤12, Ortónimo
12–20 ([Fase 5](FASE-5.md) §5.2). **Esses intervalos vieram das personas.**
Ninguém verificou se os poemas reais lá cabem.

Se não cabem, o 3b tem o defeito que a [Fase 5E](FASE-5E-RELATORIO.md) encontrou
no 3a: um critério derivado da **idealização** do poeta, usado para julgar
imitações dele. E a consequência é pior do que uma régua torta, porque é
accionável ao contrário: o «défice de forma» que o **M3 da 5H** nomeou, e que a
5I tentou corrigir por instrução, pode ser o instrumento a **penalizar o modelo
mais parecido com o original**.

---

## 2. O que já está medido, antes de esta fase ser escrita

O projecto declara as medições feitas antes do protocolo em vez de as apresentar
como testes. Três coisas estavam feitas quando escrevi o §3, e **nenhuma delas
conta como portão**:

### 2.1 O número do Caeiro, e a definição que lhe faltava

A 5I §9.2 publicou **51 de 119 (43%)** poemas reais de Caeiro dentro de 10–20
versos. A definição de «verso» **não estava registada em script nenhum** — foi
calculada na sessão. Reproduzi-a sob cada definição candidata e identifiquei-a
por coincidência exacta de todas as estatísticas publicadas: eram **linhas não
vazias**.

O problema é que as amostras **geradas** de toda esta sequência têm o seu
`n_versos` gravado pelo `plagio.analisar`, que conta com
`MIN_PALAVRAS = 3` — **cai toda a linha com menos de três palavras**. O Caeiro
escreve linhas curtas. **A tabela do §9.2 comparava duas definições.**

A sessão que correu a 5I confirmou-o e corrigiu-o em `742b9f6`
([`fase-5i/contar_versos.py`](fase-5i/contar_versos.py)). A correcção **aperta** a
conclusão em vez de a afrouxar:

| dentro de 10–20 versos | linhas não vazias | **`_versos` (≥3 palavras)** |
|---|---|---|
| **Caeiro real** (119) | 51 — 43% | **46 — 39%** |
| **llama3.1** (5H) | 9/30 | **9/30 — 30%** |
| **llama3.1** (5I braço A) | 12/30 | **12/30 — 40%** |
| **qwen2.5** (5H) | 25/30 | **25/30 — 83%** |

As geradas dão praticamente o mesmo nas duas definições — raramente têm linhas
de menos de três palavras —, logo **o único número que se move é o dos poemas
reais**, e move-se de 43% para 39%, para junto do llama.

> **A lição de instrumentação, e é a terceira vez nesta sequência.** Dois lados
> de uma comparação contados por definições diferentes dão um número que não
> mede nada. Aqui a direcção do enviesamento era favorável e a correcção
> apertou o resultado; não havia como saber isso antes de a medir. **Toda a
> comparação com `n_versos` gravado por um harness desta sequência tem de contar
> o outro lado com `plagio._versos`.**

### 2.2 Um segundo defeito, no script da correcção, sem efeito nas fracções

O `contar_versos.py` resolve cada poema por `poemas.setdefault(c.poem_id, c)` e
conta `p.text` — o texto do **chunk**, não o corpo do poema. Para os poemas
partidos em vários chunks isso conta **só o primeiro**.

Verifiquei o efeito: dos 119 poemas de Caeiro, **5 são multi-chunk**, e os cinco
já estão **acima de 20 versos no primeiro chunk**. Nenhum muda de categoria.

| poema | chunks | 1.º chunk | inteiro |
|---|---|---|---|
| `poem_1487` | 5 | 34 | **161** |
| `poem_1482` | 2 | 41 | 73 |
| `poem_1456` | 2 | 48 | 65 |
| `poem_3214` | 2 | 40 | 52 |
| `poem_344` | 2 | 34 | 40 |

**As fracções e as medianas publicadas estão certas.** O que está errado é só o
`max` — **161 e não 48**. Esta fase conta sempre sobre `parse_poem(...).body`, o
poema inteiro, e não sobre o chunk.

### 2.3 O que isto implica para o desenho

A célula do **Caeiro já foi vista**. Não a posso usar como teste: escolher a
análise depois de conhecer o número é o que o §7.1 declara como a ameaça
principal desta fase. Logo **o peso probatório do §3 está nas outras três vozes,
que não medi, e na validação retida do J4.**

---

## 3. Hipóteses e portões, escritos antes de existir qualquer das medições

| | nome | dispara se | leitura, escrita agora |
|---|---|---|---|
| **J1** | **o defeito é das quatro vozes** | em **≥3 das 4** vozes, o limite **superior** do IC95% de Wilson da fracção dentro do intervalo fica **abaixo de 0,50** | os intervalos do 3b são uma propriedade das **personas** e não do corpus. É um resultado sobre o **método** — dois critérios (3a e 3b) com a mesma origem e a mesma falha —, e não um defeito local do Caeiro |
| **J2** | **o instrumento penaliza a fidelidade** | nos braços emparelhados da 5H: conformidade(llama) **<** conformidade(qwen) **e** distância KS ao Caeiro real **D(llama) < D(qwen)** | a conformidade ao intervalo **ordena os modelos ao contrário** da fidelidade distribucional. O «défice de forma» do M3 é o instrumento, não o modelo |
| **J3** | **a elegibilidade não explica o J1** | o J1 mantém-se depois do filtro de fragmentos **e** os poemas excluídos **não** são predominantemente os curtos | a cauda de baixo é do poeta e não da transcrição |
| **J4** | **há um intervalo que se valida fora da amostra** | o intervalo derivado em metade cobre **≥0,70** da metade **retida** | autoriza propor a recalibração do 3b. Falhar **não** autoriza manter o intervalo antigo — são perguntas diferentes (ver §3.2) |
| **J5** | **inconclusivo por potência** | no J2, o IC95% de `D(qwen) − D(llama)` **inclui 0** | o J2 lê-se como «**não se mostrou** que a distância difere», e não como «mostrou-se que é igual». Precedente: [5I §6](FASE-5I.md) |

### 3.1 Porque é que o limiar do J1 é 0,50

O 3b dá **2** por estar dentro do intervalo e desce a **1** por estar «fora do
intervalo». Um intervalo que não contenha **metade** da obra do próprio autor não
pode servir de critério **positivo** — reprova a maioria do original. É o mesmo
argumento que a [5E](FASE-5E-RELATORIO.md) fez contra a âncora de 3a, que dava a
nota máxima a 15% do Caeiro autêntico.

O portão usa o **limite superior** do IC de Wilson, e não a estimativa pontual,
para que uma fracção abaixo de 0,50 por ruído de amostragem não conte.

### 3.2 O que o J4 não é

Falhar o J4 significa «não encontrei um intervalo estável», **não** «o intervalo
de 10–20 estava certo». Se o J1 disparar e o J4 falhar, a prescrição é **retirar
a contagem de versos do 3b**, não conservá-la por falta de alternativa. Está
escrito antes de medir porque é precisamente onde a tentação de salvar o
instrumento apareceria.

---

## 4. Desenho

### 4.1 População

Poemas **autênticos** da voz, **indexados** (pós-deduplicação: 2062 dos 2083),
lidos com `parse_poem` e contados sobre `.body` — o poema **inteiro**.

| voz | intervalo do 3b | n (todas as línguas) |
|---|---|---|
| Caeiro | 10–20 | 119 |
| Campos | 15–30 | 319 |
| Reis | ≤12 | 246 |
| Ortónimo | 12–20 | 1290 |

**Primário: só `language == pt`.** A âncora julga verso português; os 152 poemas
em inglês são outra tradição métrica e quase todos do ortónimo e do Search.
**Sensibilidade: todas as línguas.** Declarado agora porque é uma escolha que
mexe sobretudo numa célula.

### 4.2 Definição de verso

**Primária: `plagio._versos`** (`MIN_PALAVRAS = 3`), por ser a que **todos** os
harnesses desta sequência gravaram para as amostras geradas, e o §2.1 mostra o
preço de misturar definições.
**Sensibilidade: linhas não vazias.** As duas vão no relatório.

### 4.3 Elegibilidade — o filtro de fragmentos, e porque não pode ser por comprimento

O corpus tem transcrições incompletas. Ignorá-las sobrestima a cauda de baixo;
filtrá-las **por comprimento** pressupõe a conclusão. **Nenhum critério de
elegibilidade desta fase olha para o número de versos.**

**Excluído** — a transcrição marca texto **ausente**:
- parênteses ou rectos com só pontos: `[...]`, `(...)`, `[…]`, `(…)`
- linha composta só por três ou mais pontos

**Não excluído** — marca incerteza sobre **uma palavra**, não ausência de texto:
- `[?]` (leitura duvidosa) · `[palavra]` (reconstituição editorial) · `…` no meio
  do verso (reticência **autoral**, e Pessoa usa-a muito)

**Verificação de ortogonalidade, pré-registada:** reportar a distribuição de
versos dos **excluídos** contra os **retidos**. Se os excluídos não forem
sistematicamente mais curtos, os fragmentos não são o que produz a cauda de
baixo — é o portão J3.

> **Limitação declarada.** Um rascunho curto sem marca editorial nenhuma é
> indistinguível de um poema curto completo sem trabalho de crítica textual. O
> filtro apanha **o que a transcrição marca**, e nada mais. Não há como fechar
> isto com os dados que há, e qualquer regra por comprimento que o fechasse
> estaria a decidir a pergunta.

### 4.4 O J2: a inversão, nos braços emparelhados da 5H

A [5H](FASE-5H-RELATORIO.md) correu **qwen (Q)** e **llama (L)**, 30 amostras
cada, **nas mesmas 10 perguntas, mesmo harness, mesmas opções**. É a única
comparação de modelos desta sequência com as duas condições controladas, e por
isso o J2 corre nela e **não** mistura o qwen da 5H com o llama da 5I.

- **conformidade** = fracção das 30 dentro do intervalo de 10–20.
- **fidelidade** = estatística **KS de duas amostras** entre a distribuição de
  versos do braço e a do Caeiro real elegível. Menor D = mais parecido.
- **IC**: bootstrap de 10 000 reamostragens sobre `D(Q) − D(L)`.

**Truncaturas.** Uma amostra truncada tem a contagem **censurada** — foi cortada,
não terminou. Comparar contagens censuradas com poemas completos enviesa a
distribuição para baixo. **Primário: excluir as truncadas. Sensibilidade:
incluí-las.** A 5I identificou truncatura por **juízo dos avaliadores** (as
mesmas sete, cegos e em separado) e não há campo gravado; para a 5H aplico a
regra declarada **«a última linha não termina em `.`, `!`, `?`, `:`, `;` nem
`…`»** e reporto a contagem que ela dá, com os textos, para ser verificável.

> **Corrigido a meio da fase, e este parágrafo está errado.** **Há** campo
> gravado: `truncada`, de `done_reason == "length"`
> ([`ollama.py:107`](../src/generation/ollama.py)). A regra heurística que
> declarei aqui acertou **zero** — marcou 4 amostras, nenhuma truncada, e deixou
> passar a única que era —, porque em verso livre acabar sem pontuação é
> **estilo**. O primário passou a ser o campo gravado e a heurística ficou como
> contra-verificação. Ver o §5 do [relatório](FASE-5J-RELATORIO.md).

Com 30 por braço, o J2 é uma **demonstração de existência** sobre **dois**
modelos, não um teste sobre uma população de modelos. Estabelece que o instrumento
**pode** inverter a ordenação, não com que frequência inverte. Escrito agora para
não ser lido como mais do que é.

### 4.5 O J4: derivar numa metade, validar na outra

A [lição da 5C](FASE-5C-RELATORIO.md) é que **qualquer número de discriminação
medido nos mesmos dados que derivaram o instrumento não é um número** — a AUC do
FAS caiu de 0,869 para 0,544 ao passar a dados retidos.

1. Partir os poemas elegíveis de Caeiro em duas metades, **semente `20261005`**,
   `random.Random(semente).shuffle`.
2. **Derivar** na primeira: intervalo central `[p10, p90]`, arredondado para
   fora.
3. **Validar** na segunda, **uma só vez**: fracção dentro. Portão **≥0,70**.

O alvo de cobertura é ~0,80 por construção; 0,70 dá folga ao ruído de
amostragem. O precedente é a [5F](FASE-5F-RELATORIO.md), cuja âncora de 3a
recalibrada premeia **16 de 24 (67%)** poemas autênticos retidos.

Nota: o 3b do **Caeiro** é o que esta fase tem potência para recalibrar. Para as
outras vozes o J1 diz se o intervalo está errado; propor substitutos para as
quatro fica para o passo que o relatório nomear.

### 4.6 Estatística

Sem `scipy`, como em toda a sequência desde a [Fase 3B](FASE-3B.md): Wilson,
KS de duas amostras e bootstrap implementados em
[`fase-5j/analisar.py`](fase-5j/) com `numpy`, e os números crus em JSON.

---

## 5. O que esta fase não mede

- **Não gera amostras.** O J1, o J3 e o J4 são deterministas sobre o corpus; o J2
  reutiliza as amostras da 5H. **Não ocupa o slot do Ollama** — relevante porque
  há outra sessão viva neste repositório.
- **Não repontua 3b à mão.** A contagem de versos é a parte **mecânica** do 3b; a
  âncora tem também verso livre, rima, imagem e ornamento, que esta fase não
  toca.
- **Não decide a troca de modelo.** O M3 da 5H fica condicionado até o passo 16
  medir as outras três vozes. Esta fase diz se o **critério** que condicionou o
  M3 é válido, o que é outra pergunta.
- **Não mede o passo 20** (reforço + `num_predict` juntos). Se o J1 e o J2
  dispararem, o passo 20 fica **sem motivo** — corrigiria a forma na direcção de
  uma régua errada —, e o relatório tem de o dizer.

---

## 6. Ameaças

### 6.1 A principal: eu já vi o número do Caeiro

Escolhi esta análise **depois** de conhecer os 39%. Não há como desfazer isso.
O que há é limitar-lhe o alcance, e está no §2.3: a célula do Caeiro no J1 é
**descritiva e não probatória**; o peso está nas **três vozes que não medi** e na
**metade retida** do J4, que só se lê uma vez.

### 6.2 Cegueira não se aplica, e isso não é uma vantagem

Não há avaliador humano: tudo no §4 é determinista e re-executável. Logo as
ameaças de avaliador único e de erro correlacionado **desaparecem** — e em troca
**desaparece também a defesa que a cegueira dá contra escolhas minhas**. Os graus
de liberdade desta fase estão todos nas **definições** (verso, elegibilidade,
truncatura, língua), e é por isso que estão fixadas por escrito aqui, com
sensibilidades declaradas, em vez de serem decididas ao ver os resultados.

### 6.3 O corpus não é uma amostra aleatória do poeta

Os 119 poemas de Caeiro são o que o Arquivo Pessoa transcreveu, com as escolhas
editoriais que isso traz (ver [`data/README.md`](../data/README.md): a recolha
não tem script e os termos não foram verificados). «O Caeiro real» desta fase
significa **«o Caeiro deste corpus»**, e é o mesmo corpus que o RAG serve, logo é
a população certa para julgar **este** sistema — mas não é uma afirmação sobre a
obra.

### 6.4 O intervalo pode estar errado e o 3b continuar a discriminar

Um critério pode ser descritivamente falso e ainda assim separar gerado de real,
se os modelos errarem **mais** do que o poeta. O J1 mede se o intervalo descreve
o poeta; **não** mede o valor discriminativo do 3b. Se o J1 disparar e o J2 não,
a leitura é «a régua está torta mas ainda separa», e a prescrição passa a ser
medir o 3b recalibrado contra o antigo em dados retidos — não está nesta fase.

---

## 7. Lista de verificação

```
[x] A1  elegibilidade e contagem: fase-5j/contar.py -> 01-contagem.json
[x] A2  verificacao de ortogonalidade (excluidos vs retidos) -> J3, e ao contrario
[x] B1  J1 nas quatro vozes, Wilson 95%, pt e todas as linguas  -> DISPARA (3/4)
[x] B2  J2 nos bracos Q/L da 5H: conformidade, KS, bootstrap    -> NAO dispara
[x] B3  J3 com e sem o filtro de fragmentos                     -> DISPARA
[x] B4  J4 derivar em metade (semente 20261005), validar UMA vez -> DISPARA, e a
        consequencia mata-o: 100% aos dois modelos contra 86% do poeta
[x] C1  portoes -> 03-resultados.json
[x] C2  relatorio FASE-5J-RELATORIO.md
[x] C3  CONTROLO.md: estado da fase e passo 19 fechado
```

**Duas correccoes ao proprio protocolo, feitas a meio e registadas no §5 do
relatorio:** o §4.4 dizia que a truncatura nao estava gravada (estava, e a
heuristica que declarei acertou zero), e a sensibilidade do §4.2 mostrou que o
J1 **nao** aguenta as quatro combinacoes de lingua x definicao — o nucleo solido
e Campos e ortonimo, nao o Caeiro.

**Combinação de ficheiros com a sessão paralela** (`Phase 5B`, que correu 5B–5I):
`docs/FASE-5J*` e `docs/fase-5j/` são desta sessão, e o `CONTROLO.md` também —
combinado por escrito antes de abrir a fase, depois de a memória do projecto ter
registado uma duplicação de fase em 2026-10-03.
