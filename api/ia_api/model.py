# Fichier : api/ia_api/model.py (Version Corrigée et Finale)

import requests
import os
from dotenv import load_dotenv

load_dotenv()

class LLMTranslator:
    def __init__(self):
        """
        Initialise le traducteur pour communiquer avec l'API d'inférence de Hugging Face.
        """
        self.api_url = os.getenv("HF_INFERENCE_ENDPOINT_URL")
        self.api_token = os.getenv("HF_TOKEN_AI")

        if not self.api_url or not self.api_token:
            raise ValueError("Configuration manquante : les variables d'environnement HF_INFERENCE_ENDPOINT_URL et HF_TOKEN_AI sont requises.")
            
        print("INFO: Le traducteur est configuré pour utiliser l'endpoint Hugging Face.")
        
        # On utilise les en-têtes standards vus dans la documentation et les exemples.
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def _query_api(self, payload: dict) -> dict:
        """
        Méthode privée qui envoie la requête POST à l'API de Hugging Face.
        """
        response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
        # Lève une exception pour les erreurs HTTP (4xx, 5xx), ce qui nous donnera des logs clairs.
        response.raise_for_status()
        return response.json()

    def traiter(self, texte: str, src_lang: str, tgt_lang: str) -> str:
        """
        Traduit un texte en appelant l'API d'inférence distante de Hugging Face.
        """
        
        # ================================================================
        # ===> CORRECTION APPLIQUÉE ICI <=================================
        # ================================================================
        # La documentation de l'API confirme que les paramètres de langue
        # DOIVENT se trouver à l'intérieur d'un dictionnaire "parameters".
        payload = {
            "inputs": texte,
            "parameters": {
                "src_lang": src_lang,
                "tgt_lang": tgt_lang
                # D'autres paramètres comme "clean_up_tokenization_spaces": True pourraient être ajoutés ici si nécessaire.
            },
            # L'option "wait_for_model" est utile pour les endpoints en "scale-to-zero".
            "options": {
                "wait_for_model": True
            }
        }
        # ================================================================
        
        try:
            result = self._query_api(payload)
            
            # La réponse attendue est une liste contenant un dictionnaire.
            if isinstance(result, list) and result:
                translation = result[0].get("translation_text")
                if translation is not None:
                    return translation
            
            # Si le format de la réponse est incorrect, on log et on lève une erreur.
            print(f"AVERTISSEMENT: Format de réponse inattendu de l'API HF: {result}")
            raise ConnectionError("Format de réponse inattendu du service de traduction.")
            
        except requests.exceptions.RequestException as e:
            # Gestion des erreurs réseau ou des erreurs HTTP (comme 400, 401, 503...).
            print(f"ERREUR: Échec de l'appel à l'API Hugging Face : {e}")
            raise ConnectionError("Le service de traduction externe est actuellement indisponible.") from e