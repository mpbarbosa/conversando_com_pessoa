# Fase 5Z — A mecânica da penalização, testada com uma manipulação forte

**[Passo 40](CONTROLO.md)**, desbloqueado pelo [passo 43](CONTROLO.md).
Pré-registada em 2026-10-09, **antes de qualquer amostra**.

---

## 1. Porque uma manipulação forte e não mais amostras

A [5X](FASE-5X-RELATORIO.md) testou a hipótese de que o `repeat_penalty`
**proíbe a rima** — ele divide os *logits* dos *tokens* vistos nos últimos 64, e
a rima é repetir uma terminação. Resultado: desligá-la (1,1 → 1,0) deu **1,96×**
a densidade de rima nas células limpas, com IC a conter zero.

**Resolver 1,96× com mais amostras custa ~720 por braço**, ~10 h cada. A
alternativa é **inverter a opção em vez de a desligar**:

| `repeat_penalty` | o que faz aos *tokens* já vistos |
|---|---|
| **1,1** | penaliza — produção |
| **1,0** | neutro |
| **0,9** | **premeia** |

**Se a mecânica for real, a 0,9 o efeito tem de ser grande** — e grande é o que
este desenho consegue ver. **Efeito grande com desenho pequeno é o caminho
quando o que falta é potência.**

### 1.1 E há uma predição mais forte que qualquer contraste: monotonia

Três níveis ordenados dão uma predição que um só contraste não dá: **a densidade
tem de crescer de 1,1 para 1,0 para 0,9.** Uma inversão no meio refuta a
mecânica mesmo que os extremos difiram. É de graça — os três braços já estavam
previstos — e está escrita antes de haver número.

---

## 2. O desfecho primário é a **primeira tentativa**

É o que o [passo 43](CONTROLO.md) acabou de tornar possível. A
[5Y](FASE-5Y-RELATORIO.md) mediu que a saída final já passou pelo
`_repetir_sem`, que **troca o contexto** quando o modelo plagia — e contaminou de
7% a 40% das células das nove fases emparelhadas.

| | o que é | papel |
|---|---|---|
| `turno.primeira.resposta.texto` | a 1.ª tentativa, prompt **idêntico entre braços por construção** | **primário** |
| `turno.resposta.texto` | a saída final, depois das correcções | **secundário**, de produto |

**E isto importa mais nesta fase que em qualquer outra**, porque `repeat_penalty
= 0.9` é precisamente a manipulação que mais deve aumentar o plágio — logo a que
mais contaminaria a saída final.

**Desfecho**: densidade de rima da [5W §1](FASE-5W-RELATORIO.md) — pares de
versos que partilham a chave sobre pares possíveis, pares de palavra igual
excluídos.

**10 perguntas × 2 repetições × 3 braços = 60 amostras**, voz única (ortónimo),
braços **intercalados**, mesmas sementes, `contador(GERADOR)`.

---

## 3. Portões

| | nome | dispara se | leitura, escrita agora |
|---|---|---|---|
| **Z1** | **a mecânica é real** | densidade(**0,9**) > densidade(**1,1**) com IC95 a **excluir zero**, **e** a ordem 1,1 < 1,0 < 0,9 verificada nas médias | a penalização de repetição **é** o que suprime a rima. Explica a 5V, a 5W e a 5X de uma vez |
| **Z2** | **a 5X replica** | densidade(**1,0**) > densidade(**1,1**), razão próxima de **2×** | o 1,96× da 5X não era ruído — e agora no desfecho limpo |
| **Z3** | **sem degeneração** | **com IC**: um dano conta só se o IC95 da diferença **excluir zero** | tem veto. **E corrige o `X3` da 5X**, que vetou numa estimativa pontual de −0,0097 dentro de um IC de ±0,13 — o terceiro portão desta sequência operacionalizado sem intervalo |
| **Z4** | **a mecânica não é real** | o Z1 não dispara | então a rima não é suprimida pela penalização, e as três vias do [passo 34](CONTROLO.md) ficam todas fechadas sem causa accionável. É um resultado |

### 3.1 A decisão, pré-escrita — e continua a não ser embarcar

| | decisão |
|---|---|
| **Z1 e Z3** | **não embarca ainda.** O `_opcoes` é **global** e o Caeiro é a única voz que funciona (AUC ao poeta **0,526**). Fica **obrigatório** correr o [passo 41](CONTROLO.md) — dano no Caeiro — e só depois embarcar |
| **Z1 sem Z3** | não embarca. A degeneração é o motivo pelo qual a constante existe, e premiar repetição é a direcção que a traz de volta |
| **Z4** | nada entra; a via fecha-se com a mecânica refutada e não só por falta de potência |

### 3.2 O que esta fase não decide

- **Não mede voz nem conteúdo.** Mede forma.
- **Não decide o Caeiro.** É o passo 41, e a 5Z não o antecipa.
- **Não testa `repeat_last_n`**, que fica na omissão do Ollama (64) nos três
  braços — é ele que define a janela da hipótese.

---

## 4. Ameaças

### 4.1 Premiar repetição traz o ciclo de volta

É o risco e é o **motivo histórico da constante** — «um 8B degenerou em ciclo»,
Fase 0. A 5X mediu que **desligar** a penalização não degenerou nada no llama
(zero linhas duplicadas contra 0,0031 de produção), mas **premiar** é outra
coisa. A bateria do Z3 é a mesma, agora com intervalo.

### 4.2 Se o Z1 disparar, prova o efeito e não o mecanismo

Continuo sem ver as fronteiras de *token* do llama (§4.2 da
[5X](FASE-5X.md)). Monotonia nos três níveis é a evidência mais forte que
consigo sem isso: **é o que a mecânica prediz e o que uma coincidência não
prediz.**

### 4.3 Vinte amostras por braço

A 5X mediu a meia-largura do IC em **~0,008** sobre uma base de ~0,006. Logo este
desenho vê um **triplicar** com folga e um duplicar à tangente. **Se a 0,9 o
efeito for pequeno, a mecânica fica refutada como explicação útil** — porque a
0,9 ela está a ser empurrada na direcção favorável com toda a força disponível.

### 4.4 Eu quero que a mecânica seja verdade

É a explicação mais elegante que esta sequência produziu — a opção que evita um
defeito a causar outro — e já sobreviveu a uma fase. As defesas: o IC a excluir
zero, a **monotonia** (que uma coincidência não dá), o veto do Z3 **com
intervalo**, e a não-embarcação do §3.1.

---

## 5. Lista de verificação

```
[x] A1  tres bracos asseridos a diferir de producao so no repeat_penalty
[x] A2  60 amostras, bracos INTERCALADOS, voz unica (ortonimo), contador(GERADOR),
        40 min, e o harness a registar `turno.primeira` (passo 43)
[x] A3  desfecho PRIMARIO: densidade de rima na 1.a tentativa — e o prompt
        divergiu em 0/20 celulas, contra 4/20 na saida final
[x] A4  secundario: a saida final (onde 1,0 e 0,9 COINCIDEM); bateria do Z3 COM
        intervalo, e e ela que da o unico resultado solido da fase
[x] B1  Z1 nao dispara (monotonia SIM, IC a conter zero), Z2 dispara MAL
        OPERACIONALIZADO (1,28x contra os 1,96x da 5X), Z3 falha no braco R
        (duplicadas 0,2353 contra 0,0031; metade truncada), Z4 DISPARA
[x] B2  o achado que nao estava nos portoes: a monotonia INVERTE sem uma celula
        de vinte, e o par que decide a fase e `toque`/`que` em quatro versos —
        a propria manipulacao contada como rima pelo instrumento
[x] B3  44 das 60 amostras tem densidade ZERO: o desfecho e uma contagem de
        eventos raros, e o §4.3 estimou a potencia na grandeza errada
[x] C1  relatorio FASE-5Z-RELATORIO.md
[x] C2  CONTROLO.md — linha da fase, passos 17b/34/38/40/41, correccao 38 e um
        defeito de instrumento novo
```

**Sessões paralelas:** verificado antes de abrir. `git add` com ficheiros
nomeados.
