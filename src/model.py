from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch


class PessoaModel:
    def __init__(self, model_name="google/flan-t5-large"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        # Load a seq2seq model (Flan-T5). Use dtype (updated argument name)
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            dtype=dtype,
            device_map="auto"
        )

    def generate(self, prompt, max_tokens=256):
        # Tokenize input (encoder inputs)
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512,
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
