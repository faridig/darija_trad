# Fichier : tests/api_ia/conftest.py (La version qui fonctionne)

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
    Cela permet d'isoler les tests de l'API sans dépendre de services externes.
    """
    # Classe simulant une réponse HTTP
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            """Retourne les données JSON simulées."""
            return self.json_data
            
        def raise_for_status(self):
            """Simule la levée d'une exception pour les codes d'erreur HTTP >= 400."""
            if self.status_code >= 400:
                raise requests.exceptions.HTTPError(f"Error {self.status_code}")

    def mock_post(*args, **kwargs):
        """
        Fonction simulée pour remplacer `requests.post`.
        Retourne une réponse simulée selon le contenu du payload.
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
    Elle remplace la dépendance de vérification JWT par une version simulée.
    """
    def fake_verify_jwt_token():
        """Simule la vérification d'un token JWT et retourne un utilisateur de test."""
        return {"username": "testuser", "sub": "testuser"}
    
    # Remplacer la dépendance FastAPI pour les tests
    app.dependency_overrides[core_auth.verify_jwt_token] = fake_verify_jwt_token
    
    # Créer un client de test et le fournir aux tests
    with TestClient(app) as test_client:
        yield test_client
        
    # Nettoyer les overrides après les tests
    app.dependency_overrides.clear()
