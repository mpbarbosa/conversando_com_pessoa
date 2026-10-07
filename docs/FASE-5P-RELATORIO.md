# Fase 5P — relatório: o passo 28 estava apontado à fronteira errada

**Protocolo:** [`FASE-5P.md`](FASE-5P.md), pré-registado em `5655c5d`.
**Dados:** [`fase-5p/02-resultados.json`](fase-5p/). Não gerou nem pontuou nada.

---

## 0. Os portões, e a prescrição que eles accionam

| | | |
|---|---|---|
| **P1** a discordância vive na fronteira 1/2 | ❌ **não dispara** | a maioria envolve um **0**, não o 1/2 |
| **P2** a posição da fronteira muda uma conclusão | ✅ dispara | mas **só o O3**, e por tautologia — ver o §2 |
| **P3** afrouxar não piora o tecto | ❌ **não dispara** | os reais vão a **100%** no máximo |

**A prescrição da tabela do §3.1, escrita antes de medir:**

> **retirar o passo 28 e reapontar a fronteira 0/1 (passo 12)**

**O passo 28 era meu, nasceu de uma inferência minha que o §1 do protocolo já
tinha enfraquecido, e os dados retiram-no.** E dizem onde está o problema a
sério.

---

## 1. P1 — a discordância está no 0/1, e eu estava a olhar para o outro lado

Sete dos 24 poemas reais não são unânimes entre os três avaliadores:

| poema | R1 | R2 | **eu (R3)** | tipo |
|---|---|---|---|---|
| `poem_2587` | **0** | 1 | 1 | **0-vs-1** |
| `poem_3421` | **0** | **0** | 1 | **0-vs-1** |
| `poem_3436` | **0** | **0** | 1 | **0-vs-1** |
| `poem_3518` | **0** | 2 | 1 | **0-vs-2** |
| `poem_3546` | 1 | 2 | 2 | 1-vs-2 |
| `poem_598` | 1 | 1 | 2 | 1-vs-2 |
| `poem_629` | 1 | 2 | 2 | 1-vs-2 |

**Quatro dos sete envolvem um zero; três são 1-vs-2.** O P1 pedia maioria no
1/2 e não a tem.

### 1.1 E a minha prova da 5O era pior do que eu pensava

No §5 do [relatório da 5O](FASE-5O-RELATORIO.md) listei cinco poemas reais a que
dei **1** como prova de que a fronteira **1/2** era severa de mais. Quatro deles
estão na tabela acima — e em **nenhum** a discordância é 1-vs-2:

- `poem_3421` e `poem_3436`: **R1 e R2 deram 0 aos dois.** Eu fui o único a dar 1.
- `poem_2587`: R1 deu **0**.
- `poem_3518`: R1 deu **0** e R2 deu **2**.

**Não eram casos em que a âncora me fez descer de 2 para 1. Eram casos em que a
âncora fez os outros dois avaliadores descer até 0, e eu fui o generoso.** A
minha leitura do problema estava invertida.

### 1.2 O que o passo 12 já dizia, e desde quando

O passo 12 do [`CONTROLO.md`](CONTROLO.md) está aberto desde a 5G e a sua
evidência é uma **citação do R2**, dada de dentro da cegueira:

> «quando a personificação era incidental e o fecho era deflacionário, dei **1 em
> vez de 0**»

**Isso é a fronteira 0/1.** O protocolo desta fase (§2) escreveu antes de medir
que, se a discordância estivesse aí, o passo 28 estaria apontado à fronteira
errada. Está, e o R2 tinha razão há três fases.

### 1.3 Quanto da discordância é nível e não fronteira

Retirando o **R1** — que **escreveu** a âncora e que a [5N](FASE-5N-RELATORIO.md)
e a [5O](FASE-5O-RELATORIO.md) mediram a pontuar sistematicamente mais baixo — os
não unânimes caem de **7 para 4** (2 de 0-vs-1, 2 de 1-vs-2).

**Três dos sete desacordos são o R1 sozinho**, ou seja ~43% do que parecia
ambiguidade de fronteira é **efeito de nível**. Entre os dois avaliadores que
**não** escreveram a âncora, a discordância é de **4 em 24 (17%)** e está
dividida ao meio entre as duas fronteiras.

---

## 2. P2 — dispara, e a inversão é quase tautológica

Subindo **todos** os 1 a 2 e re-correndo os portões publicados:

| portão | antes | depois | inverte? |
|---|---|---|---|
| **X1** da 5F (reais) | mediana 2,0 · 79% com 2 · **passa** | mediana 2,0 · **100%** · passa | não |
| **O1** da 5O (llama − qwen) | Δ+0,667 · **p=0,0018** · d=14 | Δ+0,600 · p=0,0117 · d=11 | não |
| **O3** da 5O (o meu nível) | 1,792 · **passa** | **2,000** · **falha** | **sim** |
| **N1** da 5N (qwen − 3b) | Δ+0,467 · p=0,0636 | Δ+0,400 · p=0,2101 | não |

**O único portão que inverte é o O3, e inverte porque a própria operação o
quebra:** o O3 testa se o meu nível nos reais cai em [1,30; 1,90], e subir todos
os 1 a 2 põe-no em **2,000**, fora da faixa por construção. Não é prova de que a
fronteira importa; é prova de que afrouxá-la me descalibra.

**E as conclusões que importam sobrevivem — mais fracas.** O O1 mantém-se
significativo mas o p piora **6,5×** (0,0018 → 0,0117) e os pares discordantes
caem de 14 para 11. O N1 piora **3,3×**. **Afrouxar não inverte nada: apaga
sinal.**

---

## 3. P3 — afrouxar põe os poemas reais a 100% no tecto

| grupo | no máximo, antes | **depois** |
|---|---|---|
| **Caeiro real** (24) | 79% | **100%** |
| `llama3.1` (30) | 77% | **87%** |
| `qwen2.5:7b` (30) | 40% | 57% |
| `qwen2.5:3b` (30) | 13% | 37% |

O P3 pedia que os dois primeiros ficassem abaixo de 85% e **nenhum fica**. Com os
poemas autênticos todos no máximo, **o critério perde qualquer capacidade de
situar o gerado em relação ao original** — que é exactamente o que a
[5O §3.2](FASE-5O-RELATORIO.md) diagnosticou como o problema actual e que o §1
do protocolo previu.

---

## 4. Uma segunda afirmação minha a corrigir

O §2.2 do [relatório da 5O](FASE-5O-RELATORIO.md) escreveu que a crítica central
da [5E](FASE-5E-RELATORIO.md) — a âncora antiga dava **0** a 7 de 20 poemas
autênticos (35%) — «está resolvida na nova para os três avaliadores, e para mim
completamente».

**«Para mim completamente» é verdade. «Para os três avaliadores» não é:**

| | zeros dados a poemas **autênticos** de Caeiro |
|---|---|
| âncora **antiga** (5E) | 7 de 20 — **35%** |
| âncora nova, **R1** | **4 de 24 — 17%** |
| âncora nova, **R2** | **2 de 24 — 8%** |
| âncora nova, **eu** | 0 de 24 — 0% |

A âncora nova **melhorou** o defeito da 5E — de 35% para 8–17% — e **não o
eliminou**. Sob o R1, um em cada seis poemas autênticos de Caeiro continua a
levar zero no critério que mede ser Caeiro. Os quatro poemas são os mesmos que o
§1 lista: `poem_2587`, `poem_3421`, `poem_3436`, `poem_3518`.

**É este o defeito que sobra, e é no 0/1.**

---

## 5. O que isto autoriza, e o que não

**Retira o passo 28**, pela prescrição pré-escrita e por três razões
independentes: a discordância não está no 1/2 (§1), afrouxar não inverte
conclusões mas apaga sinal (§2), e põe os poemas reais a 100% no tecto (§3).

**Reaponta ao passo 12**, que estava certo desde a 5G e cuja evidência era uma
citação que eu não li com atenção suficiente. O defeito a corrigir é **a âncora
dar 0 a poemas autênticos de Caeiro** — 17% deles sob o avaliador mais severo —
e a fronteira a decidir é **0/1**, não 1/2.

**Não autoriza mexer na âncora agora.** Uma alteração ao 0/1 é uma fase própria,
com **validação retida**, como a 5F fez — e com a lição da 5L sobre o preço da
quebra de compatibilidade, que aqui seria maior: o 3a′ é o critério de sete fases.

**Não resolve o tecto.** O §3 confirma que o caminho não é a mesma escala mais
permissiva. Se é preciso separar o llama do original, é preciso **mais níveis** ou
outro desfecho — passo 27, e a pista continua a ser a **cauda** (4 zeros contra 0)
e não o topo.

**Não mede a fronteira nos itens gerados com três avaliadores.** Só os 24 reais
têm três leituras. Nos gerados a sensibilidade do §2 usa a minha leitura só.

### O que fica na mesa

1. **O passo 12, reapontado e com dados:** decidir a fronteira **0/1** pelos
   casos difíceis, e validar em dados retidos. Os quatro poemas do §4 são o
   conjunto de treino natural — e **os casos difíceis a escrever são poemas do
   próprio poeta**, o que é a situação que a 5E prescreveu e que nenhuma fase
   ainda usou para o 0/1.
2. **Passo 27** (resolução no tecto), intocado.
3. **Passo 25**, que continua a ser o que bloqueia a decisão da troca.
4. **Um aviso de método, para mim:** a discordância de nível entre avaliadores
   (§1.3) contamina qualquer diagnóstico de fronteira. Medir ambiguidade de
   fronteira com avaliadores de níveis diferentes mistura duas coisas, e a
   separação barata é **excluir quem escreveu a âncora**.

> **A lição, e é sobre ler a evidência que já existe.** Propus o passo 28 a
> partir de cinco itens meus, sem olhar para as notas que **outros dois
> avaliadores** já tinham dado aos **mesmos** poemas — notas que estavam no
> repositório desde a 5F e que dizem o contrário. A informação que refutava a
> minha hipótese estava a dois ficheiros de distância, commitada, e eu escrevi o
> passo sem a abrir.
>
> **O custo de a ter aberto era um `json.load`. O custo de não a ter aberto foi
> uma fase inteira** — e, se não tivesse pré-registado a tabela de prescrições,
> seria uma alteração à âncora de sete fases na direcção errada.
