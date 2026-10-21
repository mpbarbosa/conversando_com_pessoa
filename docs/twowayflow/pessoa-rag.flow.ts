import { flow } from "@twowayflow/dsl";

/**
 * ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
 * │ Name         pessoa-rag                                                                     │
 * │ Type         Flow graph — cyclic (retry loop, fan-in outside a join node)                   │
 * │ Project      conversando_com_pessoa                                                         │
 * │ Description  The query-time half of PessoaBot: route the question to a heteronym, retrieve  │
 * │              densely, rerank on request, generate locally, then accept or retry behind the  │
 * │              persona and copying guards. Projected from a real codebase, so the ids are the │
 * │              Python's own and the numbers are measured.                                     │
 * └─────────────────────────────────────────────────────────────────────────────────────────────┘
 *
 * The query-time pipeline of `conversando_com_pessoa` (PessoaBot): a local RAG chatbot that
 * answers in verse as Fernando Pessoa or one of his heteronyms.
 *
 * Projected from this repository's own code rather than invented, so the node ids are the names
 * the Python uses (`montar`, `gerar`, `verificar`, `repetir`) and the `params` carry the
 * project's own measured numbers. As a canvas exercise it covers three things the synthetic
 * twowayflow examples do not:
 *
 *  1. **A cycle.** `decidir -> repetirSem -> gerar` is the retry loop. Nothing in the DSL or
 *     the parser forbids one — edges are declared pairs, not nesting — and this is the file
 *     that proves it.
 *  2. **Fan-in that is not a `join` node.** `montar` takes the question, the persona and the
 *     retrieved poems from three different places.
 *  3. **Non-ASCII in opaque payload.** Portuguese labels and accented strings sit beside
 *     `at:`, and dragging a node must not touch a byte of them.
 *
 * The code: `src/pipeline.py` runs this as a hand-written loop, `src/grafo.py` declares the
 * same policy as a LangGraph state graph, and `tests/test_grafo.py` fails if the two ever
 * disagree.
 *
 * **What this graph deliberately does not draw.** Until 2026-10-21 it showed a BM25 arm and
 * an RRF `join` feeding the reranker. That code exists — `src/retrieval/search.py` defines
 * `BuscaHibrida` over `IndiceLexical` and `fusion.rrf` — but no module under `src/` imports
 * it: the AST import graph has no edge into `src.retrieval.search`, and the only importers
 * in the repository are `tests/test_retrieval_gold.py` and `tests/test_fusion.py`.
 * `Pipeline.recuperar` encodes the query, calls `index.search`, and optionally reranks. So
 * the hybrid arm was a projection of code that does not run, and it has been removed rather
 * than redrawn as a dotted line: this file is a graph of the query path, and the hybrid
 * retriever is not on it. The finding is written up in `uml-class-diagram.md` §2, and the
 * BM25 baseline is still measured by `tests/test_retrieval_gold.py` if it is ever rewired.
 */
export default flow("pessoa-rag")
  .node("pergunta", {
    kind: "source",
    at: [0, 400],
    label: "pergunta do utilizador",
    description:
      "The user's turn as it arrives, from the CLI or the web front end, in Portuguese or English.",
    params: { de: ["src/cli.py", "src/web/fluxo.py"], idioma: ["pt", "en"] },
  })
  // The dense index refuses to load when its manifest does not match the corpus signature,
  // the encoder, the chunk count *and* the document order. Returning nothing is deliberate:
  // a stale index does not raise, it answers wrongly.
  .node("indiceDenso", {
    kind: "source",
    at: [660, 0],
    label: "índice denso (numpy)",
    description:
      "The pre-built dense index read from disk; it declines to load unless its manifest matches the corpus signature, the encoder, the chunk count and the document order.",
    params: { caminho: "data/index", chunks: 2290, dim: 768, mb: 7.0, buscaMs: 5.57 },
  })
  // `/auto` only. Measured 72% on 40 questions at +1.2 s; a corrected embedding centroid does
  // 68% for free, so the LLM router is not established as better — see docs/fase-4.
  .node("rotear", {
    kind: "transform",
    at: [310, 400],
    label: "roteador de voz",
    description:
      "Asks a small local model which heteronym the question is about, so retrieval and persona can be scoped to one voice.",
    params: { modelo: "qwen2.5:7b", acerto: 0.72, custoS: 1.2, omissao: "desligado" },
  })
  // e5 requires its prefixes, and without them it degrades silently. The defence is not an
  // assertion but two separate methods, so there is no code path that forgets.
  .node("encodeQuery", {
    kind: "transform",
    at: [660, 160],
    label: "encode_queries",
    description: "Embeds the question with e5, under the `query: ` prefix the model requires.",
    params: { modelo: "multilingual-e5-base", prefixo: "query: " },
  })
  // The depth is not a constant: `Pipeline.recuperar` asks the index for `n_rerank`
  // candidates when a reranker is attached and `top_k` when there is none, so that the
  // reranker has something left to reorder. nDCG@5 and apt@3 measured by running
  // `pytest tests/test_retrieval_gold.py -k linha_de_base` against the closed top-20 pool.
  .node("buscaDensa", {
    kind: "transform",
    at: [1010, 300],
    label: "top-8 / top-6 denso",
    description:
      "Nearest neighbours of the query vector in the dense index, cut at 8 when a reranker will follow and at 6 when nothing will.",
    params: { ndcg5: 0.601, apt3: 0.95, comRerank: 8, semRerank: 6 },
  })
  // Opt-in: +0.090 nDCG@5 for +2.6 s. Never deeper than the top-20 pool the gold set covers,
  // or the measured delta stops meaning anything.
  .node("rerank", {
    kind: "filter",
    at: [1360, 300],
    label: "rerank (opcional)",
    description:
      "Re-scores the 8 dense candidates with a cross-encoder and keeps the top 6; opt-in, because the gain costs seconds.",
    params: { nRerank: 8, topK: 6, deltaNdcg5: 0.09, custoS: 2.6 },
  })
  .node("montar", {
    kind: "transform",
    at: [0, 940],
    label: "montar prompt",
    description:
      "Assembles the system and user messages: persona in the system slot, retrieved poems in the user slot, context cut when the token budget runs out.",
    params: { personaEm: "system", orcamentoTokens: 500, cortaContextoNoLimite: true },
  })
  .node("gerar", {
    kind: "transform",
    at: [340, 940],
    label: "gerar (Ollama)",
    description:
      "Streams the answer from the local Ollama model, first tokens arriving under a second.",
    params: { modelo: "llama3.1:8b-instruct-q4_K_M", fluxo: true, prefillDaEspera: [0.58, 0.89] },
  })
  // Each guard here answers a failure mode seen in the blind evaluation, not an imagined one.
  .node("verificarPersona", {
    kind: "filter",
    at: [680, 940],
    label: "guarda de persona e língua",
    description:
      "Rejects an answer that speaks as the wrong heteronym, or in the wrong language, or that breaks frame to discuss the persona instead of inhabiting it.",
    params: { observado: ["«Reis, na minha voz»", "«este poema não é do Reis»"] },
  })
  // The plan specified 8-gram overlap. The first full run copied three of eight verses at 2%
  // 8-gram overlap: the copying is paraphrase at verse level. Metric replaced, thresholds
  // calibrated on 30 real answers. Median verses copied went 82% -> 0%.
  .node("detectarPlagio", {
    kind: "filter",
    at: [1020, 940],
    label: "guarda de cópia",
    description:
      "Compares each generated verse against the retrieved poems and rejects the answer when a verse is substantially the source's own.",
    params: { metrica: "difflib por verso", limiarVerso: 0.72, naoUsa: "8-gramas" },
  })
  // The acceptance rule. In `pipeline.py` this is an `if` inside a `for`; in `grafo.py` it is
  // a conditional edge. Same condition either way, truncation included.
  .node("decidir", {
    kind: "fanout",
    at: [1360, 940],
    label: "serve?",
    description:
      "The acceptance rule: serve the answer when nothing flagged it and it was not truncated, otherwise send it back for another attempt until the cap.",
    run: (plagiou: boolean, truncada: boolean, tentativa: number, max = 2) => {
      const serve = !plagiou && !truncada;
      return serve || tentativa >= max ? "fim" : "repetir";
    },
  })
  // Asking the model to resist what is in front of it did not work: the retry on the same
  // context returned to the same poem. Dropping the copied poems removes the occasion, and
  // because the budget then admits the next candidates, the model gets new material rather
  // than less of it.
  .node("repetirSem", {
    kind: "transform",
    at: [680, 1160],
    label: "repetir sem os copiados",
    description:
      "Rebuilds the prompt with the copied poems removed, which both takes away the occasion to copy and lets the next candidates into the budget.",
    params: { maxTentativas: 2, taxaMedida: 0.21, corrigiu: "3 de 3", custoMedioGeracoes: 1.21 },
  })
  .node("turno", {
    kind: "sink",
    at: [1700, 940],
    label: "Turno",
    description:
      "The finished turn handed back to the caller: the verse, its sources, and what the run cost.",
    params: { mostra: ["texto", "fontes", "recuperacao_ms", "rerank_ms", "tentativas"] },
  })
  .edge("pergunta", "rotear", { label: "texto" })
  .edge("pergunta", "encodeQuery", { label: "consulta" })
  .edge("pergunta", "montar")
  .edge("rotear", "buscaDensa", { label: "voz" })
  .edge("rotear", "montar", { label: "persona" })
  .edge("indiceDenso", "buscaDensa", { label: "vectores" })
  .edge("encodeQuery", "buscaDensa", { label: "qv" })
  .edge("buscaDensa", "rerank", { label: "candidatos" })
  .edge("rerank", "montar", { label: "top-6 poemas" })
  .edge("montar", "gerar", { label: "system + user" })
  .edge("gerar", "verificarPersona", { label: "versos" })
  .edge("verificarPersona", "detectarPlagio", { label: "texto aceite" })
  .edge("detectarPlagio", "decidir", { label: "veredicto" })
  .edge("decidir", "turno", { label: "fim" })
  .edge("decidir", "repetirSem", { label: "plagiou ou truncou" })
  // The back edge. `mostrados` accumulates across the whole turn, not just the current
  // attempt: dropping a poem from the prompt does not make it acceptable to hand back.
  .edge("repetirSem", "gerar", { label: "contexto novo + reforço" });
