# api/ia_api/model.py (VERSION FINALE - pour charger un modèle complet fusionné)

# On a besoin de 'pipeline' pour l'inférence
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import torch

class LLMTranslator:
    def __init__(
        self,
        # Le chemin pointe maintenant vers le modèle complet et autonome sur le Hub
        model_id: str = "Farid59/nllb-darija-lora-model"
    ):
        print(f"Chargement du modèle de traduction COMPLET depuis : {model_id}")

        # 1) Charger directement le tokenizer et le modèle final.
        #    Plus besoin de PeftModel ou de charger un modèle de base.
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_id)
        
        print("Modèle complet chargé avec succès.")

        # 2) Déterminer le device (GPU si disponible, sinon CPU)
        device = 0 if torch.cuda.is_available() else -1
        print(f"Utilisation du device d'inférence : {'cuda:0' if device == 0 else 'cpu'}")

        # 3) Créer la pipeline de traduction de Hugging Face
        #    C'est une manière propre et optimisée de gérer l'inférence.
        self.translator = pipeline(
            "translation",
            model=model,
            tokenizer=tokenizer,
            device=device
        )

    def traiter(self, texte: str, src_lang: str, tgt_lang: str) -> str:
        """
        Traduit un texte d'une langue source à une langue cible.
        """
        # 4) Appel simple de la pipeline en passant les langues dynamiquement
        outputs = self.translator(
            texte,
            src_lang=src_lang,
            tgt_lang=tgt_lang,
            max_new_tokens=100
        )
        # 5) Extraire et retourner le texte traduit
        return outputs[0]["translation_text"]