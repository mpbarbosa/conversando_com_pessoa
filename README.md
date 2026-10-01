# PessoaBot

Chatbot que responde **em verso**, na voz de Fernando Pessoa ou de um heterónimo,
fundamentado por **RAG** sobre 2083 poemas. Corre **inteiramente local**: índice
e encoder nesta máquina, geração num Ollama local, sem chamada a API externa e
sem credenciais.

```
você [caeiro]> por que é que as pessoas acham melancólico o fim do dia?

  Nunca sei como é que se pode achar um poente triste.
  Só se é por um poente não ser uma madrugada.
  Mas se ele é um poente, como é que ele havia de ser uma madrugada?

  fontes: poem_1019, poem_1108
  412 ms recuperação · 18,7 s até ao 1.º verso · 300 tok
```

> ⚠️ O exemplo acima é ilustrativo do formato da saída, não uma transcrição de
> execução.

---

## O que está medido

Não há aqui nenhuma decisão por preferência: as que importam têm número por trás,
e os números estão em [`docs/CONTROLO.md`](docs/CONTROLO.md), que é o índice-mestre
do estado do projecto.

### Recuperação — linha de base do conjunto dourado

| recuperador | nDCG@5 | apt@3 |
|---|---|---|
| **denso** (`multilingual-e5-base`) | **0,719** | **95%** |
| BM25 (`rank_bm25`, stopwords revistas à mão) | 0,488 | 65% |

40 perguntas (10 por voz), 20 julgadas, **176 candidatos** avaliados por *pooling*
TREC — top-5 do denso **e** do BM25, deduplicado por grupo e ordenado por id para
não revelar o ranking de nenhum. Escala de relevância **graduada** (0/1/2), porque
`recall` com gabarito único é inválido neste corpus: Pessoa escreveu dezenas de
quadras sobre cada tema. `apt@3 = 95%` = em 19 de 20 perguntas há um poema de nota
2 no top-3. A **sobreposição entre os dois recuperadores é de mediana 1/5, e zero
em 9 das 40 perguntas** — vêem coisas diferentes, o que é o que dá sentido à fusão
híbrida da Fase 2. Relatório: [`docs/fase-1/08-RELATORIO.md`](docs/fase-1/08-RELATORIO.md).

### Sistema

| | |
|---|---|
| poemas | 2083 (2062 após deduplicação) |
| chunks indexados | 2290 |
| índice | 7,0 MB · busca em **5,57 ms** |
| construção do corpus · do índice | ~40 s · 383 s |
| latência de resposta | ~44 s a 500 tokens de contexto (CPU) |
| testes | **237, todos a passar** |

---

## Como funciona

```
data/pessoa_poems/ (2083 .txt)
        │
        ├─ src/corpus/parse.py      cabeçalho autor/título/corpo · 2083/2083
        ├─ src/corpus/dedupe.py     3 pares exactos + 18 grupos de variantes
        ├─ src/corpus/chunk.py      limite de 480 tokens, DERIVADO: 512−2−27−2
        └─ src/corpus/build.py      → data/corpus.jsonl
        │
        ├─ src/retrieval/encoder.py  multilingual-e5-base
        ├─ src/retrieval/index.py    índice denso em numpy + manifesto
        └─ src/retrieval/lexical.py  BM25
        │
        ├─ src/generation/prompt.py  persona no `system`, orçamento de tokens
        ├─ src/generation/ollama.py  qwen2.5:7b-instruct-q4_K_M, em fluxo
        ├─ src/guard.py              guardas de persona e de língua
        └─ src/plagio.py             guarda de cópia
        │
        └─ src/cli.py                `pessoa`
```

### Quatro decisões que valem explicação

**O índice é `numpy`, não FAISS.** 2290 × 768 = 7,0 MB; uma busca é um produto
matriz-vector de 1,8 M operações, microssegundos. O `IndexFlatIP` do FAISS faz
exactamente o mesmo cálculo — força bruta — com uma dependência a mais. IVF e HNSW
existem para milhões de vectores e aqui só trariam perda de *recall*.

**O índice recusa-se a carregar quando não é de confiança.** Os ids são
posicionais, logo o índice só é reutilizável acompanhado da ordem dos documentos
que o gerou. O manifesto compara encoder, assinatura do corpus, contagem **e
ordem**, e devolve `None` em vez de reconstruir em silêncio — porque um índice
velho carregado por engano **não dá erro: dá respostas erradas**.

**Os prefixos do e5 são impostos pela estrutura, não por convenção.** O modelo
exige `query: ` nas consultas e `passage: ` nos documentos; sem eles funciona e
devolve resultados piores, sem avisar. A defesa não é uma asserção: são **dois
métodos distintos**, `encode_queries` e `encode_passages`. Não há caminho para
encodar texto sem prefixo, logo não há como esquecer.

**A guarda de plágio não usa n-gramas, e isso foi uma correcção.** O plano
especificava sobreposição de 8-gramas. A primeira travessia completa do pipeline
devolveu **três de oito versos copiados do contexto com 2% de sobreposição de
8-gramas** — a cópia é paráfrase ao nível do verso: troca uma palavra, encurta,
reordena. Métrica trocada, e os limiares calibrados sobre 30 respostas reais
(`LIMIAR_VERSO = 0,72`, da lacuna entre 0,70 nas respostas limpas e 0,79 nas que
copiam). Mediana de versos copiados: **82% → 0%**.

---

## Correr

Precisa de **Python 3.12**, de [Ollama](https://ollama.com) local e dos 2083
ficheiros em `data/pessoa_poems/` (ver *Corpus*, abaixo — não vêm no repositório).

```bash
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
ollama pull qwen2.5:7b-instruct-q4_K_M
python -m src.cli --voz caeiro
```

Na primeira execução constrói o `corpus.jsonl` (~40 s) e o índice (~6,4 min) e
grava-os em `data/`; nas seguintes carrega-os, se o manifesto os aceitar. Use
`--verboso` para ver o progresso.

Dentro da conversa: `/auto` deixa o roteador propor a voz a cada pergunta
(72% de acerto, +0,5 s); `/rerank` reordena os candidatos por cross-encoder
(+0,090 de nDCG@5, +2,6 s); `/caeiro` `/campos` `/reis` `/pessoa` `/search` trocam de voz
e desligam o roteador,
`/pt` `/en` de língua, `/sair` sai. Cada resposta imprime as **fontes** usadas e os
tempos — o *prefill* domina a espera (58–89%), e mostrá-lo ensina o custo em vez de
o esconder.

```bash
pytest          # 237 testes, ~2 min
```

---

## Corpus

Os 2083 ficheiros **não estão no repositório**. Vêm do
[Arquivo Pessoa](http://www.arquivopessoa.net/); a obra de Pessoa está em domínio
público desde 2006 (morreu em 1935), mas **os termos de uso do sítio não estão
confirmados** e a transcrição de uma edição digital concreta pode ter protecção
própria. Procedência, defeitos conhecidos dos dados e situação de direitos em
[`data/README.md`](data/README.md).

Pela mesma razão ficam fora do repositório as **folhas de julgamento** do conjunto
dourado, que contêm os poemas inteiros (34 384 palavras). As **notas** ficam
publicadas — [`docs/fase-1/08-julgamentos.json`](docs/fase-1/08-julgamentos.json)
e [`docs/fase-0/06c-julgamentos.json`](docs/fase-0/06c-julgamentos.json), que são
ids e graus sem texto — e os scripts que geram as folhas também
([`pool_dourado.py`](docs/fase-1/pool_dourado.py),
[`pool_julgamento.py`](docs/fase-0/pool_julgamento.py)), de modo que com o corpus
local a avaliação é reproduzível por inteiro.

Derivados reconstruíveis (`corpus.jsonl`, `index.npy`, `index.manifest.json`)
também ficam fora, por serem precisamente isso.

---

## Estado

| Fase | Estado |
|---|---|
| **0 — Medir** (hardware, modelos, encoders, voz às cegas) | ✅ completa, com adenda de 3 correcções |
| **1 — Pipeline** (parsing → índice → vozes → gerador → guardas → conjunto dourado → CLI) | ✅ **completa, 9 de 9** |
| **2 — Busca híbrida** (fundir denso + BM25) | ⬜ desbloqueada pela linha de base |
| **3 — Rerank** | 🔄 candidato escolhido por *benchmark* (MiniLM-L12 a 1694 tok/s contra 90 do bge-m3) |
| **4 — Enriquecimento e roteador de voz** | ✅ roteador em `/auto` (72%, 92% com etiqueta múltipla); enriquecimento **vetado** por medição |
| **5 — Interface e geração remota** | ⬜ |

Limitações conhecidas e não resolvidas estão listadas em
[`docs/CONTROLO.md`](docs/CONTROLO.md) §5 — entre elas a principal pergunta aberta:
**sem copiar, nem sempre sai a voz pedida**, porque os versos originais explicam e
atribuem significado, o que Caeiro proíbe.

> ⚠️ [`ROADMAP.md`](ROADMAP.md) descreve o objectivo **anterior** deste repositório
> — um chatbot CLI com Flan-T5 — e o «Ready for Production» dele refere-se a esse
> escopo. Para o estado actual, leia [`docs/CONTROLO.md`](docs/CONTROLO.md).
> `src/{main,model,retriever}.py` são desse sistema anterior e continuam no
> repositório até serem removidos.

---

## Documentação

| | |
|---|---|
| [`docs/CONTROLO.md`](docs/CONTROLO.md) | **índice-mestre**: estado, decisões com a medição de origem, correcções a afirmações próprias, defeitos encontrados nos próprios instrumentos de medida, limitações |
| [`docs/PLANO-RAG-LOCAL.md`](docs/PLANO-RAG-LOCAL.md) | o plano original, em 5 fases |
| [`docs/FASE-0.md`](docs/FASE-0.md) · [relatório](docs/FASE-0-RELATORIO.md) | medição de hardware, calibração, escolha de gerador às cegas e de encoder |
| [`docs/FASE-1.md`](docs/FASE-1.md) | o pipeline, passo a passo |
| [`docs/FASE-2.md`](docs/FASE-2.md) · [`FASE-3.md`](docs/FASE-3.md) | busca híbrida e rerank, planeadas |
| [`docs/BIBLIOGRAFIA.md`](docs/BIBLIOGRAFIA.md) | as fontes, e onde cada uma falhou na verificação |
| `docs/fase-*/` | dados brutos e *scripts* de *benchmark* de cada fase |

Duas secções do `CONTROLO.md` são deliberadas e provavelmente mais úteis que o
resto: **«Correcções a afirmações minhas»** (10 entradas, cada uma com o que foi
afirmado, o que a medição mostrou e onde) e **«Defeitos encontrados nos meus
próprios instrumentos»** — por exemplo, o cache de KV reaproveitado entre
repetições de um *benchmark*, que reportou *prefill* a 25 625 tok/s e invalidou
4 horas de dados, e uma avaliação de voz **não cega** que produziu um viés que
mudou a recomendação de modelo.

## Licença

Código sem licença declarada. O corpus não é distribuído aqui; ver
[`data/README.md`](data/README.md).
