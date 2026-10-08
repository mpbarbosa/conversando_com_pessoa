# Fase 5W — Fazer o ortónimo rimar

**[Passo 37](CONTROLO.md), aberto pela [5V](FASE-5V-RELATORIO.md).**
Pré-registada em 2026-10-08. **É a primeira intervenção desta sequência com um
desfecho mecânico e já medido** — e a primeira em que o objectivo é melhorar o
poema, e não rejeitar o mau.

---

## 1. O que está medido e entra como dado

| | | fase |
|---|---|---|
| o ortónimo **real** rima | **0,7769** dos poemas | [5V §2](FASE-5V-RELATORIO.md) |
| o ortónimo **gerado** rima | **0,2167** — que **é** o seu nulo de permutação | [5V §3](FASE-5V-RELATORIO.md) |
| a persona manda rimar | «**Metro regular e rima.** Quadras ou quintilhas.» | `src/voices.py` |
| o Reis manda «sem rima» e **cumpre** | 0,1992 real, 0,1667 gerado, IC a conter zero | 5V §3.1 |
| mexer na instrução já deu saldo **negativo** | uma vez | [5I](FASE-5I-RELATORIO.md) |

**A instrução existe, é explícita, e é ignorada por completo.** Esta fase
pergunta se é alcançável pelo prompt.

### 1.1 O esquema, derivado do corpus e não adivinhado

Nas 3744 janelas de quatro versos do ortónimo, entre as que mostram **algum**
esquema:

| esquema | janelas | |
|---|---|---|
| **XAXA** (só os pares rimam) | 314 | **8,4%** |
| **ABAB** | 173 | 4,6% |
| AABB | 33 | 0,9% |
| ABBA | 29 | 0,8% |

**A rima alternada é ~8× mais frequente que a emparelhada ou a interpolada.** O
absoluto (85,3% sem esquema) **não é interpretável**: as janelas de quatro não
se alinham com as estrofes reais, que é a limitação que a [5V §2.3](FASE-5V.md)
declarou ao deixar o esquema rimático de fora.

> **E note-se o que isto é e não é.** O **tratamento** é derivado do corpus; o
> **desfecho** é o detector que a 5V calibrou contra as quatro poéticas, antes
> desta fase existir. Derivar o tratamento do corpus é o contrário do erro da
> [5E](FASE-5E.md) — que foi derivar o **critério** da persona que estava a ser
> tratada.

---

## 2. Os três braços

Muda-se **só** o campo `forma` da persona do ortónimo, e **só** a parte da rima.
O resto — «Quadras ou quintilhas», a dicção, e **«Entre doze e vinte versos»** —
fica **idêntico nos três braços**, byte a byte.

> **O intervalo de versos não se toca nesta fase**, apesar de ser um dos quatro
> que a [5L](FASE-5L.md) invalidou (o [passo 24](CONTROLO.md)). Mexer nele aqui
> confundiria duas intervenções.

| braço | `forma`, na parte da rima |
|---|---|
| **C** | «Metro regular e rima.» — **como está em produção** |
| **R** | **directiva**: acrescenta «Rima alternada: em cada quadra, o segundo verso rima com o quarto. A rima é obrigatória, não decorativa.» |
| **X** | **exemplo**: o de R, mais um exemplo esquemático a mostrar dois pares de terminações que rimam |

### 2.1 A predição registada: X > R

A [5U §1.3](FASE-5U-RELATORIO.md) deixou registada a hipótese da **escorva**: o
bloco de língua traz três exemplos com clítico e o braço completo usava **54**
clíticos contra **38** do ablado (IC a conter zero, logo hipótese). **Esta fase
testa-a num desfecho com eventos**: se exemplos escorvam, o braço **X** bate o
**R**. Está escrito antes de correr.

### 2.2 Os braços são **intercalados**

Defeito nº 1 do [§3 da 5U](FASE-5U-RELATORIO.md): ali o ciclo exterior era o
braço, logo as 60 amostras de um correram todas antes das do outro e a latência
ficou não interpretável. **Aqui o ciclo exterior é `(pergunta, repetição)` e o
braço é o interior.**

**10 perguntas × 2 repetições × 3 braços = 60 amostras**, voz única (ortónimo),
modelo de serviço, mesmas sementes.

---

## 3. O desfecho, e o seu ponto cego declarado

**Rima** pelo detector da [5V](FASE-5V-RELATORIO.md), com os pares de **palavra
igual excluídos** — logo o instrumento é **imune à maneira mais barata de
fingir**, que é acabar dois versos na mesma palavra.

**Duas chaves, co-primárias, cada uma contra o seu próprio nulo de permutação:**

- **consoante** (desde a penúltima vogal). **Ponto cego: as oxítonas.** «dizer»
  dá `izer` e «ver» dá `er`, logo este par **não** é visto. O viés é
  **conservador** — só pode **subestimar** o efeito.
- **toante** (desde a última vogal). Vê as oxítonas e colide muito mais por
  acaso — e é exactamente por isso que vai acompanhada do nulo, que mede a
  colisão.

Reportar as duas cobre o ponto cego de cada uma. **A decisão do §5 usa a
consoante**, porque é a que a 5V calibrou contra as quatro poéticas.

---

## 4. Portões

| | nome | dispara se | leitura, escrita agora |
|---|---|---|---|
| **W1** | **a rima é alcançável pelo prompt** | num braço de intervenção: a taxa de rima consoante **passa de 0,50** *e* fica acima do **nulo de permutação desse braço** *e* o IC95 da diferença contra o **C** exclui zero | a instrução actual era fraca, não impossível. **0,50** é o meio do caminho entre o 0,2167 medido e o 0,7769 do poeta, e está acima de qualquer nulo que a 5V viu (0,21–0,32) |
| **W2** | **o exemplo bate a directiva** | taxa de X > taxa de R, IC95 da diferença a excluir zero | a hipótese da escorva da 5U §1.3 **confirma-se** num desfecho com eventos |
| **W3** | **sem dano colateral** | em nenhum braço de intervenção: a regularidade métrica **afasta-se** do 0,7572 do poeta mais que o C; sobem o plágio, a truncatura, as falhas de guarda, as palavras suspeitas; ou cai o `e_verso` | tem **veto**: sem W3, o W1 não vale. Rimar escrevendo pior não é rimar |
| **W4** | **não é alcançável pelo prompt** | o W1 não dispara em braço nenhum | então a forma **não se corrige no prompt** — e, com a 5U, fecha-se o prompt como via para a superfície. O que sobra é descodificação ou afinação |

### 4.1 A decisão, pré-escrita

| | decisão |
|---|---|
| **W1 e W3** num braço | **entra em `src/voices.py`**, esse braço, com a proveniência no comentário e um teste a fixar o texto. É a primeira mudança desta sequência a **melhorar** o poema |
| **W1 e W3** nos dois | entra o de **taxa mais alta**; se empatarem dentro do IC, entra o **R**, por ser o mais curto (o `system` é pago em *tokens*) |
| **W1** sem **W3** | **não entra**, e o relatório diz o que se estragou |
| **W4** | nada entra; declara-se que a forma não é alcançável por instrução |

### 4.2 O que esta fase não decide

- **Não mede voz nem conteúdo.** Rimar não é ser Pessoa. A âncora de conteúdo é
  o [passo 25](CONTROLO.md).
- **Não toca no Campos nem no Reis.** O Reis manda «sem rima» e **cumpre**;
  mexer-lhe seria estragar o que funciona.
- **Não fecha o AUC da 5Q.** A 5V mediu a rima a **0,780** e o número da 5Q é
  0,938–1,000. Mesmo um W1 perfeito não fecha a diferença, e o
  [passo 38](CONTROLO.md) (combinar, com validação retida) continua aberto.
- **Não toca no intervalo de versos** (§2).

---

## 5. Ameaças

### 5.1 A rima forçada estraga o resto

É o risco central e é o que o **W3 tem veto** para apanhar. Um modelo que tem de
rimar inverte a sintaxe, repete, enche o verso. As medidas que o vigiam já
existem todas: `plagio.analisar`, `e_verso`, `lexico.suspeitas`, as falhas de
guarda, a truncatura, e a **regularidade métrica** da 5V.

### 5.2 O detector pode ser enganado

Pela repetição — e **não pode**, porque os pares de palavra igual estão
excluídos (§3). Por rimas pobres («-ão»/«-ão» em toda a parte) — e **pode**: o
nulo de permutação mede a colisão por acaso, mas não distingue rima rica de
pobre. Declarado, e o relatório mostrará as terminações mais usadas por braço.

### 5.3 Dez perguntas é pouco

São as 10 do ortónimo no banco dourado (`q31`–`q40`), as mesmas da 5M e da 5U, o
que mantém a comparabilidade. O n efectivo é **10 agrupamentos** por braço, pela
lição do [5K](FASE-5K-RELATORIO.md) — e o desfecho é binário por poema, logo o
IC será largo. **O W1 exige passar de 0,50 precisamente para não depender de uma
diferença pequena.**

### 5.4 Eu quero que esta dispare

É a primeira intervenção da sequência e a tentação é lê-la com generosidade. As
três defesas estão escritas: o limiar **absoluto** de 0,50, o **nulo por braço**,
e o **veto do W3**. E o W4 tem uma leitura útil: fecha o prompt como via.

---

## 6. Lista de verificação

```
[ ] A1  os tres `forma` escritos e asseridos a diferir SO na parte da rima
[ ] A2  60 amostras, bracos INTERCALADOS, voz unica, mesmas sementes
[ ] A3  desfecho: rima consoante e toante, cada uma contra o nulo do braco
[ ] A4  W3: metro, plagio, e_verso, suspeitas, guarda, truncatura, comprimento
[ ] B1  W1, W2, W3, W4 e a decisao do §4.1
[ ] C1  se autorizado: entra em src/voices.py com teste
[ ] C2  relatorio FASE-5W-RELATORIO.md
[ ] C3  CONTROLO.md
```

**Sessões paralelas:** verificado antes de abrir. `git add` com ficheiros
nomeados.
