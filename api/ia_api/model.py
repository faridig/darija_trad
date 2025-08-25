import requests
import os
from dotenv import load_dotenv

# Charge les variables d'environnement depuis un fichier .env à la racine du projet.
# Cela permet de séparer la configuration (clés d'API, URLs) du code.
load_dotenv()

class LLMTranslator:
    """
    Classe "connecteur" responsable de la communication avec un service d'inférence
    de traduction externe hébergé sur Hugging Face.

    Elle encapsule toute la logique d'appel réseau : construction de la requête,
    gestion de l'authentification et traitement des réponses et des erreurs.
    """
    def __init__(self):
        """
        Initialise le traducteur.

        Cette méthode charge les informations de connexion nécessaires depuis les
        variables d'environnement et prépare les en-têtes HTTP qui seront
        réutilisés pour chaque appel à l'API.

        Raises:
            ValueError: Si les variables d'environnement requises
                        (HF_INFERENCE_ENDPOINT_URL, HF_TOKEN_AI) ne sont pas définies,
                        ce qui empêche le service de fonctionner correctement.
        """
        # Récupère l'URL du service d'inférence depuis les variables d'environnement.
        self.api_url = os.getenv("HF_INFERENCE_ENDPOINT_URL")
        # Récupère le token secret pour s'authentifier auprès du service.
        self.api_token = os.getenv("HF_TOKEN_AI")

        # Vérification de la configuration : C'est une garde de sécurité pour s'assurer
        # que l'application ne démarre pas avec une configuration invalide.
        if not self.api_url or not self.api_token:
            raise ValueError("Configuration manquante : les variables d'environnement HF_INFERENCE_ENDPOINT_URL et HF_TOKEN_AI sont requises.")
            
        print("INFO: Le traducteur est configuré pour utiliser l'endpoint Hugging Face.")
        
        # Prépare le dictionnaire d'en-têtes HTTP. Il sera utilisé pour chaque requête.
        # C'est plus efficace que de le recréer à chaque fois.
        self.headers = {
            # L'en-tête 'Authorization' est le standard pour l'envoi de tokens.
            "Authorization": f"Bearer {self.api_token}",
            # On indique au serveur que le corps de notre requête est au format JSON.
            "Content-Type": "application/json",
            # On indique au serveur que nous attendons une réponse au format JSON.
            "Accept": "application/json"
        }

    def _query_api(self, payload: dict) -> dict:
        """
        Méthode privée et générique pour envoyer une requête POST à l'API.

        Args:
            payload (dict): Le corps de la requête au format dictionnaire Python.

        Returns:
            dict: La réponse de l'API au format dictionnaire Python.

        Raises:
            requests.exceptions.RequestException: Si un problème réseau survient
                                                  ou si l'API retourne un code d'erreur HTTP (4xx, 5xx).
        """
        # Envoi de la requête POST avec la librairie 'requests'.
        # Le payload est automatiquement converti en JSON.
        # Un timeout de 30s est défini pour éviter que la requête ne reste bloquée indéfiniment.
        response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
        
        # C'est une bonne pratique : cette ligne va automatiquement lever une exception
        # si le code de statut de la réponse est une erreur (ex: 401 Unauthorized, 503 Service Unavailable).
        response.raise_for_status()
        
        # Si tout s'est bien passé, on retourne le corps de la réponse parsé en JSON.
        return response.json()

    def traiter(self, texte: str, src_lang: str, tgt_lang: str) -> str:
        """
        Traduit un texte en appelant l'API d'inférence distante de Hugging Face.
        C'est la méthode publique principale de cette classe.

        Args:
            texte (str): Le texte source à traduire.
            src_lang (str): Le code de la langue source (format NLLB, ex: "fra_Latn").
            tgt_lang (str): Le code de la langue cible (format NLLB, ex: "ary_Arab").

        Returns:
            str: Le texte traduit.

        Raises:
            ConnectionError: Si la communication avec l'API externe échoue (erreur réseau,
                             timeout, erreur serveur) ou si le format de la réponse est inattendu.
        """
        
        # Construction du payload (corps de la requête) selon le format attendu par l'API
        # d'inférence de Hugging Face pour les modèles de traduction.
        payload = {
            # Le texte à traduire est placé dans la clé "inputs".
            "inputs": texte,
            # Les paramètres spécifiques au modèle (comme les langues) sont dans un sous-objet "parameters".
            "parameters": {
                "src_lang": src_lang,
                "tgt_lang": tgt_lang
            },
            # Les options contrôlent le comportement de l'endpoint. "wait_for_model" est crucial
            # pour les services qui se mettent en veille ("scale-to-zero"), pour leur laisser le temps de démarrer.
            "options": {
                "wait_for_model": True
            }
        }
        
        # Le bloc try...except est utilisé pour gérer les erreurs qui peuvent survenir
        # lors de l'appel réseau ou du traitement de la réponse.
        try:
            # On appelle notre méthode privée pour exécuter la requête.
            result = self._query_api(payload)
            
            # Traitement de la réponse en cas de succès.
            # On vérifie que le format est bien celui attendu (une liste avec au moins un élément).
            if isinstance(result, list) and result:
                # On extrait la traduction du premier élément de la liste.
                # L'utilisation de .get() est plus sûre que l'accès direct par clé,
                # car elle retourne None si la clé n'existe pas, évitant un crash.
                translation = result[0].get("translation_text")
                if translation is not None:
                    return translation
            
            # Si le format de la réponse n'est pas celui attendu, c'est une erreur.
            # On log le problème pour le débogage et on lève une exception claire.
            print(f"AVERTISSEMENT: Format de réponse inattendu de l'API HF: {result}")
            raise ConnectionError("Format de réponse inattendu du service de traduction.")
            
        except requests.exceptions.RequestException as e:
            # Ce bloc intercepte toutes les erreurs liées à la communication réseau
            # (timeout, erreur DNS, erreur HTTP 4xx/5xx levée par raise_for_status).
            print(f"ERREUR: Échec de l'appel à l'API Hugging Face : {e}")
            # On "enveloppe" l'erreur technique d'origine dans une exception plus métier.
            # Cela permet aux couches supérieures de l'application de gérer une seule
            # sorte d'erreur (ConnectionError) sans se soucier des détails de l'implémentation.
            raise ConnectionError("Le service de traduction externe est actuellement indisponible.") from e