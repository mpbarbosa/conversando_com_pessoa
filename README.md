# conversando_com_pessoa

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
