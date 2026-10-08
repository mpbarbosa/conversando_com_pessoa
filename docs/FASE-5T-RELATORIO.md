# Fase 5T — relatório: duas das três regras de língua não descrevem o poeta

**Protocolo:** [`FASE-5T.md`](FASE-5T.md), pré-registado em `a2db2ee`.
**Dados:** [`fase-5t/01-deteccao.json`](fase-5t/) · [`02-correccao.json`](fase-5t/)
· [`03-atraccao.json`](fase-5t/)
**Produto:** `Veredicto.gramatica` e `tratamento_indevido` em
[`src/guard.py`](../src/guard.py).

Nenhuma geração nova. Corpus (1926 poemas em pt), 48 gerados + 24 reais da
[5Q](FASE-5Q-RELATORIO.md), 180 da [5M](FASE-5M-RELATORIO.md).

---

## 0. Os portões

| | | |
|---|---|---|
| **T1** `R-PRO` seguro | ❌ **não dispara** | **22,6%** à 1.ª régua, **2,65%** à régua corrigida — contra um limiar de 1% |
| **T1** `R-GER` seguro | ❌ **não dispara** | **5,24%** (101 de 1926) |
| **T1** `R-VOC` seguro | ✅ dispara | **0,21%** (4 de 1926) |
| **T2** `R-VOC` discrimina | ✅ dispara | 1 de 48, limite inferior de Wilson acima de 0,0021 |
| **T3** a instrução é desobedecida | ⚠️ **dispara só pelo `R-VOC`** | e **com uma ocorrência**, o que é um defeito do portão (§4) |
| **T4** inútil | ❌ não dispara | mas é o §5 que diz o que isto decide de facto |

**Pela decisão pré-escrita no §4.1:** o `R-VOC` entra como **aviso** (0,21% fica
acima dos 0,2% da rejeição, por uma centésima); os outros dois não entram.

---

## 1. A próclise, em três passagens — e as três estão aqui

Esta é a parte da fase que vale, e vale por ter corrido mal duas vezes.

### 1.1 Primeira passagem: o detector marca 435 poemas de Pessoa

A regra do §2.1, tal como foi pré-registada: pronome átono (`me`, `te`, `lhe`,
`lhes`) cujo *token* **imediatamente anterior** não licencia próclise.

| | corpus | gerados 5Q | reais 5Q |
|---|---|---|---|
| `R-PRO` | **435/1926 = 22,6%** | 4/48 | 6/24 |

**O T1 não dispara, e com folga de vinte vezes.** O §5.1 do protocolo tinha
antecipado isto como resultado possível («se Pessoa o faz, o T1 não dispara e o
detector morre»). Mas ao olhar para **o que** foi marcado, não era Pessoa a
procliticizar: era o meu detector a estar errado.

| linha do corpus | marcou | mas |
|---|---|---|
| «Por tu **me escolheres** para te ter e **te amar**» | `tu [me] escolheres`, `e [te] amar` | é **infinitivo** (e infinitivo pessoal): a próclise é obrigatória |
| «Só tu, Senhor, **me dás** viver.» | `, [me] dás` | o atractor «Só» está **três *tokens* atrás**, com um vocativo pelo meio |
| «Se eu interrogasse e **me espantasse**» | `e [me] espantasse` | o «Se» governa a oração **coordenada** também |

As três têm uma causa só: **a próclise é licenciada por atracção, e o atractor
não tem de estar colado ao pronome.**

> **E o §5.2 tinha escrito que era assim que isto apareceria:** «se a lista
> estiver incompleta, o T1 falha por excesso de marcações no corpus — isto é, o
> erro de desenho **aparece no portão de segurança** em vez de se esconder». Foi
> exactamente o que aconteceu, e é a única razão por que a fase não publicou um
> detector errado.

### 1.2 Segunda passagem: a correcção que não corrigiu, e a leitura que eu quase publiquei

Duas emendas, **ambas declaradas posteriores aos dados**
([`corrigir.py`](fase-5t/corrigir.py)):

1. **em verso, o fim da linha não é fronteira de oração** — a oração corre
   através da quebra, e 88 das 635 ocorrências tinham a quebra como único
   motivo;
2. **a taxa por item depende do comprimento, logo não é a taxa** — a medida é a
   proporção da construção, `próclise / (próclise + ênclise)`, que é também o
   que a persona afirma ao dizer «colocação enclítica, **sempre**».

A primeira **não mudou nada**: 435 poemas antes, **435** depois (635 ocorrências
para 630). Os 88 casos estavam em poemas já marcados por outra ocorrência.

A segunda deu isto:

| conjunto | próclise | ênclise | proporção | IC95 por item |
|---|---|---|---|---|
| corpus pt | 630 | 1349 | **0,318** | [0,283, 0,353] |
| reais da 5Q | 8 | 9 | **0,471** | [0,231, 0,700] |
| **gerados da 5Q** | 5 | 30 | **0,143** | [0,031, 0,250] |
| gerados da 5M | 36 | 128 | **0,220** | [0,157, 0,286] |

**E aqui eu quase publiquei a conclusão errada.** A leitura que isto convida é
forte e contra-intuitiva: *Pessoa procliticiza 32% das vezes, os modelos 14%; a
instrução está a ser obedecida e obedecer-lhe afasta o texto do poeta.* Os
reais da 5Q, que passaram pelo mesmo funil, até concordavam com o corpus.

**É um artefacto.** As classes que o detector marcava a mais — infinitivos,
atracção à distância, coordenação — são **mais frequentes em Pessoa** do que nas
respostas dos modelos, porque ele escreve orações longas com «se», «porque»,
«só» e infinitivos encadeados. O numerador inflacionado era o dele.

### 1.3 Terceira passagem: a próclise por atracção, e o resultado

Uma regra de gramática, e sem constante nenhuma ajustada aos dados
([`atraccao.py`](fase-5t/atraccao.py)): licencia-se se **houver atractor em
qualquer ponto anterior da mesma oração** (desde a última pontuação **forte** —
a vírgula não fecha oração) **ou** se o *token* seguinte for infinitivo.

| conjunto | itens marcados | proporção | IC95 por item |
|---|---|---|---|
| corpus pt | **51/1926 = 2,65%** | **0,045** | [0,031, 0,060] |
| reais da 5Q | 2/24 | 0,182 | [0,000, 0,400] |
| gerados da 5Q | 2/48 = 4,2% | **0,062** | [0,000, 0,154] |
| gerados da 5M | 7/180 = 3,9% | **0,052** | [0,020, 0,087] |

**Dois resultados, e fecham a via duas vezes:**

1. **O T1 continua a não disparar** — 2,65% contra 1%. Mesmo à régua correcta, o
   detector marca 51 poemas autênticos.
2. **Não há sinal para detectar.** À mesma régua, o poeta está em **0,045** e os
   modelos em **0,052** e **0,062**. Os intervalos sobrepõem-se por completo.
   **Os modelos procliticizam como Pessoa procliticiza.**

O ramo do `se`, reportado à parte como o §2.1 mandava, confirma porque foi
excluído: 359 poemas no corpus. É conjunção na maioria dos casos e não serve.

---

## 2. O gerúndio: a regra proíbe o que o poeta faz

`R-GER` marca a perífrase progressiva (`estar`/`andar`/`ir`/`ficar` + `-ndo`),
não o gerúndio solto. **101 poemas de 1926 (5,24%)**, e as linhas são
inequívocas:

```
poem_1042  «Quando o revejo em mim, onde é que o estou vendo?»
poem_1104  «Vou escrevendo os meus versos sem querer,»
poem_1130  «O «homem» vai andando com as suas ideias, falso e estrangeiro,»
poem_1012  «São os sentimentos que nascem de estar olhando para a madrugada,»
```

Nos gerados: 2 de 48. **O poeta usa a construção mais do que os modelos.**

**E a persona proíbe-a:** «Não uses gerúndio onde o português europeu usa «a» +
infinitivo» ([`src/voices.py`](../src/voices.py)). A instrução está certa como
norma de 2026 e **errada como descrição de Pessoa**, que escreve «Vou
escrevendo».

> Isto é **a mesma classe de defeito** que a [5L](FASE-5L.md) encontrou nos
> quatro intervalos de versos: uma instrução que não descreve o poeta, a correr
> em produção. A 5L removeu-os do **instrumento**; o [passo 24](CONTROLO.md)
> trata de os remover da **instrução**. Esta fase acrescenta-lhe um item, com
> número.

---

## 3. «Você»: a única que resiste, e é residual

| | corpus | gerados (5Q + 5M, n=228) |
|---|---|---|
| `você`/`vocês` | **4/1926 = 0,21%** | **2** |

Os quatro no corpus são deliberados — «O quê — você não chega? Então você
desaparece?» (`poem_1225`), «E você devia revelar-se menos.» (`poem_3326`).

**A regra da persona está certa**, e é a única das três que está. Mas duas
ocorrências em 228 textos **não são parte dos 67% da 5Q**.

### 3.1 O que entrou em `src/`

Pela decisão pré-escrita, e nada além dela:

```python
def tratamento_indevido(texto: str) -> tuple[str, ...]:
    """«você» onde a persona manda «tu». **Reporta e não rejeita.**"""
```

Canal próprio — `Veredicto.gramatica` — e **não** `suspeitas`, porque ali os
elementos são palavras com `.palavra` e aqui são construções. O CLI mostra-o a
par das palavras desconhecidas. **243 testes passam** (eram 239), e um deles fixa
a **ausência** do detector de colocação pronominal, para que ninguém o reponha
sem medir outra vez.

**E corrigi um comentário que prometia o que não existia.** O `verificar` dizia
«Brasileirismos e **colocação pronominal** só fazem sentido em português» — e
verificação de colocação pronominal não havia nenhuma, nem antes nem agora.

Verificado a correr, no Campos: «As coisas que vejo **fazem-me** pensar», «um
sorriso a **sussurrar-me** pela palma da mão». Ênclise correcta, e a próclise que
aparece é licenciada («que **me** perde», «que **se** rompe»).

---

## 4. Correcções a afirmações minhas, dentro desta fase

| | eu | de facto |
|---|---|---|
| o detector do §2.1 | mediria próclise brasileira | marcava infinitivos e atracção à distância — **22,6% dos poemas do poeta** |
| a 2.ª passagem | «os modelos são mais enclíticos que Pessoa» (0,143 contra 0,318) | **artefacto** do numerador inflacionado; à régua correcta, 0,062 contra 0,045, indistinguíveis |
| a correcção da quebra de linha | salvaria o portão | **não mudou nada**: 435 poemas antes e depois |
| o `T2`, como o pré-registei | mediria discriminação | **dispara com uma ocorrência em 48.** O limite inferior de Wilson de 1/48 é 0,0037, logo bate qualquer taxa de corpus abaixo disso. Para uma regra rara, o portão é vazio |

O último é um defeito do **meu portão**, e é da mesma família do `M4` que
disparou num empate de 7,6×10⁻⁵: **um portão operacionalizado sem olhar para o
regime em que ia correr**. Honrei-o porque estava pré-escrito — mudar um portão
depois de ver o número é o que o pré-registo existe para impedir —, mas o que
ele autoriza vale o que vale: uma ocorrência.

---

## 5. O que isto decide

**Fecha a gramática como via mecânica**, e é a segunda metade do que a 5Q
nomeou. A [5R](FASE-5R-RELATORIO.md) fechou a ortografia por **tamanho do
corpus**; esta fecha a gramática por **não haver diferença**:

| via | fechada por | número |
|---|---|---|
| ortografia (5R) | as canónicas que interessam são raras | 8, 7 e 2 ocorrências |
| **gramática (5T)** | **o poeta faz o mesmo que os modelos** | 0,045 contra 0,052–0,062 |

São razões **diferentes**, e a desta é mais definitiva: um corpus maior resolvia
a 5R e não resolve esta. Não há nada a detectar.

**E reposiciona duas das três regras da persona:**

| regra, em `src/voices.py` | o corpus | veredicto |
|---|---|---|
| «colocação enclítica, **sempre**» | Pessoa procliticiza em 51 poemas; 0,045 das ocorrências | **demasiado forte como absoluto**, mas os modelos já estão na taxa do poeta — não é por aqui que se perde |
| «não uses gerúndio» | Pessoa usa a perífrase em **101 poemas** | **errada como descrição do poeta** |
| «usa «tu», não «você»» | 4 poemas em 1926 | **certa** |

**Não corrige as personas**, porque o §4.2 pré-escreveu que não o faria. O que
faz é dar ao [passo 24](CONTROLO.md) um segundo item com número ao lado dos
quatro intervalos de versos da 5L — e a 5I já mediu que mexer na instrução deu
saldo líquido **negativo** uma vez, logo é pré-registo próprio.

**Não diz que a instrução causa a taxa.** Os modelos estão na taxa de Pessoa
**com** a instrução no prompt; se é por causa dela ou apesar dela só uma ablação
emparelhada diz, e esta fase não a fez.

### O que fica na mesa

1. **A forma de verso** — é agora **o que resta** do passo 34. As duas metades
   que a [5Q §3](FASE-5Q-RELATORIO.md) nomeou estão ambas fechadas do lado da
   detecção: ortografia pela 5R, gramática por esta. O AUC de 0,938–1,000
   continua de pé e não é explicado por nenhuma das duas.
2. **O passo 24, com dois itens** — os quatro intervalos de versos (5L) e o
   gerúndio (esta fase). E com a predição direccional da [5M §3.1](FASE-5M-RELATORIO.md) já registada.
3. **Uma ablação da instrução de língua**, que é a única maneira de saber se as
   regras da persona fazem alguma coisa. Barata: as regras estão num bloco só.

> **A lição, e é a nona.** As oito anteriores foram sobre instrumentos. Esta é
> sobre **a ordem em que se olha**.
>
> O portão de segurança — correr o detector no corpus **antes** de o apontar ao
> alvo — apanhou-me três vezes na mesma fase: matou a primeira régua, desmentiu
> a segunda, e na terceira mostrou que não havia sinal. Se o tivesse corrido
> depois, teria publicado «os modelos são mais enclíticos que Pessoa» com um
> intervalo de confiança a sustentá-la, e estaria errada.
>
> **Um intervalo de confiança não protege de um numerador errado.** O que
> protege é medir o instrumento no material que ele não pode marcar — e aqui esse
> material eram os 1926 poemas do próprio poeta, que estavam lá desde o primeiro
> dia.
