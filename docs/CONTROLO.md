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
| **2 — Busca híbrida** | [`FASE-2.md`](FASE-2.md) · [relatório](FASE-2-RELATORIO.md) | ✅ **negativo**: +0,004 é ruído; `apt@3` cai 95%→90% |
| **3 — Rerank** | [`FASE-3.md`](FASE-3.md) · [P1](FASE-3-PASSO-1.md) · [relatório](FASE-3-RELATORIO.md) | ✅ **inconclusivo**: sinal inverte com o gabarito; `apt@3` inalterado |
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

**188 testes a passar.** `src/main.py`, `src/model.py` e `src/retriever.py`
(280 linhas, o código antigo corrigido no início da sessão) continuam no
repositório e serão substituídos no Passo 9.

---

## 3. Decisões fechadas, e de onde vêm

Nenhuma destas é preferência: todas têm medição por trás.

| Decisão | Valor | Vem de |
|---|---|---|
| Hardware | **CPU para gerar** — a iGPU existe e é 6x no prefill, 0,55x no decode | `lscpu`; [`fase-0/07-igpu-vulkan.md`](fase-0/07-igpu-vulkan.md) |
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
| 11 | Esta máquina não tem GPU utilizável | **Tem**: Intel Arc por Vulkan. Concluí de `nvidia-smi` ausente, vi o `lspci` dizer «Intel Graphics» e não verifiquei | [`fase-0/07-igpu-vulkan.md`](fase-0/07-igpu-vulkan.md) |
| 12 | A guarda de idioma estava com o limiar alto | **Não estava**: contra o corpus, 0,12 rejeita 3 de 1906 (0,16%). O errado era o **instrumento** — media registo, não língua | secção abaixo |

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
| Fracção de stopwords tomada por teste de língua | Verso telegráfico dado por língua errada: 38 s de regeneração por uma resposta boa |
| `fracao_lingua` caindo no pt quando a língua é `?` | 4 poemas reais dados por língua errada |
| Buffer do CLI sem `remover_preambulo` | O ecrã mostrava mais do que o veredicto julgara |

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
| [`fase-0/07-igpu-vulkan.md`](fase-0/07-igpu-vulkan.md) | a iGPU por Vulkan: prefill 6x, decode 0,55x — corrige a premissa «CPU-only» |
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

### Suporte a inglês implementado

Em resposta à correcção acima. **44 testes novos**, total 164.

| camada | alteração |
|---|---|
| `voices.py` | `PERSONAS` indexado por `(Voice, Lang)`; 6 personas, 2 novas: **Alexander Search** (EN) e **ortónimo em inglês** (EN) |
| `voices.py` | `REGRAS_LINGUA`, `REGRAS_SAIDA`, `REGRAS_NAO_COPIAR` por língua |
| `guard.py` | `fracao_lingua(texto, idioma)` com stopwords EN **incluindo as arcaicas** (`thy`, `thou`, `doth`, `hath`) — sem elas um soneto à maneira de Pessoa reprovaria na língua em que foi escrito |
| `guard.py` | brasileirismos e colocação pronominal só se aplicam a PT; preâmbulos meta em EN |
| `lexico.py` | dicionário `en` do aspell + vocabulário inglês do corpus (3784 tipos) |
| `plagio.py` | `REFORCO_EN` |
| `pipeline.py` | idioma atravessa `recuperar`, `responder`, `responder_em_fluxo`, `Turno` |
| `cli.py` | `--idioma`, comandos `/pt` `/en` `/search`; voz de língua única força a sua |

#### O mesmo padrão em inglês

O dicionário moderno desconhece `giveth` e `storiless`, que Pessoa **usa**, e o
corpus salva-os — exactamente como o `acção` e o `nocturno` em português. A
palavra inventada `danceth`, produzida na primeira resposta real do Search, foi
apanhada: formada por analogia com `giveth` e `doth`, não existe no corpus nem
no dicionário.

#### O inglês **não** é mais lento

A primeira corrida mostrou prefill de 41,4 s e 52,1 s, contra 7,8–20 s em
português, e eu suspeitei da língua. **Medido: é o contrário.**

| caso | prefill a frio | a quente |
|---|---|---|
| pt Caeiro (421 tok) | 34,3 s = 14,2 tok/s | 0,7 s |
| en Search (360 tok) | 25,2 s = **16,6 tok/s** | 0,7 s |
| en ortónimo (410 tok) | 30,3 s = **15,5 tok/s** | 0,7 s |

Duas causas, nenhuma linguística: o chip estava a **82 °C** após horas de carga,
e cada pergunta em inglês era a **primeira daquela persona**, logo sem cache.

**Consequência a registar: o orçamento de 45 s assume a máquina fria.** A frio
agora dá 14–17 tok/s contra os ~21 tok/s da Fase 0, e a mesma configuração sai
do orçamento sem nada ter mudado no código. Os números do plano são de uma
máquina em repouso.


---

## As duas fases de melhoria não melhoraram, e a causa é a mesma

| fase | resultado |
|---|---|
| **2 — busca híbrida (RRF)** | **negativo**: a melhor fusão dá +0,004 de nDCG@5, ruído a n=20, e o `apt@3` cai de 95% para 90% |
| **3 — reranking (cross-encoder)** | **inconclusivo**: o sinal inverte-se com o gabarito (−0,048 no original, +0,074 no ampliado) e o `apt@3` fica a 95% nos três |

### A causa, medida

| | documentos de nota 2 no top-5, somados em 20 perguntas |
|---|---|
| denso | **40** |
| fusão | 39 |

Há **84 documentos de nota 2** no gabarito, mediana de 4 por pergunta, e o top-5
só leva cinco. Reordenar **troca respostas boas por outras respostas boas** — e
o `apt@3` constante a 95% nos dois casos é a assinatura disso.

Não é propriedade dos algoritmos: é propriedade do corpus, medida desde a Fase 0
(67% dos candidatos agrupados eram aproveitáveis).

**A recuperação densa simples parece estar no tecto do que este corpus permite a
k=5.** O caminho que resta não é melhorar o ranking — é mudar o que se mede. O
`apt@3` de 95% diz que o sistema já encontra quase sempre uma resposta apta; a
pergunta aberta desde o Passo 7 da Fase 1 continua a ser a que importa, e é
sobre **geração**: se o modelo é a voz pedida quando não copia.

### Código mantido fora do caminho de execução

`fusion.py`, `search.py` e `rerank.py` ficam no repositório, testados, e **não
ligados ao pipeline** — não desligados por configuração, porque um componente
desligado por omissão é dívida. O que os limita é mensurável e pode mudar:
julgar as 20 perguntas restantes, agrupar a top-10, ou um orçamento de contexto
maior que 300 tokens.


---

## Correcção: «sem GPU» era incompleto

A Fase 0 concluiu **CPU-only** de `nvidia-smi` ausente. Vi o `lspci` reportar
«Intel Corporation Meteor Lake-P [Intel Graphics]» e não verifiquei. O Ollama
0.35.0 **detecta a iGPU por Vulkan e desliga-a por omissão**, com uma linha de
log que diz exactamente como a ligar:

```
msg="dropping integrated GPU; to enable, set OLLAMA_IGPU_ENABLE=1"
library=Vulkan name=Vulkan0 description="Intel(R) Graphics (MTL)"
```

Ligada, reporta `type=iGPU total="22.5 GiB" available="11.4 GiB"`.

| | CPU | iGPU | razão |
|---|---|---|---|
| prefill (421 tok, Caeiro pt) | 34,3 s · 14,2 tok/s | **5,5 s · 89,1 tok/s** | **6,28x** |
| prefill (360 tok, Search en) | 25,2 s · 16,6 tok/s | **4,9 s · 85,8 tok/s** | 5,20x |
| **decode** | 5,2–7,1 tok/s | **3,30 tok/s** (n=3) | **0,55x** |

**Nenhuma decisão fechada muda.** Para ~700 tokens de prompt e 150 de saída:
CPU a frio 74,3 s, iGPU a frio 53,3 s, **CPU a quente 25,7 s**, iGPU a quente
46,1 s. A iGPU ganha 21 s na primeira pergunta de cada voz e perde 20 s em todas
as seguintes — e com `keep_alive` de 30 min quase todas são «seguintes». A linha
«CPU-only» da §3 passa a «CPU para gerar», que é a afirmação que as medições
sustentam.

**O que isto reabre é o orçamento de contexto.** A Fase 0 rejeitou 1500 tokens
porque custavam 84 s de prefill; na iGPU custariam ~17 s. Se a Fase 4 precisar de
contexto maior — metadado enriquecido, por exemplo — a rejeição tem de ser
reavaliada, não herdada.

Dois avisos sobre esta medição: a iGPU foi medida com o pacote a 52–60 °C, mais
frio que a CPU nos seus próprios testes, o que a favorece; e nunca se testou o
desenho que ninguém considerou, **prefill na iGPU e decode na CPU**
(`llama.cpp --n-gpu-layers` parcial), que é onde os dois números apontam.

Detalhe e reprodução: [`fase-0/07-igpu-vulkan.md`](fase-0/07-igpu-vulkan.md).


---

## Correcção: a guarda de idioma media registo, não língua

Observado a correr o chatbot, à pergunta «qual é o futuro de portugal?». O
modelo respondeu isto, e a guarda rejeitou-o por «idioma improvável (fracção pt
0,077)», custando 38 s de nova geração:

> os passos ecoam / silêncio envolve / vogais cantam / pés descalços ligam terra
> ar / brotam esperanças / raízes aprofundam

É português inequívoco. O que lá não há são palavras funcionais: o registo é
telegráfico, sem artigos nem preposições.

**O meu primeiro diagnóstico — «o limiar está alto» — estava errado, e a medição
diz porquê.** Contra o corpus, 0,12 rejeita 3 de 1906 poemas portugueses
(0,16%), e um desses três é francês. Os poemas reais têm mediana 0,385 e p5
0,267. O limiar está bem posto; o instrumento é que mede a coisa errada.

### As três perguntas, em ordem de custo

| | pergunta | medida que a sustenta |
|---|---|---|
| 1 | há stopwords em abundância? | mediana 0,385 (pt) e 0,375 (en); resolve 99,8% dos casos sem subprocessos |
| 2 | outra língua pontua mais que a pedida? | pt dá 0,385 na própria e 0,048 na alheia; en 0,375 e 0,035. Em 2058 poemas, **zero** pontuam mais na língua errada |
| 3 | o dicionário reconhece o vocabulário? | **a única que não depende do registo** |

A terceira é a que separa o caso telegráfico do latim, e é a única que o faz:

| | dicionário pt | dicionário en |
|---|---|---|
| verso telegráfico (o caso observado) | **1,000** | 0,050 |
| latim (a falha da Fase 0) | **0,043** | 0,130 |
| poemas reais | p1 **0,857** | p1 **0,900** |

`MIN_FRACAO_DICIONARIO = 0,50` fica no meio dessa lacuna. A folga é deliberada:
o dicionário é pós-acordo de 1990 e rejeita 7,1% do vocabulário real de Pessoa.

**O teste relativo sozinho não bastaria**, e foi o teste que já existia que o
provou: o latim de `tests/test_guard.py` contém `se`, stopword portuguesa, logo
pontua 0,040 em pt contra 0,000 em inglês e passaria. Escrevi a versão relativa,
ela passou no meu próprio caso de latim, e reprovou no do repositório.

### Dois defeitos encontrados pelo caminho

**`fracao_lingua` caía no português quando não conhecia a língua.** `Lang.INDETERMINADO`
existe para poemas curtos demais para classificar, e `_STOPWORDS` não o cobre.
A primeira versão da correcção dava 4 poemas reais por língua errada — entre
eles «Iniguais pertencemos.» Sem autoridade sobre a língua, a guarda é agora
inerte.

**`poem_561` é francês, rotulado como português.** «Elle est si belle, / La
petite rebelle» — e é o único: medido com palavras funcionais francesas, nenhum
outro poema do corpus tem o francês a dominar (0,460 contra 0,046 de português).
A guarda sinaliza-o, e tem razão; a etiqueta do corpus é que está errada. O
teste afirma esse único positivo pelo nome, para que qualquer outro o faça
reprovar.

### E o preâmbulo que chegava ao ecrã

Na mesma resposta, o modelo começou por «Aqui está um poema novo, seguindo as
instruções:», e essa linha **foi impressa**. O `remover_preambulo` existe e a sua
regex apanha-a, mas o buffer de streaming do CLI só chamava `remover_cercas` e
`remover_eco_da_pergunta`. O texto validado não tinha o preâmbulo; o ecrã tinha.

A correcção não foi só acrescentar a chamada: a retenção passou a ser **por
linha, enquanto a linha limpa sair vazia**. Com uma só linha de retenção, um
preâmbulo seguido do eco da pergunta deixava o segundo passar.

### Sem dicionário

A guarda volta ao limiar absoluto, que é o comportamento antigo: rejeita. «Não
sei» não pode virar «está bem» — sem a ressalva, uma máquina sem `aspell`
perderia a guarda contra o latim. O preço é o falso positivo telegráfico voltar
nessas máquinas.
