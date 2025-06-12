# model.py
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

class LLMDarija:
    def __init__(self, chemin_modele: str):
        self.tokenizer = AutoTokenizer.from_pretrained(chemin_modele)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(chemin_modele)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)

    def traiter(self, texte: str) -> str:
        inputs = self.tokenizer(texte, return_tensors="pt").to(self.device)
        outputs = self.model.generate(**inputs, max_new_tokens=100)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)


modele = LLMDarija("llm/nllb-darija-lora-model")  