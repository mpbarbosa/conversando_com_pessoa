# A tokenização neste projecto

Documento temático, escrito em 2026-10-12. **Não é uma fase**: não tem protocolo
nem portões, e não mede nada de novo. Reúne o que as fases mediram sobre
tokenização, e existe porque essa história está hoje espalhada por
`src/tokens.py`, `src/corpus/chunk.py`, `src/generation/prompt.py` e seis
entradas do [`CONTROLO.md`](../CONTROLO.md).

Cada número aqui vem de um ficheiro citado. Onde eu afirmei coisas erradas, está
dito qual e onde.

---

## 1. Há dois tokenizadores, e não são intercambiáveis

É a decisão de que tudo o resto decorre.

| | tokenizador | o que define |
|---|---|---|
| **encoder** | `intfloat/multilingual-e5-base` | o limite de *chunk* (`model_max_length=512`) |
| **gerador** | `Qwen/Qwen2.5-7B-Instruct` | o orçamento de prompt (`ORCAMENTO_USER = 300`) |

Vivem os dois em [`src/tokens.py`](../../src/tokens.py) como `ENCODER` e `GERADOR`,
e a função é uma só:

```python
def contador(nome: str) -> Callable[[str], int]:
```

**O `nome` é obrigatório**, e o §4 explica porquê — a omissão existiu, era o
`ENCODER`, e custou nove fases.

### 1.1 Quanto diferem, medido

Nos mesmos 25 poemas do corpus:

| tokenizador | mediana de *tokens* | razão ao e5 |
|---|---|---|
| e5 | **111** | 1,000 |
| qwen (gerador) | **133** | **1,167** |
| llama 3.1 (o que serve) | **135** | 1,182 — e **1,000 × qwen** |

E, por palavra, o e5 dá mediana de **1,469 *tokens* por palavra** no corpus —
número que validou a estimativa de 1,45 usada no planeamento.

O [`prompt.py`](../../src/generation/prompt.py) já publicava a razão qwen/e5 como
**17% mais** (mediana 1,166, **máximo 1,458**) e avisava que orçamentar o prompt
do gerador com o contador do encoder «subestimaria até **46%**». O aviso estava
escrito; o §4 conta o que aconteceu apesar disso.

---

## 2. O limite de *chunk*: 480, derivado e não escolhido

De [`src/corpus/chunk.py`](../../src/corpus/chunk.py):

```
512 - 2 ("passage: ") - 27 (pior caso de "Autor — Título") - 2 (especiais)
    = 481  ->  480
```

Com esse limite e **o tokenizador real**, 95,3% dos poemas cabem inteiros, e das
**6619 estrofes** do corpus só **12** excedem o limite sozinhas. A estrofe é a
unidade; nunca se parte um verso.

**Dois textos por *chunk*, de propósito:** o `text` vai ao **prompt** (verso
puro, porque o gerador deve ver poesia e não fichas bibliográficas) e o
`indexed_text` vai ao **índice** (com «Autor — Título» à cabeça, que dá ao
encoder contexto que o verso sozinho não carrega). São os prefixos do
`indexed_text` que consomem os 32 *tokens* da conta acima.

**E há uma consequência que custou um número publicado.** O chunker tem
`SOBREPOSICAO = 1`: repete uma estrofe por fronteira. Juntar os textos dos
*chunks* de um poema **duplica versos** — 21 linhas duplicadas no `poem_1487` —
e foi assim que o máximo de versos do Caeiro foi publicado como **181** quando é
**161**. A fonte certa é o `.body` do `parse_poem`
([correcção 16 do `CONTROLO.md`](../CONTROLO.md)).

---

## 3. O orçamento de prompt: 300 *tokens*, e porque é só da mensagem do utilizador

O orçamento não é sobre o prompt todo. É sobre a **parte variável** — e a razão é
uma medição do cache de KV.

Com o `system` **fixo**, o `llama.cpp` reaproveita o cache do prefixo: os **313
*tokens*** da persona passam de **13,63 s a 0,91 s** da segunda pergunta em
diante, **15×**. Logo a persona custa quase zero por pergunta e o que se paga é a
pergunta mais o contexto.

Daí `ORCAMENTO_USER = 300`, derivado de latência: a quente o prefill corre a ~16
tok/s e o decode leva ~23 s, logo 300 *tokens* dão ~18,8 + 23 = **~41,8 s**,
dentro do limite de 45 s fixado na Fase 0. Medido nos extremos: **168 *tokens* →
33,7 s** e **448 → 53,7 s**, este fora do limite.

Três detalhes que são decisões:

- **a pergunta vem antes do contexto**, porque o tokenizador trunca pela direita
  e com o contexto primeiro um poema longo empurrava a pergunta fora do prompt —
  era o defeito do `main.py` original;
- **um *chunk* que não caiba inteiro é deixado de fora, não truncado**, porque
  meio poema não é contexto, é ruído;
- `RESERVA = 24` cobre o enquadramento do chat.

> **O mesmo mecanismo que torna isto possível invalidou um benchmark.** Na Fase 0
> o cache de KV foi reaproveitado entre repetições e o prefill saiu reportado a
> **25 625 tok/s** — quatro horas de dados inválidos. Lá foi preciso um **nonce**
> para medir prefill honesto; aqui o mesmo cache é o que torna uma persona
> detalhada acessível. **Defeito de medição e capacidade de produto são o mesmo
> fenómeno visto de dois lados.**

---

## 4. O defeito: a omissão de `contador()` era o encoder

A função tinha omissão, e a omissão era o `ENCODER`. **O `src/` nunca caiu
nisso** — as duas chamadas sempre passaram o nome: `contador(encoder)` no
`build.py` e `contador(GERADOR)` no `cli.py`.

**Nove *scripts* de fase caíram**: Fases 5, 5B, 5G, 5H, 5I, 5M, 5N, 5U e 5W,
todos com `n_tokens = contador()`. Como o e5 subconta 17%, o `montar` encaixava
mais contexto do que o orçamento pretende: as amostras correram com **~350
*tokens* de gerador onde o orçamento pede 300**.

**O que isto afecta e o que não:**

| | |
|---|---|
| comparações **dentro** de cada fase | **intactas** — os braços partilharam o mesmo orçamento |
| o rótulo «configuração de produção» | **errado** nessas nove fases |

Na [5W](../FASE-5W-RELATORIO.md) escrevi que o braço de controlo era idêntico a
produção «byte a byte»: era verdade da **persona** e falso do **orçamento**
([correcção 30](../CONTROLO.md)).

**A correcção foi de API e não de valor:** o `nome` passou a obrigatório, a
constante `GERADOR` substituiu um literal no `cli.py`, e nada em `src/` mudou de
comportamento. Dois testes fixam-no — um mede os ~17% para a diferença deixar de
ser folclore, outro verifica por introspecção que a omissão não voltou.

### 4.1 E o defeito teve um filho pior

Entre a [5W](../FASE-5W-RELATORIO.md) e a [5X](../FASE-5X-RELATORIO.md) eu corrigi o
tokenizador — a 5W com o e5, a 5X com o do gerador. Resultado: **18 das 20
células receberam prompts diferentes** (4 *chunks* onde a 5X encaixou 3), e eu li
a diferença de desfecho que isso produziu (0,00951 contra 0,00615) como **«chão
de ruído»**, publicando que «a mesma configuração, medida duas vezes, varia
1,54×».

**Não era a mesma configuração.** E o modelo é determinista: nas **2** células em
que o prompt coincidiu, o texto saiu **idêntico byte a byte** — logo o remédio
que prescrevi, «correr o controlo duas vezes», devolveria resultados iguais e não
mediria nada. Premissa e remédio errados, com um intervalo de confiança a
sustentá-los ([correcção 33](../CONTROLO.md)).

**A regra que ficou:** asserir a identidade do prompt **contra a fase anterior**,
e não só dentro da fase. Cada fase verificava a identidade dentro de si — a 5M
byte a byte, a 5W no campo `forma`, a 5X nas opções — e **nenhuma** a verificava
contra a corrida anterior.

---

## 5. O tokenizador do gerador ficou o do qwen, com o modelo a ser llama

A [5S](../FASE-5S-RELATORIO.md) trocou o modelo para `llama3.1:8b` e o orçamento
continuou a ser contado com o tokenizador do **qwen**. Essa fase tinha escrito,
como lição, que «medir uma troca não é medir a coisa trocada; é medir **tudo o
que lhe está ligado**» — foi ver o roteador, que partilhava a constante, e **não
foi ver o tokenizador**.

**Verificado em 2026-10-08, e é benigno.** A medição usou o
**`prompt_eval_count` do próprio Ollama**, que é a contagem autoritativa do
modelo que serve e não precisa de descarregar nada: nos mesmos 25 poemas o llama
dá mediana **135** contra **133** do qwen — razão **1,000**, máximo **1,031**. O
orçamento descreve o llama dentro de 3%, logo trocar o tokenizador não compraria
nada e custaria uma descarga.

**Fica como está, e com a medição no comentário** — porque «benigno» e «não
medido» são estados diferentes, e só um deles se pode afirmar.

### 5.1 A técnica, que vale por si

Para contar *tokens* de um modelo cujo tokenizador está atrás de autenticação:
envia-se o texto ao Ollama com `num_predict: 1` e lê-se `prompt_eval_count`,
subtraindo a sobrecarga do gabarito medida com um prompt mínimo (`"x"` dá 11
*tokens*, logo a sobrecarga é 10). É exacto, é local, e não depende de conseguir
o ficheiro do tokenizador.

---

## 6. O que a tokenização **não** conseguiu responder

A [5X](../FASE-5X.md) levantou uma hipótese mecanística sobre rima: o
`repeat_penalty` divide os *logits* dos *tokens* vistos nos últimos
`repeat_last_n` (64, a omissão do Ollama), e **a rima é repetir uma terminação**.
Se `ade` em «estabilidade»/«tranquilidade» ou `ia` em «havia»/«servia» for um
*token* próprio, a opção que existe para evitar degeneração está a penalizar a
segunda rima.

**Esta pergunta ficou sem resposta directa**, e por uma razão de ferramenta: o
`prompt_eval_count` dá **contagens, não fronteiras**, e o tokenizador do llama
está atrás de autenticação. Logo a hipótese foi a teste **pela sua predição** e
não pela sua mecânica — declarado como ameaça nas duas fases que a testaram.

**E a predição não passou.** A [5Z](../FASE-5Z.md) levou a constante ao outro
extremo (0,9, que *premeia* repetição) e o que saiu foi **repetição e não rima**:
as médias de densidade crescem monotonamente (0,0075 → 0,0096 → 0,0144) mas o
**nulo de permutação cresce mais depressa** (0,400 → 0,450 → **0,550**), e a 0,9
o texto traz **23,5% de linhas duplicadas** e **50%** das primeiras tentativas
truncadas. Nos três braços, nenhum rima acima do seu próprio nulo.

> **A lição de tokenização que fica desta parte é negativa e útil:** uma hipótese
> formulada ao nível do *token* precisa de acesso ao *token*. Sem fronteiras, o
> melhor que se consegue é testar o comportamento que ela prediz — e um
> comportamento pode falhar por a hipótese estar errada **ou** por a manipulação
> trazer um efeito maior pelo caminho. Aqui foi a segunda: a penalização mexe na
> rima e mexe mais na repetição.

---

## 7. Resumo, para quem chega agora

1. **Dois tokenizadores, nunca intercambiáveis.** `ENCODER` para *chunks*,
   `GERADOR` para prompt. O `contador` exige que se diga qual.
2. **O gerador conta 17% mais que o encoder em português.** Confundi-los
   subestima o prompt e enche-o de mais contexto do que o orçamento pede.
3. **480 e 300 são derivados, não escolhidos** — o primeiro do `model_max_length`
   do e5 menos os prefixos, o segundo de uma medição de latência contra o limite
   de 45 s.
4. **O cache de KV é a razão de o orçamento ser só da mensagem do utilizador**, e
   é também o que invalidou quatro horas de *benchmark* na Fase 0.
5. **O tokenizador do llama difere do do qwen em 0,1% na mediana**, medido pelo
   `prompt_eval_count` do Ollama — logo o orçamento sobrevive à troca de modelo.
6. **O custo de ter havido uma omissão** foram nove fases com o rótulo de
   produção errado e uma conclusão publicada e retirada.

**Ficheiros:** [`src/tokens.py`](../../src/tokens.py) ·
[`src/corpus/chunk.py`](../../src/corpus/chunk.py) ·
[`src/generation/prompt.py`](../../src/generation/prompt.py) ·
[`CONTROLO.md`](../CONTROLO.md) §3 e correcções 16, 30, 33.
