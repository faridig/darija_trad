# api/ia_api/model.py

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel
import torch

class LLMTranslator:
    def __init__(
        self,
        base_model_id: str = "facebook/nllb-200-distilled-600M",
        adapter_path: str = "Farid59/nllb-darija-lora-model"
    ):
        """
        Initialise le traducteur en chargeant le modèle de base, l'adaptateur LoRA,
        et en les préparant pour l'inférence.
        """
        # 1. Déterminer le device (GPU si disponible, sinon CPU)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"LLMTranslator: Utilisation du device '{self.device}'")

        # 2. Charger le tokenizer et le modèle de base
        self.tokenizer = AutoTokenizer.from_pretrained(base_model_id)
        base_model = AutoModelForSeq2SeqLM.from_pretrained(base_model_id)

        # 3. Appliquer l'adaptateur LoRA au modèle de base
        self.model = PeftModel.from_pretrained(base_model, adapter_path)
        
        # 4. Déplacer le modèle sur le bon device et le mettre en mode évaluation (optimisation)
        self.model.to(self.device)
        self.model.eval() 
        print("LLMTranslator: Modèle chargé et prêt.")

    def traiter(self, texte: str, src_lang: str, tgt_lang: str) -> str:
        """
        Traduit `texte` de `src_lang` vers `tgt_lang` en contrôlant manuellement
        les étapes de génération pour une fiabilité maximale.
        """
        # Étape 1 : Configurer le tokenizer avec la langue source AVANT de tokeniser
        self.tokenizer.src_lang = src_lang
        
        # Étape 2 : Tokeniser le texte d'entrée et le déplacer sur le device
        inputs = self.tokenizer(texte, return_tensors="pt", padding=True, truncation=True).to(self.device)
        
        # Étape 3 : Forcer le modèle à commencer la génération avec le token de la langue cible.
        # C'est l'étape la plus critique que la `pipeline` automatisée ne gérait pas correctement.
        forced_bos_token_id = self.tokenizer.convert_tokens_to_ids(tgt_lang)
        
        # Étape 4 : Générer la traduction avec le modèle.
        # `torch.no_grad()` désactive le calcul de gradient pour une inférence plus rapide.
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                forced_bos_token_id=forced_bos_token_id,
                max_new_tokens=100  # Limite de sécurité pour la longueur de la réponse
            )
            
        # Étape 5 : Décoder les tokens de sortie en texte lisible
        reponse = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
        
        return reponse