# Fase 1 — Pipeline honesto ponta a ponta

Protocolo de execução da Fase 1 de [`PLANO-RAG-LOCAL.md`](PLANO-RAG-LOCAL.md),
revisto pelas conclusões de [`FASE-0-RELATORIO.md`](FASE-0-RELATORIO.md).

**Objectivo:** um chatbot CLI que, dada uma pergunta e uma voz escolhida,
recupera poemas dessa voz e responde **em verso**, em português europeu, dentro
do orçamento de latência medido.

**Critério de saída:** 20 perguntas verificadas à mão produzem verso em PT-PT
na voz pedida, com a pergunta presente no prompt e as fontes citadas.

---

## 0. O que a Fase 0 mudou neste plano

Quatro decisões já não são escolhas — são consequências de medição:

| Decisão | Vem de |
|---|---|
| Gerador: `qwen2.5:7b-instruct-q4_K_M` via Ollama | 7,0 às cegas vs 6,5 do 8B; ver adenda A.2 |
| **Orçamento de contexto: 500 tokens**, não 1500 | 1500 → 104 s (inutilizável); 500 → 44 s |
| Encoder: `intfloat/multilingual-e5-base`, `batch_size=8` | `maxlen=512`; lote 8 é 1,6x mais rápido que 64 |
| `threads=10`, `taskset -c 0-11` | varredura monotónica, LP-E excluídos |

E duas correções ao desenho original:

- **O conjunto dourado não pode ter gabarito único.** A §6.1 do plano
  especificava «1–3 poemas esperados»; a redundância temática do corpus
  invalida isso. Usar relevância graduada (0/1/2) sobre candidatos agrupados.
- **A detecção de duplicados precisa de dois modos novos**: por tradução
  (`poem_1794` é a *Ode Marítima* em inglês) e por variante (`poem_17` e
  `poem_23` são esboços da mesma ode).
- **Quatro modos de falha novos**, vistos na avaliação às cegas (adenda A.4):
  resposta em latim, quebra de persona nomeando o heterónimo, preâmbulo meta
  («Aqui está um poema...»), e ortografia brasileira com casos concretos. Os
  três primeiros são detectáveis por pós-processamento determinístico.

---

## 1. Arquitectura-alvo

```
src/
├── config.py          # orçamentos, nomes de modelo, caminhos
├── corpus/
│   ├── models.py      # Poem, Chunk, Voice, Lang  (dataclasses)
│   ├── parse.py       # .txt -> Poem   (cabeçalho, limpeza, idioma)
│   ├── dedupe.py      # exacto + tradução + variante
│   ├── chunk.py       # Poem -> [Chunk]  (estrofe)
│   └── build.py       # pipeline -> data/corpus.jsonl
├── retrieval/
│   ├── encoder.py     # e5 com prefixos query:/passage:
│   ├── index.py       # numpy + manifesto
│   └── search.py      # filtro por voz/idioma + top-k
├── generation/
│   ├── base.py        # Generator (Protocol)
│   ├── ollama.py      # OllamaGenerator
│   └── prompt.py      # orçamento de 500 tok, pergunta primeiro
├── voices.py          # poética de cada heterónimo
├── guard.py           # guarda de plágio (n-grama)
└── cli.py             # typer

tests/
├── test_parse.py
├── test_chunk.py
├── test_dedupe.py
├── test_prompt_budget.py
└── test_retrieval_gold.py   # conjunto dourado
```

`src/main.py`, `src/model.py` e `src/retriever.py` (280 linhas) são
**substituídos**. O `retriever.py` actual tem lógica boa — manifesto,
fingerprint, normalização — que migra para `retrieval/index.py`.

---

## 2. Passos

### Passo 1 — Modelo de domínio e parsing (meio dia)

```python
class Voice(StrEnum):
    ORTONIMO = "ortonimo"; CAMPOS = "campos"; REIS = "reis"
    CAEIRO = "caeiro"; SOARES = "soares"; SEARCH = "search"; OUTRO = "outro"

@dataclass(frozen=True)
class Poem:
    id: str; author: str; voice: Voice; title: str
    body: str; language: Lang; stanzas: tuple[str, ...]; n_tokens: int
```

Parsing: autor na linha 1, `Titulo:` por regex — **100% de cobertura medida**
nos 2083 ficheiros, sem excepções. Limpeza: remover o título repetido no início
do corpo (82% dos casos); corrigir o mojibake de `poem_224.txt`; normalizar
`'ร\x81lvaro de Campos'` → `Álvaro de Campos`.

Idioma por stopwords — heurística já validada na análise inicial (1928 PT /
154 EN / 1 indeterminado).

**Aceite:** `test_parse.py` verifica que todos os 2083 ficheiros produzem um
`Poem` com voz conhecida, e que a distribuição bate na medida: Pessoa 1298,
Campos 323, Reis 252, Caeiro 120, Search 52, Soares 6.

### Passo 2 — Deduplicação ✅ FEITO

**O desenho mudou por medição.** O plano previa três modos; a medição mostrou
que dois estavam justificados por leitura errada dos dados e que um terceiro
fenómeno, não previsto, era o relevante.

| Modo planeado | Resultado |
|---|---|
| Exacto | **mantido** — e são **3** pares, não 1: o hash sobre o ficheiro em bruto subestimava |
| Tradução | **abandonado** — não detectável. `poem_135`/`poem_1794` tem similaridade de verso **0,000** e é tradução **parcial** (1094 contra 7325 palavras), logo nem a razão de comprimento o apanha. Resolvido pelo filtro de idioma, que já era necessário |
| Variante | **mantido, mas com outra métrica** — e o caso que eu citei (`poem_17`/`poem_23`) **não é** variante: 0,111 de similaridade, partilham só o incipit |
| *(novo)* Incipit partilhado | **18 grupos, 40 poemas.** Relação registada, **não** duplicação — colapsá-la perderia odes distintas |

**A métrica.** Jaccard de n-gramas de palavra não serve: pequenas diferenças
palavra-a-palavra destroem a sobreposição sem mudar o poema. `poem_3222`/
`poem_955` são a mesma composição («umbrela»/«umbela») e dão 0,457, enquanto
poemas distintos sobre o mesmo tema dão 0,480. A métrica adoptada é a **fracção
de versos do poema mais curto com par próximo no outro**, que normalizada pelo
mais curto faz a **contenção** pontuar alto — a relação certa num corpus de
esboços. Separa limpo: exactos 1,000 · variantes 0,875–1,000 · incipit 0,111 ·
tradução 0,000. Limiar em **0,70**, com folga grande em ambos os lados.

**Resultado:** 3 grupos exactos + 18 grupos de variantes = **21 poemas
marcados**, 2062 representantes. 35 s sobre o corpus inteiro, com blocagem por
índice invertido de trigramas.

**Limitação registada.** O representante é «o mais longo do grupo». Funciona
para contenção, mas é arbitrário para variantes de transcrição quase iguais —
em `poem_1000`/`poem_629` escolhe o `poem_629`, que ganha por 2 palavras mas
tem um erro de transcrição («mais como vida e próxima» em vez de «mais comovida
e próxima»). Para recuperação é indiferente; para citação não. Sem correcção
automática barata.

**Consequência para o conjunto dourado (Passo 8).** O `poem_1000` é gabarito de
uma pergunta do conjunto de fumo e passou a não-representante. O conjunto
dourado tem de comparar **grupos**, não ids: uma resposta conta se estiver no
mesmo grupo de deduplicação que um id de gabarito.

### Passo 3 — Chunking ✅ FEITO

**O limite de 480 tokens é derivado, não escolhido.** O e5 tem
`model_max_length=512`, e o texto indexado leva prefixos:

```
512 − 2 ("passage: ") − 27 (pior caso de "Autor — Título") − 2 (especiais) = 481 → 480
```

**Medição com o tokenizador real** (a estimativa de 1,45 tokens/palavra do
planeamento estava certa: real 1,469):

| | valor |
|---|---|
| tokens por poema | mediana **93**, p95 448, máx 12 790 |
| poemas acima de 480 tokens | **98** (4,7%) |
| estrofes | 6619, mediana 34 tokens, **12 excedem 480 sozinhas** |

**Resultado:** 2062 poemas (sem duplicados) → **2290 chunks**, em 1,5 s.
97 poemas partidos; a *Ode Marítima* em **43 chunks**. Texto indexado: mediana
116 tokens, **máximo 500** — nenhum chunk excede o limite do e5.

Índice previsto: 2290 × 768 × 4 bytes = **7,0 MB**. Confirma que `numpy` basta
e que FAISS seria desproporcionado.

**Dois textos por chunk, de propósito.** `text` é o que vai no **prompt**:
verso puro, porque o gerador deve ver poesia e não fichas bibliográficas.
`indexed_text` leva «Autor — Título» à cabeça, que dá ao encoder contexto que o
verso sozinho não carrega.

**Regras garantidas por teste:** nunca se parte um verso; a união dos chunks de
um poema contém todos os seus versos; janelas consecutivas sobrepõem uma
estrofe, excepto quando uma estrofe sozinha enche a janela — aí não há
sobreposição, para garantir progresso e evitar ciclo infinito. Um verso que
sozinho exceda o limite sai sozinho, com excesso aceite: partir um verso é pior
que exceder o limite.

Os duplicados marcados no Passo 2 são **excluídos do índice** por omissão —
indexar um poema e a sua variante devolveria o mesmo poema duas vezes.

### Passo 4 — Índice (meio dia)

Migrar `retrieval/index.py` do actual `retriever.py`, trocando FAISS por
`numpy`: ~2800 chunks × 768 dims = 8,6 MB, produto interno directo. Manter o
manifesto (encoder, ordem, fingerprint) — é o que impede o desalinhamento
id↔texto.

e5 **exige** os prefixos `query: ` e `passage: `. Sem eles degrada em silêncio.
Isto vai numa asserção, não num comentário.

**Aceite:** `test_retrieval_gold.py` reproduz o resultado da Fase 0 no conjunto
de fumo; recarregar o índice em processo novo preserva o alinhamento.

### Passo 5 — Vozes e prompt ✅ FEITO

**Entregáveis:** `src/voices.py`, `src/generation/prompt.py`, `src/guard.py`,
29 testes. Relatório da medição:
[`fase-1/05-RELATORIO-ORCAMENTO.md`](fase-1/05-RELATORIO-ORCAMENTO.md).

#### Personas: descrever o olhar, não o nome

As duas amostras 10/10 de toda a Fase 0 vieram de prompts que descreviam **como**
Caeiro olha, não de «escreve como Caeiro». As quatro personas descrevem postura,
forma e o que evitar.

Cada uma combate um modo de falha observado às cegas: a de Reis diz
explicitamente «a dicção é latinizante, a língua não é latim: nunca escrevas em
latim», porque uma amostra saiu inteiramente em latim agramatical.

#### Duas camadas, por razão medida

A persona vive no `system`, a pergunta e o contexto no `user`. Medido: com
`system` fixo, os 313 tokens da persona passam de **13,63 s a 0,91 s** da
segunda pergunta em diante.

É o mesmo mecanismo que invalidou o benchmark da Fase 0, onde tive de o
neutralizar com um nonce. Lá era defeito de medição; aqui é o que torna uma
persona detalhada acessível.

#### Orçamento: 300 tokens, derivado

| poemas | user tok | prefill quente | total quente |
|---|---|---|---|
| 1 | 168 | 10,7 s | **33,7 s** ✅ |
| 2 | 398 | 30,6 s | 54,9 s ❌ |
| 3 | 448 | 27,7 s | 53,7 s ❌ |

A taxa a quente é ~16 tok/s e o decode ~23 s, logo 300 tokens dão ~41,8 s —
dentro do limite de 45 s. Deixa ~243 para contexto: **1 a 2 poemas**.

**A diferença entre 2 e 3 poemas está abaixo do ruído** (o `n=2` deu prefill
*maior* que o `n=3` com *menos* tokens). Não afirmar que uma é melhor.

**Consequência:** com 1–2 poemas, a qualidade da recuperação importa **mais**,
não menos — não há redundância que cubra uma escolha má. Reforça a prioridade
do Passo 8 e da Fase 2.

#### Guarda de saída

Contra os quatro modos de falha de A.4. Dois níveis na detecção de quebra de
persona, porque a primeira versão tinha falsos positivos graves: em português
`pessoa` é palavra comum, `reis` são reis, `campos` são campos — e «Olho os
campos, Neera» é um verso real de Reis que a guarda rejeitaria. Nomes
inequívocos contam sempre; ambíguos só com linguagem meta à volta.

### Passo 6 — Gerador ✅ FEITO

`src/generation/base.py` (interface `Generator`, `Resposta` com tempos) e
`src/generation/ollama.py`. 15 testes, com servidor falso para não depender do
modelo carregado. Erros com mensagem accionável: «arrancar com ollama serve»,
«descarregar com ollama pull», não um stack trace.

Parâmetros todos vindos da Fase 0. `keep_alive="30m"` é load-bearing: sem ele a
persona voltaria a custar os 13,63 s de prefill a frio em cada pergunta.

**Primeira travessia completa do pipeline:** recuperação acertou o `poem_1019`
em 1.º lugar em 66 ms, 14,7 s até ao primeiro verso visível, 28,1 s total. E
revelou que a resposta copiava 3 de 8 versos do contexto — o que levou ao
Passo 7.

### Passo 7 — Guarda de plágio ✅ FEITO

`src/plagio.py` e `src/pipeline.py`, 11 testes. Relatório:
[`fase-1/07-RELATORIO-PLAGIO.md`](fase-1/07-RELATORIO-PLAGIO.md).

**O plágio era o modo de falha dominante.** Medido em 24 respostas reais, a
resposta mediana copiava **82%** dos seus versos; o ortónimo copiava 100% nas
seis perguntas.

**E resolve-se no prompt, não na guarda.** Uma regra preventiva no `system`
(`REGRAS_NAO_COPIAR`) baixa a mediana de 82% para **0%**, e custa zero por
pergunta porque vive no prefixo em cache.

| | sem regra | com regra |
|---|---|---|
| mediana | 82% | **0%** |
| acima de 20% | 16/24 (67%) | 3/24 (12%) |

**Métrica ao nível do verso, não n-gramas.** No caso real do Passo 6 a
sobreposição de 8-gramas era 2% enquanto 38% dos versos eram cópia. Há um teste
que prova o contraste e falha se alguém voltar a n-gramas.

**Limiares calibrados**, não escolhidos: `LIMIAR_VERSO = 0,72` cai na lacuna
entre 0,70 (máximo das limpas) e 0,79 (mínimo das que copiam);
`LIMIAR_FRACAO = 0,10` dá 21% de repetição e 33,8 s de média.

A guarda de saída do Passo 5 aprovou **24/24** — zero falsos positivos em dados
reais, depois da correcção dos dois níveis de detecção de nomes.

### Passo 8 — Conjunto dourado (1 dia)

O entregável de avaliação, com o desenho **corrigido**: relevância graduada,
não gabarito único.

- 40–60 perguntas, cobrindo as quatro vozes principais
- Candidatos por **pooling**: top-10 do e5 + top-10 do BM25 lexical, agrupados
- Julgamento 0/1/2, com `pool_julgamento.py` da Fase 0 já adaptado
- Métricas: **nDCG@5** (usa a graduação) e `apt@3`
- Os 13 pares do `smoke-set.json` e os 125 julgamentos já feitos são a semente

**Nota sobre a nota 1:** na Fase 0 fui permissivo e o `util@3` saturou — até o
controlo inglês fez 9/10. Apertar o critério: `1` reservado para «serviria se
nada melhor houvesse», não «é também sobre melancolia».

### Passo 9 — CLI ✅ FEITO

`src/cli.py` com `typer`, `responder_em_fluxo` no pipeline, 7 testes.

```
você [caeiro]> o que vês quando olhas para uma árvore?

Ela estende-se ao céu,
manos do vento dançantes.
Não penso, apenas vejo —
folhas que se agitam,
ramos que se entrelaçam.

  fontes: poem_2578
  833 ms recuperação · 1.1 s até ao 1.º verso · 13.2s decode (94 tok, 7.1 tok/s)
```

Seleção de voz **explícita** (`/caeiro` `/campos` `/reis` `/pessoa`), streaming
sempre, fontes citadas e tempos à vista.

#### A travessia expôs três defeitos que os testes não apanhavam

**1. Truncagem silenciosa.** Uma ode de Reis foi cortada a meio da palavra («e
brota ao vento ímpetu») porque `num_predict=150`. Subido a **220** e a
`Resposta` passou a expor `truncada` a partir do `done_reason` do Ollama — uma
resposta cortada é pior que uma resposta lenta, e custa ~12 s.

**2. Eco da pergunta.** À pergunta «o que vês quando olhas para uma árvore?» o
modelo respondeu com «O que vejo quando olho para uma árvore» como primeiro
verso. Não é plágio do contexto, logo a guarda de plágio não o via.

**3. Fuga das instruções.** A resposta continha «Não busques na sua presença /
Significado oculto» — paráfrase da própria persona de Caeiro. Acrescentada
interdição explícita.

#### Streaming e validação estão em tensão

A correcção do eco não funcionou à primeira, e a razão é de desenho: **o CLI
imprime os fragmentos crus à medida que chegam, antes de a guarda poder correr.**
A versão limpa ficava em `veredicto.texto` e era descartada.

Resolvido com um **buffer de uma linha**: retém até à primeira mudança de linha,
limpa o eco, e só então começa a imprimir. Custa o tempo de gerar uma linha
(~2 s a 6 tok/s), não os 42 s de não haver streaming.

Os brasileirismos aparecem a meio do texto e o buffer de uma linha não os
apanha. Em vez de reimprimir a resposta corrigida, o rodapé **avisa** o que foi
trocado.

## 3. Riscos

| Risco | Sinal | Resposta |
|---|---|---|
| 340 tokens de contexto são pouco para fundamentar | respostas genéricas, sem marca do poema | a redundância temática do corpus (67% aproveitáveis) sugere que 3–4 poemas bastam; se não, subir para 700 tok e aceitar ~60 s |
| PT-BR persiste apesar do few-shot | critério 2 continua a 0–1 | lista de interdições em pós-processamento, ou fine-tune (Fase 4+) |
| Guarda de plágio dispara sempre | >50% de regenerações | o limiar está apertado; calibrar com dados, não por intuição |
| Deduplicação por variante com falsos positivos | poemas distintos colapsados | limiar alto + marcar, nunca apagar |
| Conjunto dourado enviesado pelo e5 | o e5 ganha sempre | pooling inclui BM25, que é lexical e independente |

---

## 4. Checklist

```
[ ] 1  Poem/Chunk/Voice + parse.py, 2083/2083 parseados
[ ] 2  dedupe.py apanha exacto + traducao + variante
[ ] 3  chunk.py, nenhum chunk > 480 tok
[ ] 4  corpus.jsonl gerado e versionado
[ ] 5  index.py em numpy com manifesto, alinhamento testado
[ ] 6  prefixos query:/passage: em asserção
[ ] 7  voices.py com a poética das 4 vozes principais
[ ] 8  prompt.py: 500 tok, pergunta primeiro, few-shot da voz
[ ] 9  OllamaGenerator com streaming e repeat_penalty=1.1
[ ] 10 guard.py com limiar calibrado em 30 respostas reais
[ ] 11 conjunto dourado 40-60 perguntas, relevancia graduada, nDCG@5
[ ] 12 CLI com /voz, fontes citadas e tempos
[ ] 13 20 perguntas verificadas a mao -> verso PT-PT na voz pedida
```
