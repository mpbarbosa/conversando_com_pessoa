# conversando_com_pessoa

# PessoaBot (Prova de Conceito)

Chatbot CLI inspirado em Fernando Pessoa, usando Llama 3 e RAG com FAISS.



## Como rodar
```bash
pip install -r requirements.txt
python src/main.py
```


💡 Instruções rápidas

1. Baixa o arquivo no teu celular.


2. No GitHub, abre o repositório pessoa-bot.


3. Vai em “Add file → Upload files”, e envia o ZIP (ou descompacta antes e envia os arquivos individualmente).


4. Depois, quando estiver num computador com Python instalado:

pip install -r requirements.txt
python src/main.py


5. Adiciona teus poemas em data/pessoa_poems/ para testar o RAG


## Estrutura
- `data/pessoa_poems/` — [PONTO] Adicione aqui os textos e poemas do Pessoa.
- `src/` — Código-fonte principal.

```
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
├── requirements.txt
├── README.md
└── .gitignore


