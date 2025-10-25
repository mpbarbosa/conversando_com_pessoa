from retriever import PessoaRetriever
from model import PessoaModel

def build_prompt(user_input, retrieved_texts):
    context = "\n---\n".join(retrieved_texts)
    return f"""Você é Fernando Pessoa. Responda com o estilo e pensamento dele.
Contexto (poemas e textos):
{context}

Usuário: {user_input}
Pessoa:"""

def main():
    retriever = PessoaRetriever()
    model = PessoaModel()

    print("=== PessoaBot CLI ===")
    print("Fale com Fernando Pessoa. Digite 'sair' para encerrar.\n")

    retriever.load_texts()
    retriever.build_index()

    while True:
        user_input = input("Você: ")
        if user_input.lower() in ["sair", "exit", "quit"]:
            print("PessoaBot: Adeus, como quem se despede de si mesmo.")
            break

        retrieved = retriever.retrieve(user_input)
        prompt = build_prompt(user_input, retrieved)
        response = model.generate(prompt)
        print(f"\nPessoaBot: {response}\n")

if __name__ == "__main__":
    main()
