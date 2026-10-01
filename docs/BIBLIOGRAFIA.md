# Bibliografia — RAG do zero, orientada a este projeto

Para quem nunca trabalhou com RAG e quer entender as decisões de
[`PLANO-RAG-LOCAL.md`](PLANO-RAG-LOCAL.md) em vez de aceitá-las.

**Nota de honestidade:** todos os links abaixo foram verificados em 2026-09-30 —
autoria, título, ano e identificador conferem. Verifiquei que cada obra existe e
é o que digo que é; não li cada uma de ponta a ponta agora. Se um link morrer,
o identificador (arXiv, DOI) permite reencontrar a obra.

---

## Como usar isto

A ordem importa mais do que a quantidade. Um caminho de leitura possível:

| Quando | O que | Tempo |
|---|---|---|
| Primeiros dias | Nível 0 inteiro | ~4 h |
| Primeira semana | Nível 1 inteiro, com as mãos no código | ~1 dia |
| Antes da Fase 1 | Nível 2, itens 2.1 e 2.2 | ~2 h |
| Antes da Fase 2 | Nível 2 completo | ~3 h |
| Antes de ajustar prompts | Nível 3 inteiro | ~2 h |
| Quando for escolher o encoder | Nível 4 | ~2 h |
| Por curiosidade, depois | Nível 5 | — |

Etiquetas de esforço: **[intro]** acessível sem pré-requisitos ·
**[prático]** documentação para usar · **[artigo]** artigo científico, pode ler
só o resumo e a conclusão · **[referência]** consultar, não ler.

---

## Nível 0 — O que é isto, afinal

Três leituras. Depois destas, a arquitetura do plano faz sentido.

### 0.1 Embeddings, explicado sem matemática **[intro]**

Simon Willison, *Embeddings: What they are and why they matter* (2023).
<https://simonwillison.net/2023/Oct/23/embeddings/>

**Comece por aqui.** Explica a única ideia de que tudo depende: transformar um
texto num vetor de números de tamanho fixo, de modo que textos parecidos fiquem
perto no espaço. Nenhum pré-requisito. Uma hora.

Se depois disto você entender por que `all-MiniLM-L6-v2` (treinado em inglês)
recuperava quase ruído num corpus português, já ganhou o dia.

### 0.2 Embeddings, com profundidade **[intro]**

Vicki Boykis, *What are embeddings* (2023), ~70 páginas, livre.
<https://vickiboykis.com/what_are_embeddings/> ·
código: <https://github.com/veekaybee/what_are_embeddings>

O mesmo assunto com fundamento: de onde vêm os embeddings, a história do PLN até
aqui, e as decisões de engenharia envolvidas. É o melhor material gratuito sobre
o tema para quem começa. Leia os capítulos iniciais; o resto pode esperar.

### 0.3 O artigo que nomeou "RAG" **[artigo]**

Lewis, Perez, Piktus, Petroni, Karpukhin, Goyal, Küttler, Lewis, Yih,
Rocktäschel, Riedel & Kiela, *Retrieval-Augmented Generation for
Knowledge-Intensive NLP Tasks*, NeurIPS 2020. arXiv:2005.11401
<https://arxiv.org/abs/2005.11401>

A origem do termo. Leia o resumo e a Figura 1 — isso já dá a intuição completa:
um recuperador busca documentos, um gerador escreve condicionado a eles.

Aviso útil: o que o artigo chama de RAG envolve treinar recuperador e gerador
juntos. **Quase nenhum sistema "RAG" de hoje faz isso**, incluindo o nosso. O que
hoje se chama RAG é a versão simplificada: recuperar e colar no prompt. Saber
disso evita confusão ao ler a literatura.

---

## Nível 1 — O pipeline mínimo, com as mãos

Documentação para construir a Fase 1. Ler enquanto codifica, não antes.

### 1.1 Sentence Transformers — a biblioteca que vamos usar **[prático]**

<https://sbert.net/>

- Quickstart: <https://sbert.net/docs/quickstart.html>
- Busca semântica: <https://sbert.net/examples/sentence_transformer/applications/semantic-search/README.html>
- **Recuperar e reordenar**: <https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html>

A terceira página é a arquitetura da Fase 3 do plano, explicada pelos autores da
biblioteca: um *bi-encoder* rápido traz 20 candidatos, um *cross-encoder* lento e
preciso reordena para 4. Entender por que são dois modelos diferentes, e não um,
é o salto conceitual mais rentável deste nível.

### 1.2 Ollama — como rodar o modelo localmente **[prático]**

<https://docs.ollama.com/> · repositório: <https://github.com/ollama/ollama> ·
modelos: <https://ollama.com/library>

É o que a Fase 0 instala. A referência da API interessa quando o `Generator` do
plano for implementado.

### 1.3 llama.cpp e quantização **[referência]**

<https://github.com/ggml-org/llama.cpp> ·
quantização: <https://github.com/ggml-org/llama.cpp/blob/master/tools/quantize/README.md>

O motor que corre por baixo do Ollama. Consulte quando quiser entender o que
significa `Q4_K_M` — por que os pesos cabem em ~4,5 bits em média, e o que se
perde. Relevante porque, sem GPU, a quantização é o que torna este projeto
possível.

---

## Nível 2 — As decisões do plano, e por quê

Cada item aqui sustenta uma decisão concreta em `PLANO-RAG-LOCAL.md`.

### 2.1 Por que a pergunta vem antes do contexto **[artigo]**

Liu, Lin, Hewitt, Paranjape, Bevilacqua, Petroni & Liang, *Lost in the Middle:
How Language Models Use Long Contexts*, TACL 2023. arXiv:2307.03172
<https://arxiv.org/abs/2307.03172>

Modelos usam melhor a informação que está no **início ou no fim** do contexto, e
pior a que está no meio — mesmo modelos feitos para contexto longo. É a
justificação da ordem do prompt no plano (§3), e vale por si: enterrar o poema
relevante no meio de cinco outros desperdiça a recuperação.

Leia o resumo e a Figura 1 (a curva em U).

### 2.2 Os modos de falha, catalogados **[artigo]**

Barnett, Kurniawan, Thudumu, Brannelly & Abdelrazek, *Seven Failure Points When
Engineering a Retrieval Augmented Generation System* (2024). arXiv:2401.05856
<https://arxiv.org/abs/2401.05856>

**Leia isto antes de escrever código.** Relato de experiência com três sistemas
reais, catalogando sete formas de falhar: conteúdo ausente, falha de busca,
limite de contexto, geração ruim, formato errado, resposta vaga, resposta
incompleta. Curto e directo.

A conclusão é a mais útil do género: *validar um sistema de RAG só é viável em
operação* — a robustez evolui, não se projeta de véspera. É exactamente o
argumento da Fase 0 e da §6 do plano.

### 2.3 Por que busca híbrida: BM25 **[referência]**

Robertson & Zaragoza, *The Probabilistic Relevance Framework: BM25 and Beyond*,
Foundations and Trends in IR 3(4), 2009. DOI 10.1561/1500000019
PDF livre: <https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf>

O algoritmo lexical que, em 2026, continua a ser a linha de base que os métodos
neurais têm de bater. Em poesia as palavras exactas pesam — "Tejo", "tabacaria",
"saudade" — e é isso que BM25 captura e o embedding dilui.

**Não leia as 57 páginas.** As secções 3 e 4 dão a fórmula e a intuição. O resto
é referência.

Implementação: <https://github.com/dorianbrown/rank_bm25> — Python puro, sem
dependências, e é o que a Fase 2 usa.

### 2.4 Como fundir duas listas de resultados **[artigo]**

Cormack, Clarke & Buettcher, *Reciprocal Rank Fusion Outperforms Condorcet and
Individual Rank Learning Methods*, SIGIR 2009.
PDF: <https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf>

Duas páginas e meia, uma fórmula de uma linha, e resolve o problema de combinar o
ranking denso com o do BM25 sem ter de normalizar pontuações incomparáveis. É o
"RRF" do diagrama do plano. **Melhor relação valor/páginas de toda esta lista.**

### 2.5 Enriquecer o documento antes de indexar **[intro]**

Anthropic, *Contextual Retrieval* (2024).
<https://www.anthropic.com/engineering/contextual-retrieval>

Descreve exactamente a mitigação 2 da §2 do plano: passar cada trecho por um LLM
uma vez, gerar contexto descritivo, e indexar isso junto com o texto original.
Reportam redução de 49% nas falhas de recuperação, e 67% somando reordenação.

Leia com uma ressalva: é material de um fornecedor, com os incentivos que isso
implica, e os números são do domínio deles, não de poesia portuguesa. A técnica
é sólida; a magnitude, a medir na Fase 4.

### 2.6 Gerar um documento falso para buscar melhor **[artigo]**

Gao, Ma, Lin & Callan, *Precise Zero-Shot Dense Retrieval without Relevance
Labels* (HyDE), ACL 2023. arXiv:2212.10496
<https://arxiv.org/abs/2212.10496>

A ideia: em vez de embeddar a pergunta, peça ao LLM um documento *hipotético* que
a responderia, e embedde esse. Aproxima o vetor da consulta do espaço dos
documentos.

No plano está **adiado** (§2, mitigação 3), e a razão é o hardware: custa uma
chamada de LLM extra por pergunta, o que em CPU sem GPU é caro. Leia para saber
que existe, não para implementar agora.

---

## Nível 3 — Avaliação

A parte que quase todo projeto de RAG salta, e a razão pela qual quase todo
projeto de RAG não sabe se melhorou.

### 3.1 Como se mede recuperação, e por que BM25 continua de pé **[artigo]**

Thakur, Reimers, Rücklé, Srivastava & Gurevych, *BEIR: A Heterogenous Benchmark
for Zero-shot Evaluation of Information Retrieval Models*, NeurIPS 2021
(Datasets & Benchmarks). arXiv:2104.08663
<https://arxiv.org/abs/2104.08663>

Ensina o vocabulário de métricas que a §6.1 do plano usa — recall@k, nDCG, MRR —
e traz a conclusão que poupa tempo: fora do domínio de treino, **BM25 é uma linha
de base robusta**, e reordenação com cross-encoder é o que de facto ganha, ao
custo de computação.

Poesia portuguesa de 1915 é o caso extremo de "fora do domínio de treino". Trate
esta conclusão como directamente aplicável.

### 3.2 Métricas automáticas para a geração **[artigo]**

Es, James, Espinosa-Anke & Schockaert, *Ragas: Automated Evaluation of Retrieval
Augmented Generation* (2023). arXiv:2309.15217
<https://arxiv.org/abs/2309.15217>

Propõe avaliação sem referência escrita à mão, com três eixos: *faithfulness*
(a resposta assenta no contexto recuperado), *answer relevance*, *context
relevance*.

**Leia como inspiração, não como receita.** Os três eixos do RAGAS medem se a
resposta é fiel à fonte — o que é o objectivo certo para um chatbot de
documentação e o objectivo **errado** para o nosso caso. Uma resposta de Caeiro
não deve ser fiel a um poema: deve ser um poema novo na voz dele, e uma cópia
fiel é precisamente a falha que a guarda de plágio (§6.3 do plano) existe para
apanhar. Aproveite a estrutura — rubrica explícita, avaliação automatizável —
e escreva os seus próprios critérios.

---

## Nível 4 — Português, e este corpus

Onde a literatura genérica deixa de servir.

### 4.1 Codificadores para português europeu **[artigo]** ⭐

Santos, Rodrigues, Branco et al., *Open Sentence Embeddings for Portuguese with
the Serafim PT\* Encoders Family* (2024). arXiv:2407.19527
<https://arxiv.org/pdf/2407.19527>

Modelos: <https://huggingface.co/PORTULAN>
- `serafim-100m-portuguese-pt-sentence-encoder`
- `serafim-335m-portuguese-pt-sentence-encoder`
- `serafim-900m-portuguese-pt-sentence-encoder`
- variantes `-ir`, afinadas para recuperação de informação

Família de codificadores de frases **para português**, do grupo NLX da
Universidade de Lisboa, construída sobre Albertina e BERTimbau, em vários
tamanhos e com licença permissiva.

**Isto é uma actualização ao plano.** A §4.1 do `PLANO-RAG-LOCAL.md` recomenda
`multilingual-e5-base`, um modelo multilíngue genérico. O Serafim é específico
de português e tem variante dedicada a recuperação — e o corpus é português
europeu com ortografia de época. A Fase 0 deve comparar os dois no conjunto
dourado, não assumir o multilíngue. O `-335m-ir` parece o ponto de partida certo
pelo tamanho.

Que um modelo específico da língua bata um multilíngue genérico é plausível, não
garantido: mede-se.

### 4.2 O encoder multilíngue de referência **[artigo]**

Wang, Yang, Huang, Yang, Majumder & Wei, *Multilingual E5 Text Embeddings: A
Technical Report* (2024). arXiv:2402.05672
<https://arxiv.org/abs/2402.05672>

O que o plano recomenda hoje. Detalhe operacional que causa erros silenciosos:
estes modelos **exigem prefixos** — `query: ` na pergunta e `passage: ` no
documento. Sem os prefixos o modelo funciona e devolve resultados piores, sem
avisar. Vale ler a secção de uso.

### 4.3 O encoder multilíngue mais forte, e mais pesado **[artigo]**

Chen, Xiao, Zhang, Luo, Lian & Liu, *BGE M3-Embedding: Multi-Lingual,
Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge
Distillation*, Findings of ACL 2024. arXiv:2402.03216
<https://arxiv.org/abs/2402.03216> · modelo: <https://huggingface.co/BAAI/bge-m3>

Mais de 100 línguas, até 8192 tokens, e faz recuperação densa, esparsa e
multi-vetor no mesmo modelo — ou seja, poderia dar a busca híbrida da Fase 2
sem BM25 separado. Custa ~2,2 GB.

Terceiro candidato do banco de ensaios da Fase 0. Como o corpus só tem ~325 mil
tokens, embeddar com um modelo grande é um custo único e pequeno (§1.3 do plano),
o que torna o teste barato.

---

## Nível 5 — Os fundamentos, por curiosidade

Nada disto é necessário para construir o projecto. É a genealogia das ideias.

### 5.1 Sentence-BERT — a origem dos embeddings de frase **[artigo]**

Reimers & Gurevych, *Sentence-BERT: Sentence Embeddings using Siamese
BERT-Networks*, EMNLP 2019. arXiv:1908.10084
<https://arxiv.org/abs/1908.10084>

O artigo que criou a biblioteca do item 1.1. Resolve o problema de o BERT
original ser inutilizável para busca por similaridade: comparar todos os pares
passava de 65 horas para ~5 segundos. É a razão pela qual busca semântica é
viável num portátil.

### 5.2 Dense Passage Retrieval **[artigo]**

Karpukhin, Oguz, Min, Lewis, Wu, Edunov, Chen & Yih, *Dense Passage Retrieval
for Open-Domain Question Answering*, EMNLP 2020. arXiv:2004.04906
<https://arxiv.org/abs/2004.04906>

Mostrou que recuperação densa treinada bate BM25 por 9–19 pontos em precisão de
top-20. Metade da razão pela qual todo o campo passou a usar embeddings.

Note a tensão com o item 3.1: DPR ganha **no domínio em que treinou**; o BEIR
mostrou que fora dele o BM25 se aguenta. É por isso que o plano usa os dois.

### 5.3 ColBERT — interação tardia **[artigo]**

Khattab & Zaharia, *ColBERT: Efficient and Effective Passage Search via
Contextualized Late Interaction over BERT*, SIGIR 2020. arXiv:2004.12832
<https://arxiv.org/abs/2004.12832>

Um meio-caminho entre bi-encoder rápido e cross-encoder preciso: guarda um vetor
por *token* em vez de um por documento. Explica o que o `bge-m3` quer dizer com
"multi-vetor".

### 5.4 FAISS **[artigo]**

Johnson, Douze & Jégou, *Billion-scale similarity search with GPUs* (2017).
arXiv:1702.08734 <https://arxiv.org/abs/1702.08734>

A biblioteca que o projecto usa hoje, e que o plano propõe **remover**. Leia o
resumo para ver por quê: foi desenhada para mil milhões de vetores em GPU.
O nosso índice tem ~2 800 vetores em CPU. Um `numpy.matmul` faz o mesmo trabalho
em microssegundos, sem a dependência.

É um bom exemplo de como a escala determina a ferramenta — e de como copiar a
arquitetura de um tutorial traz complexidade que não se precisa.

### 5.5 Panorama geral do campo **[referência]**

Gao, Xiong, Gao, Jia, Pan, Bi, Dai, Sun, Wang & Wang,
*Retrieval-Augmented Generation for Large Language Models: A Survey* (2023-2024).
arXiv:2312.10997 <https://arxiv.org/abs/2312.10997>

Levantamento amplo, organizado em Naive / Advanced / Modular RAG. **Não leia
linearmente** — sirva-se dele como mapa quando encontrar um termo desconhecido.
Um *survey* de 2023-24 num campo que se move rápido tem partes já datadas;
use-o para vocabulário e taxonomia, não para escolher tecnologia em 2026.

---

## O que não está aqui, e por quê

- **Tutoriais de LangChain / LlamaIndex.** O plano remove o LangChain (§4.3).
  Aprender RAG através de um *framework* ensina a API do framework, não o
  mecanismo — e depois não se sabe depurar. Construa o pipeline a mão primeiro;
  são ~200 linhas.
- **Comparações de bancos vetoriais.** Irrelevante a 2 800 vetores.
- **Material sobre fine-tuning e LoRA.** Só faz sentido depois de a avaliação
  mostrar que o prompt esgotou o que dava. Antes disso, é optimização cega.
- **Tutoriais de "RAG em 5 minutos".** Produzem exactamente o sistema que este
  repositório já tinha: encoder errado para a língua, pergunta truncada fora do
  prompt, índice gravado e nunca lido.

---

## O caminho mais curto

Se ler só três coisas antes de começar:

1. **Simon Willison sobre embeddings** (0.1) — o mecanismo
2. **Seven Failure Points** (2.2) — como isto falha na prática
3. **RRF** (2.4) — duas páginas e meia que melhoram a recuperação

E uma coisa a medir antes de decidir: **Serafim vs. multilingual-e5 vs. bge-m3**
no conjunto dourado (4.1, 4.2, 4.3). É a decisão técnica de maior impacto no
projecto, e não tem resposta a priori.
