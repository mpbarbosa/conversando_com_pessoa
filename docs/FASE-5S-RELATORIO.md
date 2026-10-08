# Fase 5S — relatório: a troca está feita, e custou duas perguntas no roteador

**Protocolo:** [`FASE-5S.md`](FASE-5S.md), pré-registado em `8c10452`.
**Dados:** [`fase-5s/01-roteador.json`](fase-5s/)
**Produto:** `MODELO = "llama3.1:8b-instruct-q4_K_M"` em
[`src/generation/ollama.py`](../src/generation/ollama.py).

---

## 0. Os portões, e a decisão que accionaram

| | | |
|---|---|---|
| **S1** o roteador aguenta a troca | ✅ **dispara** | **68%** (27/40), contra um limiar de 65% |
| **S2** o roteador degrada | ❌ não dispara | — |
| **S3** o llama bate o qwen a rotear | ❌ não dispara | 68% contra 72% |

**Pela decisão pré-escrita no §4.1: trocar globalmente.** Está feito.

---

## 1. O roteador: 68% contra 72%, que são duas perguntas

| roteador | certos | exactidão | caeiro | campos | **reis** | ortónimo |
|---|---|---|---|---|---|---|
| lexical@20 (Fase 4) | 18/40 | 45% | 0,1 | 0,7 | 0,1 | 0,9 |
| llm `qwen2.5:3b` (Fase 4) | 17/40 | 42% | 0,4 | 0,4 | 0,1 | 0,8 |
| **llm `qwen2.5:7b`** (Fase 4) | **29/40** | **72%** | **0,7** | **0,9** | 0,5 | **0,8** |
| **llm `llama3.1:8b`** (esta fase) | **27/40** | **68%** | 0,5 | 0,7 | **0,9** | 0,6 |

A diferença é de **duas perguntas em 40**. O §5.1 do protocolo escreveu, antes de
medir, que «uma diferença de uma ou duas perguntas não se lê como diferença» — e
fixou o limiar do S1 em 0,65 precisamente para não fingir precisão que 40 itens
não dão.

**E o custo é baixo por desenho:** a Fase 4 decidiu que **o roteador propõe e não
decide** (`CONTROLO.md` §3), porque a 72% uma em quatro iria à voz errada. Uma
proposta que o utilizador vê e corrige com uma tecla não é o mesmo que uma
decisão silenciosa.

Latência do roteador: **1,28 s** de parede mediana, na mesma ordem do 1,2 s que a
Fase 4 publicou para o qwen.

### 1.1 Os dois modelos são complementares, e o Reis repete-se

O llama é **muito melhor no Reis** (0,9 contra 0,5) e pior nas outras três. E os
seus erros têm direcção: **`caeiro`→`reis` quatro vezes** e
`ortonimo`→`campos` quatro. **Sobre-roteia para o Reis.**

Isso faz da afinidade do llama com o Reis o achado que aparece agora em **três
medições independentes**:

| medição | fase | resultado |
|---|---|---|
| distribuição de comprimento | [5M](FASE-5M-RELATORIO.md) | `reis/L` é a **única célula de toda a sequência** a reproduzir a de um poeta (KS 0,196 contra p95 0,207) |
| predição registada antes de correr | [5K §2.2](FASE-5K-RELATORIO.md) | o llama devia sair melhor no Reis — **confirmada** |
| roteamento | esta fase | 0,9 no Reis contra 0,5 do qwen |

Três instrumentos diferentes, construídos para outras perguntas, a dizer a mesma
coisa. É a convergência mais forte da sequência.

---

## 2. O que mudou no `src/`

Uma constante, com a proveniência no comentário e um teste a fixá-la:

```python
#: Trocado de `qwen2.5:7b-instruct-q4_K_M` em 2026-10-08, pela Fase 5S.
MODELO = "llama3.1:8b-instruct-q4_K_M"
```

O teste novo
([`tests/test_generation.py`](../tests/test_generation.py)) afirma **duas**
coisas: o modelo, e que `OllamaGenerator().modelo` é a mesma constante — isto é,
que **a partilha com o roteador é deliberada** e não um acidente. Se alguém
separar os dois modelos, é ali que se vê que a partilha foi medida.

**239 testes passam** (eram 238).

### 2.1 Verificado a correr

```
A água é água e o chão é chão.
Nem tem o cheiro a terra que faz ser terra,
nem a umidade que faz ser água.
E não há um som que lhe fale da chuva
que a enche, nem uma cor que se apanhe no vento.
```

Tautologia deflacionária de ponta a ponta — «a água é água», «o cheiro a terra
que faz ser terra» — e fecho na coisa. Pela âncora 3a′ da [5F](FASE-5F.md) é um
**2**, e é o comportamento que os +0,667 da 5O previam.

Duas observações da mesma corrida:

1. **A guarda lexical apanhou «umidade»**, que é grafia brasileira (`humidade` em
   português europeu). É uma classe que o detector da [5R](FASE-5R-RELATORIO.md)
   **não cobria** — não é consoante muda nem acento, é um `h` em falta. A guarda
   que já existe cobre parte do que aquela fase não conseguiu derivar.
2. **«2 tentativas»**: a guarda rejeitou a primeira resposta e regenerou — o
   caminho que o passo 30 da 5R acabou de tornar sensível à truncatura está
   activo.

---

## 3. O que isto decide, e o que não

**Decide a troca de modelo**, que estava aberta desde a 5H. A evidência é a mais
completa que qualquer decisão deste projecto teve: sete fases, três avaliadores
em duas sessões, e **nenhuma medição em que o llama seja pior no conteúdo**.

**E decide-a sabendo o que custa:** quatro pontos de exactidão no roteador, numa
mecânica que só propõe.

**Não melhora as outras três vozes.** A [5Q](FASE-5Q-RELATORIO.md) mediu que
**os dois modelos** são trivialmente distinguíveis de Pessoa em Campos, Reis e
ortónimo (AUC 0,938–1,000). A troca **não corrige** isso — apenas não o piora, e
melhora a forma em três das quatro vozes. **O produto continua a funcionar bem
numa voz de quatro.**

**Não fecha o roteador.** O S3 não disparou, logo a reabertura do `/auto` como
**decisor** (em vez de proponente) não é autorizada — e agora tem um argumento a
mais contra, porque o modelo que serve é o pior dos dois a rotear.

**Não separa os modelos.** O S1 disparou, logo não foi preciso. Se alguém quiser
o melhor dos dois mundos — poeta llama, roteador qwen — o §5.2 do protocolo diz
o que medir primeiro: **dois modelos de ~5 GB em memória** e a recarga por
pergunta.

### O que fica na mesa

1. **As outras três vozes**, que é o problema real do produto e que nenhum dos
   dois modelos resolve. A [5Q §3](FASE-5Q-RELATORIO.md) nomeou a causa —
   competência de superfície em português europeu e em forma de verso — e a
   [5R](FASE-5R-RELATORIO.md) fechou a via de a **detectar** com este corpus.
2. **O roteador híbrido** (poeta llama, roteador qwen), com a medição de memória
   do §5.2 por fazer. Vale 4 pontos de exactidão numa proposta.
3. **A limpeza**: 280 linhas de código morto em `src/{main,model,retriever}.py`,
   declaradas para remoção desde o Passo 9 e importadas em lugar nenhum.
4. **O passo 24** (as personas que pedem os intervalos invalidados), que a
   [5M §3.1](FASE-5M-RELATORIO.md) deixou com uma predição registada: corrigi-las
   deve beneficiar sobretudo o **qwen** — que acabou de sair de serviço, o que
   lhe baixa a prioridade.

> **A lição, e é de engenharia e não de método.** Sete fases mediram um modelo
> contra outro e nenhuma perguntou **o que mais depende dessa constante**. A
> resposta estava a duas linhas de `grep`: o roteador partilha a instância de
> gerador, e os seus 72% tinham sido medidos com o modelo que ia sair.
>
> **Medir uma troca não é medir a coisa trocada; é medir tudo o que lhe está
> ligado.** Custou um minuto de bench descobri-lo, e teria sido uma regressão
> silenciosa em produção.
