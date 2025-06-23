# 

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel
import torch

class LLMDarija:
    def __init__(self, chemin_adapter: str = "Farid59/nllb-darija-lora-model"):
        # Charger le modèle de base
        base_model_id = "facebook/nllb-200-distilled-600M"
        self.tokenizer = AutoTokenizer.from_pretrained(base_model_id)
        base_model = AutoModelForSeq2SeqLM.from_pretrained(base_model_id)

        # Appliquer l'adapter LoRA
        self.model = PeftModel.from_pretrained(base_model, chemin_adapter)

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)

    def traiter(self, texte: str) -> str:
        inputs = self.tokenizer(texte, return_tensors="pt").to(self.device)
        outputs = self.model.generate(**inputs, max_new_tokens=100)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
