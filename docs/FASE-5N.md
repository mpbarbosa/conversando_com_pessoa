# Fase 5N — O `qwen2.5:3b`: capacidade ou família?

**Passo 18** da tabela do [`CONTROLO.md`](CONTROLO.md) §6. Pré-registada em
2026-10-07, antes de qualquer amostra desta fase existir.

---

## 1. A pergunta, e porque é que o 3b a responde

A [5H](FASE-5H-RELATORIO.md) mediu **+0,700** em 3a′ para o `llama3.1:8b` sobre o
`qwen2.5:7b` (IC95% [+0,42; +0,98], p=0,0002, 19 pares contra 2). Há duas
explicações e a fase não as separou:

- **capacidade** — o modelo maior ganha;
- **família** — o `llama3.1` tem algo que o `qwen2.5` não tem.

Os tamanhos reais, lidos do Ollama, tornam a pergunta aguda:

| modelo | parâmetros | salto de capacidade |
|---|---|---|
| `qwen2.5:3b-instruct-q4_K_M` | **3,1B** | — |
| `qwen2.5:7b-instruct-q4_K_M` | **7,6B** | **+145%** sobre o 3b |
| `llama3.1:8b-instruct-q4_K_M` | **8,0B** | **+5%** sobre o 7b |

**O ganho de 0,700 da 5H veio com +5% de parâmetros.** Se um salto de **+145%**
dentro da **mesma família** render muito menos que 0,700, a capacidade não pode
explicar a 5H — e o que sobra é família. É um argumento de **dose-resposta**, e é
o desenho desta fase.

---

## 2. Desenho

### 2.1 Braços, e porque é que só um se gera

| braço | modelo | origem |
|---|---|---|
| **T** | `qwen2.5:3b-instruct-q4_K_M` | **gerado aqui** — 30 amostras |
| **Q** | `qwen2.5:7b-instruct-q4_K_M` | **reutilizado da [5H](FASE-5H-RELATORIO.md)** |

Voz **Caeiro**, as 10 perguntas do banco dourado (`q01`–`q10`), **3 repetições**,
e **as mesmas sementes da 5H** (`20261006 + 100·r + i`), para que o
emparelhamento `(pergunta, repetição)` seja exacto e seed-a-seed.

O braço Q não se regera: existe, com o mesmo harness, as mesmas opções e as
mesmas perguntas. **Só o modelo muda.**

### 2.2 Desfecho primário: 3a′

A âncora da [5F §2](FASE-5F.md), **inalterada** — é a única que mede conteúdo e
existe para o Caeiro. Emparelhado por `(pergunta, repetição)`.

**O 3b vai como secundário e com uma ressalva que o torna incomparável com a
5H:** a [5L](FASE-5L.md) retirou-lhe a cláusula de comprimento em 2026-10-06.
As notas de 3b desta fase usam a âncora **nova** e **não** se comparam com as da
5H; só a comparação **interna** T contra Q é válida.

### 2.3 Cegueira, e a parte dela que está comprometida

As 60 amostras vão embaralhadas com semente fixa e identificadores opacos
`N01`–`N60`, mostrando só pergunta e texto; o mapa vai para `01-chave.json` e não
se abre antes de as pontuações estarem commitadas. Duas amostras da mesma
pergunta nunca ficam adjacentes.

> **Declaração de contaminação.** Nesta sessão, antes de abrir esta fase, imprimi
> texto de **5 das 30 amostras do braço Q** ao inspeccionar o esquema dos dados e
> as truncaturas da 5H:
>
> | item | o que vi |
> |---|---|
> | `Q q01 r0` | **o texto quase todo** (~700 caracteres) |
> | `Q q06 r2` · `Q q07 r0` · `Q q07 r1` · `Q q07 r2` | **a última linha** |
>
> Posso reconhecê-las, e reconhecê-las é saber que são do **7b** — o braço que
> espero ser melhor. O viés tem **direcção conhecida**: inflaciona o Δ e
> favorece o portão N1.
>
> **Por isso o primário exclui esses 5 pares** e a análise com os 30 vai como
> sensibilidade. Fica escrito antes de pontuar, com os ids nomeados, para não ser
> uma escolha posterior.

### 2.4 Estatística

Sem `scipy`, como desde a [Fase 3B](FASE-3B.md): binomial bilateral sobre pares
discordantes, IC95% por bootstrap de 10 000 sobre as diferenças emparelhadas, e
κ linear para a concordância. Reutiliza `fase-5i/analisar.py`.

---

## 3. Portões

| | nome | dispara se | leitura, escrita agora |
|---|---|---|---|
| **N1** | **a capacidade tem tracção** | em 3a′, Δ(Q − T) com binomial **p ≤ 0,05** e IC95% a excluir 0, a favor do **Q** | dentro da família, o modelo maior ganha. Então parte do +0,700 da 5H **pode** ser capacidade, e o N2 diz quanto |
| **N2** | **a capacidade não explica a 5H** | Δ(Q − T) **< 0,700**, isto é, menos do que a 5H obteve com **+5%** de parâmetros contra os **+145%** aqui | o ganho da 5H **não é de capacidade**. É o argumento de dose-resposta e é o desfecho que importa |
| **N3** | **inconclusivo por potência** | pares discordantes **d < 8** em 3a′ | nada se decide. Precedente: o G4 da [5B](FASE-5B-RELATORIO.md) e o I3 da [5I](FASE-5I.md) |
| **N4** | **o 3b também perde na forma** | KS do braço T ao corpus do Caeiro **>** os 0,288 do braço Q | secundário e **mecânico**, sem avaliador. Usa o nulo por voz da [5K](FASE-5K-RELATORIO.md) |

### 3.1 O N2 é o portão que importa, e tem uma armadilha

Se o **N1 não disparar** (o 3b iguala o 7b), o N2 passa trivialmente e a
conclusão é forte: 145% de capacidade não compram nada, logo 5% não compraram
0,700.

Se o **N1 disparar**, o N2 ainda decide — mas então a leitura é mais fina: a
capacidade tem tracção **e** é insuficiente, e a parte do +0,700 que sobra por
explicar é `0,700 − Δ(Q−T)`. **Escrevo agora que não vou tratar essa subtracção
como uma decomposição causal**: as duas comparações não são a mesma escala e não
há garantia de linearidade. É uma ordem de grandeza, não uma partição.

### 3.2 O que esta fase não pode concluir

- **Não mede o `llama3.1:3b`**, que não está instalado. Logo não separa
  capacidade de família **dentro** da família llama, e a conclusão «é família»
  significa «não é capacidade **na família qwen**, nesta gama».
- **Não revisita o +0,700.** Esse número é da 5H e não se remede aqui.
- **Não decide a troca de modelo**, que continua bloqueada no passo 25 (uma
  âncora 3a′ por voz).
- **Não compara 3b com a 5H** (§2.2).

---

## 4. Ameaças

### 4.1 A contaminação da cegueira, que é a principal

Está no §2.3, com os ids nomeados e a direcção do viés declarada. A mitigação é
o primário excluir os 5 pares.

### 4.2 Sou o terceiro avaliador dos mesmos itens, e isso é um bónus

O braço Q já foi pontuado **duas vezes** — por R1 e R2 da 5H, ambos cegos. Ao
repontuá-lo aqui, às cegas e noutra sessão, produzo uma **terceira leitura
independente** dos mesmos 30 itens com a **mesma** âncora.

**Declarado como medição-bónus e não como portão:** reporto κ linear e
concordância exacta contra R1 e contra R2 da 5H. É a primeira verificação de
**reprodutibilidade entre sessões** da sequência — todas as outras compararam
dois avaliadores na **mesma** sessão, o que a [5B](FASE-5B-RELATORIO.md) já
nomeou como ameaça de **erro correlacionado**.

Se a minha leitura divergir muito das duas, isso é um resultado **sobre o
instrumento** e tem de ser dito mesmo que não mude o veredicto da fase.

### 4.3 O 3b pode falhar por razões que não são conteúdo

Um modelo de 3,1B pode produzir texto que não é verso, ou que sai de português,
e aí o 3a′ mede ruído e não conteúdo. **Verificação declarada:** reportar os
critérios automáticos (c1 verso, c2 português, c5 plágio, truncatura) por braço
**antes** de ler o 3a′. Se o braço T falhar o c1 ou o c2 com frequência
materialmente maior, a comparação de 3a′ lê-se como contaminada por qualidade de
superfície — e isso é dito, não contornado.

### 4.4 O 3b é mais rápido, e isso não entra em nenhum portão

~1,9 GB contra 4,7 GB: a geração vai ser bem mais rápida. É uma vantagem real do
3b que **esta fase não mede** e que não pertence a nenhum portão aqui — se o 3b
empatar em qualidade, a velocidade passa a argumento, e isso fica para quem
decidir a troca.

---

## 5. Lista de verificação

```
[ ] A1  gerar 30 amostras do braco T (qwen2.5:3b), sementes da 5H
[ ] A2  automaticos por braco (§4.3) ANTES de pontuar
[ ] A3  folha embaralhada N01-N60 + 01-chave.json fechada
[ ] B1  pontuar 3a' e 3b as cegas, com razao por amostra
[ ] B2  N1/N2/N3 em 3a', primario SEM os 5 pares contaminados
[ ] B3  N4 a forma, mecanico, contra o nulo da 5K
[ ] B4  bonus: kappa contra R1 e R2 da 5H nos 30 itens do braco Q
[ ] C1  portoes -> 03-resultados.json
[ ] C2  relatorio FASE-5N-RELATORIO.md
[ ] C3  CONTROLO.md: fase e passo 18
```

**Sessões paralelas:** verificado com `ListAgents` e `list_sessions` — nenhuma
outra sessão neste repositório. `git add` com ficheiros nomeados.
