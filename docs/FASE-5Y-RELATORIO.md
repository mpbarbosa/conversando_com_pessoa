# Fase 5Y — auditoria: o modelo em produção sobrevive, a célula mais citada da sequência não

**[Passo 42](CONTROLO.md), aberto pela emenda da
[5X](FASE-5X-RELATORIO.md).**
**Dados:** [`fase-5y/01-auditoria.json`](fase-5y/), de
[`auditar.py`](fase-5y/auditar.py). **Nenhuma geração nova.**

> **Sem protocolo pré-registado, e a razão está declarada.** Não há medição nova,
> não há portão a escrever, e a pergunta nasceu dos dados. **A protecção contra
> escolher o resultado que me convém não é um portão: é cobertura** — a auditoria
> corre as **nove** fases emparelhadas e reporta todas as células e todas as
> conclusões que consegue recalcular, **incluindo as que sobrevivem**.

---

## 1. O mecanismo, e não é um defeito

O `Pipeline._repetir_sem` é deliberado e documentado: quando o modelo plagia, a
repetição **tira do contexto os poemas de que ele copiou** e deixa entrar os
seguintes da recuperação. Foi desenhado contra um ciclo observado a correr — «à
pergunta *você conhece o senhor fernando pessoa?* a primeira tentativa copiou 9
de 14 versos do `poem_1164` … a repetição, com o mesmo contexto, voltou **ao
mesmo poema**».

**É bom produto e é mau para uma fase emparelhada.** O prompt final diverge
entre braços sempre que os braços plagiarem de forma diferente — e isso é *a
jusante* do tratamento. **Não é um confundidor a declarar: é um mediador.**

---

## 2. Quanto, em cada fase

| fase | células | braços | tentativas ≠ | **prompt ≠** | % | |
|---|---|---|---|---|---|---|
| 5B | 30 | 2 | 6 | **7** | 23,3% | +1 por plágio diferente |
| **5G** | 30 | 2 | 12 | **12** | **40,0%** | |
| **5H** | 30 | 2 | 5 | **5** | 16,7% | |
| 5I | 30 | 2 | 2 | 2 | 6,7% | |
| **5M** | 90 | 2 | 17 | **17** | 18,9% | |
| 5N | 30 | 1 | 0 | 0 | 0% | um braço só |
| 5U | 60 | 2 | 15 | **7** | 11,7% | +5 por plágio diferente |
| 5W | 20 | 3 | 7 | **2** | 10,0% | |
| 5X | 20 | 3 | 5 | **3** | 15,0% | |

**Duas leituras que a emenda da 5X não tinha:**

1. **Repetir não implica prompt diferente.** Na 5U há 15 células com tentativas
   desiguais e só 7 com prompt divergente — porque **a truncatura também causa
   repetição**, e aí `copiados` fica vazio e `_repetir_sem` devolve o mesmo
   contexto.
2. **E prompt diferente não implica tentativas desiguais.** Na 5U há **5**
   células, e na 5B **1**, em que os braços repetiram o **mesmo** número de vezes
   e ficaram com prompts diferentes: **plagiaram poemas diferentes, logo
   removeram poemas diferentes**. A emenda da 5X dizia «todas, sem excepção» com
   base em duas fases; **com nove, a afirmação é falsa**.

---

## 3. O que decidiu o modelo em produção: **sobrevive**

A [5H](FASE-5H-RELATORIO.md) deu `+0,700` no conteúdo do Caeiro (âncora 3a′,
leitura conjunta de dois avaliadores cegos), e foi essa diferença que, replicada
a `+0,667` na [5O](FASE-5O-RELATORIO.md), levou à troca de modelo da
[5S](FASE-5S-RELATORIO.md) — a que está em produção.

| | n | delta médio | IC95 | sinais L/Q | p binomial |
|---|---|---|---|---|---|
| todas | 30 | **+0,7000** | [+0,417, +0,983] | 19/2 | 0,00022 |
| **limpas** | **25** | **+0,6600** | **[+0,340, +0,960]** | **16/2** | **0,00131** |

**Sobrevive com folga.** O IC continua a excluir zero, o teste de sinais continua
a 16 contra 2, e o p sobe de 0,0002 para 0,0013 — as duas leituras decidem o
mesmo.

> **E há uma convergência que melhora.** O delta nas células limpas é **+0,660**,
> e o terceiro avaliador cego da 5O, noutra sessão e sem ver nada disto, produziu
> **+0,667**. A contaminação estava a **inflacionar** ligeiramente o número
> original, e o valor limpo é quase exactamente o da replicação independente.

---

## 4. O que não sobrevive: a célula mais citada da sequência

A [5M](FASE-5M-RELATORIO.md) publicou que `reis/L` era **«a única célula de toda
a sequência a reproduzir a distribuição de um poeta»** — KS 0,1956 contra um
p95 do nulo de 0,2046.

| célula | n | KS | p95 | dentro? | n | KS | p95 | dentro? | |
|---|---|---|---|---|---|---|---|---|---|
| campos/Q | 30 | 0,3143 | 0,2163 | não | 24 | 0,3143 | 0,2398 | não | |
| campos/L | 30 | 0,2803 | 0,2034 | não | 24 | 0,2653 | 0,2364 | não | |
| reis/Q | 30 | 0,3756 | 0,2089 | não | 24 | 0,4411 | 0,2289 | não | |
| **reis/L** | 30 | **0,1956** | 0,2046 | **SIM** | 24 | **0,2333** | 0,2294 | **não** | **inverte** |
| ortonimo/Q | 30 | 0,3752 | 0,2104 | não | 25 | 0,3685 | 0,2322 | não | |
| ortonimo/L | 30 | 0,3286 | 0,2137 | não | 25 | 0,3721 | 0,2337 | não | |

**Inverte, e era a única das seis que podia inverter** — porque era a única
dentro do nulo, e estava dentro por **0,009**. Nas células limpas fica **fora por
0,004**.

**A honestidade exige dizer que nunca foi um resultado robusto.** Uma margem de
0,009 num KS calculado sobre 30 amostras não suporta a frase «a única célula de
toda a sequência a reproduzir um poeta», e eu repeti-a em quatro relatórios.

### 4.1 E uma das três pernas da convergência llama–Reis cai

Eu declarei a afinidade llama–Reis como **o achado confirmado por três
instrumentos independentes**:

| medição | fase | estado |
|---|---|---|
| distribuição de comprimento (`reis/L` dentro do nulo) | 5M | ❌ **cai** nesta auditoria |
| predição registada antes de correr | 5K | ✅ mantém-se |
| roteamento (0,9 no Reis contra 0,5 do qwen) | 5S | ✅ mantém-se |

**Passa de três para duas**, e as duas que ficam são de naturezas diferentes
(uma predição e um classificador), o que ainda é convergência — mas «a mais forte
da sequência» era uma frase construída sobre a perna que caiu.

---

## 5. O que isto decide

**Não muda o produto.** A troca de modelo sobrevive à auditoria, e era a única
decisão de produto que dependia de uma fase emparelhada.

**Não invalida as fases.** O que invalida é **uma célula numa delas** — a que
estava na fronteira. As restantes cinco células da 5M não mexem, e os nulos das
fases com instrumento já rejeitado (5B, 5G) não mudam o que elas concluíram.

**E muda como se desenha a próxima.** A análise primária de uma fase emparelhada
não pode ser sobre a **saída final**, porque essa já passou pelo mediador. Tem de
ser sobre a **primeira tentativa**, cujo prompt é idêntico entre braços por
construção — e o `Turno` **não a guarda**.

### O que fica na mesa

1. **Registar as tentativas, e não só a última.** É o que torna possível a
   análise primária correcta, e é pequeno: o `responder` já tem cada tentativa na
   mão. **É o próximo passo e é de produto, não de medição.**
2. **O passo 40 fica em espera por isto**, e não por capricho: `repeat_penalty =
   0.9` é precisamente a manipulação que mais provavelmente aumenta o plágio, logo
   a que mais contamina — as 3 células em 20 da 5X deixariam de ser 3.
3. **A 5G, com 40% de contaminação**, é a fase mais afectada da sequência. O seu
   instrumento já estava rejeitado, logo não há conclusão a reverter; mas se
   alguém a quiser reaproveitar, é o número que tem de saber.

> **A lição, e é a décima primeira.** As três anteriores são sobre o desenho —
> **onde** medir, **com que resolução**, e **verificar que «a mesma coisa» é a
> mesma coisa**. Esta é sobre o que se mede **no fim**: **o desfecho de um turno
> não é a saída do tratamento; é a saída do tratamento mais tudo o que o sistema
> fez para a corrigir.**
>
> O `_repetir_sem` é bom produto — foi desenhado contra um ciclo real e observado.
> E é por ser bom produto que estraga a medição: **quanto melhor o sistema se
> auto-corrige, menos a saída final revela do que o tratamento fez.** A fase que
> quer medir o tratamento tem de olhar para antes da correcção.
>
> E um corolário sobre a própria emenda que abriu esta auditoria: eu escrevi
> **«todas, sem excepção»** com base em duas fases. Com nove, há **seis células**
> em que os braços repetiram o mesmo número de vezes e ficaram com prompts
> diferentes. **Uma regularidade confirmada em duas fases é uma hipótese, não uma
> regra** — e eu acabara de aprender isso sobre as razões dos juízes na
> [5U](FASE-5U-RELATORIO.md).
