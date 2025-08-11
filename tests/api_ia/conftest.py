# Fichier : tests/api_ia/conftest.py (La version qui fonctionne)

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from api.ia_api.main import app
import database.core.auth as core_auth

@pytest.fixture(autouse=True)
def prevent_network_calls(monkeypatch):
    """
    Fixture auto-exécutée qui empêche TOUT appel réseau sortant
    en simulant la méthode `post` de la librairie `requests`.
    C'est la méthode la plus robuste pour isoler les tests.
    """
    # On simule une réponse de succès générique
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data
            
        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.exceptions.HTTPError(f"Error {self.status_code}")

    def mock_post(*args, **kwargs):
        # Pour le test de traduction, on retourne une réponse formatée
        if "inputs" in kwargs.get("json", {}):
            return MockResponse([{"translation_text": "traduction simulée réussie"}], 200)
        # Pour d'autres appels post, on peut retourner autre chose
        return MockResponse(None, 200)

    # On remplace `requests.post` par notre fonction simulée
    monkeypatch.setattr(requests, "post", mock_post)


@pytest.fixture
def client():
    """Crée un client de test FastAPI."""
    def fake_verify_jwt_token():
        return {"username": "testuser", "sub": "testuser"}
    app.dependency_overrides[core_auth.verify_jwt_token] = fake_verify_jwt_token
    
    with TestClient(app) as test_client:
        yield test_client
        
    app.dependency_overrides.clear()