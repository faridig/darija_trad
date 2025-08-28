```python
# tests/api_ia/test_model.py
"""
Ce module contient les tests unitaires pour la classe LLMTranslator.

LLMTranslator est le composant qui gère les appels à l'API Hugging Face 
pour la traduction de textes entre différentes langues.

Ces tests permettent de vérifier:
- L'initialisation correcte de la classe avec les variables d'environnement
- Le comportement lors d'une requête réussie
- La gestion des erreurs (variables manquantes, erreurs HTTP, format de réponse incorrect)
"""

import pytest
from unittest.mock import patch, Mock
import requests

from api.ia_api.model import LLMTranslator

# Définition des constantes pour les tests
DUMMY_URL = "https://fake.endpoint.url"
DUMMY_TOKEN_AI = "hf_faketoken_for_ai"

@pytest.fixture
def mock_env(monkeypatch):
    """
    Fixture pour simuler les variables d'environnement nécessaires à l'API.
    
    Cette fixture configure temporairement les variables d'environnement
    requises par le LLMTranslator avec des valeurs factices pour les tests.
    
    Args:
        monkeypatch: Objet pytest permettant de modifier temporairement 
                    l'environnement d'exécution
    """
    monkeypatch.setenv("HF_INFERENCE_ENDPOINT_URL", DUMMY_URL)
    monkeypatch.setenv("HF_TOKEN_AI", DUMMY_TOKEN_AI)

def test_translator_initialization_success(mock_env):
    """
    Vérifie que le traducteur s'initialise correctement avec les variables d'environnement.
    
    Ce test s'assure que la classe LLMTranslator récupère correctement les 
    valeurs des variables d'environnement configurées par la fixture mock_env.
    """
    translator = LLMTranslator()
    # Vérifie que les attributs de l'instance correspondent aux valeurs des variables d'environnement
    assert translator.api_url == DUMMY_URL
    assert translator.api_token == DUMMY_TOKEN_AI

def test_translator_initialization_failure(monkeypatch):
    """
    Vérifie que le traducteur lève une erreur si les variables d'environnement sont manquantes.
    
    Ce test s'assure que la classe LLMTranslator détecte correctement l'absence
    des variables d'environnement requises et lève une exception appropriée.
    """
    # Supprime délibérément les variables d'environnement nécessaires
    monkeypatch.delenv("HF_INFERENCE_ENDPOINT_URL", raising=False)
    monkeypatch.delenv("HF_TOKEN_AI", raising=False)
    
    # Vérifie qu'une exception ValueError est levée avec un message contenant "sont requises"
    with pytest.raises(ValueError, match="sont requises"):
        LLMTranslator()

@patch('api.ia_api.model.requests.post')
def test_traiter_success(mock_post, mock_env):
    """
    Vérifie le cas nominal où l'API Hugging Face répond correctement.
    
    Ce test simule une réponse réussie de l'API Hugging Face et vérifie que:
    1. La méthode traiter renvoie la traduction attendue
    2. La requête à l'API est correctement formée avec tous les paramètres requis
    
    Args:
        mock_post: Mock de la fonction requests.post
        mock_env: Fixture pour configurer les variables d'environnement
    """
    # On simule une réponse réussie de l'API externe
    mock_response = Mock()
    mock_response.json.return_value = [{"translation_text": "Salam Alikoum"}]  # Format de réponse attendu
    mock_response.raise_for_status.return_value = None  # Simule une réponse HTTP 200 OK
    mock_post.return_value = mock_response

    # Création et utilisation du traducteur
    translator = LLMTranslator()
    result = translator.traiter("Bonjour", "fra_Latn", "ary_Arab")

    # Vérification du résultat de la traduction
    assert result == "Salam Alikoum"
    
    # On vérifie que la méthode `post` a été appelée avec la bonne structure de payload.
    # Cette vérification est essentielle pour s'assurer que les paramètres sont correctement transmis à l'API
    mock_post.assert_called_once_with(
        DUMMY_URL,
        headers={
            "Authorization": f"Bearer {DUMMY_TOKEN_AI}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        json={
            "inputs": "Bonjour",
            "parameters": {
                "src_lang": "fra_Latn",
                "tgt_lang": "ary_Arab"
            },
            "options": {"wait_for_model": True}
        },
        timeout=30  # Vérifie que le timeout est correctement configuré
    )

@patch('api.ia_api.model.requests.post')
def test_traiter_http_error(mock_post, mock_env):
    """
    Vérifie que le traducteur gère correctement une erreur réseau ou HTTP.
    
    Ce test simule une erreur de connexion ou une erreur HTTP lors de l'appel
    à l'API externe et vérifie que la classe LLMTranslator transforme cette
    erreur en une exception ConnectionError avec un message approprié.
    
    Args:
        mock_post: Mock de la fonction requests.post
        mock_env: Fixture pour configurer les variables d'environnement
    """
    # Simule une erreur réseau ou HTTP
    mock_post.side_effect = requests.exceptions.RequestException("Server Error")
    
    translator = LLMTranslator()
    # Vérifie que l'exception est bien transformée en ConnectionError avec le message attendu
    with pytest.raises(ConnectionError, match="Le service de traduction externe est actuellement indisponible."):
        translator.traiter("test", "fra_Latn", "ary_Arab")

@patch('api.ia_api.model.requests.post')
def test_traiter_unexpected_response_format(mock_post, mock_env):
    """
    Vérifie que le traducteur gère un format de réponse JSON inattendu.
    
    Ce test simule une réponse valide de l'API mais avec un format JSON inattendu
    (clé manquante ou incorrecte). Il vérifie que la classe LLMTranslator
    détecte ce problème et lève une exception appropriée.
    
    Args:
        mock_post: Mock de la fonction requests.post
        mock_env: Fixture pour configurer les variables d'environnement
    """
    # Simule une réponse avec un format JSON incorrect
    mock_response = Mock()
    mock_response.json.return_value = [{"wrong_key": "some_value"}]  # Format incorrect, pas de "translation_text"
    mock_response.raise_for_status.return_value = None  # La réponse HTTP est OK, mais le contenu est invalide
    mock_post.return_value = mock_response

    translator = LLMTranslator()
    # Vérifie que l'exception est levée avec le message attendu sur le format de réponse
    with pytest.raises(ConnectionError, match="Format de réponse inattendu"):
        translator.traiter("test", "fra_Latn", "ary_Arab")
```