# Fichier : api/ia_api/model.py (Version Corrigée pour l'API Hugging Face)

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
        
        # ================================================================
        # ===> CORRECTION 1 : Mise à jour des en-têtes HTTP <=============
        # ================================================================
        # On ajoute les en-têtes 'Content-Type' et 'Accept' pour correspondre
        # à l'exemple du Playground, ce qui est une meilleure pratique.
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        # ================================================================

    def _query_api(self, payload: dict) -> dict:
        """
        Méthode privée qui envoie la requête POST à l'API de Hugging Face.
        """
        response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    def traiter(self, texte: str, src_lang: str, tgt_lang: str) -> str:
        """
        Traduit un texte en appelant l'API d'inférence distante de Hugging Face.
        """
        # ================================================================
        # ===> CORRECTION 2 : Restructuration du payload JSON <===========
        # ================================================================
        # L'API d'inférence de Hugging Face pour cette tâche attend souvent
        # les paramètres au niveau supérieur, et non imbriqués dans un dict "parameters".
        payload = {
            "inputs": texte,
            # On passe les paramètres de langue directement ici
            "src_lang": src_lang,
            "tgt_lang": tgt_lang,
            # Ajouter des options peut être utile, notamment pour les cold starts
            "options": {
                "wait_for_model": True
            }
        }
        # ================================================================
        
        try:
            result = self._query_api(payload)
            
            if isinstance(result, list) and result:
                translation = result[0].get("translation_text")
                if translation is not None:
                    return translation
            
            print(f"AVERTISSEMENT: Format de réponse inattendu de l'API HF: {result}")
            raise ConnectionError("Format de réponse inattendu du service de traduction.")
            
        except requests.exceptions.RequestException as e:
            print(f"ERREUR: Échec de l'appel à l'API Hugging Face : {e}")
            raise ConnectionError("Le service de traduction externe est actuellement indisponible.") from e