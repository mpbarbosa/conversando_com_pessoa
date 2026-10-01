from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch


class PessoaModel:
    def __init__(self, model_name="google/flan-t5-large", max_input_tokens=512):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        # Exposed so the prompt builder can fit the context to the budget
        # instead of letting the tokenizer cut the tail off the prompt.
        self.max_input_tokens = max_input_tokens

        # Load a seq2seq model (Flan-T5). Use dtype (updated argument name)
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            dtype=dtype,
            device_map="auto"
        )

    def count_tokens(self, text):
        return len(self.tokenizer(text, add_special_tokens=False).input_ids)

    def fit_to_tokens(self, text, max_tokens):
        """Cut `text` down to at most `max_tokens` tokens."""
        if max_tokens <= 0:
            return ""
        ids = self.tokenizer(text, add_special_tokens=False).input_ids
        if len(ids) <= max_tokens:
            return text
        return self.tokenizer.decode(ids[:max_tokens], skip_special_tokens=True)

    def generate(self, prompt, max_tokens=256):
        # Tokenize input (encoder inputs). truncation stays on as a backstop,
        # but build_prompt() is responsible for keeping the prompt inside
        # max_input_tokens so nothing meaningful reaches this cut.
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_input_tokens,
        )

        # Try to place tensors on the same device as the model parameters.
        try:
            device = next(self.model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}
        except StopIteration:
            # Fallback: keep on CPU
            pass

        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=0.8,
                do_sample=True,
                no_repeat_ngram_size=2,
                top_p=0.9,
            )

        response = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return response.strip()
