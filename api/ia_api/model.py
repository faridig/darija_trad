# api/ia_api/model.py

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from peft import PeftModel
import torch

class LLMTranslator:
    def __init__(
        self,
        base_model_id: str = "facebook/nllb-200-distilled-600M",
        adapter_path: str = "Farid59/nllb-darija-lora-model"
    ):
        # 1) Tokenizer + modèle de base
        tokenizer = AutoTokenizer.from_pretrained(base_model_id)
        base_model = AutoModelForSeq2SeqLM.from_pretrained(base_model_id)

        # 2) Charger l’adapter LoRA
        model = PeftModel.from_pretrained(base_model, adapter_path)

        # 3) Déterminer le device
        device = 0 if torch.cuda.is_available() else -1

        # 4) Créer la pipeline de traduction
        #    On ne donne PAS src_lang/tgt_lang ici : on les passera à l'appel
        self.translator = pipeline(
            "translation",
            model=model,
            tokenizer=tokenizer,
            device=device
        )

    def traiter(self, texte: str, src_lang: str, tgt_lang: str) -> str:
        """
        Traduire `texte` de `src_lang` vers `tgt_lang`.
        La HF TranslationPipeline prend en charge le préfixe automatique,
        le forced_bos_token_id, etc.
        """
        # 5) Appel de la pipeline avec override dynamique des langues
        outputs = self.translator(
            texte,
            src_lang=src_lang,
            tgt_lang=tgt_lang,
            max_new_tokens=100
        )
        # 6) Extraire le texte traduit
        return outputs[0]["translation_text"]
