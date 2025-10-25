# PessoaBot - AI Coding Instructions

## Project Overview
This is a CLI chatbot that emulates Fernando Pessoa using Llama 3 and RAG (Retrieval-Augmented Generation) with FAISS vector search. The bot retrieves relevant Pessoa poems/texts to inform contextual responses.

## Architecture Components

### Core Pipeline
1. **Text Loading** (`retriever.py`): Loads `.txt` files from `data/pessoa_poems/`
2. **Embedding Generation**: Uses `all-MiniLM-L6-v2` sentence transformer
3. **Vector Search**: FAISS IndexFlatL2 for semantic similarity search
4. **Response Generation**: Llama 3 model with retrieved context in prompt

### Key Files
- `src/main.py`: CLI loop with prompt template `build_prompt(user_input, retrieved_texts)`
- `src/retriever.py`: `PessoaRetriever` class handles text loading, indexing, and retrieval
- `src/model.py`: `PessoaModel` wrapper for Llama 3 with auto device mapping
- `data/pessoa_poems/`: Text corpus (poems numbered like `poem_100.txt`, `poem_1000.txt`)

## Development Patterns

### RAG Implementation
- **Retrieval**: `retrieve(query, top_k=3)` returns most similar texts via FAISS search
- **Context Building**: Join retrieved texts with `"\n---\n"` separator
- **Prompt Structure**: Fixed template with "Você é Fernando Pessoa" persona + context + user input

### Model Loading
- Uses `torch.float16` on CUDA, `torch.float32` on CPU
- `device_map="auto"` for multi-GPU setups
- Default model: `meta-llama/Meta-Llama-3-8B`

### Index Management
- FAISS index saved to `data/index.faiss` (not in repo)
- `build_index()` creates new index from loaded texts
- `load_index()` loads existing index file

## Critical Workflows

### Setup & Run
```bash
# Recommended: Use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

### Common Issues
- **Import Error**: If `ModuleNotFoundError: No module named 'src'`, imports in `main.py` use relative paths (`from retriever import...`)
- **Missing activate**: If `venv/bin/activate` missing, recreate venv with `--without-pip` then install pip manually
- **First Run**: Expect ~90MB download for `all-MiniLM-L6-v2` model on initial execution
- **Llama 3 Access**: Requires Hugging Face authentication - run `hf auth login` or set HF_TOKEN environment variable

### Adding New Content
- Place `.txt` files in `data/pessoa_poems/`
- Restart application to rebuild index (no incremental updates)
- Index rebuilds automatically on each startup via `load_texts()` → `build_index()`

### Debugging RAG
- Check `retrieved = retriever.retrieve(user_input)` for context quality
- Modify `top_k` parameter in `retrieve()` for more/fewer context documents
- Inspect `build_prompt()` output for prompt engineering

## Project-Specific Conventions

### File Naming
- Poems follow pattern: `poem_{number}.txt` (e.g., `poem_100.txt`, `poem_1000.txt`)
- Numbers are not sequential (gaps like 100→102→104)

### Portuguese Context
- All prompts and responses in Portuguese
- Persona instruction: "Você é Fernando Pessoa. Responda com o estilo e pensamento dele."
- Exit commands: `["sair", "exit", "quit"]`

### Performance Considerations
- No index persistence between runs - rebuilds from scratch each time
- Embeddings computed fresh on startup (no caching)
- GPU automatically detected via `torch.cuda.is_available()`

## Integration Points
- **Transformers**: Hugging Face model loading with device optimization
- **FAISS**: CPU-only version (faiss-cpu) for vector similarity search  
- **Sentence Transformers**: Multilingual embedding model for Portuguese text
- **Torch**: Automatic dtype selection based on hardware capabilities