# What notation this project is missing — an assessment

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ Name         notacao-assessment                                                             │
│ Type         Analysis note — no graph                                                       │
│ Project      conversando_com_pessoa                                                         │
│ Description  An inventory of the diagrams this repository already has, and an argument for  │
│              the three it is missing: the wire protocol in time, the runtime topology of    │
│              the service, and the egress surface of the poem body. Written 2026-10-21 from  │
│              the code, not from the docs about the code.                                    │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 1. What is already drawn

| Artifact | Notation | What it covers | Where |
|---|---|---|---|
| module → file sketch | ASCII tree | the build-time spine, `parse` → `dedupe` → `chunk` → `build` → index | `README.md` |
| `graph TD` of the state graph | Mermaid flowchart | the 6 LangGraph nodes and the retry back-edge — emitted by LangGraph itself | `README.md`, `docs/FASE-6.md` |
| `erDiagram` of persistence | Mermaid ER | `Sessao`/`Mensagem`/`TurnoReg`/`Fonte`/`PropostaReg` | `docs/FASE-6.md` §3.4 |
| `pessoa-corpus-build.flow.ts` | twowayflow dataflow | build-time, with measured params | `docs/twowayflow/` |
| `pessoa-rag.flow.ts` | twowayflow dataflow | query-time, with the retry cycle and the non-join fan-in | `docs/twowayflow/` |

Everything else — 30+ phase documents, 13 thematic ones, a 162 KB `CONTROLO.md` — is prose
and tables.

**The asymmetry worth naming first:** the one entity-level diagram in the repository describes
`data/sessoes.db`, which **does not exist** (Fase 6 passo 8 is unbuilt; nothing in `src/`
imports sqlite3). The three things that do exist and run every day — the wire protocol, the
systemd topology, and the set of paths a poem body can leave by — have no diagram at all.

## 2. The gap that matters most: the dataflow projection hides the I7′ bug class

`pessoa-rag.flow.ts` draws

```
gerar → verificarPersona → detectarPlagio → decidir → turno
```

and that picture is true of `src/pipeline.py` and false of `src/web/app.py`. On the wire the
fragments of a *rejected* attempt have already left the process before `detectarPlagio` can
reject it — measured, 6 of 8 verses of `poem_1104` — because `POST /api/perguntar` streams
NDJSON and the guard is downstream in the *dataflow*, not downstream in *time*. That is the
whole finding of the I7′ sweep (`src/web/retencao.py`, `tests/test_i7.py`), and a dataflow
graph structurally cannot express it: edges are data dependencies, and there are no lifelines
to be concurrent on.

So the missing notation is not another graph of the same thing. It is the one notation whose
primitive is **ordering**.

### Recommendation 1 — a sequence diagram of one turn (highest value, lowest cost)

Four lifelines: browser (`app.js`), the FastAPI handler, the pipeline thread, Ollama. What it
must show, all of which is in the code today and in no diagram:

- `GET /api/estado` answering **during** a generation (gate I4) — why asking the state must
  load nothing (`estado.py`: no `Encoder()`, no reranker).
- the `trinco` (`asyncio.Lock`) taken in the handler, released in the generator's `finally`
  and not at handler return, because a `StreamingResponse` body runs after the handler returns.
- the sentinel check **before** the lock, so a refusal during a measurement window costs nobody
  the lock.
- the four events in time order: `proposta` (only with `auto`, before generation), `fragmento`×N,
  `turno` **per attempt** — not once — then more fragments on a retry, and `erro` after the HTTP
  status was already 200.
- the point where `Retentor.redigir` sits, and the dotted line marking what has already left.
- the cancel path: client `AbortController` → socket closed → `GeradorCancelavel` → lock freed.

One Mermaid `sequenceDiagram`, maybe 40 lines. It belongs next to `docs/FASE-6.md` §4.4 and it
earns its place by making an argument the prose makes three times in three files.

## 3. Recommendation 2 — the runtime topology of the service

`docs/producao/SERVICO.md` is 11 KB of prose read off the machine, and the facts in it are
positional: which of the **two checkouts** is running, which is being edited, where the state
files are, which units depend on which and how.

No diagram shows:

- the work checkout vs `~/.local/share/pessoabot/servico`, and that `unidades.py`
  **refuses** to install units pointing at the work checkout (`recusar_o_trabalho`) — an
  asserted invariant, not a convention;
- the five user units (`ollama`, `pessoabot`, `cloudflared`, `pessoabot-tunel-guarda` and its
  `.timer`), with `After=ollama.service` and deliberately **no** `Requires=` — so that a dead
  Ollama is a diagnosable component state (I3) rather than a dead process;
- `enable-linger` as the reason any of it survives a logout;
- the out-of-checkout state files that are load-bearing: `~/.local/state/pessoabot/.medicao-a-correr`,
  `~/.config/pessoabot/convidados`, `~/.config/pessoabot/tunel-desligado`;
- **the single Ollama slot** shared by the service and a measurement phase, which is the entire
  reason `sentinela.medicao(...)` exists and takes the tunnel down while it measures.

A deployment/topology diagram (host box, two checkout boxes, unit boxes with dependency edges,
state files, the one contended resource). Not a dataflow — this is placement and dependency, so
Mermaid or a C4-container-style box diagram, not a `.flow.ts`.

## 4. Recommendation 3 — the egress surface of the poem body

The open question in this repository is a disclosure question (`docs/EXPOSICAO-CORPUS.md`,
options A–F, decision untaken). The I7′ sweep found that the body left by **four** paths, three
of which nobody was looking at:

1. `GET /api/poema/{id}` — the one everybody knew about, and the one that was suspended;
2. streamed fragments of the plagiarising attempt;
3. the `turno` event of the rejected attempt, carrying the whole text;
4. `serial.verso_copiado` — "the generated verse, without the original", true except in the
   literal-copy case, which is the case that matters.

Plus the paths that are not HTTP at all: 2083 files in `HEAD` of a public repo since `396cca7`,
and three judgment sheets with whole poems, one of them still versioned.

A data-flow diagram **with trust boundaries** — the loopback bind, the `cloudflared` process
that connects from inside and therefore passes I7 literally while defeating it, the git remote
as a second boundary, `Retentor` drawn as the control on the three wire paths — is the artifact
the undecided question actually needs. It also happens to be the diagram that makes the
"`bind` did not change and the service is on the internet" sentence self-evident instead of
needing two paragraphs.

## 5. Second tier — worth it, but after the three above

- **The manifest as a decision table.** Five conditions (encoder, dim, corpus signature, chunk
  count, document order) and one output: `None`. The point of the table is that
  `estado.diagnosticar_indice` **re-implements** the same five checks to say *which* one failed
  (I3), that this duplication is deliberate, and that a parity test is what holds it. A 5-row
  table with two implementation columns and the test that joins them states a known risk better
  than the two docstrings that currently carry it.
- **The readiness statechart.** `docs/FASE-6.md` §4.2 lists four waits that are not the
  generation (corpus ~40 s, index ~6,4 min, router warm-up ~20 s, reranker load). It is a table
  of states with no transitions; `app.js` has the transitions and the locked/generating/cancelled
  states on top. A statechart adds exactly what the table is missing.
- **The measurement provenance DAG.** This repository's thesis is that every decision has a
  number behind it, and `CONTROLO.md` is the index: 55 corrections, plus defects found in the
  instruments themselves — a reused KV cache that invalidated four hours of data and contaminated
  cells in five phases, a non-blind voice evaluation that changed a model recommendation. A graph
  of *phase → artifact → claim*, with `invalidates` edges, would be the most distinctive diagram
  this project could have. It is also the most expensive and the fastest to rot, which is why it
  is second tier and not first.

## 6. Not worth drawing

| Candidate | Why not |
|---|---|
| UML class diagram | 42 classes, almost all frozen dataclasses; two inheritance edges in the whole tree (`GeradorCancelavel`→`OllamaGenerator`) and two `Protocol`s. A class diagram would be a list of records with no structure to show. |
| module import graph | auto-generatable, and the README's ASCII already carries the spine with the measurements attached. One exception below. |
| domain → wire schema map | `src/web/serial.py` *is* that map, one function per type, with a test that fails when a domain field is added and not serialized. A diagram would be a worse copy. |
| C4 context diagram | one user, one machine, no external system but a local Ollama. The box would contain the whole repository. |
| another dataflow of the query path | `pessoa-rag.flow.ts` already does it, and §2 above is the argument that a second one would repeat the same blind spot. |

**The one import-graph diagram that would earn its place** is narrow: PRODUCAO §9 asserts that a
publication plan needing to touch the policy is badly designed, and the code honours it —
`src/web/` reads constants and dataclasses from `voices`, `roteador`, `pipeline`, `guard`,
`plagio` and never writes policy, which is why `retencao.py` lives in the transport layer. That
is a **layering constraint with a forbidden direction**, it is the load-bearing claim of the
whole production plan, and it is currently enforced by nothing — there is no test on the import
direction. A small layer diagram plus the test it implies would be worth more than the diagram
alone.

## 7. If only one thing gets drawn

The sequence diagram (§2). It is the cheapest, it is the only one of the three whose absence has
already cost this project a bug, and it is the one the existing `.flow.ts` projection cannot be
extended to cover.
