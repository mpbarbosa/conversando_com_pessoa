# Documento de controlo — PessoaBot

Estado do projecto, decisões tomadas, correcções feitas e próximos passos.
**Actualizado em 2026-10-07.**

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
| **3B — Rerank, 2.ª tentativa** | [`FASE-3B.md`](FASE-3B.md) · [relatório](FASE-3B-RELATORIO.md) | ✅ **integrado** em `/rerank`: +0,090 nDCG@5 (16/20 perguntas, p=0,012) por 2,6 s, com o pool de candidatos **fechado** |
| **4 — Enriquecimento e roteador** | [`FASE-4.md`](FASE-4.md) · [relatório](FASE-4-RELATORIO.md) | ✅ **roteador integrado** (`/auto`, 72% · 92% com etiqueta múltipla); **enriquecimento vetado** por medição |
| **5 — A voz** | [`FASE-5.md`](FASE-5.md) · [relatório](FASE-5-RELATORIO.md) | ✅ **completa. H rejeitada** pelos dois instrumentos. O contexto não degrada a poética (4 pares contra 4); o Caeiro falha a **0,0 nas duas condições** e é identificado ao nível do Caeiro **real** — logo identificabilidade e poética divergem, e o défice está na persona |
| **5B — A persona do Caeiro** | [`FASE-5B.md`](FASE-5B.md) · [relatório](FASE-5B-RELATORIO.md) | ✅ **inconclusivo por potência (G4)**, nos dois avaliadores. O desfecho **saturou no chão**: 22 dos 30 pares empataram em 0–0, e H5B ficou **sem teste** — nem confirmada nem refutada. O que fica medido: o **0,0 do Caeiro reproduz-se a n=10**, a 60 amostras, 3 repetições por célula e um segundo avaliador cego ao desenho |
| **5C — O instrumento** | [`FASE-5C.md`](FASE-5C.md) · [relatório](FASE-5C-RELATORIO.md) | ✅ **instrumento rejeitado**: V1 e V3 falham. A AUC cai de **0,869 in-sample para 0,544 retida** — todo o sinal era sobreajustamento. O diagnóstico localiza a causa: **78 poemas limpos de Caeiro não bastam** para derivar uma lista lexical que generalize. Fecha a via lexical, e com ela o passo 4 |
| **5D — A contagem de voltas** | [`FASE-5D.md`](FASE-5D.md) · [relatório](FASE-5D-RELATORIO.md) | ✅ **instrumento não aceite (V4 falha)**, mas **a resolução resolve-se**: 38 valores distintos contra os 3 do 3a. E devolve um achado que põe em dúvida a cadeia toda — o **Caeiro real não cumpre a âncora de 3a** (`poem_1485`, «Pensar em Deus é desobedecer a Deus», dá 0,700 nos dois contadores), e o Caeiro gerado **não é distinguível** dele |
| **5E — Medir a âncora** | [`FASE-5E.md`](FASE-5E.md) · [relatório](FASE-5E-RELATORIO.md) | ✅ **W1 dispara, W2 falha** — a célula pré-registada como «o pior caso para as quatro fases». A âncora de 3a dá a nota máxima a **3 de 20** poemas **autênticos** de Caeiro, e reprova «Vi que não há Natureza» por filosofar. Com W3 e W4 a passar (AUC 0,811 · κ 0,784), e os três avaliadores a coincidir. **Autoriza recalibrar a âncora** |
| **5F — Endireitar a régua** | [`FASE-5F.md`](FASE-5F.md) · [relatório](FASE-5F-RELATORIO.md) | ✅ **os três portões passam: a âncora recalibrada é aceite**. Premeia **16 de 24** poemas autênticos retidos (67%, contra os 15% da antiga) e a discriminação **melhorou** (AUC 0,913 contra 0,811). E, sem portão, a pergunta aberta desde a Fase 5 tem resposta: **AUC(gerado < real) passa de 0,655 (p=0,112) para 0,851 (p=0,0003)** |
| **5G — A 5B remedida** | [`FASE-5G.md`](FASE-5G.md) · [relatório](FASE-5G-RELATORIO.md) | ✅ **G2 nas três leituras: H5B cai.** E a medição **correu**: `d` passou de **7** (5B) para **17**, com os mesmos n, perguntas e harness — a diferença foi a régua. IC95% do Δ em **[−0,30; +0,18]**, contra uma distância real-para-gerado de **0,93**: as interdições explicam no máximo um quinto disso |
| **5H — Trocar o modelo** | [`FASE-5H.md`](FASE-5H.md) · [relatório](FASE-5H-RELATORIO.md) | ✅ **M1 dispara nas três leituras: era o modelo.** `llama3.1:8b` dá **+0,700** sobre o `qwen2.5:7b` em 3a′ (IC95% [+0,42; +0,98], p=0,0002, 19 pares contra 2), o que fecha **75%** do fosso de 0,929 que separa o Caeiro gerado do real. **M3 condiciona**: escreve poemas demasiado curtos (7,5 versos contra 10–20 pedidos). Autoriza **investigar** a troca, não trocá-la |
| **5I — A forma do llama** | [`FASE-5I.md`](FASE-5I.md) · [relatório](FASE-5I-RELATORIO.md) | ✅ **I0 passa, I1 e I2 falham: o reforço não é autorizado.** A instrução pega (12→18 em 30 dentro de 10–20 versos) e o tecto corta (truncaturas de 2 para **6**), com saldo de **−0,150** em 3b. E levanta uma dúvida maior: só **43%** dos poemas **reais** de Caeiro cabem no intervalo que a âncora exige, contra 40% do llama e **83%** do qwen. **Dois números desta linha foram corrigidos depois:** os 43% são **39%** com uma definição de verso só (adenda `742b9f6`), e a leitura de que o llama se parece com o poeta **cai** na [5J §2.1](FASE-5J-RELATORIO.md) |
| **5J — A âncora de forma** | [`FASE-5J.md`](FASE-5J.md) · [relatório](FASE-5J-RELATORIO.md) | ✅ **J1 dispara, J2 não: a régua está torta e endireitá-la deixa-a cega.** Os intervalos de versos do 3b não descrevem o poeta, por **um** mecanismo — os **pisos** das personas: o do Campos (15) está acima da mediana real (14), o do ortónimo (12) acima da sua (9), e o **Reis é a única voz sem piso** e a única que passa (73%). Mas **não exonera o llama**, que está *mais longe* da distribuição real (KS 0,347 contra 0,288): a 5I inferiu a semelhança de **um escalar**, e 42+19 ≈ 70+0 dá a mesma fracção com distribuições diferentes. E o intervalo honesto `[4,31]`, validado a 86% em dados retidos, dá **100% aos dois modelos contra 86% do poeta** — logo a contagem de versos **sai** do 3b |
| **5K — Calibrar a forma** | [`FASE-5K.md`](FASE-5K.md) · [relatório](FASE-5K-RELATORIO.md) | ✅ **K1 dispara a n=30 e não agrupado; K2, K3 e K4 disparam.** O substituto da 5J **funciona** — AUC 0,999 e 1,000 contra **0,000** da conformidade monótona, que está *invertida* — mas **não ao n do desenho da 5H**: respeitado o agrupamento (10 perguntas × 3), o desvio do qwen **não está demonstrado** (percentil 90, potência 24%). **A n=20 é 100% nos dois.** E a régua: uma diferença entre heterónimos **reais** vale 0,149–0,317, logo o llama (0,347 do Caeiro) está **mais longe do que quaisquer dois heterónimos**, e **nenhum braço cabe no intervalo de voz nenhuma** |
| **5L — Retirar a cláusula** | [`FASE-5L.md`](FASE-5L.md) | ✅ **passo 22 feito: a contagem de versos sai do 3b.** Autorizada pela 5J, pela 5K e por uma verificação desta nota — **os quatro intervalos premeiam acima do poeta uma distribuição que não é a dele**, inclusive o do **Reis**, que está descritivamente **correcto** (73%) e é invertido pelo llama (83%). Fica a regra da **truncatura** (falha de fecho, detectável sem juízo) e saem os quatro limiares por poema. **Quebra de compatibilidade medida: a cláusula tinha sido aplicada em 68 de 69 casos aplicáveis, logo até 36% das 180 pontuações históricas de 3b mudariam** |
| **5M — A forma das 4 vozes** | [`FASE-5M.md`](FASE-5M.md) · [relatório](FASE-5M-RELATORIO.md) | ✅ **M1 e M2 disparam, M3 não — e é o M3 que muda a decisão.** A predição que a 5K registou **antes** desta corrida confirma-se: o llama vai de **0,347** no Caeiro a **0,196** no Reis. **O custo de forma da troca é só do Caeiro** (llama pior em 1 de 4; no Reis bate o qwen por 0,180). E **`reis/L` é a primeira célula de toda a sequência a reproduzir a distribuição do poeta** (0,196 contra p95 0,207). Mecanismo: **o qwen obedece à persona errada** (83% contra 39% do poeta no Caeiro) e a obediência custa-lhe fidelidade; o llama desobedece e acerta a mediana real em 3 de 4. O **M4 disparava por um desempate de 7,6×10⁻⁵** e foi corrigido |
| **6 — Interface e remoto** | §Fase 5 do [plano](PLANO-RAG-LOCAL.md) | ⬜ não planeada em detalhe |

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

**237 testes a passar.** `src/main.py`, `src/model.py` e `src/retriever.py`
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
| Repetição por plágio | **sem os poemas copiados** | rejeições 4/5 → 1/5; reincidência 3/5 → 0/5 |
| `LIMIAR_VERSO` de plágio | **0,72** | lacuna entre 0,70 (limpas) e 0,79 (copiam) |
| `LIMIAR_FRACAO` de plágio | **0,10** | 21% de repetição, 33,8 s de média |
| Encoder | **`intfloat/multilingual-e5-base`** | `maxlen=512` cobre 96% dos poemas inteiros |
| Lote de embedding | **8** | 1,6x mais rápido que 64, o inverso do esperado |
| Limite de chunk | **480 tokens** | 512 − 2 − 27 − 2 = 481, derivado |
| Índice | **`numpy`**, não FAISS | 2290 × 768 = **7,0 MB**; busca em 5,57 ms |
| Reranker candidato | **MiniLM-L12-H384** (~120M) | 1694 tok/s contra 90 do bge-m3 de 568M |
| LangChain | **removido** | declarado no `requirements.txt`, usado em zero linhas |
| Roteador de voz | **chamada ao qwen2.5:7b** | 72% contra 52,5% do melhor embedding; o 3b faz 42% |
| `temperature` do roteador | **0,0** | um classificador tem de ser determinista; os 0,9 são para verso |
| O roteador **propõe** | não decide | a 72%, 1 em 4 iria à voz errada; em silêncio custa 30 s, à vista custa uma tecla |
| Enriquecimento offline | **não se faz** | 88% da falta do nDCG@5 é reordenação; o enriquecimento ataca 12% por 3,2–7,5 h |
| Reranker | **`bge-reranker-v2-m3`** | +0,090 contra +0,018 do MiniLM, no pool fechado |
| Candidatos a reordenar | **8, truncados a 120 tok** | n=20 dá +0,124, mas a diferença é +0,033 com IC95% [−0,017, +0,081] |
| Reordenação ligada? | **por escolha, `/rerank`** | 2,6 s em ~30 s é uma troca, e a troca é do utilizador |
| Fronteira de profundidade | **top-20** | é até onde o gabarito está completo; mais fundo volta a pontuar não julgados |
| Comprimento do poema no **3b** | **sai da âncora por amostra** | os quatro intervalos são **invertíveis**: premeiam um braço acima do poeta ([5L §2.1](FASE-5L.md)). Mede-se ao nível do **conjunto** (passo 21) |
| Comprimento do poema, **onde se mede** | **KS ao corpus, por conjunto** | calibrado na [5K](FASE-5K-RELATORIO.md): chão p95 = 0,190 a n=30, régua 0,149–0,317 entre vozes reais |
| Truncatura no 3b | **continua a levar 0** | é falha de **fecho**, não juízo de intervalo, e lê-se de `done_reason == "length"` sem avaliador |

### Números do sistema

| | |
|---|---|
| poemas | 2083 (2062 após deduplicação) |
| chunks indexados | **2290** |
| índice | 7,0 MB · busca 5,57 ms |
| recuperação | **nDCG@5 = 0,606** (denso) · **0,696** com rerank · apt@3 = 95% · oráculo@20 = **0,980** |
| conjunto dourado | **433 julgamentos**, 125 de nota 2, top-20 denso fechado |
| corpus.jsonl | 3,0 MB · build em ~40 s |
| construção do índice | 383 s (6,4 min) |
| latência de resposta prevista | ~44 s a 500 tokens de contexto |
| roteador de voz (`/auto`) | +0,5 s por pergunta, e ~20 s uma vez a aquecer |
| reordenação (`/rerank`) | +2,6 s por pergunta, e ~4,8 s na primeira |

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
| 13 | O llama3.1 reproduz a distribuição de comprimento do Caeiro «quase exactamente» | **Não reproduz**: está *mais longe* que o qwen (KS 0,347 contra 0,288; mediana 7,5 contra 11,5 do poeta). Inferi de **um escalar** — 40% contra 39% dentro do intervalo —, e eram **70+0** contra **42+19** | 5I §9.2, corrigido pela [5J §2.1](FASE-5J-RELATORIO.md) |
| 14 | A truncatura não está gravada no harness, logo precisa de heurística | **Está gravada** (`truncada`, de `done_reason == "length"`). A heurística que declarei — «última linha sem pontuação terminal» — acertou **zero**: 4 falsos positivos e 1 falso negativo em 60. Em verso livre, acabar sem ponto é **estilo** | [`FASE-5J.md`](FASE-5J.md) §4.4, corrigido a meio |
| 15 | Com `num_predict=150`, **todos** os números de comprimento desta sequência estão censurados em cima | **São 220** (`ollama.py:38`; li o 150 da tabela do docstring, desactualizada desde a Fase 1) — e com o valor certo a explicação cai: na 5H houve **1 truncatura em 60** e os modelos pararam com ~20 palavras de folga. A estreiteza das faixas é **dos modelos**. O tecto só morde **com** reforço (5I braço B: 6 em 30) | [5J §2.3](FASE-5J-RELATORIO.md), reescrito depois de publicado |
| 16 | O máximo do Caeiro real é 48 versos (5I) / **181** (adenda) | É **161** (`_versos`) e 165 (linhas não vazias). O 48 vinha de contar só o 1.º chunk; o 181 vem de **juntar** chunks, e o chunker tem `SOBREPOSICAO = 1` (`chunk.py:36`) — repete uma estrofe por fronteira, 21 linhas duplicadas no `poem_1487`. A fonte certa é o `.body` do `parse_poem` | [5J §2.2](FASE-5J-RELATORIO.md) |

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
| `REFORCO_EN` nunca usado no caminho do CLI | Sessão em inglês recebia o reforço em português |
| Medição condicionada a re-observar um evento estocástico | 0/3 plágios na 1.ª tentativa: zero dados |
| Dois lados de uma comparação contados por **definições diferentes** de verso | «O llama reproduz o poeta»: real por linhas não vazias, gerado por `_versos` (≥3 palavras) |
| Contagem de versos resolvida pelo **primeiro chunk** e não pelo poema | `max` publicado como 48 quando é **161**; fracções salvas por acaso (os 5 multi-chunk já estavam acima de 20) |
| Intervalo central usado para medir **dispersão** | critério por amostra a tentar medir propriedade de um conjunto: contém o poeta **ou** discrimina, nunca os dois |

---

## 5. Limitações conhecidas, não resolvidas

**As pontuações de 3b anteriores a 2026-10-06 não são comparáveis com as
posteriores.** A [Fase 5L](FASE-5L.md) retirou da âncora a contagem de versos
por poema, e essa cláusula tinha sido aplicada em **68 de 69** casos
aplicáveis: até **65 das 180** notas históricas (**36%**) estariam diferentes
sob a âncora nova. Afecta o **I1/I2 da 5I** e o **M3 da 5H**, que são leituras
de 3b. **Não afecta** nada medido em 3a′ — o M1 da 5H, a 5F, a 5G —, porque a
cláusula nunca entrou no 3a. As 180 notas **não foram repontuadas**: custaria o
mesmo que a corrida que as gerou e não serve nenhuma pergunta aberta.

| Limitação | Impacto | Estado |
|---|---|---|
| Representante de variantes é «o mais longo» | Em `poem_1000`/`poem_629` elege o que tem erro de transcrição | aceite; sem correcção barata |
| Duplicação por tradução não detectável | `poem_1794` fica no corpus | resolvida pelo filtro de idioma |
| Avaliação de voz com **um só avaliador** | Não é medição intersubjectiva | assumido |
| Throttling térmico até 101 °C | Latências com precisão menor que as casas decimais sugerem | ressalva registada |
| Qualidade do reranker em PT-PT desconhecida | Pode piorar o ranking | mede-se no Passo 2 da Fase 3 |
| ~~**Sem copiar, nem sempre é a voz pedida**~~ | **medido na Fase 5**: é verdade que nem sempre é — o Caeiro dá 0,0 de mediana em poética. Mas a explicação estava **errada**: ele quebra a interdição **sem contexto nenhum**, e a ablação dá 4 pares contra 4 | ✅ fechada, e o suspeito absolvido |
| Alguns poemas são atractores (`poem_3426`, `poem_2832`) | muito recuperados e muito copiados | pode exigir MMR na recuperação |
| **Streaming imprime antes de validar** | só o 1.º verso é retido; brasileirismos a meio só são avisados | aceite; buffer total custaria o streaming |
| Enviesamento de pooling | sistema novo é penalizado por construção | procedimento escrito no topo de `test_retrieval_gold.py` |
| Pool de top-5 era raso | 3 gabaritos estavam em 6.º–9.º | top-10 na próxima ronda |
| **Tabacaria em 37.º sem explicação** | hipótese do chunking testada e refutada | investigar chunk a chunk |
| Recolha do corpus não reproduzível | nenhum script no histórico | registado em `data/README.md` |
| `src/main.py` e companhia ainda no repo | Dois sistemas em paralelo | até ao Passo 9 |

### Uma ressalva à conclusão da Fase 4, encontrada na Fase 5

O Passo A1c da Fase 4 concluiu que **«o espaço do e5 não separa estas vozes»**,
dos 42–46% obtidos a rotear poemas reais. O instrumento estava handicapado:
`fase-4/bench_roteador_c.py:91–95` encoda os poemas de teste como `query` a
partir de `chunk.text` — verso puro — contra centróides construídos de
`indexed_text`, que leva **«Autor — Título»** à cabeça. O nome do heterónimo é o
indício mais discriminativo da tarefa, está no centróide e não está em consulta
nenhuma; os 42–46% saem **subestimados**.

**Remedido: o defeito valia 23 pontos em perguntas e 22 em poemas, e a afirmação
está refutada.** Com centróides de `c.text`, as perguntas vão de 45% para **68%**
e os poemas de 42% para **64%**. O espaço do e5 **separa** estas vozes.

E o **colapso no Caeiro era artefacto do nome**: nas perguntas, os erros a
apontar para o Caeiro caem de **19 para 1**, e o que sobra colapsa no ortónimo
(12), que é a classe maior — o comportamento banal que a tabela de riscos da
Fase 4 previa e que não se observou, porque o nome produzia o inverso.

**Mas a tabela de coerência sobrevive**, e é aqui que está a lição mais fina
desta correcção. Sem o nome, as quatro vozes continuam iguais entre si
(0,928–0,930 contra 0,934–0,939). A observação «as quatro vozes têm coerência
interna igual» **não** era artefacto; artefacto era o **facto que ela
explicava** — o colapso no Caeiro. Ficou uma medição correcta a explicar um
fenómeno que não existe, o que é um modo de falha diferente de «o número estava
errado», e mais difícil de apanhar: a medição resiste a toda a verificação, e é
a pergunta que ela responde que não existe.

E a decisão fica em dúvida, ao contrário do que eu escrevi aqui primeiro. O
roteador por LLM faz 72%: contra 45% eram +27 pontos, contra 68% são **+4**, e
+4 a n=40 não se distinguem de zero pelo mesmo critério que a Fase 3B usou para
preferir a configuração mais barata. O roteador não está **estabelecido** como
melhor — o que não é o mesmo que estar refutado: o LLM foi medido num conjunto
adversarial e numa ablação de indícios, e o centróide não, logo a robustez não
está comparada. **O que decidiria** está nomeado: correr o centróide `sem_nome`
nas 12 perguntas adversariais e nas 40 abladas. O 7B aguentou 72%→70% com os
substantivos-assinatura removidos, e um centróide que vive de superfície lexical
é precisamente o que deveria desabar nesse teste. A correcção vive na Fase 4;
aqui fica o ponteiro.

Para a Fase 5 o defeito era inócuo na **diferença**, e é por isso que o
Instrumento II passou a correr as duas variantes de centróide em vez de só a
contaminada — ver [`FASE-5.md`](FASE-5.md) §9.3.

---

### Sobre direitos

Fernando Pessoa morreu em 1935; obra em domínio público em Portugal e no Brasil
desde 2006. **Sem impedimento legal.** Mas a origem dos 2083 ficheiros não está
registada em nenhum lugar — de onde vieram, em que data, sob que licença. É
requisito de reprodutibilidade e continua pendente.

---

## 6. Próximos passos

> As Fases 1 a 4 estão feitas. Esta secção descrevia o «imediato» como sendo o
> Passo 5 da Fase 1 e ficou para trás quatro fases seguidas; o que estava aqui
> é agora história e vive nos relatórios por fase.

### Feito — a reordenação, que a Fase 4 reabriu e a 3B decidiu

A Fase 4 mediu a folga (oráculo@20 contra o denso) e a [Fase 3B](FASE-3B-RELATORIO.md)
foi buscá-la. O que a desbloqueou não foi modelo nem máquina: foi **fechar o
pool de candidatos**, julgando os 142 poemas do top-20 do denso que faltavam.

> As três razões que dei aqui para reabrir isto estavam duas erradas, e o
> relatório da Fase 3 já o dizia: «**a latência não é o obstáculo**». A iGPU nem
> se aplica — os 6x são do backend Vulkan do Ollama e um cross-encoder corre em
> PyTorch. O obstáculo era o instrumento. Ver [`FASE-3B.md`](FASE-3B.md) §1.

Resultado: **+0,090 de nDCG@5** com 16 das 20 perguntas a melhorar (p=0,012),
por 2,6 s, em `/rerank`. Captura 24% dos 0,374 do oráculo.

### Depois, em ordem

| | Passo | Desbloqueia |
|---|---|---|
| 1 | ~~**A voz gerada é a voz pedida?**~~ — **medida**: não é, e o contexto não é a causa | ✅ [Fase 5](FASE-5-RELATORIO.md). Fecha a pergunta aberta desde a Fase 1 Passo 7 |
| 2 | Julgar as outras 20 perguntas, ou um segundo avaliador | a magnitude dos Δ, que a n=20 fica em IC95% de 0,17 de largura |
| 3 | **Fase 6** — FastAPI, Gradio, histórico, `AnthropicRemote` | — |

### Depois da Fase 5, o que ela deixou nomeado

| | passo | porquê |
|---|---|---|
| 1 | ~~**A persona do Caeiro, feita de interdições**~~ — **medida, e sem veredicto** | [Fase 5B](FASE-5B-RELATORIO.md): a ablação correu com 60 amostras e dois avaliadores, e o portão **G4** disparou nos dois. O critério 3a não tem resolução onde era preciso, logo a hipótese continua aberta — ver o passo 5 |
| 2 | ~~**Um segundo avaliador**~~ — **feito** na Fase 5B | R2 foi cego ao **desenho** e não só à condição: não soube que havia dois braços nem qual era a hipótese. κ=0,301 em 3a com 81,7% de concordância exacta, e nenhuma discordância acima de 1 ponto em 60 amostras. Ressalva: são sessões do mesmo modelo a ler as mesmas âncoras, logo pode ser **erro correlacionado** |
| 3 | **`num_predict` para Campos** | 3 truncaturas em 40, pendência já conhecida desde a Fase 4 |
| 4 | ~~A sombra lexical do Caeiro~~ — **respondido, e negativo** | [Fase 5C](FASE-5C-RELATORIO.md): a regra foi construída como o §11 pedia e **reprovou na validação retida** (AUC 0,544). Não fica pendente. Bónus: a lista vinda do **corpus** correlaciona ρ≈−0,28 com o 3a e a vinda da **persona** ρ≈0, o que dá o primeiro número ao princípio do §11 |
| 5 | ~~**Um desfecho com resolução**~~ — **resolvido na 5D**, e não é o que falta | a [Fase 5D](FASE-5D-RELATORIO.md) deu 38 valores distintos contra 3, sem confundidor de comprimento (V3 e V5 passam nos dois contadores). O instrumento é rejeitado por **validade** (V4), não por resolução — e o que o bloqueia agora é o passo 7, não a escala |
| 6 | **Medir o plágio por amostra, e não só como critério de aprovação** | ver o §4 do [relatório da 5B](FASE-5B-RELATORIO.md): as três únicas amostras que chegaram a 3a=2 tinham, as três, um poema real de Caeiro **no prompt**, e uma delas é uma transposição com 33% dos versos copiados. Onde a poética chegou ao topo, chegou por cópia |
| 7 | ~~**Pontuar os poemas REAIS de Caeiro com a âncora de 3a**~~ — **feito, e a âncora reprova-os** | [Fase 5E](FASE-5E-RELATORIO.md): 3 de 20 autênticos com a nota máxima (15%), 7 de 20 a **zero** nos dois avaliadores, e o único item **gerado** a atingir o máximo é a amostra que a 5B §4 apanhou a copiar 33% dos versos. A âncora é um bom **filtro negativo** (ortónimo a 19/20 zeros) e uma má **medida positiva** |
| 8 | ~~**A regra 2 tem de decidir sobre a tautologia deflacionária**~~ — **decidido** | a âncora da [5F](FASE-5F.md) §2.1 regra 2 fixa-o: **a tautologia deflacionária é a assinatura do Caeiro, não um defeito**. «As coisas são só o que são» conta **para** a nota máxima |
| 9 | ~~**Recalibrar a âncora de 3a do Caeiro**~~ — **feito, e aceite** | [Fase 5F](FASE-5F-RELATORIO.md): a âncora passa a medir a **direcção** do movimento e não a sua presença — o Caeiro filosofa para **fechar a porta**, o ortónimo para a abrir. Validada em **24 poemas retidos** que eu nunca li, com os três portões a passar nos três avaliadores |
| 10 | ~~**Repetir a Fase 5B com a âncora nova**~~ — **feita, e H5B cai** | [Fase 5G](FASE-5G-RELATORIO.md): G2 nas três leituras, G5 não dispara. A âncora nova entregou o que a sequência de instrumentação prometia — 17 pares discordantes contra os 7 da 5B |
| 11 | **Replicar, com portão, a separação gerado/real** | a [5F](FASE-5F-RELATORIO.md) §2 deu AUC 0,851 com p=0,0003, mas foi pré-registada **sem portão** porque a 5E tinha mostrado falta de potência a n=20. Um resultado forte onde a potência era baixa pede replicação |
| 12 | **Apertar a âncora na fronteira 1/2** — passa de desejável a **necessário** | repetiu-se em duas fases independentes: R2 pontuou o dobro de R1 em média (5F: 30 notas máximas contra 16; 5G: 25 contra 7), e na 5G o κ caiu a **0,334** com 48,3% de concordância exacta. R2 nomeou a fronteira de dentro da cegueira: «quando a personificação era incidental e o fecho era deflacionário, dei 1 em vez de 0». A âncora não diz qual ganha |
| 13 | ~~**Trocar o modelo e remedir com a âncora 3a′**~~ — **feito, e era o modelo** | [Fase 5H](FASE-5H-RELATORIO.md): M1 nas três leituras, Δ=+0,700 com p=0,0002. E o llama ganhou **a correr nas condições do adversário** — `repeat_penalty` e `num_predict` foram calibrados na Fase 0 para o qwen —, logo o Δ é um **piso**. O confundidor do contexto foi verificado ausente por asserção byte a byte nas 10 perguntas |
| 14 | O terceiro braço: **negação que não nomeia** | desfaz a fusão que a [5B §2.1](FASE-5B.md) declarou e a 5G herdou — a variante afirmativa inverte a polaridade **e** deixa de nomear os referentes, e nenhuma das duas fases separou as duas coisas |
| 15 | ~~**A forma do llama3.1**~~ — **medida, e o reforço não passa** | [Fase 5I](FASE-5I-RELATORIO.md): I1 e I2 falham. E corrigiu-me a ordem — eu tinha escrito que o `num_predict` «não é o constrangimento», o que era verdade **sem** o reforço e falso **com** ele. Os dois são um par, e eu testei-os em sequência |
| 16 | **As outras três vozes com os dois modelos** — **metade feita** (forma); a outra bloqueada no passo 25 | [Fase 5M](FASE-5M-RELATORIO.md) mediu a **forma** nas 8 células e **retira a condição que o M3 da 5H pôs à troca**: o custo é **do Caeiro**, e fora dele a troca **melhora** a forma. O **conteúdo** das outras três vozes não pode ser medido com o instrumento que existe — a âncora 3a′ é do Caeiro —, logo a decisão da troca continua em aberto, agora pelo passo **25** e não por falta de corrida |
| 19 | ~~**Verificar se o intervalo de 10–20 versos da âncora de 3b é real**~~ — **feito, e não é; mas o remédio é pior** | [Fase 5J](FASE-5J-RELATORIO.md): **J1 dispara** (3 de 4 vozes, e as três falham **para baixo** — os pisos das personas estão altos demais), **J3 e J4 disparam**, e **J2 não**. O «défice de forma» do llama **não** é artefacto do instrumento: o llama está mais longe do poeta, não mais perto, e a frase da 5I §9.2 veio de uma coincidência de **um escalar**. O J4 valida `[4,31]` a 86% em dados retidos e a consequência mata-o: **100% aos dois modelos contra 86% do poeta**. A prescrição é **retirar** a contagem de versos do 3b, porque a dispersão do Caeiro (1 a 161 versos) é propriedade de **um conjunto** e não de um poema |
| 20 | **O par reforço + `num_predict`, medidos juntos** — a 5J **confirma-lhe o motivo**, e retira o segundo que eu lhe tinha dado | o §5 da [5J](FASE-5J.md) escreveu antes de medir que, se o J1 **e** o J2 disparassem, este passo ficaria sem motivo. **O J2 não disparou**: o llama escreve curto a sério (mediana 7,5 contra 11,5 do poeta). O segundo motivo que eu publiquei — um tecto a censurar a gama alta — **não existe**: são 220 e não 150, e na 5H houve 1 truncatura em 60 ([5J §2.3](FASE-5J-RELATORIO.md)). É o **reforço** que faz o tecto morder, logo os dois **têm** de ir juntos — que é o que este passo já dizia |
| 17 | **Afinar as opções por modelo e remedir** | o Δ de 0,700 da 5H é um piso, porque o llama correu com as opções do qwen |
| 18 | **O `qwen2.5:3b`**, instalado e nunca medido | diria se o resultado da 5H é de **capacidade** ou de **família** |
| 21 | ~~**Um critério de forma ao nível do conjunto**~~ — **calibrado e aceite** | [Fase 5K](FASE-5K-RELATORIO.md): o KS ao corpus bate a conformidade nos dois braços (AUC 0,999 e 1,000 contra 0,000 e 0,784), com Δ a excluir 0. Tem **chão** (nulo empírico: p95 de 0,190 a n=30) e **régua** (0,149–0,317 entre vozes reais). Instrumento em [`fase-5j/analisar.py`](fase-5j/analisar.py), calibração em [`fase-5k/01-nulo.json`](fase-5k/) |
| 22 | ~~**Retirar a cláusula de comprimento da âncora de 3b**~~ — **feito** | [Fase 5L](FASE-5L.md): a [Fase 5 §5.2](FASE-5.md) está alterada nas quatro vozes, com a âncora original preservada para ler as pontuações antigas. O caso do **Reis** fechou o argumento — intervalo **correcto** e **invertido** ao mesmo tempo —, logo a correcção descritiva não salva um escalar. Nota de compatibilidade no §3 da 5L |
| 23 | **Os limiares de estrofe e de verso, que ficaram sem teste** | a 5L retirou os limiares por **poema** e deixou ficar `estrofes de 3–4 versos`, `quadras ou quintilhas`, `linhas curtas` e `versículo longo` — comprimentos de **estrofe** e de **linha**, que a 5J nunca mediu. Pela mesma lógica podem ter o mesmo defeito, e o teste é o mesmo: contar no corpus real e ver se o intervalo descreve o poeta |
| 24 | **As personas pedem os intervalos que a 5L invalidou** — e estão em **produção** | descoberto pela verificação A3 da [5M §5.3](FASE-5M.md): `src/voices.py` manda «Entre dez e vinte versos» (:123), «Entre quinze e trinta» (:133), «No máximo doze» (:142) e «Entre doze e vinte» (:154) — **os quatro intervalos** que a [5J](FASE-5J-RELATORIO.md) mostrou não descreverem o poeta. A 5L removeu-os do **instrumento de medida** e eles ficaram na **instrução de geração**: o projecto mede sem o intervalo e continua a pedi-lo. Corrigir é uma **intervenção** e o efeito mede-se — a 5I mexeu na instrução e deu saldo líquido **negativo** —, logo pede pré-registo próprio |
| 24b | **E a 5M dá-lhe uma predição direccional** | a [5M §3.1](FASE-5M-RELATORIO.md) mediu a **obediência** à instrução errada: o qwen obedece-lhe mais do que o poeta obedece a si mesmo em **3 das 4 vozes** (Caeiro 83% contra 39%), e o llama desobedece e acerta a mediana real em 3 de 4. **Logo corrigir a persona deve beneficiar sobretudo o qwen** — registado antes de o passo 24 correr |
| 25 | **Uma âncora 3a′ por voz** — o que bloqueia metade do passo 16 | a âncora da [5F §2](FASE-5F.md) mede «o poema acaba na coisa» e é inteiramente **do Caeiro**. Ao **ortónimo**, cujo modo é acabar **além** da coisa, daria **0 por construção**: é uma anti-medida, não uma medida má. Cada voz precisa da sua, validada contra os poemas **reais** dessa voz — o percurso [5E](FASE-5E-RELATORIO.md) → [5F](FASE-5F-RELATORIO.md), três vezes. **Até isso existir, o passo 16 só se pode medir na forma** |

O **Passo 1 era o que importava mais**, e a Fase 5B foi medi-lo. Voltou sem
veredicto, e a razão é instrutiva: o instrumento com que se ia medir — o
critério 3a, com as âncoras da Fase 5 — **está saturado no mínimo nesta voz**, e
uma ablação emparelhada sobre um desfecho saturado é inconclusiva por
construção. O que falta agora não é mais uma corrida; é um desfecho com
resolução no chão.

> **A lição, e é geral.** Antes de pré-registar uma ablação emparelhada,
> **verificar que o desfecho tem variância na condição de controlo**. A Fase 5
> já tinha publicado que o Caeiro dá 0,0 de mediana em 3a, e a Fase 5B desenhou
> 60 amostras sobre esse critério de qualquer maneira. Um piloto de seis
> amostras tinha mostrado a saturação em vinte minutos, por 1/10 do custo.
> Nenhuma das outras defesas do protocolo — âncoras herdadas, dois avaliadores,
> piso de potência, portão de especificidade — compensa esta falta.

> **E o corolário, da Fase 5C.** Verificar a variância **não chega**: o FAS tinha
> 8x mais resolução que o 3a e foi rejeitado de qualquer maneira, porque a
> validade é outra pergunta. Um desfecho precisa das duas, e a validade mede-se
> em dados **retidos** — a AUC do FAS caía de 0,869 para 0,544 ao passar de
> in-sample para retida. **Qualquer número de discriminação medido nos mesmos
> dados que derivaram o instrumento não é um número.**

> **E o segundo corolário, da Fase 5D.** Um **ICC de 0,671** soa aceitável e não
> basta para estabilizar um portão com limiar: entre dois contadores que
> concordam a ρ=0,78, a AUC oscilou **0,21** — mais do que a distância entre
> passar e falhar. Portões por limiar sobre juízo precisam de concordância bem
> mais alta, ou de correr sobre a estimativa **conjunta** em vez de cada
> avaliador. E a causa foi **uma** fronteira que a definição não decidiu, o que
> é o argumento para escrever as definições pelos **casos difíceis** e não pelos
> fáceis.

> **E o quinto, da Fase 5I, que custou uma segunda adenda e veio de fora.**
> **Um escalar colapsa uma distribuição.** Eu li «40% contra 39% dentro do
> intervalo» como «o llama reproduz a distribuição do poeta quase exactamente»,
> quando era **70+0** contra **43+18**: o Caeiro real erra o intervalo para os
> dois lados e o llama só para baixo. Mesma fracção, distribuições diferentes —
> e por KS o llama está **mais longe** do poeta, não mais perto. **Antes de
> chamar duas distribuições parecidas, comparar as distribuições e não uma
> fracção delas.** Foi a sessão do passo 19 que o viu.

> **E o quarto, da Fase 5I, que custou uma adenda.** Um número calculado **ad
> hoc numa sessão** não tem definição registada, e duas definições plausíveis da
> mesma coisa dão números diferentes: contar «versos» por linhas não vazias ou
> por `plagio._versos` (≥3 palavras) move a fracção do Caeiro real de 43% para
> 39%. Foi uma sessão paralela que o apanhou, não eu. **Qualquer número que
> entre num relatório tem de ter um script no repositório que o reproduza** — e
> comparações entre grupos têm de usar a mesma definição nos dois lados, o que
> parece óbvio e não foi.

> **E o terceiro, da Fase 5E, que é o mais caro de todos.** Um critério derivado
> do **tratamento** mede a proximidade ao tratamento, e não à coisa. A Fase 5
> mediu isto no seu juiz LLM — que dava 65% ao gerado e 45% a Pessoa autêntico —
> escreveu a prescrição certa («as descrições têm de vir de outra fonte que as
> personas») e aplicou-a ao juiz e **não à sua própria rubrica manual**, que tem
> a mesma origem. Quatro fases mediram a geração contra uma idealização da
> persona. **Antes de usar um critério para julgar uma imitação, pontuar o
> original com ele.** Custou três fases de instrumentação descobri-lo e é uma
> linha de protocolo.

> **E o quarto, da Fase 5J, que é sobre a forma do instrumento e não sobre
> o seu conteúdo.** Os três anteriores são sobre **validade** (5C: medir em
> dados retidos), **resolução** (5D: variância no controlo) e **origem** (5E:
> pontuar o original com o critério). Este é sobre a **forma**: **um critério
> por amostra não pode medir uma propriedade de um conjunto.** O 3b pontua
> poemas um a um, e a coisa que distingue o Caeiro em comprimento — escrever
> ora quatro versos ora cento e sessenta — não está em nenhum poema seu, está
> na obra. Daí o dilema medido da [5J](FASE-5J-RELATORIO.md) §4.3: um
> intervalo largo o bastante para conter o poeta contém trivialmente tudo o
> que os modelos fazem, e um estreito o bastante para discriminar reprova o
> poeta. **Não é uma escolha de limiar.**
>
> E um corolário sobre resumos, que custou uma frase publicada: **uma fracção
> dentro de um intervalo não identifica uma distribuição.** A 5I concluiu que
> o llama reproduzia o poeta porque 40% e 39% coincidiam; eram 70+0 contra
> 42+19. Antes de ler uma coincidência de escalares como semelhança, **olhar
> para as duas distribuições**.

> **E o quinto, da Fase 5K, que fecha a série: a escala.** Um número de
> distância sem um **chão** — quanto dá o ruído de amostragem — e sem uma
> **régua** — quanto vale uma diferença real — **não é legível**. A 5J publicou
> `KS = 0,288` e `0,347` a achar que eram legíveis. O que a calibração mudou não
> foi o número: foi passar de «0,347 é mais que 0,288» para «**0,347 é mais do
> que a distância entre o Campos e o Reis**», e para «nenhum dos dois braços
> cabe no intervalo de amostragem de voz nenhuma». Custou uma hora de
> computação.
>
> E dois corolários operacionais, os mais caros da fase: **o nulo assintótico
> era conservador por 46%** (0,278 contra os 0,190 medidos), logo medir o chão
> em vez de o estimar mudou uma decisão à tangente numa decisão com folga; e **o
> n efectivo de um desenho agrupado é o número de agrupamentos, não de
> amostras** — as 30 amostras de 10 perguntas × 3 repetições valem n≈10, e a
> essa resolução metade do resultado da fase desaparece.

É agora a **Fase 5**, e a interface passa a Fase 6 — a renumeração está
declarada no topo de [`FASE-5.md`](FASE-5.md). A hipótese que vai a medição é a
que está na tabela de perguntas abertas do §5: o contexto recuperado explica e
atribui significado, e isso é o que Caeiro proíbe. Mede-se por **ablação
emparelhada** nas 20 perguntas já julgadas, com e sem contexto, às cegas, com os
portões escritos antes de existir qualquer amostra.

Em cima disso entrou, por **emenda declarada**, um segundo instrumento vindo de
uma sessão paralela que media a mesma pergunta por outro caminho: a voz gerada é
tão identificável quanto Pessoa autêntico? Essa pergunta **não se auto-calibra**
— é o controlo de poemas reais que a torna legível, e a Fase 4 A1c já mediu o
nível a bater (42–46% em poemas reais). Os juízes são mecânicos, logo esse
instrumento não tem a ameaça de avaliador único que a rubrica à mão tem. A
leitura final é a **concordância dos dois**; discordarem não decide nada.

### Pendências de limpeza

```
[ ] repetir o teste de voz do 8B com repeat_penalty (adenda A.3 só corrigiu o arranque)
[ ] repetir o bench de rerank com pausa de arrefecimento
[ ] medir num_predict=110 (poupa ~4-5s; medicao contaminada por cache)
    -> o valor actual e 220, nao 150. E a 5J §2.3 mostra que na 5H houve 1
       truncatura em 60, com ~20 palavras de folga: descer tem margem, e
       SUBIR nao alarga a forma. Subir so faz sentido COM reforco (passo 20)
[ ] remover src/{main,model,retriever}.py no Passo 9
[ ] remover langchain do requirements.txt
[ ] actualizar .github/copilot-instructions.md para a arquitectura nova
[ ] num_predict=220 corta o versiculo longo de Campos (visto 2x na Fase 4)
[x] remedir os centroides da Fase 4 A1c sem o nome do heteronimo: +23 pontos
[ ] correr o centroide sem_nome nas 12 adversariais e nas 40 abladas da Fase 4:
    e o que decide se o roteador LLM se mantem (68% vs 72% e so no benigno)
[ ] detector de proclise brasileira em guard.py: «Uma mao se recua» escapa a
    lista de 14 palavras. Pede medicao contra os 2083 poemas antes de entrar,
    como o lingua_errada teve (0,12 rejeita 3 de 1906) -- «se recua a mao» e
    portugues correcto, e o corpus esta cheio de inversoes. Desenho da sessao
    paralela; fase propria, pequena
[ ] variante do juiz LLM da Fase 5 com descricoes tiradas do corpus (frequencias
    de forma) em vez das personas: separa o confundidor do §9.3 da memorizacao
[ ] registar a origem dos 2083 ficheiros (reprodutibilidade, §5)
[ ] poem_224 esta indexado com mojibake e e recuperavel (visto no top-20 de q11)
[ ] um segundo avaliador para o conjunto dourado: 433 julgamentos sao todos meus
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
| [`FASE-4.md`](FASE-4.md) · [`FASE-4-RELATORIO.md`](FASE-4-RELATORIO.md) | roteador de voz, e o veto ao enriquecimento |
| [`FASE-3B.md`](FASE-3B.md) · [`FASE-3B-RELATORIO.md`](FASE-3B-RELATORIO.md) | fechar o pool de candidatos, e a reordenação a entrar |
| [`FASE-5B.md`](FASE-5B.md) · [`FASE-5B-RELATORIO.md`](FASE-5B-RELATORIO.md) | a persona do Caeiro feita de interdições, e o desfecho que saturou |
| [`FASE-5C.md`](FASE-5C.md) · [`FASE-5C-RELATORIO.md`](FASE-5C-RELATORIO.md) | o desfecho lexical, e a validação retida que o reprovou |
| [`FASE-5D.md`](FASE-5D.md) · [`FASE-5D-RELATORIO.md`](FASE-5D-RELATORIO.md) | a contagem de voltas, e o Caeiro real a não cumprir a âncora |
| [`FASE-5E.md`](FASE-5E.md) · [`FASE-5E-RELATORIO.md`](FASE-5E-RELATORIO.md) | a âncora medida contra o original, e a autorização de a recalibrar |
| [`FASE-5F.md`](FASE-5F.md) · [`FASE-5F-RELATORIO.md`](FASE-5F-RELATORIO.md) | a âncora recalibrada, aceite em dados retidos — **é esta a âncora a usar** |
| [`FASE-5G.md`](FASE-5G.md) · [`FASE-5G-RELATORIO.md`](FASE-5G-RELATORIO.md) | a hipótese das interdições, finalmente medida — e rejeitada |
| [`FASE-5H.md`](FASE-5H.md) · [`FASE-5H-RELATORIO.md`](FASE-5H-RELATORIO.md) | o modelo medido, e o único positivo da cadeia |
| [`FASE-5I.md`](FASE-5I.md) · [`FASE-5I-RELATORIO.md`](FASE-5I-RELATORIO.md) | a forma do llama, e a âncora de 3b sob a mesma suspeita da 5E |
| `fase-0/` | 21 ficheiros de evidência e 5 scripts |
| [`fase-0/07-igpu-vulkan.md`](fase-0/07-igpu-vulkan.md) | a iGPU por Vulkan: prefill 6x, decode 0,55x — corrige a premissa «CPU-only» |
| [`fase-1/09-repeticao.md`](fase-1/09-repeticao.md) | a repetição por plágio voltava ao mesmo poema: medição das duas políticas |
| `fase-3/` | latência dos rerankers e script |
| `fase-4/` | 7 bancos de roteador, o conjunto adversarial pré-registado, e a decomposição do tecto |
| `fase-3b/` | a folha dos 142 julgamentos, o pool fechado, e a análise de significância |
| `fase-5b/` | as 60 amostras dos dois braços, as duas pontuações cegas, a variante afirmativa e a verificação da regra que a produziu |
| `fase-5c/` | o FAS, a lista derivada por log-odds, e os números da sua própria rejeição |
| `fase-5d/` | a folha dos três grupos, as duas contagens verso a verso, e os portões |
| `fase-5e/` | a folha de 60 itens frescos, as duas pontuações com a âncora, e os portões W1–W4 |
| `fase-5f/` | a folha de 64 itens com os 24 retidos, as duas pontuações, e os portões X1–X3 |
| `fase-5g/` | as 60 amostras novas dos dois braços, as duas pontuações com a âncora 3a′, e os portões G0–G5 |
| `fase-5h/` | as 60 amostras dos dois modelos, com a asserção de prompt igual, e os portões M1–M5 |
| `fase-5i/` | as 60 amostras dos dois braços de forma, e os portões I0–I4 |

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

> ⚠️ **As duas frases a negrito acima estão erradas, e a Fase 4 mediu-o.** O
> oráculo sobre o top-20 — o melhor que uma reordenação da lista que o índice
> **já devolve** conseguiria — dá `nDCG@5 = 0,956` contra os 0,640 do denso. Há
> **0,316 de nDCG@5, ou 88% da falta, dentro do top-20**, e 17 das 20 perguntas
> têm notas 2 abaixo da 5.ª posição. O tecto é do MiniLM, não do corpus.
>
> O erro foi de inferência: o argumento dos 84 documentos de nota 2 explica por
> que o **`apt@3`** satura a 95%, e não por que o **`nDCG@5`** fica em 0,640.
> São perguntas diferentes — «há uma nota 2 no top-3?» satura; «quantas, e em que
> ordem?» não. Ver [`FASE-4-RELATORIO.md`](FASE-4-RELATORIO.md) §2.2.

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


---

## Correcção: a repetição por plágio voltava ao mesmo poema

Observado a correr o chatbot, à pergunta «você conhece o senhor fernando
pessoa?»: a 1.ª tentativa copiou 9 de 14 versos do `poem_1164` — um deles à
letra — por substituição de palavras (`Natureza`→`Silêncio`, `brisa`→`luz`,
`perceber`→`escutar`). A repetição voltou **ao mesmo poema**: 5/14. Duas
rejeições, ~80 s, e o utilizador interrompeu.

O `REFORCO` já dizia «não reutilizes nenhum verso nem o reescrevas trocando uma
palavra», e foi ignorado duas vezes. **O contexto não mudava entre as
tentativas** — `poem_1164` continuava no prompt, e a única diferença era o
reforço e a amostragem.

A repetição passa a **tirar do contexto os poemas de que o modelo copiou**. Não é
encolher: `montar` corta pelo orçamento, logo deixar um poema de fora deixa
entrar o seguinte da recuperação — aqui, `poem_1130` em vez de `poem_1164`.

### Medido, 5 repetições por política

| | A (antes) | B (agora) |
|---|---|---|
| rejeitadas por plágio | **4/5** | **1/5** |
| reincidiu no poema proibido | **3/5** | **0/5** |
| corridas com zero versos copiados | **0/5** | **4/5** |
| fracção nas corridas que falharam | 0,08 – 0,57 | **0,89** |

**O mecanismo faz o que foi desenhado para fazer**, e a ressalva é importante:
não remove a tendência de se encostar a um poema, remove **aquele** atractor. A
falha única do B foi a mais grave das dez em fracção copiada, e veio do poema que
acabou de entrar. Com `MAX_TENTATIVAS = 2` não há ronda para tirar o segundo.

n=5, uma pergunta, uma voz — chega para a decisão, não chega para uma taxa.

### Dois defeitos encontrados pelo caminho

**`REFORCO_EN` existia e nunca era usado.** O `responder()` escolhia a língua; o
`responder_em_fluxo()` — o caminho que o CLI corre — fazia `user = p.user +
REFORCO` sem ramo nenhum. Uma sessão em inglês recebia o reforço em português.

**O primeiro desenho da medição não produziu dados.** Condicionei a comparação a
re-observar o plágio na 1.ª tentativa, e em 3 perguntas 0 plagiaram — incluindo
esta, com o mesmo poema no contexto. Com temperatura 0,9 e sem semente o plágio é
estocástico; o ponto de partida tinha de vir da observação, não de nova geração.

Número lateral dessa corrida falhada: **0 de 3 primeiras tentativas plagiaram**,
contra 1 de 1 na sessão do utilizador. O plágio é um evento, não o estado normal
destas respostas — e isto enquadra o que a correcção vale, porque ela só age
quando a primeira tentativa falha.
