# Documento de controlo — PessoaBot

Estado do projecto, decisões tomadas, correcções feitas e próximos passos.
**Actualizado em 2026-10-01.**

Este é o índice-mestre. Os detalhes estão nos documentos por fase; aqui está o
que está feito, o que falta, e o que mudou de ideias pelo caminho.

---

## 1. Objectivo

Chatbot que responde **em verso**, na voz de Fernando Pessoa ou de um
heterónimo, fundamentado por RAG sobre 2083 poemas. Execução **local** nesta
máquina, com a camada de geração plugável para permitir uma fase remota depois.

> O `ROADMAP.md` descreve o objectivo **anterior** do repositório — um chatbot
> CLI com RAG e um modelo gratuito — e nesse escopo o «✅ Ready for Production»
> dele está correcto. Não o leia como se descrevesse o objectivo actual.

---

## 2. Estado por fase

| Fase | Documento | Estado |
|---|---|---|
| **0 — Medir** | [`FASE-0.md`](FASE-0.md) · [relatório](FASE-0-RELATORIO.md) | ✅ **completa**, com adenda de 3 correcções |
| **1 — Pipeline** | [`FASE-1.md`](FASE-1.md) | ✅ **completa** (9 de 9) |
| **2 — Busca híbrida** | [`FASE-2.md`](FASE-2.md) | ⬜ **desbloqueada**: denso 0,719 · BM25 0,488 · sobreposição 1/5 |
| **3 — Rerank** | [`FASE-3.md`](FASE-3.md) · [Passo 1](FASE-3-PASSO-1.md) | 🔄 Passo 1 feito; **2–4 desbloqueados** |
| **4 — Enriquecimento e roteador** | §Fase 4 do [plano](PLANO-RAG-LOCAL.md) | ⬜ não planeada em detalhe |
| **5 — Interface e remoto** | §Fase 5 do [plano](PLANO-RAG-LOCAL.md) | ⬜ não planeada em detalhe |

### Fase 1, passo a passo

| # | Passo | Estado | Entregável |
|---|---|---|---|
| 1 | Modelo de domínio e parsing | ✅ | `src/corpus/{models,parse}.py` · 11 testes |
| 2 | Deduplicação | ✅ | `src/corpus/dedupe.py` · 10 testes |
| 3 | Chunking | ✅ | `src/corpus/chunk.py` · `src/tokens.py` · 12 testes |
| 4 | Índice | ✅ | `src/corpus/build.py` · `src/retrieval/{encoder,index}.py` · 14 testes |
| 5 | Vozes e prompt | ✅ | `src/voices.py` · `src/generation/prompt.py` · `src/guard.py` · 29 testes |
| 6 | Gerador | ✅ | `src/generation/{base,ollama}.py` · 15 testes |
| 7 | Guarda de plágio | ✅ | `src/plagio.py` · `src/pipeline.py` · 11 testes |
| 8 | **Conjunto dourado** | ✅ | `src/avaliacao.py` · `src/retrieval/lexical.py` · `tests/test_retrieval_gold.py` · 8 testes |
| 9 | CLI | ✅ | `src/cli.py` · `pipeline.responder_em_fluxo` · 7 testes |

**121 testes a passar.** `src/main.py`, `src/model.py` e `src/retriever.py`
(280 linhas, o código antigo corrigido no início da sessão) continuam no
repositório e serão substituídos no Passo 9.

---

## 3. Decisões fechadas, e de onde vêm

Nenhuma destas é preferência: todas têm medição por trás.

| Decisão | Valor | Vem de |
|---|---|---|
| Hardware | **CPU-only**, sem GPU NVIDIA | `lscpu`, `nvidia-smi` ausente |
| Threads | **10**, `taskset -c 0-11` | varredura monotónica; LP-E a 2100 MHz excluídos |
| Python | **3.12** via `uv` | 3.14 sem wheels de torch/faiss |
| Gerador | **`qwen2.5:7b-instruct-q4_K_M`** | 7,0 às cegas vs 6,5 do llama3.1:8b |
| Orçamento da parte variável | **300 tokens** | 168 tok → 33,7 s; 448 tok → 53,7 s |
| Persona no `system` | 313 tok, em cache | 13,63 s → 0,91 s da 2ª pergunta |
| `repeat_penalty` | **1,1** | resolveu a degeneração em ciclo |
| Regra anti-cópia no `system` | preventiva, em cache | mediana de versos copiados: **82% → 0%** |
| `LIMIAR_VERSO` de plágio | **0,72** | lacuna entre 0,70 (limpas) e 0,79 (copiam) |
| `LIMIAR_FRACAO` de plágio | **0,10** | 21% de repetição, 33,8 s de média |
| Encoder | **`intfloat/multilingual-e5-base`** | `maxlen=512` cobre 96% dos poemas inteiros |
| Lote de embedding | **8** | 1,6x mais rápido que 64, o inverso do esperado |
| Limite de chunk | **480 tokens** | 512 − 2 − 27 − 2 = 481, derivado |
| Índice | **`numpy`**, não FAISS | 2290 × 768 = **7,0 MB**; busca em 5,57 ms |
| Reranker candidato | **MiniLM-L12-H384** (~120M) | 1694 tok/s contra 90 do bge-m3 de 568M |
| LangChain | **removido** | declarado no `requirements.txt`, usado em zero linhas |

### Números do sistema

| | |
|---|---|
| poemas | 2083 (2062 após deduplicação) |
| chunks indexados | **2290** |
| índice | 7,0 MB · busca 5,57 ms |
| recuperação | **nDCG@5 = 0,719** (denso) · 0,488 (BM25) · apt@3 = 95% |
| corpus.jsonl | 3,0 MB · build em ~40 s |
| construção do índice | 383 s (6,4 min) |
| latência de resposta prevista | ~44 s a 500 tokens de contexto |

---

## 4. Correcções a afirmações minhas

Registadas porque várias eram convincentes e erradas, e porque o padrão
interessa: **a aritmética estava quase sempre certa e o modelo mental errado**.

| # | Afirmei | Realidade | Onde |
|---|---|---|---|
| 1 | O ROADMAP está errado sobre estar pronto | Está correcto **para o objectivo anterior**; eu julguei contra o novo | corrigido pelo utilizador |
| 2 | Qualidade em português do Flan-T5 não se sustenta | Afirmei sem correr o código (não havia venv nem faiss) | §correcção da 1ª avaliação |
| 3 | Prefill de 1500 tok: 8–15 s (3B), 20–45 s (7–8B) | **31 s / 84 s** — optimista 2–4x. Assumi que 14 threads AVX2 ajudariam; são 2 P-cores | `FASE-0-RELATORIO.md` §2 |
| 4 | Serafim-335m-ir é o candidato preferencial | **`maxlen=128`** — trunca ¼ dos poemas. Recomendei do artigo sem verificar | `BIBLIOGRAFIA.md` 4.1 |
| 5 | O 8B deu as únicas amostras 10/10 | **Viés**: às cegas o 7B também deu | adenda A.2 |
| 6 | A contenção de rede invalidou os tempos do e5 | Valia **5%**. Fui excessivamente cauteloso | adenda A.3 |
| 7 | `poem_17`/`poem_23` são esboços da mesma ode | **Não são**: 0,111 de similaridade, partilham só o incipit | correcção de facto |
| 8 | Há 1 par de duplicados exactos | **3 pares** + 18 grupos de variantes = 21 poemas | idem |
| 9 | `poem_12`/`poem_619` não são variantes | **São**: contenção. Diagnostiquei lendo 320 caracteres | §Passo 2 |
| 10 | A extrapolação de rerank falhou por atenção quadrática | Explicação **errada**, tirada de resultados parciais. A estimativa era optimista por 1,9x | `FASE-3-PASSO-1.md` |

### Defeitos encontrados nos meus próprios instrumentos

| Defeito | Consequência se não apanhado |
|---|---|
| **KV cache reaproveitado** entre repetições do benchmark | Prefill reportado a **25 625 tok/s**; 4 h de dados inválidos |
| Flag de throttling com `REPS=2` | «Queda monotónica» = 50% por ruído; não-informativa |
| `repeat_penalty` não definido | 8B degenerou em ciclo; atribuído ao modelo em vez do arranque |
| Avaliação de voz **não cega** | Viés específico que mudou a recomendação de modelo |
| Limpeza de título apagava 3 poemas | «Vou atirar uma bomba ao destino.» — título **é** o poema |
| Sem pausa de arrefecimento no bench de rerank | Variância de 6x na mesma configuração |
| Jaccard de n-gramas para variantes | Não separa variantes de poemas distintos |

---

## 5. Limitações conhecidas, não resolvidas

| Limitação | Impacto | Estado |
|---|---|---|
| Representante de variantes é «o mais longo» | Em `poem_1000`/`poem_629` elege o que tem erro de transcrição | aceite; sem correcção barata |
| Duplicação por tradução não detectável | `poem_1794` fica no corpus | resolvida pelo filtro de idioma |
| Avaliação de voz com **um só avaliador** | Não é medição intersubjectiva | assumido |
| Throttling térmico até 101 °C | Latências com precisão menor que as casas decimais sugerem | ressalva registada |
| Qualidade do reranker em PT-PT desconhecida | Pode piorar o ranking | mede-se no Passo 2 da Fase 3 |
| **Sem copiar, nem sempre é a voz pedida** | os versos originais explicam e atribuem significado, o que Caeiro proíbe | pergunta aberta principal; Passo 8 |
| Alguns poemas são atractores (`poem_3426`, `poem_2832`) | muito recuperados e muito copiados | pode exigir MMR na recuperação |
| **Streaming imprime antes de validar** | só o 1.º verso é retido; brasileirismos a meio só são avisados | aceite; buffer total custaria o streaming |
| Enviesamento de pooling | sistema novo é penalizado por construção | procedimento escrito no topo de `test_retrieval_gold.py` |
| Pool de top-5 era raso | 3 gabaritos estavam em 6.º–9.º | top-10 na próxima ronda |
| **Tabacaria em 37.º sem explicação** | hipótese do chunking testada e refutada | investigar chunk a chunk |
| Recolha do corpus não reproduzível | nenhum script no histórico | registado em `data/README.md` |
| `src/main.py` e companhia ainda no repo | Dois sistemas em paralelo | até ao Passo 9 |

### Sobre direitos

Fernando Pessoa morreu em 1935; obra em domínio público em Portugal e no Brasil
desde 2006. **Sem impedimento legal.** Mas a origem dos 2083 ficheiros não está
registada em nenhum lugar — de onde vieram, em que data, sob que licença. É
requisito de reprodutibilidade e continua pendente.

---

## 6. Próximos passos

### Imediato — Fase 1 Passo 5: vozes e prompt

Orçamento derivado da medição:

```
500 tokens:  ~90 persona · ~30 pergunta · ~40 forma e PT-PT · ~340 contexto
             -> 3-4 poemas curtos (mediana 93 tokens)
```

Mitigação de PT-BR, que a Fase 0 mostrou ser o defeito mais consistente:
instrução de enclíticas, **few-shot da própria voz vindo da recuperação** (a
aposta mais forte), e lista de interdições povoada com os casos medidos —
`fumaça`→`fumo`, `ator`→`actor`, `demônios`→`demónios`,
`espetáculo`→`espectáculo`, `refletem`→`reflectem`, `galhos`→`ramos`.

Guarda de saída contra os quatro modos de falha vistos às cegas: preâmbulo meta,
quebra de persona nomeando o heterónimo, resposta em latim, ortografia BR.

### Depois, em ordem

| | Passo | Desbloqueia |
|---|---|---|
| 1 | Fase 1 Passo 6 — gerador com streaming | — |
| 2 | Fase 1 Passo 7 — guardas | — |
| 3 | **Fase 1 Passo 8 — conjunto dourado** | **Fases 2 e 3** |
| 4 | Fase 1 Passo 9 — CLI | critério de saída da Fase 1 |
| 5 | Fase 2 completa | — |
| 6 | Fase 3 Passos 2–4 | — |

O **Passo 8 é o nó**: sem ele, nem a busca híbrida nem o rerank podem ser
avaliados, e ambos existem exclusivamente para melhorar um número.

### Pendências de limpeza

```
[ ] repetir o teste de voz do 8B com repeat_penalty (adenda A.3 só corrigiu o arranque)
[ ] repetir o bench de rerank com pausa de arrefecimento
[ ] medir num_predict=110 (poupa ~4-5s; medicao contaminada por cache)
[ ] remover src/{main,model,retriever}.py no Passo 9
[ ] remover langchain do requirements.txt
[ ] actualizar .github/copilot-instructions.md para a arquitectura nova
```

---

## 7. Mapa de documentos

| Documento | Conteúdo |
|---|---|
| [`PLANO-RAG-LOCAL.md`](PLANO-RAG-LOCAL.md) | arquitectura, stack, 5 fases, avaliação, riscos |
| [`BIBLIOGRAFIA.md`](BIBLIOGRAFIA.md) | 23 referências verificadas, em ordem de leitura |
| [`FASE-0.md`](FASE-0.md) · [`FASE-0-RELATORIO.md`](FASE-0-RELATORIO.md) | protocolo e resultados da medição |
| [`FASE-1.md`](FASE-1.md) | 9 passos do pipeline |
| [`FASE-2.md`](FASE-2.md) | busca híbrida, BM25, ortografia histórica |
| [`FASE-3.md`](FASE-3.md) · [`FASE-3-PASSO-1.md`](FASE-3-PASSO-1.md) | rerank e latência medida |
| `fase-0/` | 21 ficheiros de evidência e 5 scripts |
| `fase-3/` | latência dos rerankers e script |

### Código

```
src/
├── tokens.py              ✅ contagem com o tokenizador real
├── corpus/
│   ├── models.py          ✅ Poem, Chunk, Voice, Lang
│   ├── parse.py           ✅ 2083/2083 parseados
│   ├── dedupe.py          ✅ exacto + variante + incipit
│   ├── chunk.py           ✅ 2290 chunks, nenhum > 512 tok
│   └── build.py           ✅ pipeline -> data/corpus.jsonl
├── retrieval/
│   ├── encoder.py         ✅ e5 com prefixos impostos pela API
│   └── index.py           ✅ numpy + manifesto
├── generation/            ⬜ vazio
└── {main,model,retriever}.py   ⚠️ código antigo, a substituir

tests/   47 testes a passar
```

### Como correr

```bash
source .venv/bin/activate
python -m pytest tests/ -q                      # 47 testes, ~90 s
python -c "from src.corpus.build import build; build()"   # corpus.jsonl, ~40 s
```

### Correr o chatbot

```bash
./pessoa --voz caeiro
```

O `./pessoa` existe para evitar um atrito real: `source .venv/bin/activate &&
python -m src.cli` **não funciona** com `setopt correct` no zsh, porque o zsh
verifica a ortografia da linha inteira **antes** de executar qualquer parte
dela. O `python` é analisado enquanto o `PATH` é ainda o antigo, e o zsh
oferece-se para o corrigir para `python3`. Um `rehash` na mesma cadeia não
ajuda, pela mesma razão. O script invoca `.venv/bin/python` directamente, logo
não há `python` na linha de comando para corrigir.

O Ollama tem de estar a correr (`ollama serve`). A primeira execução constrói
`corpus.jsonl` (~40 s) e o índice (~6 min); depois arranca em segundos.

Também vale para os testes:

```bash
.venv/bin/python -m pytest tests/ -q
```

---

## Correcção: a obra em inglês não é contaminação

Apontado pelo proprietário do repositório em 2026-10-01.

**Pessoa escreveu obra em inglês.** Foi educado em Durban, em inglês, e os *35
Sonnets*, o *Antinous* e as *Inscriptions* são dele. **Alexander Search é um
heterónimo que escrevia em inglês**, com 50 poemas no corpus.

Eu tratei os 152 poemas ingleses como ruído a filtrar, e isso aparecia em três
lugares do código, todos agora corrigidos:

| onde | dizia | passa a |
|---|---|---|
| `dedupe.py` | a duplicação por tradução é «resolvida pelo filtro de idioma» | **não são marcados**; a `NAVAL ODE` está catalogada sob Campos e a sua autoria não está estabelecida aqui |
| `lexico.py` | o inglês «contaminaria» o vocabulário de referência | a referência é PT **porque avalia respostas em PT**, não porque o inglês seja ruído |
| `index.py` | `idioma=PT` resolve a duplicação | `idioma=PT` **porque a resposta é em português**; é preferência de consulta, não juízo sobre o corpus |

### O que fica em falta

| voz | poemas | estado |
|---|---|---|
| Alexander Search | 50 em inglês | **sem persona; o sistema não o serve** |
| Charles Robert Anon | 9 em inglês | idem |
| ortónimo em inglês | 92 (*Sonnets*, *Inscriptions*) | inacessível com `idioma=PT` |
| Campos em inglês | 2 | idem |

Servir estes exige mais que trocar um parâmetro: **todas as guardas são
específicas do português** — colocação enclítica, brasileirismos, fracção de
stopwords portuguesas, e o dicionário `pt_PT` da guarda lexical. Uma voz inglesa
precisaria de persona própria, guardas conscientes da língua e do dicionário
`en` do aspell, que está instalado.

Fica como trabalho identificado, não como defeito escondido. É a decisão de
produto mais substantiva em aberto: um PessoaBot que não fala a língua em que
Pessoa publicou os *35 Sonnets* é um PessoaBot incompleto.
