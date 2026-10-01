# PessoaBot v2 — Plano de arquitetura para RAG local

Chatbot que responde **em verso**, na voz de Fernando Pessoa ou de um heterônimo,
fundamentado por RAG sobre o corpus de 2083 poemas do repositório.

Alvo inicial: **execução 100% local**, nesta máquina. A camada de geração é
plugável para permitir uma fase remota depois.

---

## 1. Restrições medidas

Tudo nesta seção foi medido nesta máquina e neste corpus, não estimado.

### 1.1 Hardware — o constrangimento dominante

| | |
|---|---|
| CPU | Intel Core Ultra 5 135U (Meteor Lake-P), 12 núcleos / 14 threads, série U (15–28 W) |
| Extensões | AVX2, FMA, F16C. **Sem AVX-512, sem AMX** |
| GPU | Intel Graphics integrada. **Sem NVIDIA, sem CUDA** — mas **a iGPU é utilizável por Vulkan**, ver nota abaixo |
| RAM | 30 GB total, ~19 GB disponíveis |
| Disco | 157 GB livres |

> **Correcção de 2026-10-01.** «Sem GPU» estava **incompleto**. Concluí-o de
> `nvidia-smi` ausente e não verifiquei a iGPU. O Ollama detecta-a por Vulkan e
> desliga-a por omissão; com `OLLAMA_IGPU_ENABLE=1` ela **acelera o prefill 6x
> (14,2 → 89,1 tok/s) e trava o decode para 0,55x (6,0 → 3,30 tok/s)**. Na carga
> real o decode domina, logo a CPU continua a ser a escolha certa — mas o
> contexto deixa de ser o constrangimento que esta secção assume. Medição em
> [`fase-0/07-igpu-vulkan.md`](fase-0/07-igpu-vulkan.md).

**Consequência:** inferência em CPU, obrigatoriamente com pesos quantizados.
Nada de fp16, nada de `device_map="auto"` sobre GPU, nada de modelos acima de
~8B. A ausência de AMX importa: é a extensão que dá aos Xeon recentes uma
vantagem grande em inferência de CPU, e ela não existe aqui.

O gargalo do *decode* é largura de banda de memória (LPDDR5, ~60–70 GB/s úteis).
Regra prática: `tok/s ≈ banda / tamanho_do_modelo`.

> **MEDIDO na Fase 0 em 2026-10-01.** A tabela abaixo foi substituída por
> medição. Ver [`FASE-0-RELATORIO.md`](FASE-0-RELATORIO.md) e
> [`fase-0/04b-analise-latencia.txt`](fase-0/04b-analise-latencia.txt).

| Modelo | Decode estimado | **medido** | Prefill 1500 tok estimado | **medido** |
|---|---|---|---|---|
| 3B (qwen2.5) | 15–22 tok/s | **15,2** ✓ | 8–15 s | **31 s** ✗ |
| 7B (qwen2.5) | 6–9 tok/s | **6,7** ✓ | 20–45 s | **84 s** ✗ |
| 8B (llama3.1) | 6–9 tok/s | **6,1** ✓ | 20–45 s | **83 s** ✗ |

As estimativas de **decode** derivadas da largura de banda de memória
acertaram. As de **prefill** estavam 2–4x optimistas: assumi que o prefill,
sendo compute-bound, aproveitaria os 14 threads AVX2, mas este é um chip U de
15–28 W com apenas 2 P-cores. Medido a `threads=10` (o óptimo encontrado).

**O prefill, não o decode, é o problema de UX.** Uma resposta em verso tem
80–200 tokens; o contexto RAG tem 1000–2000. Com um 8B, a maior parte do tempo
de espera é o modelo lendo o prompt. Isso dirige duas decisões: contexto enxuto
e reaproveitamento de cache de KV para o prefixo estável.

Esta previsão central **confirmou-se, e mais forte do que previsto**: o prefill
é 70% da espera no 3B a 1500 tokens, 78% no 7B, e 89% no 7B a 3000 tokens.

### 1.2 Ambiente Python

`python3` do sistema é **3.14.4**. Os `.pyc` remanescentes no repositório são
`cpython-313`, ou seja o venv anterior era 3.13 e já não existe.

PyTorch, faiss e boa parte do ecossistema científico não publicam wheels para
3.14 tão cedo. `/usr/bin/python3.12` está instalado e `uv` já está disponível
em `~/.local/bin/uv`.

**Decisão: fixar o venv em Python 3.12 via `uv`.** Tentar 3.14 é gastar tempo
compilando torch do zero.

### 1.3 Corpus — melhor do que o esperado

| Métrica | Valor |
|---|---|
| Arquivos | 2083 |
| Linha de autor + linha `Titulo:` | **2083 / 2083 (100%)** |
| Título reaparece no início do corpo | 1702 (82%) |
| Palavras no corpo | 224.856 |
| Tokens estimados no corpo | **~325.000** |
| Mediana / p95 / máx por poema | ~97 / ~441 / ~10.624 tokens |
| Poemas acima de 512 tokens | 86 (4,1%) |
| Estrofes | 7194 — mediana ~33 tok, p95 ~130 tok, apenas 9 acima de 512 |
| Duplicatas exatas | 1 par |
| Mojibake | 1 arquivo (`poem_224.txt`) |
| Fragmentos (<12 palavras) | 11 |
| Vocabulário | 19.965 tipos |

Distribuição por voz e idioma:

| Autor | PT | EN |
|---|---|---|
| Fernando Pessoa (ortônimo) | 1205 | 92 |
| Álvaro de Campos | 321 | 2 |
| Ricardo Reis | 252 | 0 |
| Alberto Caeiro | 120 | 0 |
| Alexander Search | 1 | 51 |
| Charles Robert Anon | 0 | 9 |
| Joaquim Moura Costa | 8 | 0 |
| Bernardo Soares | 6 | 0 |
| + 11 pré-heterônimos | | |

Três consequências que mudam o projeto:

**(a) O cabeçalho é 100% confiável.** Autor e título podem ser extraídos por
regex sem exceções. Não é preciso classificador nem curadoria manual para ter
metadado de heterônimo — ele já está lá. Isso torna o roteamento por voz um
problema resolvido, não um problema de ML.

**(b) O corpus inteiro tem ~325 mil tokens.** É pequeno. Duas implicações:

- O índice terá ~2 800 vetores. Busca exata por produto interno sobre isso é
  microssegundos em `numpy`. **FAISS é dispensável nesta escala** — `IndexFlatIP`
  já é força bruta; um `numpy.matmul` faz o mesmo sem a dependência. Manter FAISS
  é aceitável (já funciona), mas não é necessário, e nada de IVF/HNSW.
- O custo de embeddar é único e pequeno. **Não vale economizar no encoder**: dá
  para usar o melhor modelo multilíngue disponível, porque se paga uma vez.

**(c) A estrofe é a unidade natural de chunk.** 96% dos poemas cabem inteiros em
512 tokens; só 86 precisam ser partidos, e a partição por estrofe resolve todos
menos 9. Nada de chunking por janela de caracteres, que destruiria o verso.

### 1.4 O que ainda não existe

Nem `ollama`, nem `llama.cpp`, nem torch instalado. Cache do Hugging Face
praticamente vazio (892 KB) — ou seja, o Flan-T5 de 3 GB não está em cache e
tudo será baixado na primeira execução. Docker está disponível.

---

## 2. O problema difícil deste projeto

Vale nomear antes de desenhar a solução, porque é o que separa este plano de um
tutorial genérico de RAG.

**Similaridade semântica é o objetivo errado para recuperar poesia.** Um
embedding de "AS ILHAS AFORTUNADAS" captura imagética marítima e registro
arcaico. A pergunta "o que é a saudade para ti?" não se parece com isso
vetorialmente, mesmo sendo exatamente o poema certo. Poesia fala *por* imagem,
não *sobre* tema — e o encoder mede superfície.

Três mitigações, em ordem de custo-benefício:

1. **Busca híbrida (denso + BM25, fundidos por RRF).** Em poesia as palavras
   exatas pesam: "mar", "Tejo", "saudade", "tabacaria". BM25 é `rank_bm25`, Python
   puro, sem custo. Ganho grande, esforço mínimo. **Fazer na Fase 2.**
2. **Enriquecimento offline de metadado.** Passar cada poema uma vez por um LLM
   e gravar tema, tom e imagens dominantes; indexar esse texto junto com o poema.
   Isso dá ao encoder a superfície *temática* que ele não consegue inferir do
   verso. 2083 poemas é um lote pequeno: ~4 h de madrugada com um 4B local, ou
   ~2 USD via API. **Fazer na Fase 4** — é o maior ganho isolado de qualidade de
   recuperação.
3. **HyDE** (gerar um pseudo-poema a partir da pergunta e embeddar isso). Custa
   uma chamada de LLM extra por pergunta, o que em CPU é caro. **Adiar.**

O segundo problema difícil: **português europeu de 1910–1935**. Praticamente todo
modelo instruct responde em português brasileiro contemporâneo. Ricardo Reis em
PT-BR moderno não é Ricardo Reis. Isso não se resolve com RAG — resolve-se com
prompt de sistema explícito, few-shot tirado dos próprios poemas recuperados, e
avaliação que meça especificamente isso.

O terceiro: **o modelo vai plagiar.** Dado um poema no contexto e a instrução de
responder em verso, o caminho de menor resistência é devolver o poema recuperado.
Precisa de guarda ativa — ver §6.3.

---

## 3. Arquitetura proposta

```
                         pergunta do usuário
                                 │
                    ┌────────────▼────────────┐
                    │  seleção de voz         │  Fase 1: explícita (/caeiro)
                    │  (heterônimo)           │  Fase 4: roteador automático
                    └────────────┬────────────┘
                                 │
         ┌───────────────────────▼───────────────────────┐
         │                RECUPERAÇÃO                     │
         │  ┌──────────────┐      ┌──────────────┐        │
         │  │ denso        │      │ BM25         │ Fase 2 │
         │  │ (e5/bge-m3)  │      │ (rank_bm25)  │        │
         │  └──────┬───────┘      └──────┬───────┘        │
         │         └────── RRF ──────────┘                │
         │                   │                            │
         │      filtro: autor = voz, idioma = pt          │
         │                   │                            │
         │            rerank cross-encoder    Fase 3      │
         │              top-20 → top-4                    │
         └───────────────────┬────────────────────────────┘
                             │
                  ┌──────────▼──────────┐
                  │  montagem do prompt │  orçamento de tokens explícito
                  │  persona + few-shot │  pergunta ANTES do contexto
                  └──────────┬──────────┘
                             │
                  ┌──────────▼──────────┐
                  │  Generator (ABC)    │
                  │  ├─ LlamaCppLocal   │  Fase 1 — Ollama/llama.cpp
                  │  └─ AnthropicRemote │  Fase 5 — opcional
                  └──────────┬──────────┘
                             │
                  ┌──────────▼──────────┐
                  │  guarda de plágio   │  n-grama vs. corpus → regenera
                  └──────────┬──────────┘
                             │
                        resposta em verso
```

### 3.1 Camada de dados

Substituir "ler .txt cru" por um modelo de domínio explícito:

```python
@dataclass(frozen=True)
class Poem:
    id: str              # "poem_135"
    author: str          # "Álvaro de Campos"  (normalizado)
    voice: Voice         # enum: ORTONIMO, CAMPOS, REIS, CAEIRO, SOARES, SEARCH, OUTRO
    title: str           # "ODE MARÍTIMA"
    body: str            # corpo limpo, sem cabeçalho nem título repetido
    language: Lang       # PT | EN
    stanzas: list[str]
    n_tokens: int

@dataclass(frozen=True)
class Chunk:
    poem_id: str
    chunk_ix: int        # 0 quando o poema cabe inteiro
    text: str            # texto a embeddar (com prefixo de título/autor)
    poem: Poem           # referência para citação na resposta
```

Pipeline de ingestão (script único, idempotente, versionado):

1. Ler, parsear cabeçalho (regex, 100% de cobertura garantida pela medição)
2. Normalizar autor (corrigir o mojibake de `poem_224.txt`, unificar grafias)
3. Remover o título repetido no início do corpo (82% dos casos)
4. Detectar idioma (heurística de stopwords — já validada, 1928 PT / 154 EN)
5. Descartar a duplicata exata e marcar os 11 fragmentos
6. Segmentar em estrofes
7. Chunking: poema inteiro se ≤ 512 tokens; senão, janelas de estrofes contíguas
   com sobreposição de 1 estrofe, respeitando o limite
8. Serializar em `data/corpus.jsonl` — artefato versionável e inspecionável

O `corpus.jsonl` é a fronteira do sistema: tudo a jusante consome ele, não os
`.txt`. Isso torna a ingestão testável isoladamente.

### 3.2 Camada de índice

Persistência com manifesto (já implementado na correção anterior): encoder,
ordem dos documentos e fingerprint do corpus. Sem manifesto, ids posicionais
não significam nada.

Cada chunk é embeddado com um prefixo que dá contexto ao encoder:

```
Álvaro de Campos — ODE MARÍTIMA
<corpo da estrofe ou do poema>
```

Isso melhora a recuperação sem poluir o prompt, porque o texto indexado e o
texto injetado no prompt são campos distintos do mesmo `Chunk`.

### 3.3 Camada de geração

```python
class Generator(Protocol):
    def generate(self, system: str, user: str, *, max_tokens: int) -> str: ...
    @property
    def context_window(self) -> int: ...
```

Duas implementações; a escolha vem de configuração, não de `import`. Isso é o
que mantém a decisão "local vs. remoto" reversível.

O prompt de sistema é **por voz**, não único. Cada heterônimo recebe a sua
poética declarada — Caeiro e o olhar sem metafísica, em verso livre curto;
Campos e a vertigem urbana, em versículo longo; Reis e o estoicismo em odes
sáficas; o ortônimo e a fragmentação do eu, em metro regular e rima. O few-shot
não é fixo: são 2 poemas curtos da própria voz, vindos da recuperação.

---

## 4. Tech stack

### 4.1 Núcleo (Fase 1)

| Camada | Escolha | Por quê |
|---|---|---|
| Python | **3.12**, via `uv` | 3.14 não tem wheels de torch/faiss; `uv` já instalado |
| Gestão de deps | `uv` + `pyproject.toml` + lockfile | reprodutível; substitui `requirements.txt` solto |
| Embeddings | `sentence-transformers` + torch CPU | maduro; o custo é único, ver §1.3(b) |
| Encoder | `intfloat/multilingual-e5-base` (768d) | forte em PT; exige prefixos `query:`/`passage:` |
| Encoder alt. | `BAAI/bge-m3` (1024d, ~2,2 GB) | melhor qualidade; medir se compensa o tamanho |
| Índice | `numpy` (ou manter `faiss-cpu`) | ~2 800 vetores: produto interno direto basta |
| Geração | **Ollama** + modelo GGUF Q4_K_M | instalação única, API estável, gestão de modelos |
| Geração alt. | `llama.cpp` server | controle fino de cache de KV e slots de prefixo |
| Modelo | Qwen2.5-7B-Instruct, ou Llama-3.1-8B-Instruct | multilíngue com PT decente; **medir os dois** |
| Modelo leve | Gemma-3-4B-it / Qwen3-4B | fallback se 7B for lento demais |
| Config | `pydantic-settings` + `config.toml` | tira valores mágicos do código |
| Log | `logging` stdlib, JSON em ficheiro | substitui os `print` |
| Interface | CLI (`typer`) na Fase 1 | menor superfície; o valor está no pipeline |
| Testes | `pytest` | inclui o harness de avaliação |

### 4.2 Acréscimos por fase

| Fase | Pacote | Papel |
|---|---|---|
| 2 | `rank_bm25` | busca lexical para a fusão híbrida |
| 3 | `BAAI/bge-reranker-v2-m3` via `sentence-transformers` | rerank de top-20 → top-4 |
| 4 | — | enriquecimento offline usa o próprio Generator |
| 5 | `fastapi` + `uvicorn` + `gradio` | API e UI de chat |
| 5 | `anthropic` | backend remoto opcional |

### 4.3 O que deliberadamente **não** entra

- **LangChain.** Está no `requirements.txt` atual e não é usado por nenhuma linha.
  Para um pipeline deste tamanho, acrescenta abstração e instabilidade de API sem
  entregar nada. **Remover.**
- **Banco vetorial** (Chroma, Qdrant, pgvector). 2 800 vetores em memória. Um
  serviço a mais para operar, zero ganho.
- **IVF / HNSW / quantização de índice.** Aproximação existe para milhões de
  vetores. Aqui a busca exata é instantânea e não tem perda de recall.
- **Fine-tuning / LoRA.** Só faz sentido depois de a avaliação mostrar que o
  prompt esgotou o que dava. Sem métrica, é otimização cega.

---

## 5. Fases

Cada fase tem um critério de aceite verificável. Nenhuma fase começa antes de a
anterior passar.

### Fase 0 — Medir (meio dia)

Sem isto, todo o resto é palpite.

1. Criar o venv 3.12 com `uv`; confirmar que torch e sentence-transformers instalam
2. Instalar Ollama; baixar Qwen2.5-7B-Instruct Q4_K_M e um 4B
3. **Benchmark:** para cada modelo, medir prefill e decode em tok/s com prompts
   de 500 / 1500 / 3000 tokens
4. **Teste de voz:** pedir a cada modelo 5 poemas curtos em português europeu
   sobre temas pessoanos, sem RAG. Registar as saídas cruas no repositório.

**Aceite:** uma tabela de latência real e uma amostra de saída que permita
decidir 7B vs 4B com base em evidência, não em suposição. Se nenhum modelo local
produzir verso aceitável, essa é a descoberta mais valiosa possível — e muda o
plano para a Fase 5 imediatamente.

### Fase 1 — Pipeline honesto ponta a ponta (2–3 dias)

- Ingestão → `corpus.jsonl` com o modelo de domínio de §3.1
- Índice denso com manifesto sobre os chunks
- Filtro por voz, com seleção **explícita** (`/caeiro`, `/campos`, `/reis`,
  `/pessoa`) — zero custo, nunca erra, e adia o roteador
- Prompt de sistema por voz + few-shot recuperado
- Generator local via Ollama
- CLI com a voz corrente visível e as fontes citadas no fim da resposta

**Aceite:** dado "o que é a saudade?" com `/campos`, o sistema recupera poemas de
Campos (não de Reis), o prompt contém a pergunta, e a saída é verso em português
europeu. Verificado à mão em 20 perguntas.

### Fase 2 — Busca híbrida (1 dia)

BM25 sobre o corpo dos chunks, fusão RRF com o denso, pesos configuráveis.

**Aceite:** recall@5 no conjunto dourado (§6.1) melhora face ao denso puro. Se
não melhorar, reverter e registar o resultado negativo.

### Fase 3 — Rerank (meio dia)

Cross-encoder multilíngue sobre top-20 → top-4. Custa 1–3 s em CPU; medir se o
ganho justifica a latência somada ao prefill.

**Aceite:** MRR melhora e a latência total continua tolerável. É uma troca
explícita, decidida com número.

### Fase 4 — Enriquecimento e roteador (2 dias)

- Enriquecimento offline: tema, tom e imagens por poema, gravados no
  `corpus.jsonl` e indexados junto do verso (§2, mitigação 2)
- Roteador automático de voz: centróide de embedding por heterônimo, ou uma
  chamada curta ao LLM. Mantém o modo explícito como override.

**Aceite:** recall@5 melhora no conjunto dourado; o roteador acerta a voz em
≥80% de um conjunto rotulado à mão de 40 perguntas.

### Fase 5 — Interface e backend remoto (2 dias)

FastAPI + Gradio, histórico de conversa, e o `AnthropicRemote` como opção.

---

## 6. Avaliação

É onde a maioria dos projetos de RAG falha: sem métrica, cada mudança de prompt
é uma opinião.

### 6.1 Recuperação

Conjunto dourado de 40–60 perguntas, escritas à mão, cada uma com 1–3 poemas
esperados. Métricas: recall@5, recall@10, MRR. Roda em segundos, entra no
`pytest`, e é o que autoriza ou veta as Fases 2, 3 e 4.

### 6.2 Geração

Rubrica de 5 critérios, pontuada de 0 a 2:

1. **É verso?** (quebra de linha deliberada, não prosa com enters)
2. **Português europeu, registo de época?** (não PT-BR contemporâneo)
3. **A voz é a pedida?** (Caeiro não filosofa; Reis não usa versículo longo)
4. **Responde à pergunta**, em vez de divagar
5. **Não plagia** (ver §6.3)

Aplicada a um conjunto fixo de 25 perguntas, a cada mudança de prompt. Pode ser
pontuada à mão no início; depois, por LLM-juiz com a mesma rubrica.

### 6.3 Guarda de plágio — específica deste projeto

Dado um poema no contexto e a instrução "responda em verso", o caminho de menor
resistência do modelo é devolver o poema recuperado. Isso não é uma resposta, é
uma citação disfarçada.

Guarda: calcular a maior sobreposição de n-gramas (n=8) entre a resposta e cada
chunk do contexto. Acima de um limiar, regenerar com instrução reforçada; na
segunda falha, responder citando explicitamente o poema como citação. Barato,
determinístico, e mede exatamente o modo de falha que importa.

### 6.4 O oráculo de qualidade

O corpus inteiro tem ~325 mil tokens — cabe na janela de 1 M do `claude-opus-5`.
Dá para montar, **uma vez**, um baseline sem RAG nenhum: corpus completo no
prompt, com cache. Custo: ~2 USD de escrita de cache e ~0,17 USD por pergunta.

Isso não é o produto — é o **teto de qualidade** contra o qual medir o RAG local.
Saber o quanto se perde por ser local transforma "está bom?" numa pergunta com
resposta numérica.

---

## 7. Riscos

| Risco | Probabilidade | Mitigação |
|---|---|---|
| Nenhum modelo local de 4–8B escreve verso aceitável em PT-PT | **Média-alta** | Fase 0 descobre isto em meio dia, antes de qualquer investimento. Saída: backend remoto (Fase 5) ou fine-tune |
| Latência intolerável (prefill dominante) | Média | Contexto enxuto, cache de KV do prefixo estável, modelo 4B, streaming na UI |
| Recuperação semântica fraca em poesia | **Alta** | É o problema nomeado em §2; Fases 2 e 4 atacam-no diretamente, e a §6.1 mede |
| Modelo responde em PT-BR moderno | Alta | Prompt explícito + few-shot de época + critério 2 da rubrica |
| Plágio dos poemas recuperados | **Alta** | Guarda de n-grama (§6.3) |
| Wheels indisponíveis em Python 3.14 | Alta se ignorado | Fixar 3.12 na Fase 0 |

### Procedência do corpus

Fernando Pessoa morreu em 1935; a obra está em domínio público em Portugal e no
Brasil desde 2006 (70 anos após a morte). Não há impedimento legal.

Mas **a origem dos 2083 ficheiros não está registada em nenhum lugar do
repositório**. Isso deve ser documentado na Fase 1: de onde vieram, em que data,
sob que licença. É requisito de reprodutibilidade, não formalidade.

---

## 8. Fase remota (opcional, depois do local)

Para quando fizer sentido comparar ou servir a outros.

- SDK: `anthropic` (Python), `client.messages.create`
- Modelo: `claude-opus-5` — 1 M de contexto, 5 USD/MTok entrada, 25 USD/MTok saída
- Alternativa de volume: `claude-haiku-4-5` (1 / 5 USD por MTok)
- Cache de prompt: o prefixo estável (persona + few-shot fixo) com
  `cache_control: {"type": "ephemeral"}`; leitura de cache custa 0,1x

Custo por pergunta, estimado:

| Abordagem | Entrada | Custo/pergunta |
|---|---|---|
| RAG (≈2 k tokens) com Opus 5 | 2 k | ~0,018 USD |
| RAG com Haiku 4.5 | 2 k | ~0,0035 USD |
| Corpus inteiro em cache, Opus 5 | 325 k (cache) | ~0,17 USD |

O RAG continua a ser a escolha certa por custo. A terceira linha existe como
oráculo de avaliação (§6.4), não como produto.

---

## 9. Resumo das decisões

1. **CPU-only com GGUF quantizado.** Não há GPU; isto não é negociável.
2. **Python 3.12 via `uv`.** 3.14 não tem wheels.
3. **Medir antes de construir.** A Fase 0 pode invalidar o plano de geração local
   em meio dia, e isso é bom.
4. **Estrofe como unidade de chunk**, poema inteiro nos 96% que cabem.
5. **Metadado de heterônimo é grátis** — está em 100% dos ficheiros. Seleção
   explícita primeiro, roteador depois.
6. **Índice em `numpy`.** FAISS e bancos vetoriais são desproporcionados a 2 800
   vetores.
7. **Remover LangChain.** Declarado e não usado.
8. **Geração atrás de uma interface.** Mantém local-vs-remoto reversível.
9. **Avaliação antes de otimização.** Conjunto dourado + rubrica + guarda de
   plágio, tudo no `pytest`.
10. **O problema é recuperação de poesia, não RAG.** Busca híbrida e
    enriquecimento offline são o núcleo, não enfeites.
