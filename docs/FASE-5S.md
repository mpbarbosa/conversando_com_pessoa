# Fase 5S — A troca de modelo, e o roteador que ninguém olhou

**Fecha a decisão** que a 5H abriu e que o passo 25 bloqueava. Pré-registada em
2026-10-08. **É uma fase de decisão e de produto**, não de medição de voz.

---

## 1. O que a troca custa de facto, e não é uma linha

Sete fases mediram a troca `qwen2.5:7b` → `llama3.1:8b`. Nenhuma olhou para o que
mudar o modelo **faz ao resto do sistema**. Fui ver:

```
src/generation/ollama.py:28   MODELO = "qwen2.5:7b-instruct-q4_K_M"
src/cli.py:322                aquecer(pipeline.gerador)
```

**O roteador de voz e o poeta partilham a mesma instância de gerador.** O
`rotear()` recebe um `Generator` por parâmetro, e o CLI passa-lhe o do pipeline.

Logo mudar `MODELO` mudaria **duas coisas**: o poeta, que está medido, e o
**roteador**, cujos **72% de exactidão** (92% com etiqueta múltipla) foram
medidos na [Fase 4](FASE-4-RELATORIO.md) **com o qwen2.5:7b** e nunca com o
llama.

> **E isto nunca foi uma decisão.** O gerador corre a `temperature=0,9` e o
> roteador a `0,0` — o projecto já documentou que são tarefas diferentes
> ([`roteador.py`](../src/roteador.py) §«O gerador usa 0,9… um classificador é
> outra coisa»). Partilharem o modelo é um acidente da ligação, não uma escolha.

---

## 2. O que já está medido, e entra como dado

| | resultado | fase |
|---|---|---|
| Caeiro, conteúdo (3a′) | llama **+0,700**, p=0,0002 | [5H](FASE-5H-RELATORIO.md) |
| **replicado** por um 3.º avaliador cego, noutra sessão | **+0,667**, IC contém 0,700 | [5O](FASE-5O-RELATORIO.md) |
| Caeiro, distância ao poeta | AUC **0,526** (llama) contra **0,851** (qwen) | 5F · 5O |
| capacidade como explicação | **excluída**: +145% de parâmetros rendem +0,400 n.s. | [5N](FASE-5N-RELATORIO.md) |
| forma, 4 vozes | llama pior **só no Caeiro**; melhor nas outras três | [5M](FASE-5M-RELATORIO.md) |
| conteúdo, outras 3 vozes | **sem diferença** (médias 1,42 e 1,42) | [5Q](FASE-5Q-RELATORIO.md) |
| latência | **igual** (28,6 s contra 29,3 s nas 3 vozes) | 5M |

**Não há nenhuma medição em que o llama seja pior no conteúdo.** A única célula
desfavorável é a **forma do Caeiro**, e a [5J](FASE-5J-RELATORIO.md) mostrou que
o critério que a media estava errado.

**O que falta é uma coisa só, e é mecânica:** o roteador.

---

## 3. O desenho

Reutiliza o harness da Fase 4, [`fase-4/bench_roteador_llm.py`](fase-4/), que já
itera sobre modelos — mediu o `qwen2.5:3b` a 42% e o `qwen2.5:7b` a **72%**.
Acrescenta-se o `llama3.1:8b` ao mesmo ciclo.

**40 perguntas** do conjunto dourado ([`fase-1/08-perguntas.json`](fase-1/)), 10
por voz, etiquetadas. `temperature=0`, logo **determinista**: não há repetições a
fazer. Custo: ~1 minuto.

**Desfecho**: exactidão exacta, e exactidão com **etiqueta múltipla** (a Fase 4
reporta as duas, 72% e 92%, porque há perguntas que admitem mais de uma voz).

---

## 4. Portões

| | nome | dispara se | leitura, escrita agora |
|---|---|---|---|
| **S1** | **o roteador aguenta a troca** | exactidão do llama **≥ 0,65** (o 72% do qwen menos uma margem de ~3 perguntas em 40) | o roteador sobrevive, e a troca é **global**: um modelo só, como hoje |
| **S2** | **o roteador degrada** | exactidão do llama **< 0,65** | a troca **não pode ser global**. Então separam-se os modelos — poeta llama, roteador qwen — e isso custa **dois modelos em memória** (4,9 + 4,7 GB) e uma possível recarga por pergunta no `/auto` |
| **S3** | **o llama bate o qwen a rotear** | exactidão do llama **> 0,72** | bónus: a troca melhora também o roteador, e o §5 da Fase 4 (que deixou o roteador a **propor** e não a decidir) pode ser reaberto |

### 4.1 A decisão, pré-escrita

| S1 | decisão |
|---|---|
| dispara | **trocar globalmente**: `MODELO = "llama3.1:8b-instruct-q4_K_M"` |
| não dispara | **trocar só o poeta**, separando as duas constantes, **se** o custo de memória for aceitável; medir a recarga antes |

**Em nenhum dos dois casos a troca é adiada.** A evidência do §2 é a melhor que
qualquer decisão deste projecto teve, e a única medição que faltava é esta.

### 4.2 O que esta fase não decide

- **Não decide as outras três vozes como produto.** A [5Q](FASE-5Q-RELATORIO.md)
  mostrou que **os dois modelos** são trivialmente distinguíveis de Pessoa nelas.
  A troca não corrige isso; apenas não o piora.
- **Não mede o roteador às cegas.** É exactidão contra um gabarito de etiquetas,
  não juízo — não há cegueira a preservar.
- **Não reabre o `/auto` como decisor.** O S3 autoriza reabrir, não reabre.

---

## 5. Ameaças

### 5.1 O gabarito do roteador tem 40 perguntas

Uma diferença de 3 perguntas é 7,5 pontos. O limiar do S1 (0,65) é precisamente
«o qwen menos três perguntas», e está escrito assim para não fingir precisão que
40 itens não dão. **Uma diferença de uma ou duas perguntas não se lê como
diferença.**

### 5.2 O `keep_alive` e a troca de modelos

Se o S2 disparar e os modelos se separarem, cada pergunta com `/auto` alterna
entre dois modelos de ~5 GB. O Ollama mantém ambos com `keep_alive=30m` se a
memória der; se não der, paga recarga. **Mede-se antes de decidir**, não depois.

### 5.3 Eu quero que a troca aconteça

Sete fases minhas apontam para ela, e isso é exactamente a situação em que o §4.1
pré-escreve a decisão **antes** de ver o número. O S2 tem uma saída que **não** é
«trocar de qualquer maneira»: é separar os modelos **com** a medição de memória
feita primeiro.

---

## 6. Lista de verificação

```
[x] A1  bench corrido, reutilizando o harness da Fase 4 sem o alterar
[x] B1  S1 DISPARA (68%, 27/40) · S2 nao · S3 nao (68% contra 72%)
[x] C1  MODELO = "llama3.1:8b-instruct-q4_K_M", com a proveniencia no
        comentario e um teste que fixa TAMBEM a partilha com o roteador
[x] C2  239 testes (eram 238) e o ./pessoa responde
[x] C3  relatorio FASE-5S-RELATORIO.md
[x] C4  CONTROLO.md: a decisao em §3, a fase, e os passos 31-33 fechados
```

**A decisao do §4.1 accionada foi a primeira linha: trocar globalmente.** E o
§1.1 do relatorio registra a convergencia: a afinidade do llama com o **Reis**
aparece agora em **tres medicoes independentes** — a forma (5M), a predicao
registada (5K) e o roteamento (esta fase).

**Sessões paralelas:** verificado antes de abrir. `git add` com ficheiros
nomeados.
