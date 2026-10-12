# Fase 5Z — relatório: a mecânica não se demonstra, e o número que quase a demonstrou é um par `toque`/`que`

**Protocolo:** [`FASE-5Z.md`](FASE-5Z.md), pré-registado em `e44213a`.
**Gerador e analisador:** fixados em `bca13a8`, **antes de os dados existirem**.
**Dados:** [`fase-5z/01-cru.jsonl`](fase-5z/) (60) ·
[`02-resultados.json`](fase-5z/)
**Modelo:** `llama3.1:8b-instruct-q4_K_M`, voz **ortónimo**, braços
**intercalados** (`B N R B N R …`), mesmas sementes, 40 min de geração.
**Produto:** **nada**, e o [§3.1](FASE-5Z.md) pré-escreveu que não embarcaria de
qualquer modo.

---

## 0. Os portões

| | | |
|---|---|---|
| **Z1** a mecânica é real | ❌ **não dispara** | monotonia **sim**, IC [−0,0093, **+0,0283**] contém zero |
| **Z2** a 5X replica | ✅ dispara — **e o portão está mal operacionalizado** (§3) | **1,28×** onde a 5X deu 1,96× |
| **Z3** sem degeneração | ✅ no braço **N** · ❌ no braço **R** | **linhas duplicadas 0,2353 contra 0,0031**, IC [+0,126, +0,347] |
| **Z4** a mecânica não é real | ✅ **dispara** | |

| braço | `rp` | **densidade 1.ª** | ×poeta | rima bin. | nulo p99 | dens. final | dupl. | trunc. | plág. | 2 tent. | seg |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **B** produção | 1,1 | 0,00750 | 13,3× | 0,200 | 0,400 | 0,00793 | 0,0031 | 0,10 | 0,00 | 2/20 | 38 |
| **N** neutro | **1,0** | 0,00960 | 10,4× | 0,400 | 0,450 | 0,01262 | **0,0000** | 0,05 | 0,05 | 2/20 | 30 |
| **R** premeia | **0,9** | **0,01437** | 6,9× | 0,200 | 0,550 | 0,01264 | **0,2353** | **0,50** | 0,10 | **10/20** | 46 |
| *poeta* | | **0,09969** | — | 0,8367 | — | — | — | — | — | — | — |

**Nenhum braço passa o seu próprio nulo de permutação na rima binária** — a
quarta fase seguida em que isso acontece.

---

## 1. A monotonia aconteceu. E cai se eu tirar **uma** célula

O [§1.1](FASE-5Z.md) do protocolo escreveu, antes de haver número, que a
monotonia era «a predição que um só contraste não dá» e «o que uma coincidência
não prediz». Ela verificou-se:

| `repeat_penalty` | 1,1 | 1,0 | **0,9** |
|---|---|---|---|
| densidade na 1.ª tentativa | 0,00750 | 0,00960 | **0,01437** |

Três níveis, três médias ordenadas, na direcção prevista. **E não vale nada**,
porque o IC da diferença que importa contém zero com folga — `R − B = +0,00687`,
IC95 **[−0,0093, +0,0283]** — e porque a ordenação não sobrevive a um teste que
custa três linhas.

**Análise posterior e declarada** (não está no pré-registo; está em §1.1 abaixo
e é reproduzível a partir do `01-cru.jsonl`):

| | B | N | **R** | monótona? |
|---|---|---|---|---|
| 20 células | 0,00750 | 0,00960 | **0,01437** | **sim** |
| **19 células**, sem `q34/r1` | 0,00790 | 0,01011 | **0,00635** | **não — inverte** |

**Sem uma célula de vinte, o braço que premeia repetição rima 0,8× o braço de
produção**, e a predição que o protocolo declarou impossível de obter por
coincidência obtém-se, aqui, por uma.

### 1.1 Porque é uma célula e não vinte: o desfecho é zero em 73% das amostras

| | B | N | R |
|---|---|---|---|
| células com densidade **exactamente zero** | **16/20** | 12/20 | **16/20** |
| células onde o braço **supera** B (das 20) | — | **7** (2 abaixo, 11 empatadas a zero) | **4** (2 abaixo, 14 empatadas) |

**44 das 60 primeiras tentativas não rimam um único par.** O que eu chamei «média
de densidade» é, neste regime, a **frequência de um evento raro multiplicada pelo
seu tamanho** — e com 20 amostras por braço estou a comparar **4 ocorrências
contra 2**. O emparelhamento por célula, que estes dados permitem e o analisador
não usou, **não ajuda nada**: o IC emparelhado é [−0,0096, +0,0283] contra o
não-emparelhado [−0,0093, +0,0283]. Não há variância pareada para extrair quando
14 dos 20 pares são `0 − 0`.

O [§4.3](FASE-5Z.md) do protocolo estimou a potência pela meia-largura do IC da
5X (~0,008 sobre uma base de ~0,006) e concluiu que o desenho «vê um triplicar
com folga». **A conta estava certa e a grandeza era a errada:** triplicar uma
base de 4 eventos em 20 significa chegar a 12, e nada no desenho garantia que
o faria.

---

## 2. O número que decide a fase, verso a verso

A célula `q34/r1` do braço R tem densidade **0,1667** — o único valor de toda a
fase **acima do poeta** (0,09969). São quatro versos, e a pergunta era «ofereço-lhe
o meu afecto e ela nem repara»:

```
A tua falta de olhar, é o teu olhar
A tua falta de toque, é o teu toque
A tua falta de voz, é a voz que
Faz que eu te chame, de perto, de perto.
```

As chaves de rima que o instrumento extrai:

| verso | palavra final | chave |
|---|---|---|
| 1 | `olhar` | `olhar` |
| 2 | `toque` | **`ue`** |
| 3 | `que` | **`ue`** |
| 4 | `perto` | `erto` |

**Um par em seis possíveis: `toque` / `que`.** Quatro versos dão 6 pares, logo
1/6 = 0,1667 — e `0,1667/20 = 0,0083`, que é **mais** do que a diferença total
entre o braço R e produção (+0,0069).

**A fase inteira depende de o braço que premeia *tokens* repetidos ter acabado
dois versos seguidos na mesma sílaba.** O instrumento exclui pares de **palavra
igual** — e é por isso que `olhar`/`olhar` e `toque`/`toque`, que estão no mesmo
poema, não contam. Não exclui `toque`/`que`, que é a mesma sílaba numa palavra
de função e **exactamente aquilo que a manipulação foi desenhada para produzir**.

Isto é um defeito do instrumento **sob esta manipulação**, e não tinha como
aparecer antes: nos braços 1,1 e 1,0 nada empurra os versos para terminações
repetidas. Vai para os defeitos do [§4 do `CONTROLO.md`](CONTROLO.md).

---

## 3. O Z2 disparou, e é a **quarta** vez que um portão meu está mal operacionalizado

O protocolo escreveu o Z2 como «densidade(1,0) > densidade(1,1), **razão próxima
de 2×**». O analisador — fixado antes dos dados, como deve ser — implementou-o
como `razao > 1.0`:

| | 5X (17 células limpas) | **5Z (1.ª tentativa)** |
|---|---|---|
| razão `rp=1,0` / `rp=1,1` | **1,96×** | **1,28×** |
| IC95 da diferença | [−0,0037, +0,0092] | **[−0,0083, +0,0116]** |

**A 5X não replica.** 1,96× passa a **1,28×**, com um intervalo que contém zero
e que é mais largo que a estimativa. O Z2 dispara porque `1,28 > 1,0`, o que não é
a condição que o protocolo em prosa pedia.

**E o braço N é o único da fase que aguenta o teste do §1:** tirando a sua célula
mais alta aos dois lados, a razão fica em **1,29×** — não se move. Tem também a
contagem de sinais mais consistente (**7 células acima de produção contra 2
abaixo**, onde R tem 4 contra 2). **O braço robusto desta fase é o neutro, não o
invertido** — e nem assim exclui zero. É a 5X a repetir-se em metade do tamanho,
e é tudo o que 20 amostras por braço dão.

**Honro-o** — está no JSON como «dispara» e fica assim, porque mudar um portão
depois de ver o número é o que o pré-registo existe para impedir. E leio-o pelo
que vale: **não replicou.**

E o padrão é o que dói. O [§5 da 5X](FASE-5X-RELATORIO.md) escreveu, como terceiro
item do que ficava na mesa, «**portões com intervalo, não com estimativa pontual**
— três vezes o mesmo defeito; passa a regra e não a lição». **Eu apliquei a
regra ao Z3, que é onde a 5X tinha falhado, e não a revi no Z2**, que é o portão
que não me tinha dado problemas. Os três anteriores — `M4`, `T2` da 5U, `X3` da
5X — **vetaram** em ruído; este **aprova** em ruído. A regra é a mesma e eu
apliquei-a a **um dos três portões** que esta fase tinha para escrever.

---

## 4. O Z3 é o único resultado sólido da fase: premiar repetição degenera

| medida (1.ª tentativa) | **B** 1,1 | **N** 1,0 | **R** 0,9 | IC95 de R − B |
|---|---|---|---|---|
| linhas duplicadas | 0,0031 | **0,0000** | **0,2353** | **[+0,126, +0,347]** |
| truncatura | 0,10 | 0,05 | **0,50** | **[+0,150, +0,650]** |
| plagiou | 0,00 | 0,05 | 0,10 | contém zero |
| não-verso | 0,00 | 0,00 | 0,00 | — |
| versos (mediana) | 10,0 | 10,5 | **16,0** | — |
| 2.ª tentativa necessária | 2/20 | 2/20 | **10/20** | — |

**Dois danos com IC a excluir zero**, logo o Z3 **não** dispara no braço R: 76×
mais linhas duplicadas e **metade das amostras cortadas a meio**. Uma em cada
duas respostas de `rp=0,9` foi rejeitada pela guarda e teve de ser regerada.

E o modo de falha é literalmente o da Fase 0. A célula `q38/r1` do braço R
começa a copiar um poema real do corpus e termina assim:

```
E que é o que se passa
Nessa não lembrança?
E que é o que se sente?
E que é o que se é?
E que é o que se não é?
…
```

**É o ciclo.** A [5X](FASE-5X-RELATORIO.md) §3.1 mediu que **desligar** a
penalização (1,0) não degenera nada — e isso confirma-se aqui: o braço N é, outra
vez, mais limpo que produção em todas as medidas. **Premiar** é outra coisa, e a
diferença entre «não degenera a 1,0» e «degenera a 0,9» é o que faltava saber
sobre a constante:

> **O `REPEAT_PENALTY = 1.1` está justificado contra 0,9 e continua
> injustificado contra 1,0.** Os dois lados são agora medidos, e são medições
> diferentes.

E há uma leitura que atravessa o §2: **a mesma manipulação que produz as linhas
duplicadas produz o par `toque`/`que`.** O pouco de «rima» que o braço R mostra
é da mesma família que o seu dano — terminações repetidas —, o que é a razão
mecânica pela qual este caminho não serve mesmo que o número tivesse aguentado.

---

## 5. O desfecho primário funcionou, e era mesmo necessário

O [passo 43](CONTROLO.md) foi escrito para esta fase. O que ele deu:

| | células com prompt divergente entre braços |
|---|---|
| **1.ª tentativa** (primário) | **0 / 20** |
| saída final (secundário) | **4 / 20** |

**Zero**, como o §2 do protocolo previu — o `_repetir_sem` só actua depois da
primeira tentativa. E **4 em 20 na saída final** — **20%**, que na tabela do
[passo 42](CONTROLO.md) só fica atrás da 5G (40%) e da 5B (23%). Se eu tivesse
medido esta fase como medi as nove anteriores, uma célula em cada cinco estaria
contaminada, e pela razão que a [5Y](FASE-5Y-RELATORIO.md) nomeou: o braço R é o
que mais repete (**10/20**), logo é o braço cujo prompt mais divergia.

**E a saída final apagava o resultado:**

| | B | N | R |
|---|---|---|---|
| densidade na 1.ª tentativa | 0,00750 | 0,00960 | **0,01437** |
| densidade na saída final | 0,00793 | **0,01262** | **0,01264** |

Na saída final, **N e R coincidem até à quarta casa decimal** — a
monotonia desaparece, porque o braço R tem metade das suas primeiras tentativas
rejeitadas e regeradas. O tratamento com o efeito nominal maior é o que o sistema
mais corrige, logo é o que a saída final menos mostra. **É a décima primeira
lição a ganhar a sua confirmação directa**, e passou de auditoria retrospectiva a
previsão verificada.

---

## 6. O que isto decide

**O Z4 dispara, e está pré-escrito o que isso significa:** o [§4.3](FASE-5Z.md)
declarou, antes de haver dados, que «se a 0,9 o efeito for pequeno, a mecânica
fica refutada como explicação útil — porque a 0,9 ela está a ser empurrada na
direcção favorável com toda a força disponível».

É o que aconteceu. Com a opção **invertida**, a premiar precisamente aquilo de
que a rima é feita:

- a diferença ao braço de produção **contém zero**;
- vive numa célula de quatro versos, e inverte sem ela;
- e o par que a produz é `toque`/`que`, não uma rima.

| via do [passo 34](CONTROLO.md) | fase | estado |
|---|---|---|
| detecção (ortografia, gramática) | 5R · 5T · 5U | **fechada** |
| instrução (prompt) | 5V · 5W | **fechada** |
| descodificação | 5X · **5Z** | **fechada**: a manipulação forte não a demonstra, e a direcção favorável degenera |

**As três vias estão fechadas, e a terceira fecha com causa e não por falta de
potência** — que é a diferença entre esta fase e as três que morreram «por
potência». Sobra **afinação**, que esta máquina não faz em CPU.

**Nada embarca.** O [§3.1](FASE-5Z.md) pré-escreveu-o para os três desfechos
possíveis, e o desfecho que saiu é o que o dizia de forma mais simples: não há o
que embarcar. O [passo 41](CONTROLO.md) — dano no Caeiro — **deixa de ser
bloqueio de embarque** e fica como passo por mérito próprio; o
[passo 40](CONTROLO.md) **fecha-se**.

### O que fica na mesa

1. **O instrumento de rima precisa de excluir terminações repetidas, e não só
   palavras repetidas.** `toque`/`que` conta como rima e não é. Afecta todas as
   densidades publicadas desde a 5W — na direcção de as **inflacionar**, incluindo
   as do poeta, que é a régua.
2. **Um desfecho de rima que não seja zero em 73% das amostras**, ou então um
   desenho que admita que está a contar eventos raros e dimensione em
   ocorrências, não em médias. O [passo 38](CONTROLO.md) herda isto.
3. **Revisão dos portões escritos e ainda não corridos**, todos, contra a regra
   do intervalo. O Z2 passou porque eu só olhei para onde já tinha falhado.
4. **O `REPEAT_PENALTY` fica onde está**, agora com os dois lados medidos: 1,0
   não degenera, 0,9 degenera, e nenhum dos dois dá forma.

> **A lição, e é a décima segunda.** As quatro anteriores são sobre o desenho —
> **onde** medir, **com que resolução**, verificar que «a mesma coisa» é a mesma
> coisa, e medir **antes** das correcções do sistema. Esta é sobre o desfecho
> em si: **uma média de um desfecho que é zero na maioria das amostras não é uma
> média; é uma contagem de eventos raros disfarçada, e a sua incerteza vem de
> quais células calharam não ser zero.**
>
> Eu tinha tudo para ver isto antes de gerar. A 5W publicou densidades de 0,003 a
> 0,009 num desfecho cujo valor mínimo não-nulo, num poema de dez versos, é
> **1/45 = 0,022** — ou seja, **qualquer média abaixo de 0,022 é, por
> construção, uma média de maioritariamente zeros**. O número estava publicado em
> três relatórios e eu lia-o como se fosse contínuo.
>
> E o corolário é o mais desconfortável: **a predição mais forte que esta
> sequência produziu — a monotonia em três níveis — verificou-se, e não vale
> nada.** Verificou-se porque uma célula de quatro versos caiu no braço certo.
> Uma predição qualitativa sobre uma ordenação de médias é tão frágil quanto a
> média mais frágil das três, e eu escrevi-a no protocolo como se a sua força
> viesse da sua forma lógica em vez de vir dos dados que a iam avaliar.
