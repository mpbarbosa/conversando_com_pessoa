from retriever import PessoaRetriever
from model import PessoaModel

PERSONA = "Você é Fernando Pessoa. Responda com o estilo e pensamento dele."
SEPARATOR = "\n---\n"


def build_prompt(user_input, retrieved_texts, model, reserve=16):
    """Compose the prompt so the question always survives truncation.

    The question comes before the context, and the context is trimmed to
    whatever token budget is left -- previously the tokenizer cut the tail of
    the prompt, which is where the question used to sit, so a long retrieved
    poem could drop the question entirely.
    """
    head = (
        f"{PERSONA}\n\n"
        f"Pergunta: {user_input}\n\n"
        f"Contexto (poemas e textos):\n"
    )
    tail = "\n\nPessoa:"

    budget = (
        model.max_input_tokens
        - model.count_tokens(head)
        - model.count_tokens(tail)
        - reserve
    )
    separator_cost = model.count_tokens(SEPARATOR)

    blocks = []
    for text in retrieved_texts:
        cost_of_separator = separator_cost if blocks else 0
        room = budget - cost_of_separator
        if room <= 0:
            break
        block = model.fit_to_tokens(text.strip(), room)
        if not block.strip():
            break
        budget -= model.count_tokens(block) + cost_of_separator
        blocks.append(block)

    return head + SEPARATOR.join(blocks) + tail


def main():
    retriever = PessoaRetriever()
    model = PessoaModel()

    print("=== PessoaBot CLI ===")
    print("Fale com Fernando Pessoa. Digite 'sair' para encerrar.\n")

    # Reuses data/index.faiss when the corpus and encoder are unchanged,
    # instead of re-embedding the whole corpus on every start.
    retriever.load_or_build_index()

    while True:
        user_input = input("Você: ")
        if user_input.lower() in ["sair", "exit", "quit"]:
            print("PessoaBot: Adeus, como quem se despede de si mesmo.")
            break

        retrieved = retriever.retrieve(user_input)
        prompt = build_prompt(user_input, retrieved, model)
        response = model.generate(prompt)
        print(f"\nPessoaBot: {response}\n")


if __name__ == "__main__":
    main()
