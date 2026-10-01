# PessoaBot Development Roadmap

> ⚠️ **Documento histórico (Outubro de 2025).** Descreve o objectivo **anterior**
> deste repositório — um chatbot CLI com RAG sobre FAISS e um modelo gratuito
> (Flan-T5) — e o «✅ Ready for Production» abaixo está correcto **para esse
> escopo**. O sistema actual é outro: encoder `multilingual-e5-base`, índice denso
> em `numpy` com manifesto de integridade, BM25, avaliação por nDCG@5 e geração em
> Ollama. **Para o estado actual, leia [`docs/CONTROLO.md`](docs/CONTROLO.md)** —
> o índice-mestre — ou o [`README.md`](README.md).
>
> Mantido por valer como registo: as secções «Common Setup Issues» e «Alternative
> Free Models» documentam problemas reais e as suas soluções.

## Current Status (October 2025)
- ✅ **Project Setup Complete**: Virtual environment, dependencies installed, accelerate added
- ✅ **Import Issues Resolved**: Fixed relative import paths in `main.py`
- ✅ **Documentation Created**: `.github/copilot-instructions.md` and `ROADMAP.md`
- ✅ **Free Model Successfully Deployed**: Switched to `google/flan-t5-large` (no auth required)
- ✅ **Full Pipeline Tested**: RAG retrieval + Flan-T5 generation working in Portuguese
- ✅ **Code Quality**: Fixed deprecation warnings (torch_dtype, early_stopping)
- ✅ **Ready for Production**: Chatbot responds authentically as Fernando Pessoa

## Immediate Priorities

### 1. Enhancement Opportunities (MEDIUM PRIORITY)
- **Prompt Engineering**: Fine-tune persona consistency and response quality
- **Retrieval Optimization**: Adjust top_k parameters and similarity thresholds  
- **Performance Tuning**: Monitor memory usage and generation speed
- **Content Expansion**: Add more poems or heteronym-specific texts

### 2. Core Stability Improvements (MEDIUM PRIORITY)
- **Error Handling**: Add graceful failures for model loading, file access
- **Configuration Management**: Move hardcoded values to config file
- **Logging System**: Replace print statements with proper logging
- **Memory Management**: Monitor GPU/CPU usage during inference

## Future Enhancement Areas

### 3. RAG Implementation & Model Configuration
- **Question**: Are there specific aspects of the RAG implementation or model configuration that need elaboration?
- **Potential improvements**:
  - Add incremental index updates instead of full rebuilds
  - Implement embedding caching for faster startup
  - Fine-tune similarity search parameters
  - Experiment with different embedding models for Portuguese

### 4. Performance Optimizations & Scaling
- **Question**: Should we document performance optimizations or scaling considerations?
- **Potential improvements**:
  - Add FAISS GPU support for larger datasets
  - Implement batch processing for multiple queries
  - Add memory usage monitoring and optimization
  - Consider distributed search for very large corpora

### 5. Development Workflows & Debugging
- **Question**: Are there common development workflows or debugging techniques that should be documented?
- **Potential improvements**:
  - Add logging framework for retrieval quality analysis
  - Create evaluation metrics for response quality
  - Add tools for corpus analysis and quality assessment
  - Implement A/B testing framework for prompt variations

### 6. Prompt Engineering & Persona Implementation
- **Question**: Should we include more details about prompt engineering or Fernando Pessoa persona implementation?
- **Potential improvements**:
  - Document different persona variations (heteronyms)
  - Add prompt template versioning
  - Implement context window management for long conversations
  - Create evaluation framework for persona consistency

## Common Setup Issues & Solutions

### Virtual Environment Problems
- **Issue**: Corrupted `venv/` missing activation scripts (`activate`, `pip`, etc.)
- **Symptoms**: `venv/bin/` only contains Python executables, no `activate` or `pip`
- **Solution**: 
  ```bash
  rm -rf venv
  python3 -m venv venv --without-pip
  source venv/bin/activate
  curl https://bootstrap.pypa.io/get-pip.py | python
  pip install -r requirements.txt
  ```

### Import Path Issues
- **Issue**: `ModuleNotFoundError: No module named 'src'` when running `python src/main.py`
- **Root Cause**: Relative imports fail when running script from project root
- **Solution**: Use relative imports in `src/main.py`:
  ```python
  # Change from:
  from src.retriever import PessoaRetriever
  from src.model import PessoaModel
  
  # To:
  from retriever import PessoaRetriever
  from model import PessoaModel
  ```
- **Alternative**: Run from `src/` directory: `cd src && python main.py`

### Model Loading Performance
- **Issue**: First run downloads large models (sentence-transformers, Llama 3)
- **Expected Behavior**: `all-MiniLM-L6-v2` (~90MB) downloads on first execution
- **Tip**: Model files cached in `~/.cache/huggingface/` for subsequent runs

### Hugging Face Authentication Required
- **Issue**: `401 Client Error: Unauthorized` when accessing `meta-llama/Meta-Llama-3-8B`
- **Root Cause**: Llama 3 is a gated model requiring authentication and license acceptance
- **Prerequisites**:
  1. Create Hugging Face account at https://huggingface.co/
  2. Request access to `meta-llama/Meta-Llama-3-8B` and accept license
  3. Generate access token at https://huggingface.co/settings/tokens
- **Solutions**:
  ```bash
  # Option 1: Login via CLI
  pip install huggingface_hub
  hf auth login
  
  # Option 2: Environment variable
  export HF_TOKEN="your_token_here"
  
  # Option 3: Use alternative open model (if Llama 3 access unavailable)
  # Edit src/model.py to use "microsoft/DialoGPT-large" or similar
  ```

### Alternative Free Models (No Authentication Required)

#### **Active: Google Flan-T5-Large** ✅ **DEPLOYED & WORKING**
- **Model**: `google/flan-t5-large` 
- **Size**: ~3.13GB (instruction-following, multilingual)
- **Pros**: Excellent Portuguese support, instruction-following, no auth required
- **Cons**: Larger download, slower initial startup
- **Status**: **Fully integrated and tested** - authentic Portuguese responses confirmed!

#### **Other Strong Options:**
- **`google/flan-t5-large`**: Instruction-following, multilingual (3GB)
- **`EleutherAI/gpt-neo-2.7B`**: GPT-style architecture, fully open (10GB)
- **`facebook/blenderbot-400M-distill`**: Conversational, very fast (400MB)
- **`microsoft/DialoGPT-medium`**: Smaller version of DialoGPT (355MB)

#### **Quick Model Switching:**
```python
# In src/model.py, change the default model_name to:
"google/flan-t5-large"           # ✅ CURRENT: Best multilingual performance
"microsoft/DialoGPT-large"      # Alternative: Faster conversational model  
"EleutherAI/gpt-neo-2.7B"       # Alternative: Larger context window
"microsoft/DialoGPT-medium"     # Alternative: Fastest performance
```

## Technical Debt & Code Quality

### Code Organization
- Add proper error handling throughout the pipeline
- Implement configuration management (YAML/JSON config files)
- Add type hints and documentation strings
- Create proper logging instead of print statements

### Testing Framework
- Unit tests for retrieval accuracy
- Integration tests for the full pipeline
- Performance benchmarks
- Regression tests for model outputs

### Documentation
- API documentation for each component
- Usage examples and tutorials
- Troubleshooting guide
- Performance tuning guide

## Feature Requests

### User Experience
- Web interface option
- Conversation history persistence
- Multiple conversation threads
- Export conversation functionality

### Content Management
- Tools for corpus preprocessing and validation
- Automated content ingestion from various sources
- Content deduplication and quality filtering
- Metadata management for poems and texts

### Advanced Features
- Multi-language support
- Voice input/output integration
- Integration with external APIs (poetry databases)
- Real-time learning from user interactions

---

*This roadmap should be updated as the project evolves and new requirements emerge.*