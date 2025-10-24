# conversando_com_pessoa

# PessoaBot (Prova de Conceito)

Chatbot CLI inspirado em Fernando Pessoa, usando Llama 3 e RAG com FAISS.

## Estrutura
- `data/pessoa_poems/` — [PONTO] Adicione aqui os textos e poemas do Pessoa.
- `src/` — Código-fonte principal.

## Como rodar
```bash
pip install -r requirements.txt
python src/main.py



pessoa-bot/
│
├── data/
│   └── pessoa_poems/        # <- [PONTO] Aqui você colocará os textos e poemas de Pessoa
│
├── src/
│   ├── main.py              # CLI principal (loop de conversa)
│   ├── retriever.py         # RAG: carrega textos, cria embeddings e busca contexto
│   ├── model.py             # Carrega e configura o modelo Llama 3
│   ├── utils.py             # Funções auxiliares (limpeza de texto, logs etc.)
│
├── requirements.txt
├── README.md
└── .gitignore
