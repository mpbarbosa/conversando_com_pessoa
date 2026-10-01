# PessoaBot - AI Coding Instructions

## Project Overview
This is a CLI chatbot that emulates Fernando Pessoa using Flan-T5 and RAG (Retrieval-Augmented Generation) with FAISS vector search. The bot retrieves relevant Pessoa poems/texts to inform contextual responses.

## Architecture Components

### Core Pipeline
1. **Text Loading** (`retriever.py`): Loads `.txt` files from `data/pessoa_poems/` in sorted order
2. **Embedding Generation**: Uses the `paraphrase-multilingual-MiniLM-L12-v2` sentence transformer
3. **Vector Search**: FAISS `IndexFlatIP` over L2-normalised vectors (cosine similarity)
4. **Response Generation**: Flan-T5 with retrieved context in a token-budgeted prompt

### Key Files
- `src/main.py`: CLI loop plus `build_prompt(user_input, retrieved_texts, model)`
- `src/retriever.py`: `PessoaRetriever` handles text loading, indexing, persistence, and retrieval
- `src/model.py`: `PessoaModel` wrapper for Flan-T5 with auto device mapping
- `data/pessoa_poems/`: Text corpus (poems numbered like `poem_100.txt`, `poem_1000.txt`)

### Corpus Shape
Every file starts with the author line (the orthonym or a heteronym) followed by a `Titulo:` line. The current distribution is roughly: Fernando Pessoa 1298, Álvaro de Campos 323, Ricardo Reis 252, Alberto Caeiro 120, Alexander Search 52, Bernardo Soares 6, plus a tail of pre-heteronyms. About 160 poems are in English. This metadata is **not** parsed out yet — it is embedded as part of the document text.

## Development Patterns

### RAG Implementation
- **Embeddings must stay multilingual.** The corpus is overwhelmingly Portuguese; an English-only encoder (such as `all-MiniLM-L6-v2`) retrieves close to noise here.
- **Similarity**: vectors are L2-normalised and searched with `IndexFlatIP`, which makes the metric cosine. Do not switch to raw `IndexFlatL2` — these embeddings are not trained for it.
- **Retrieval**: `retrieve(query, top_k=3)` returns the most similar texts. It raises if no index is loaded rather than returning garbage.
- **Context Building**: retrieved texts joined with `"\n---\n"`, fitted to the remaining token budget.

### Prompt Structure
`build_prompt()` puts the persona and the **question first**, then the context, then the `Pessoa:` cue. It measures the fixed parts against `model.max_input_tokens` and trims the context to what is left. This ordering is deliberate: the tokenizer truncates from the right, so with context-first a single long poem (the corpus has 88 files over 2 KB, and *Ode Marítima* is 44 KB) would push the question out of the prompt entirely.

When changing the prompt, keep the question ahead of the context and keep the budget accounting, or that bug returns silently.

### Model Loading
- Uses `torch.float16` on CUDA, `torch.float32` on CPU
- `device_map="auto"` for multi-GPU setups
- Default model: `google/flan-t5-large` (no Hugging Face authentication required)
- `max_input_tokens` (default 512) is exposed on `PessoaModel` so the prompt builder can respect it

### Index Management
- FAISS index at `data/index.faiss`, with a sibling `data/index.manifest.json`. Both are gitignored build artifacts.
- The manifest records the embedding model name, the ordered filename list, and a fingerprint of the corpus (names + sizes).
- **FAISS ids are positional**, so the index is only meaningful alongside the document order it was built from. That is what the manifest exists for; never load the index without it.
- `load_or_build_index()` is the entry point: it reuses the persisted index when the manifest matches the corpus and encoder, and rebuilds otherwise.
- `load_index()` returns `None` (rather than a stale index) when the corpus changed, the encoder changed, the manifest is missing or unreadable, or the vector count disagrees with the document count.

## Critical Workflows

### Setup & Run
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

### Common Issues
- **Import Error**: If `ModuleNotFoundError: No module named 'src'`, imports in `main.py` use relative paths (`from retriever import...`)
- **Missing activate**: If `venv/bin/activate` missing, recreate venv with `--without-pip` then install pip manually
- **First Run**: expect a download for the embedding model (~470 MB) and for `google/flan-t5-large` (~3 GB), cached in `~/.cache/huggingface/`
- **First run after upgrading**: an index built by an older version has no manifest, so it is rejected and rebuilt once

### Adding New Content
- Place `.txt` files in `data/pessoa_poems/`
- Restart the application; the corpus fingerprint changes, so the index rebuilds automatically
- Rebuilds are all-or-nothing — there are no incremental updates

### Debugging RAG
- Check `retriever.retrieve(user_input)` for context quality
- Modify `top_k` in `retrieve()` for more/fewer context documents
- Inspect `build_prompt()` output to confirm the question is present and the prompt fits the budget

## Project-Specific Conventions

### File Naming
- Poems follow pattern: `poem_{number}.txt` (e.g., `poem_100.txt`, `poem_1000.txt`)
- Numbers are not sequential (gaps like 100→102→104)
- Files are loaded in lexicographic order, which is stable but **not** numeric (`poem_10` precedes `poem_2`). Only stability matters.

### Portuguese Context
- All prompts and responses in Portuguese
- Persona instruction: "Você é Fernando Pessoa. Responda com o estilo e pensamento dele."
- Exit commands: `["sair", "exit", "quit"]`

### Performance Considerations
- The index persists between runs; the corpus is only re-embedded when it or the encoder changes
- GPU automatically detected via `torch.cuda.is_available()`

## Known Gaps
Deliberately not implemented yet, and tracked in `ROADMAP.md`:
- Heteronym-aware retrieval and persona routing (the author metadata is present but unused)
- Chunking of long poems, which currently become a single diluted vector
- Language separation for the English poems
- Conversation memory, structured logging, and error handling

## Integration Points
- **Transformers**: Hugging Face model loading with device optimization
- **FAISS**: CPU-only version (faiss-cpu) for vector similarity search
- **Sentence Transformers**: multilingual embedding model, required for the Portuguese corpus
- **Torch**: Automatic dtype selection based on hardware capabilities
