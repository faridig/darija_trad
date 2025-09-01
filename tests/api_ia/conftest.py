# Fichier : tests/api_ia/conftest.py
"""
Configuration et fixtures pour les tests de l'API IA.
Ce module contient les fixtures partagées pour les tests de l'API FastAPI.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import requests

from api.ia_api.main import app
import database.core.auth as core_auth


@pytest.fixture(autouse=True)
def prevent_network_calls(monkeypatch):
    """
    Fixture auto-exécutée qui empêche tous les appels réseau sortants
    en simulant la méthode `requests.post`. 
    
    Cette fixture est automatiquement utilisée par tous les tests du module
    pour isoler les tests de l'API sans dépendre de services externes.
    
    Args:
        monkeypatch: Fixture pytest pour modifier le comportement des objets
        
    Returns:
        None: La fixture modifie le comportement de requests.post globalement
    """
    # Classe simulant une réponse HTTP
    class MockResponse:
        """
        Classe de simulation d'une réponse HTTP pour les tests.
        Imite le comportement d'un objet Response de la bibliothèque requests.
        """
        
        def __init__(self, json_data, status_code):
            """
            Initialise la réponse simulée.
            
            Args:
                json_data: Données JSON à retourner par la méthode json()
                status_code: Code HTTP de statut de la réponse
            """
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            """
            Simule la méthode json() d'une réponse requests.
            
            Returns:
                dict: Les données JSON simulées
            """
            return self.json_data
            
        def raise_for_status(self):
            """
            Simule la levée d'une exception pour les codes d'erreur HTTP.
            
            Raises:
                requests.exceptions.HTTPError: Si le status_code >= 400
            """
            if self.status_code >= 400:
                raise requests.exceptions.HTTPError(f"Error {self.status_code}")

    def mock_post(*args, **kwargs):
        """
        Fonction simulée pour remplacer `requests.post`.
        
        Cette fonction analyse le contenu de la requête et retourne une réponse
        appropriée selon le scénario simulé.
        
        Args:
            *args: Arguments positionnels de l'appel
            **kwargs: Arguments nommés de l'appel
            
        Returns:
            MockResponse: Une réponse HTTP simulée adaptée au contexte
        """
        # Si la requête contient un champ "inputs", simuler une traduction réussie
        if "inputs" in kwargs.get("json", {}):
            return MockResponse([{"translation_text": "traduction simulée réussie"}], 200)
        # Sinon, renvoyer une réponse générique de succès
        return MockResponse(None, 200)

    # Remplacer `requests.post` par notre fonction simulée
    monkeypatch.setattr(requests, "post", mock_post)


@pytest.fixture
def client():
    """
    Fixture qui crée un client de test FastAPI.
    
    Cette fixture initialise un client de test pour l'application FastAPI
    et remplace la dépendance de vérification JWT par une version simulée
    pour éviter de dépendre d'un système d'authentification réel pendant les tests.
    
    Yields:
        TestClient: Client de test FastAPI configuré pour les tests
        
    Notes:
        La fixture nettoie automatiquement les overrides après utilisation
    """
    def fake_verify_jwt_token():
        """
        Simule la vérification d'un token JWT.
        
        Returns:
            dict: Un dictionnaire contenant des informations d'utilisateur de test
        """
        return {"username": "testuser", "sub": "testuser"}
    
    # Remplacer la dépendance FastAPI pour les tests
    app.dependency_overrides[core_auth.verify_jwt_token] = fake_verify_jwt_token
    
    # Créer un client de test et le fournir aux tests
    with TestClient(app) as test_client:
        yield test_client
        
    # Nettoyer les overrides après les tests pour éviter les effets de bord
    app.dependency_overrides.clear()