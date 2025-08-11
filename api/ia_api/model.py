# api/ia_api/model.py (Version MISE À JOUR pour l'inférence via API Hugging Face)

import requests
import os
from dotenv import load_dotenv

# Charge les variables d'environnement (ex: .env) pour le développement local
load_dotenv()

class LLMTranslator:
    def __init__(self):
        """
        Initialise le traducteur pour qu'il communique avec l'API d'inférence
        de Hugging Face au lieu de charger un modèle localement.
        """
        # 1) On récupère l'URL de l'endpoint et le token depuis les variables d'environnement.
        #    Ces variables seront fournies par le secret Kubernetes en production.
        self.api_url = os.getenv("HF_INFERENCE_ENDPOINT_URL")
        self.api_token = os.getenv("HF_TOKEN_AI")

        # 2) Vérification critique : si les secrets ne sont pas configurés, l'application ne peut pas fonctionner.
        if not self.api_url or not self.api_token:
            raise ValueError("Configuration manquante : les variables d'environnement HF_INFERENCE_ENDPOINT_URL et HF_TOKEN_AI sont requises.")
            
        print(f"INFO: Le traducteur est configuré pour utiliser l'endpoint Hugging Face.")
        
        # 3) On prépare l'en-tête d'autorisation qui sera utilisé pour chaque requête.
        self.headers = {"Authorization": f"Bearer {self.api_token}"}

    def _query_api(self, payload: dict) -> dict:
        """
        Méthode privée qui envoie la requête POST à l'API de Hugging Face.
        """
        # On utilise la bibliothèque 'requests' pour faire l'appel HTTP.
        # Un timeout est essentiel pour éviter que notre API ne reste bloquée indéfiniment.
        response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
        
        # Cette ligne est très importante : elle lèvera une exception (HTTPError)
        # si l'API de Hugging Face renvoie une erreur (ex: 401, 404, 500, 503).
        response.raise_for_status()
        
        return response.json()

    def traiter(self, texte: str, src_lang: str, tgt_lang: str) -> str:
        """
        Traduit un texte en appelant l'API d'inférence distante de Hugging Face.
        """
        # 4) On construit le payload JSON dans le format attendu par l'API d'inférence.
        payload = {
            "inputs": texte,
            "parameters": {
                "src_lang": src_lang,
                "tgt_lang": tgt_lang
            }
        }
        
        try:
            result = self._query_api(payload)
            
            # 5) On traite la réponse. L'API renvoie généralement une liste de résultats.
            #    On vérifie que la réponse est bien une liste non vide.
            if isinstance(result, list) and result:
                translation = result[0].get("translation_text")
                if translation is not None:
                    return translation
            
            # Si le format de la réponse est inattendu, on lève une erreur claire.
            print(f"AVERTISSEMENT: Format de réponse inattendu de l'API HF: {result}")
            raise ConnectionError("Format de réponse inattendu du service de traduction.")
            
        except requests.exceptions.RequestException as e:
            # 6) Gestion robuste des erreurs réseau (connexion impossible, timeout, erreur HTTP...).
            print(f"ERREUR: Échec de l'appel à l'API Hugging Face : {e}")
            raise ConnectionError("Le service de traduction externe est actuellement indisponible.") from e