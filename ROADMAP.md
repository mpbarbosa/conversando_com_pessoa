# PessoaBot Development Roadmap

## Current Status (October 2025)
- ✅ **Project Setup Complete**: Virtual environment, dependencies installed
- ✅ **Import Issues Resolved**: Fixed relative import paths in `main.py`
- ✅ **Documentation Created**: `.github/copilot-instructions.md` and `ROADMAP.md`
- ✅ **Model Updated**: Changed to `meta-llama/Meta-Llama-3-8B` (base model)
- ⏳ **Pending**: Hugging Face authentication setup for Llama 3 access
- ⏳ **Next**: Full application testing with authenticated model access

## Immediate Priorities

### 1. Complete Basic Setup (HIGH PRIORITY)
- **Hugging Face Authentication**: Get model access working
  - Request access to `meta-llama/Meta-Llama-3-8B`
  - Generate and configure HF token
  - Test full application pipeline
- **Validate RAG Pipeline**: Ensure text retrieval and context building works
- **Test Portuguese Response Quality**: Verify Pessoa-style responses

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

### Alternative Models (Backup Options)
If Llama 3 access is delayed, consider these alternatives for testing:
- **`microsoft/DialoGPT-large`**: Conversational model, no authentication required
- **`EleutherAI/gpt-neo-2.7B`**: Open source GPT-style model
- **`google/flan-t5-large`**: Instruction-following model, good for structured responses
- **Note**: May require prompt template adjustments for optimal Portuguese responses

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