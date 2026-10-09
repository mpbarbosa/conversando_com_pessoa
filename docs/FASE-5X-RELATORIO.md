# Fase 5X — relatório: a mesma configuração, medida duas vezes, varia tanto como o efeito que eu queria ver

**Protocolo:** [`FASE-5X.md`](FASE-5X.md), pré-registado em `8789c58`.
**Analisador:** fixado em `18daafd`, antes de os dados existirem.
**Dados:** [`fase-5x/01-cru.jsonl`](fase-5x/) (60) ·
[`02-resultados.json`](fase-5x/)
**Produto:** **nada**, e o §3.1 pré-escreveu que não embarcaria de qualquer modo.

---

## 0. Os portões

| | | |
|---|---|---|
| **X1** a penalização proíbe a rima | ❌ não dispara | +54%, IC [−0,0074, +0,0140] |
| **X2** menos entropia dá mais rima | ❌ não dispara | **−36%**: a direcção é a contrária |
| **X3** sem degeneração | ❌ não dispara | **e o veto é meu, não dos dados** (§3) |
| **X4** a descodificação também não | ✅ **dispara** | |

| braço | `rp` | `temp` | **densidade** | ×poeta | rima binária | nulo | dupl. | metro |
|---|---|---|---|---|---|---|---|---|
| **B** produção | 1,1 | 0,9 | 0,00615 | 16,2× | 0,150 | 0,400 | 0,0031 | 0,630 |
| **P** | **1,0** | 0,9 | **0,00945** | 10,6× | **0,400** | 0,400 | **0,0000** | 0,620 |
| **T** | 1,1 | **0,5** | 0,00396 | 25,2× | 0,250 | 0,450 | 0,0048 | 0,590 |
| *poeta* | | | **0,09969** | — | 0,8367 | — | — | 0,7572 |

---

## 1. O número que decide a fase não está na tabela dos portões

A 5W mediu o braço de **produção** no ortónimo e deu densidade **0,00951**. Esta
fase mediu o braço de **produção** no ortónimo e deu **0,00615**.

| | densidade do ortónimo em **produção** | n |
|---|---|---|
| [5W](FASE-5W-RELATORIO.md), braço C | **0,00951** | 20 |
| 5X, braço B | **0,00615** | 20 |
| **razão entre as duas medições da mesma coisa** | **1,54×** | |
| razão P/B **dentro** desta fase | **1,54×** | |

**A mesma configuração, medida duas vezes com 20 amostras, varia exactamente
tanto como o efeito que eu estava a tentar detectar.** Não é uma analogia: é o
mesmo número, 1,54.

Isto não invalida nada do que foi publicado — nenhuma conclusão da 5W depende de
0,0095 em vez de 0,0062, porque **o fosso ao poeta é de 10 a 16 vezes** e
sobrevive a esta variação com folga. O que isto mata é a pretensão de **comparar
braços** a esta escala.

> **E é a medição que faltava a três fases.** A 5T, a 5U e a 5W morreram «por
> potência», e eu estimei a potência a partir do IC de dentro de cada fase. Esta
> dá-a de fora: **o chão de ruído de uma célula de 20 amostras é um factor de
> 1,5**, e está medido, não derivado. Qualquer efeito menor que isso é invisível
> neste desenho, e nenhum número de braços o conserta.

---

## 2. O X1: a direcção é a prevista e o tamanho é o que eu declarei não conseguir ver

| | B | **P** | |
|---|---|---|---|
| densidade de rima | 0,00615 | **0,00945** | **+54%** (1,54×) |
| rima binária | 0,150 | **0,400** | **2,7×** |
| IC95 da diferença de densidades | | | [−0,0074, **+0,0140**] |

**O §2.1 do protocolo escreveu, antes de haver amostras, que este desenho
«detecta uma duplicação da densidade e não menos».** O observado é **+54%**,
abaixo desse limiar. Logo o X1 não disparar é **o que o pré-registo previu que
aconteceria para um efeito deste tamanho** — e o §4.3 escreveu também como se
deve ler: «não detectável aqui», **não** «não existe».

A rima binária salta 2,7× (0,150 → 0,400), mas **0,400 é exactamente o nulo de
permutação do próprio braço P**. Pela lição da 5W, a presença de rima é a
resolução errada; é a densidade que manda, e a densidade diz +54% com um
intervalo que contém zero.

**A hipótese do §1 do protocolo fica onde estava: plausível, não demonstrada.** E
a mecânica continua por verificar — não consigo ver as fronteiras de *token* do
llama, o que o §4.2 já declarava.

---

## 3. O X3 vetou, e o veto é um defeito meu

O X3 foi escrito como uma comparação de **estimativas pontuais, sem intervalo**.
Com isso, vetou:

| «dano» | diferença | **IC95** |
|---|---|---|
| metro, P contra B | **−0,0097** | **[−0,145, +0,116]** |
| metro, T contra B | −0,0399 | [−0,157, +0,070] |

**O intervalo é quinze vezes mais largo que a estimativa.** O veto disparou em
ruído, e é a **terceira vez** nesta sequência que um portão meu é
operacionalizado sem olhar para o regime em que ia correr — depois do `M4` a
disparar num empate de 7,6×10⁻⁵ e do `T2` da 5U a disparar com **uma** ocorrência
em 48.

Honro-o, porque mudar um portão depois de ver o número é o que o pré-registo
existe para impedir. Mas o que ele veta vale o que vale: −0,0097 num intervalo de
±0,13.

### 3.1 E a degeneração — o motivo pelo qual a constante existe — **não apareceu**

| | **B** (rp 1,1) | **P** (rp 1,0) | T |
|---|---|---|---|
| linhas duplicadas | 0,0031 | **0,0000** | 0,0048 |
| palavras suspeitas | 6 | **0** | 2 |
| truncatura | 0 | **0** | 0 |
| falhas de guarda | 0 | **0** | 0 |
| `e_verso` | 1,00 | **1,00** | 1,00 |

**Com a penalização desligada, o braço P é mais limpo que produção em todas as
medidas.** Zero linhas duplicadas contra 0,0031, zero palavras suspeitas contra
seis.

**O `REPEAT_PENALTY = 1.1` entrou na Fase 0 porque «um 8B degenerou em ciclo».
Esse motivo não se reproduz no `llama3.1:8b`** — 20 amostras com a penalização
desligada e nenhuma degeneração em medida nenhuma. É o achado mais sólido da
fase, e é sobre a constante e não sobre a rima.

---

## 4. O X2: a temperatura vai para o lado errado

Baixar a temperatura para 0,5 deu **0,64× a densidade de rima** (0,00396 contra
0,00615) e o metro mais longe do poeta (0,590 contra 0,630, poeta 0,7572).
Nenhuma das duas exclui zero, mas **a direcção é consistentemente a contrária** da
intuição que motivou o braço — «menos entropia, mais formulaico, mais rima».

Pela metade da temperatura, o [passo 17](CONTROLO.md) fica **sem direcção
plausível** para a forma.

---

## 5. O que isto decide

**O X4 dispara: nem o prompt nem a descodificação alcançam a forma.** É a leitura
mais consequente que a fase podia dar, e está pré-escrita. As três vias que o
projecto tinha para o [passo 34](CONTROLO.md):

| via | fase | estado |
|---|---|---|
| detecção (ortografia, gramática) | 5R · 5T · 5U | **fechada**: 7 próclises e 1 marca em 120 amostras |
| instrução (prompt) | 5V · 5W | **fechada**: a instrução existe, é ignorada, reforçá-la dá sinal negativo |
| **descodificação** | **5X** | **sem efeito detectável**, e o chão de ruído é 1,5× |

**Nada embarca**, e o §3.1 já o dizia antes de haver número — o `_opcoes` é
global e o Caeiro é a única voz que funciona.

**Mas uma coisa fica estabelecida e é para usar:** a justificação do
`REPEAT_PENALTY` não se reproduz no modelo que serve. Isso não autoriza
desligá-lo — autoriza **medi-lo a sério**, e agora sabe-se o que isso custa.

### O que fica na mesa

1. **Testar a mecânica com uma manipulação forte, em vez de a resolver com mais
   amostras.** Para resolver +54% com este desfecho fariam falta **~720 amostras
   por braço** (~10 h cada). A alternativa é `repeat_penalty = 0.9`, que
   **premeia** *tokens* repetidos: se a mecânica do §1 for real, a predição é um
   aumento **grande** de rima — e possivelmente degeneração, que a bateria do §3.1
   apanha. **Efeito grande, desenho pequeno** é o caminho quando a potência é o
   que falta.
2. **A verificação de dano no Caeiro**, que o §3.1 exige antes de qualquer
   embarque de opção global — e que agora tem um motivo adicional: o braço P é
   *mais limpo* que produção no ortónimo.
3. **Portões com intervalo, não com estimativa pontual.** Três vezes o mesmo
   defeito; passa a regra e não a lição.
4. **Afinação**, que é o que sobra do passo 34 depois de três vias fechadas — e
   está fora do que esta máquina faz em CPU.

> **A lição, e é a décima.** A oitava foi **onde** medir, a nona **com que
> resolução**. Esta é a terceira do mesmo eixo e a mais básica: **medir o chão de
> ruído do desenho antes de interpretar diferenças nele.**
>
> Eu tinha o chão à mão desde a 5W e não o vi, porque estava **entre fases** em
> vez de dentro de uma: a mesma configuração de produção, as mesmas 10 perguntas,
> 20 amostras cada, deu **0,00951** na 5W e **0,00615** aqui. **1,54×** — o mesmo
> factor que separa o braço P do braço B e que eu quase li como efeito da
> penalização.
>
> **Um IC calculado dentro de uma corrida não vê a variação entre corridas.** Os
> meus intervalos estavam certos e mediam a coisa errada: a incerteza de
> amostragem dentro da célula, não a reprodutibilidade da célula. O remédio é
> barato e não o fiz em sete fases — **correr a configuração de controlo duas
> vezes** e olhar para a diferença antes de olhar para os braços.
