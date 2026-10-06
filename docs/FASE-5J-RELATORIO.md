# Fase 5J — relatório: a régua está torta, e endireitá-la deixa-a cega

**Protocolo:** [`FASE-5J.md`](FASE-5J.md), pré-registado em `13247b9`.
**Dados:** [`fase-5j/01-contagem.json`](fase-5j/) · [`03-resultados.json`](fase-5j/)
**Não gerou amostras.** Tudo é determinista sobre o corpus, ou reutiliza as
amostras da [5H](FASE-5H-RELATORIO.md).

---

## 0. Os portões

| | | |
|---|---|---|
| **J1** o defeito é das quatro vozes | ✅ **dispara** (3 de 4) | **mas não é robusto às quatro sensibilidades** — ver §1.2 |
| **J2** o instrumento penaliza a fidelidade | ❌ **não dispara** | e falha **ao contrário** do previsto: o llama está *mais longe* do poeta |
| **J3** a elegibilidade não explica o J1 | ✅ dispara com folga | os excluídos são **mais longos**, não mais curtos |
| **J4** há um intervalo que se valida fora da amostra | ✅ dispara | `[4,31]` cobre 86% da retida contra 42% — **e a sua consequência mata-o** (§4.2) |
| **J5** inconclusivo por potência | ✅ dispara | o IC do J2 inclui 0; não se mostra a inversão **nem** o contrário |

**A leitura em uma frase.** Os intervalos de versos do 3b **não descrevem o
poeta** — e a razão é um mecanismo único, os **pisos das personas** —, mas isso
**não exonera o llama3.1**, que é o que a 5I esperava. E o intervalo
descritivamente correcto **premeia os dois modelos acima do original**, o que
torna a contagem de versos imprestável como critério **positivo** por uma razão
mais funda do que estar mal calibrada.

---

## 1. J1 — os pisos das personas estão altos demais

Primário: poemas autênticos, `language == pt`, elegíveis, contados com
`plagio._versos` sobre o poema inteiro.

| voz | intervalo | piso | mediana real | **abaixo** | dentro | acima | Wilson95 | |
|---|---|---|---|---|---|---|---|---|
| **caeiro** | 10–20 | 10 | 11,5 | **42%** | 39% | 19% | [0,31; **0,48**] | falha |
| **campos** | 15–30 | 15 | **14** | **51%** | 32% | 17% | [0,26; **0,38**] | falha |
| **reis** | ≤12 | **nenhum** | 10 | **0%** | **73%** | 27% | [0,67; 0,79] | passa |
| **ortonimo** | 12–20 | 12 | **9** | **65%** | 25% | 10% | [0,23; **0,28**] | falha |

### 1.1 Um mecanismo, e explica as quatro células

As três vozes que falham **falham todas para baixo**, e a causa é visível na
coluna do piso:

- **Campos**: o piso exigido é **15** e a mediana do poeta é **14**. O intervalo
  começa acima do meio da obra.
- **Ortónimo**: piso **12**, mediana **9**. Dois terços da obra ficam abaixo do
  mínimo.
- **Caeiro**: piso **10**, mediana 11,5 — mas o **p25 é 8**. A persona pede
  «linhas curtas» e impõe ao mesmo tempo um mínimo de dez versos; **pede o
  contrário de si mesma**.
- **Reis** é a única voz cujo intervalo **não tem piso** («≤12»), tem por isso
  **0% abaixo**, e é a única que passa.

A demonstração mais limpa está em comparar o Caeiro com o Reis: **escrevem
praticamente o mesmo comprimento** — medianas 11,5 e 10 — e a conformidade dá
**39% contra 73%**. A diferença não está nos poetas; está em um dos intervalos
ter chão e o outro não. **A conformidade mede a forma do intervalo, não a forma
do verso.**

### 1.2 A ressalva, e é do lado que importa

O J1 **não aguenta as quatro combinações** de língua × definição de verso que o
§4.1 e o §4.2 declararam:

| | vozes que falham |
|---|---|
| pt · `_versos` **(primário)** | caeiro, campos, ortonimo — **3** ✅ |
| pt · linhas não vazias | campos, ortonimo — **2** ❌ |
| todas · `_versos` | caeiro, campos, ortonimo — **3** ✅ |
| todas · linhas não vazias | campos, ortonimo — **2** ❌ |

Sob «linhas não vazias» o limite superior do Caeiro é **0,52** e a célula deixa
de falhar por dois centésimos.

**Logo o disparo formal do J1 depende da célula do Caeiro — que é a mais frágil
e a única que eu já tinha visto antes de escrever o protocolo (§2.3).** Não
tenho como lhe dar mais peso do que isso.

**O que não depende dela:** Campos e ortónimo falham **decisivamente nas quatro
combinações**, com limites superiores entre 0,28 e 0,42. Para a conclusão sobre o
**método** — intervalos tirados das personas não descrevem o corpus — bastam
essas duas, e nenhuma delas foi vista antes de o protocolo estar escrito.

---

## 2. J2 — não dispara, e a 5I inferiu de um escalar

O portão pedia duas coisas ao mesmo tempo: menos conformidade **e** mais
fidelidade no llama. A primeira confirma-se; **a segunda inverte-se.**

| braço | n | conformidade a 10–20 | mediana | **KS ao Caeiro real** |
|---|---|---|---|---|
| **qwen2.5** | 30 | **83%** | 13,5 | **0,288** |
| **llama3.1** | 30 | **30%** | **7,5** | **0,347** |
| *Caeiro real* | 118 | *39%* | *11,5* | — |

O llama tem menos conformidade **e está mais longe** da distribuição real, nos
dois indicadores: KS 0,347 contra 0,288, e mediana 7,5 contra 11,5 do poeta,
enquanto o qwen erra por 2 (13,5). **Não há inversão para mostrar.**

### 2.1 Onde a 5I se enganou, e é um erro de tipo conhecido

A 5I §9.2 escreveu que «**o llama3.1 reproduz a distribuição do poeta quase
exactamente**». A base era uma coincidência de **um escalar**: 40% das amostras
do llama dentro do intervalo contra 39% dos poemas reais. As distribuições por
trás desse escalar não se parecem nada:

| | abaixo de 10 | 10–20 | acima de 20 |
|---|---|---|---|
| **Caeiro real** | **42%** | 39% | **19%** |
| **llama3.1** | **70%** | 30% | **0%** |
| **qwen2.5** | 17% | 83% | **0%** |

O Caeiro real erra o intervalo **para os dois lados**; o llama erra **só para
baixo**. A fracção dentro coincide porque 42+19 ≈ 70+0, e não porque os poemas
se pareçam. **Uma fracção dentro de um intervalo não identifica uma
distribuição** — qualquer par de caudas que some o mesmo dá o mesmo número.

É o mesmo tipo de erro que a sequência já apanhou três vezes: um resumo a passar
por aquilo que resume. Aqui chegou a uma frase publicada, e a frase é falsa.

### 2.2 E o J5 impede-me de virar a conclusão ao contrário

O IC95% de `D(qwen) − D(llama)` está em **[−0,21; +0,12]** (bootstrap agrupado
na pergunta, 10 000 reamostragens; ingénuo dá [−0,21; +0,11]). **Inclui 0.**

Logo: **não se mostra que o llama esteja mais perto** — era a hipótese da 5I, e
cai — **e também não se mostra que o qwen esteja**. Com 30 amostras em 10
agrupamentos não há potência para a distância. O que fica estabelecido é o
**negativo**: a afirmação da 5I não tem apoio nos dados que a geraram.

### 2.3 O tecto do harness não explica nada, e eu publiquei que explicava

**Esta secção dizia o contrário e estava errada.** Fica reescrita em vez de
apagada, porque o erro é instrutivo e porque a versão errada esteve num commit.

Eu escrevi `num_predict = 150`, lido da **tabela do docstring** de
[`ollama.py`](../src/generation/ollama.py) linha 11, que ficou desactualizada
desde a Fase 1. **A constante é `NUM_PREDICT = 220`** (linha 38), e o próprio
comentário ao lado explica a subida. A sessão da 5I apanhou-o.

E com o número certo a inferência **cai inteira**, porque 220 tokens são ~147
palavras e as amostras não chegaram perto:

| braço | truncaturas | palavras: máx · mediana | versos: máx |
|---|---|---|---|
| **5H qwen** | **1** de 30 | 125 · 81 | 17 |
| **5H llama** | **0** de 30 | 126 · 63 | 15 |
| *5I braço A* | *2 de 30* | *139 · 70* | *22* |
| **5I braço B** *(com reforço)* | **6** de 30 | 153 · 85,5 | 20 |

**Uma truncatura em 60 na 5H**: os dois modelos **pararam sozinhos**, com folga
de vinte palavras para o tecto. Logo a ausência de poemas acima de 20 versos é
**dos modelos** e não do orçamento, e não há «fosso superior do harness» para
descontar.

O tecto **morde**, mas só quando se instrui para o comprimento: é o braço B da
[5I](FASE-5I-RELATORIO.md), com 6 truncaturas em 30 — precisamente o «o tecto
corta» que essa fase mediu. Os dois factos convivem, e a ordem é a que a 5I já
tinha corrigido a si mesma: o `num_predict` é irrelevante **até** a instrução
pegar.

**Consequência para o §2:** isto **reforça** o J2 em vez de o ressalvar. A
estreiteza das duas faixas — qwen 8–17, llama 4–15 — é dos modelos, e os `D`
absolutos podem ser lidos como distância ao poeta sem desconto nenhum.

---

## 3. J3 — os fragmentos não são a cauda de baixo

A suspeita era que transcrições incompletas puxassem o comprimento para baixo e
fabricassem o resultado. **É o contrário.**

| voz | excluídos | mediana dos excluídos | mediana dos retidos |
|---|---|---|---|
| campos | 70 | **23,5** | 14 |
| ortonimo | 143 | **18** | 9 |
| reis | 20 | 11,0 | 10 |
| caeiro | **1** | 8 | 11,5 |

Os textos com marca de lacuna são **mais longos** — um texto longo tem mais
ocasiões de conter uma marca editorial. Removê-los **baixa** a conformidade em
vez de a subir, logo trabalha **contra** a hipótese da fase. E no Caeiro o filtro
é praticamente inerte: **exclui 1 poema em 119**.

A conclusão do J1 é idêntica com e sem filtro em todas as vozes.

> **Limitação, como declarada no §4.3 e não resolvida.** Isto só mostra que as
> lacunas **marcadas** não produzem a cauda de baixo. Um rascunho curto **sem
> marca** continua indistinguível de um poema curto completo, e nenhuma regra por
> comprimento podia separá-los sem decidir a pergunta. Fica em aberto.

---

## 4. J4 — o intervalo honesto, e porque não serve

### 4.1 Valida-se

Metade de derivação (n=59, semente `20261005`), metade retida lida **uma só
vez**:

| | intervalo | cobertura na **retida** |
|---|---|---|
| derivado `[p10, p90]` | **[4, 31]** | **86%** [0,75; 0,93] |
| antigo | [10, 20] | **42%** |

**+44 pontos**, e o `[4,31]` sai da metade que não foi usada para o derivar — a
lição da [5C](FASE-5C-RELATORIO.md) cumprida.

### 4.2 E é inútil, o que o §6.4 tinha previsto

Aplicado às 60 amostras da 5H, o intervalo honesto dá:

| | conformidade a [10,20] | conformidade a **[4,31]** |
|---|---|---|
| **qwen2.5** | 83% | **100%** |
| **llama3.1** | 30% | **100%** |
| *Caeiro real (retida)* | *42%* | *86%* |

**Os dois modelos passam a 100% e o poeta fica em 86%.** O critério corrigido
premeia as imitações **acima do original** e perde **toda** a capacidade de
separar os dois modelos — 100% contra 100% onde antes havia 83% contra 30%.

O §3.2 do protocolo tinha escrito que falhar o J4 não autorizaria manter o
intervalo antigo. O que aconteceu foi o simétrico e não estava previsto: **o J4
passou, e passar também não autoriza adoptá-lo.**

### 4.3 Porque é que nenhum intervalo pode servir

A assinatura formal do Caeiro em comprimento **não é a tendência central; é a
dispersão**: de 1 a **161** versos, p25=8 e p90=28. Os dois modelos produzem
faixas estreitas — qwen 8–17, llama 4–15.

E **a dispersão é uma propriedade de um conjunto, não de um poema.** Um poema
sozinho não pode ser «correctamente disperso». Um critério por amostra que
pontua a filiação a um intervalo central está a tentar medir, uma amostra de cada
vez, uma propriedade que só existe no conjunto — e isso não é uma calibração
errada, é a **forma errada de instrumento**.

Um intervalo largo o bastante para conter o poeta contém trivialmente tudo o que
os modelos fazem; um estreito o bastante para discriminar reprova o poeta. **As
duas pontas do dilema estão medidas acima**, e não é uma escolha de limiar.

---

## 5. Correcções a afirmações minhas, feitas a meio da fase

1. **O §4.4 dizia que não havia campo de truncatura gravado. Havia.** O harness
   grava `truncada` de `done_reason == "length"`
   ([`ollama.py:107`](../src/generation/ollama.py)). Eu declarei uma heurística
   — «a última linha não termina em pontuação terminal» — e ela acertou
   **zero**: marcou 4 amostras, nenhuma delas truncada, e deixou passar a única
   que era. Num corpus de verso livre, acabar sem ponto é **estilo**, não
   corte. O primário passou a ser o campo gravado.
2. **O `max` publicado pela adenda da 5I está errado**, e a causa é o
   `contar_versos.py` resolver cada poema pelo **primeiro chunk**. São **161**
   versos e não 48. As **fracções e medianas publicadas estão certas**: dos 119
   poemas de Caeiro só 5 são multi-chunk e os cinco já estavam acima de 20
   versos no primeiro chunk, logo nenhum muda de categoria. Esta fase conta
   sempre sobre `.body`.

   **E 161 é o valor certo, não 181.** A sessão da 5I corrigiu o `setdefault`
   juntando os textos dos chunks, e isso troca um defeito por outro: o chunker
   tem **`SOBREPOSICAO = 1`** ([`chunk.py:36`](../src/corpus/chunk.py)) e repete
   **uma estrofe** em cada fronteira. No `poem_1487`, que é o que move o máximo,
   os cinco chunks juntos dão 181 contra os **161** do `.body`, com **21 linhas
   duplicadas e zero em falta** — contei os multiconjuntos. A fonte certa é o
   `body` do `parse_poem`, que é o poema antes de ser partido para indexação.

3. **Escrevi `num_predict = 150` e são 220.** Li a **tabela do docstring** de
   [`ollama.py`](../src/generation/ollama.py) linha 11, desactualizada desde a
   Fase 1, em vez da constante na linha 38 — e a constante tinha ao lado o
   comentário que explicava a subida. Pior do que o número: construí sobre ele
   uma explicação («a gama alta é inalcançável por construção») que **não se
   sustenta**, porque na 5H houve **1 truncatura em 60**. O §2.3 está reescrito.
   A lição é a de sempre nesta sequência, agora aplicada a mim a ler código:
   **um docstring não é a fonte de um valor; a constante é.**

E uma que não é minha, mas é desta fase: **a definição de verso do §9.2 da 5I
misturava duas** (linhas não vazias nos poemas reais, `plagio._versos` nas
amostras geradas). Foi apanhada antes de o protocolo ser escrito e corrigida
pela sessão da 5I em `742b9f6`; o §2.1 do protocolo registra a reprodução que a
identificou.

---

## 6. O que isto autoriza, e o que não

**Autoriza retirar a contagem de versos do 3b como critério positivo.** Não por
estar mal calibrada — está, e sabe-se para onde (§1.1) — mas porque o §4.3 mostra
que **nenhuma** recalibração a torna simultaneamente verdadeira e discriminativa.
A prescrição é a do §3.2 do protocolo, escrita antes de medir: **retirar**, não
conservar por falta de alternativa.

**Não autoriza dizer que o llama3.1 não tem défice de forma.** Era a hipótese que
abriu a fase e **cai**: o llama está mais longe da distribuição do poeta, não mais
perto. O **M3 da 5H mantém-se de pé** e a troca de modelo continua condicionada.

**Não autoriza retirar o motivo ao passo 20.** O §5 do protocolo escreveu que, se
o J1 **e** o J2 disparassem, o passo 20 — reforço mais `num_predict`, juntos —
ficaria sem motivo. **O J2 não disparou**, logo o passo 20 **conserva o motivo**:
o llama escreve curto a sério. O **segundo** motivo que eu tinha dado ao passo 20
— um tecto a proibir a gama alta — **não existe**: ver o §2.3 corrigido. Fica o
primeiro, que é o da 5I e basta.

**Não autoriza concluir nada sobre o qwen estar mais perto.** O J5 dispara
(§2.2).

**Não mede o valor discriminativo do 3b inteiro.** A contagem de versos é a parte
mecânica da âncora; verso livre, rima, imagem e ornamento não foram tocados, e o
§6.4 do protocolo já separava as duas perguntas.

### O que fica na mesa

1. **Um critério de forma ao nível do conjunto**, e não da amostra: comparar a
   **distribuição** de comprimentos de um braço com a do corpus (foi o que o J2
   fez com o KS) em vez de pontuar cada poema contra um intervalo. É a única
   forma que o §4.3 deixa de pé, e já está implementada.
2. ~~Subir o `num_predict` e remedir~~ — **retirado**, e a razão está no §2.3: o
   tecto é 220 e não 150, e na 5H houve **1 truncatura em 60**. Os modelos param
   sozinhos com vinte palavras de folga, logo subir o orçamento não lhes alarga a
   forma. **Só o passo 20 — com reforço — tem motivo**, porque é o reforço que
   faz o tecto morder (braço B da 5I: 6 em 30).
3. **As três outras vozes com os dois modelos** — passo 16, intocado, e agora com
   uma razão a mais: os pisos do Campos e do ortónimo são os piores de todos
   (§1.1), logo é lá que a âncora de forma mais engana.
4. **O 3b das outras vozes**, se a contagem de versos sair: o §1 diz que os
   intervalos estão errados nas três, mas esta fase só teve potência para derivar
   um substituto para o Caeiro — e o §4.3 diz que nem esse serve.

> **A lição, e é a quarta desta sequência sobre instrumentos.** As três
> anteriores foram sobre **validade** (5C: medir em dados retidos), **resolução**
> (5D: variância no controlo) e **origem** (5E: pontuar o original com o
> critério). Esta é sobre **forma**: um critério por amostra não pode medir uma
> propriedade de um conjunto. O 3b foi escrito para pontuar poemas um a um, e a
> coisa que distingue o Caeiro em comprimento — escrever ora quatro versos ora
> cento e sessenta — não está em nenhum poema seu. Está na obra.
>
> E o corolário prático: **pontuar o original com o critério**, a prescrição da
> 5E, teria apanhado isto em vinte minutos. Foi o que esta fase fez, e bastou
> contar.
