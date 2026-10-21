# twowayflow — design projections of this project

This folder is the default home for everything produced when `conversando_com_pessoa` is
explored or analyzed with [twowayflow](https://github.com/mpbarbosa/twowayflow): dataflow
diagrams, `*.flow.ts` projections, and analysis notes.

## What is here

| File | What it projects |
|---|---|
| [`pessoa-corpus-build.flow.ts`](pessoa-corpus-build.flow.ts) | The build-time half: 2083 poem files → `corpus.jsonl` → dense index, BM25 index and manifest. Code: `src/corpus/build.py`, `src/retrieval/index.py`. |
| [`pessoa-rag.flow.ts`](pessoa-rag.flow.ts) | The query-time half: route to a heteronym, retrieve densely and lexically, fuse by reciprocal rank, generate locally, then accept or retry behind the persona and copying guards. Code: `src/pipeline.py`, `src/grafo.py`. |
| [`turno-sequencia.md`](turno-sequencia.md) | One turn of `POST /api/perguntar` **in time**: the lock, the point past which no failure can be an HTTP status, the two retentions, and the fact that the plagiarism guard runs after its own fragments have left. Two Mermaid sequence diagrams. Code: `src/web/app.py`, `fluxo.py`, `cancelar.py`, `retencao.py`, `estatico/app.js`. |
| [`servico-topologia.md`](servico-topologia.md) | Where the public service sits on the machine: the two checkouts and why that is a correctness property, the five user units and the dependency they deliberately do not declare, the three state files outside every checkout, and the single Ollama slot. Code: `src/web/unidades.py`, `instalar.py`, `tunel.py`, `sentinela.py`. |
| [`NOTACAO.md`](NOTACAO.md) | An assessment of which diagrams this repository has and which three it is missing, with the reasons. Analysis note, no graph. |

Each file carries a titleblock naming the diagram, its graph type, the project, and what it
shows, so it stays readable when pulled out of this repo.

## What they are, and what they are not

A `*.flow.ts` file is a design artifact in its own right — a graph of computation steps and the
data moving between them, written in twowayflow's embedded DSL and editable either as text or on
twowayflow's canvas. The node ids are the Python's own names and the `params` carry measured
numbers from this project, which is what makes them useful for reading the pipeline.

They are **not** generated output and nothing keeps them in sync with the Python: twowayflow's
one architectural rule is that code on disk is the only source of truth, and these files are not
that code. Treat them as documentation that has to be updated by hand when the pipelines change,
like any other diagram in `docs/`.

## Viewing them

The DSL is TypeScript, so the files read fine in any editor. To open one on the canvas, clone
twowayflow, run `pnpm install`, press <kbd>F5</kbd> ("Run twowayflow extension"), then open the
file in the new window and run **twowayflow: Open Flow Canvas**. The `@twowayflow/dsl` import
only resolves inside that workspace — this folder has no `node_modules`, and is not part of any
build or test run in this repository.
