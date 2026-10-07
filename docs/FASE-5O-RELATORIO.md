# Fase 5O — relatório: o +0,700 replica, e o 3a′ bate no tecto

**Protocolo:** [`FASE-5O.md`](FASE-5O.md), pré-registado em `0c324f8`.
**Dados:** [`fase-5o/02-pontuacoes.json`](fase-5o/) (às cegas, commitadas antes
de abrir a chave) · [`03-resultados.json`](fase-5o/)

---

## 0. Os portões

| | | |
|---|---|---|
| **O1** a direcção do +0,700 replica | ✅ **dispara** | Δ=**+0,667**, p=0,0018, **13 de 14** pares a favor do llama |
| **O2** a magnitude é compatível | ✅ **dispara** | o meu IC95% **[+0,33; +1,00] contém +0,700** |
| **O3** o meu nível está calibrado | ✅ dispara | 1,792 nos reais, dentro da faixa [1,30; 1,90] |
| **O4** a âncora premeia o original | ✅ dispara | mediana **2,0**, **19 de 24** (79%) com a nota máxima |
| **O5** inconclusivo por potência | ❌ não dispara | d=14 |

**Em uma frase.** O número em que a troca de modelo assenta **sobrevive a um
avaliador de fora da sessão que o produziu** — e a fase devolve uma coisa que
ninguém tinha medido: no critério 3a′, **o `llama3.1:8b` não se distingue de
Pessoa autêntico**. Com uma ressalva grande, que é o §3.

---

## 1. O1 e O2 — a replicação

| | média 3a′ |
|---|---|
| **L** = `llama3.1:8b` (30, cegas, **esta fase**) | **1,633** |
| **Q** = `qwen2.5:7b` (30, cegas, da [5N](FASE-5N-RELATORIO.md)) | **0,967** |
| **Δ (L − Q)** | **+0,667** · IC95% **[+0,333; +1,000]** · p=**0,0018** · d=14 (**13 L / 1 Q**) |

**A 5H publicou +0,700. Eu obtive +0,667, e o meu IC contém o valor dela.** A
direcção replica (O1) e a magnitude é compatível (O2).

**E replica contra o vento.** O §4.1 declarou, antes de medir, que as minhas notas
do braço Q foram dadas contra um fundo de `qwen2.5:3b` e as do L contra um fundo
de **Pessoa autêntico** — e que se o fundo mexesse na minha régua, enviesaria o Δ
para **baixo**. O Δ saiu ligeiramente **abaixo** de 0,700, que é o sinal
compatível com esse enviesamento, e ainda assim passou os dois portões.

Treze pares discordantes em catorze a favor do llama. **Isto não é um resultado
frágil**, e o §3.1 do protocolo tinha nomeado o desfecho incómodo — direcção
certa, magnitude menor — que **não** se materializou.

---

## 2. O3 e O4 — o nível e a âncora, por um terceiro avaliador

### 2.1 O meu nível está calibrado, e é consistentemente o mais alto dos três

Nos **24 poemas reais** de Caeiro retidos da [5F](FASE-5F.md):

| | média | 0 / 1 / 2 | com nota 2 |
|---|---|---|---|
| **R1** da 5F *(escreveu a âncora)* | 1,50 | 4 / 4 / 16 | 16/24 — 67% |
| **R2** da 5F | 1,71 | 2 / 3 / 19 | 19/24 — 79% |
| **eu**, nesta fase | **1,792** | **0 / 5 / 19** | 19/24 — 79% |

O O3 dispara: 1,792 cai na faixa pré-registada [1,30; 1,90], que era o intervalo
dos dois avaliadores da 5F com folga de 0,20.

**Mas a ordenação da [5N §3](FASE-5N-RELATORIO.md) repete-se:** eu pontuo acima
de R1 nos dois conjuntos de dados, e o limite inferior do meu IC (1,625) fica
**acima** da média do R1 (1,50). O efeito de avaliador é real e sistemático; o
que o O3 estabelece é que está **dentro da tolerância** que eu fixei antes de
medir, logo o Δ de **+0,400 da 5N** não foi medido numa escala inflacionada a
ponto de o invalidar.

### 2.2 A condição de aceitação da âncora replica, e mais forte

O **X1 da 5F** pedia mediana ≥ 1 e ≥ 30% com nota 2 nos 24 retidos. Sob a minha
leitura: **mediana 2,0 e 79%**. A âncora que sete fases usam **só tinha sido
aceite por uma sessão**; passa agora com um terceiro avaliador e com margem
larga.

E **zero zeros** nos 24 autênticos, contra 4 do R1 e 2 do R2. A crítica central
da [5E](FASE-5E-RELATORIO.md) à âncora **antiga** — que dava zero a 7 de 20
poemas autênticos — está resolvida na nova para os três avaliadores, e para mim
completamente.

---

## 3. O número novo, e o tecto que o limita

### 3.1 No 3a′, o llama não se distingue de Pessoa autêntico

| | 0 / 1 / 2 | média | **no tecto (nota 2)** |
|---|---|---|---|
| **Caeiro real** (24) | 0 / 5 / 19 | 1,792 | **79%** |
| **`llama3.1:8b`** (30) | **4** / 3 / 23 | 1,633 | **77%** |
| `qwen2.5:7b` (30, da 5N) | 13 / 5 / 12 | 0,967 | 40% |

**AUC(real > llama) = 0,526** — indistinguível do acaso.

Para contexto: a [5F §2](FASE-5F-RELATORIO.md) mediu
**AUC(real > qwen) = 0,851** (p=0,0003). O contraste aqui é com o **llama** e não
com o qwen, logo **não é uma replicação** — é um número novo, como o §3.2 do
protocolo declarou. E o que ele diz é que **a troca de modelo não melhora o 3a′:
fecha-o**.

### 3.2 Mas 78% da folha está no tecto, e isso é o espelho da 5B

**42 dos 54 itens levaram 2.** O critério 3a′ está **saturado no máximo** nesta
folha.

> **É o problema da [5B](FASE-5B-RELATORIO.md) ao contrário.** Ali o 3a estava
> saturado no **chão** — 22 de 30 pares empatados em 0–0 — e a ablação ficou
> inconclusiva por construção. Aqui o 3a′ está saturado no **tecto**, e uma
> AUC de 0,526 é ambígua entre **«são indistinguíveis»** e **«a régua acabou»**.
>
> A lição da resolução (5D) reaparece na outra ponta, e o diagnóstico é o mesmo:
> **um desfecho sem variância num dos grupos não separa nada.**

**O que a saturação não esconde.** Há um sinal que a média apanha e a AUC quase
não: o llama tem **4 zeros** e os poemas reais têm **zero**. Nenhum dos 24
autênticos acaba além da coisa; **4 dos 30 do llama acabam**. É uma cauda de
falhas que o original não tem, e é a diferença que sobra quando os topos
coincidem.

**Logo a leitura honesta é dupla:** no topo da escala o llama iguala o original
(77% contra 79%), e tem uma cauda de falha que o original não tem. Dizer «não se
distingue» é verdade **neste instrumento** e o instrumento já não tem resolução
onde a diferença está.

---

## 4. Uma correcção a uma afirmação minha, encontrada a pontuar

O §2.3 da [5N](FASE-5N.md) escreveu, ao listar a contaminação: «só vi H01, que é
L mas **não entra nesta fase**». Entrava **nesta**, que é a seguinte — o `H01` é
o item **O42** desta folha, e **reconheci-o** a pontuar.

Dei-lhe **0**, que é **contra** a direcção do meu viés (esperava que o braço L
fosse bom), logo o erro não favoreceu a hipótese. Mas a afirmação estava errada e
a lição é estreita e útil: **uma declaração de contaminação tem de dizer o que o
item é, não em que fase não vai entrar** — eu não sabia, ao escrevê-la, que fase
viria a seguir.

É 1 item em 30 do braço L. Excluí-lo faria o Δ subir, não descer, logo o primário
fica como está.

---

## 5. O que isto autoriza, e o que não

**Autoriza tratar o +0,700 da 5H como replicado.** Direcção, magnitude e
significância, por um avaliador de outra sessão, às cegas, contra um
enviesamento declarado em sentido contrário. **É a verificação mais forte que
qualquer número desta sequência tem.**

**Autoriza tratar a âncora 3a′ da 5F como aceite por três avaliadores**, e não
por um (O4).

**Não autoriza dizer que o llama escreve como Caeiro.** Autoriza dizer que **no
critério 3a′, e com a resolução que ele tem**, não se distingue — o que é
diferente, e o §3.2 diz porquê. Rima, forma, dicção e as outras três vozes não
entram aqui.

**Não desbloqueia a troca de modelo.** Falta o conteúdo das **outras três vozes**,
que é o passo 25 e continua a exigir uma âncora por voz. O que esta fase muda é
que o lado do **Caeiro** está agora medido com três avaliadores em vez de dois, e
o custo de forma que a [5M](FASE-5M-RELATORIO.md) encontrou é **só do Caeiro**.
**A troca está mais perto de ser decidível do que em qualquer ponto anterior, e
não é decidível aqui.**

**Não tem segundo avaliador**, como a 5N. A diferença é que aqui o objecto é o
**efeito de avaliador**, e o O3 e o O4 medem-no contra dois avaliadores
anteriores em vez de o assumirem.

### O que fica na mesa

1. **Um desfecho com resolução no tecto**, que é novo e é o preço do progresso: o
   3a′ foi recalibrado na 5F para deixar de saturar no chão, e com o llama
   saturou no topo. Para separar o llama do original **neste** critério é preciso
   uma escala mais fina, ou um desfecho diferente — e a pista está no §3.2: a
   diferença que sobra é a **cauda de falhas** (4 contra 0), não o topo.
2. **Passo 25**, intocado, e é o que bloqueia a decisão.
3. **Passo 24** (corrigir as personas), que continua barato e com predição
   registada.
4. **A fronteira 1/2**, pela quarta fase seguida — e aqui o resultado é
   categórico. Dei **1** a oito itens. Cinco são **Pessoa autêntico**, e são
   **exactamente os cinco** poemas reais que não levaram o máximo:

   | item | poema | o que me fez descer de 2 |
   |---|---|---|
   | `O04` | `poem_2587` | «uma ninfa pequena», «um ser interior longínquo» — ditos para os colapsar em corpo |
   | `O28` | `poem_3436` | «a nossa comum divindade» |
   | `O41` | `poem_3518` | «a Natureza é bela e antiga» — atribui beleza, o que o `poem_2669` nega |
   | `O43` | `poem_1469` | «aquela grande tristeza que ele nunca disse bem que tinha» |
   | `O49` | `poem_3421` | «o mesmo sorriso antigo» das flores |

   **Os cinco casos em que a âncora me fez descer da nota máxima são os cinco
   poemas do próprio poeta.** É o argumento mais forte da sequência para a
   fronteira 1/2 estar severa de mais — o passo 12 do
   [`CONTROLO.md`](CONTROLO.md), em aberto desde a 5G.

   E o simétrico: **os quatro zeros são todos do llama** (`O13`, `O21`, `O26`,
   `O42`). Nenhum poema autêntico acaba além da coisa; quatro dos trinta do
   llama acabam.

> **A lição, e é sobre o que replicar significa.** A sequência mediu dez fases
> com avaliadores da mesma sessão que escreveu os protocolos, e a 5N levantou a
> dúvida certa: quanto do resultado é do gerador e quanto é do leitor? A resposta,
> medida: **o nível é do leitor — por um factor até dois — e a diferença
> emparelhada é do gerador.** O +0,700 sobreviveu porque era um Δ; se a
> sequência tivesse construído as suas conclusões sobre **níveis** em vez de
> **diferenças**, metade delas cairia aqui.
