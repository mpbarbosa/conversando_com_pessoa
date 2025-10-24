from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class PessoaModel:
    def __init__(self, model_name="meta-llama/Llama-3-8b-chat-hf"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto"
        )

    def generate(self, prompt, max_tokens=512):
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        output = self.model.generate(**inputs, max_new_tokens=max_tokens, temperature=0.8)
        return self.tokenizer.decode(output[0], skip_special_tokens=True)
