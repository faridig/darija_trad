# Fichier : tests/api_ia/conftest.py (Version Finale Corrigée)
"""
Configuration et fixtures pour les tests de l'API IA.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import requests
import os

from api.ia_api.main import app
import database.core.auth as core_auth

# ==============================================================================
# === CONFIGURATION GLOBALE AVANT LES TESTS ====================================
# ==============================================================================

# Définir des variables d'environnement de test.
os.environ["ADMIN_USERNAME"] = "test_admin"
os.environ["ADMIN_PASSWORD"] = "test_password"

# ==============================================================================
# === FIXTURES PYTEST ==========================================================
# ==============================================================================

@pytest.fixture(autouse=True)
def disable_rate_limiter_and_network(monkeypatch):
    """
    Fixture auto-exécutée qui s'applique à TOUS les tests pour :
    1. Désactiver complètement la logique de rate limiting.
    2. Empêcher les appels réseau sortants en simulant `requests.post`.
    """
    # --- 1. Désactivation complète du Rate Limiting ---
    # On patche la méthode `hit` de l'instance de limiter partagée.
    # C'est cette méthode qui renvoie True (limite non atteinte) ou False (limite atteinte).
    # En la forçant à toujours retourner True, on désactive de fait toute la logique de limitation.
    monkeypatch.setattr(
        "api.ia_api.limiter.limiter.hit",
        lambda *args, **kwargs: True
    )

    # --- 2. Simulation des appels réseau (inchangé) ---
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
        if "inputs" in kwargs.get("json", {}):
            return MockResponse([{"translation_text": "traduction simulée réussie"}], 200)
        return MockResponse(None, 200)

    monkeypatch.setattr(requests, "post", mock_post)


@pytest.fixture
def client():
    """
    Fixture qui crée un client de test FastAPI avec l'authentification simulée.
    """
    def fake_verify_jwt_token():
        return {"username": "testuser", "sub": "testuser"}
    
    app.dependency_overrides[core_auth.verify_jwt_token] = fake_verify_jwt_token
    
    # On s'assure que le rate limiter est désactivé sur l'état de l'app pour le gestionnaire d'erreurs
    # au cas où une exception RateLimitExceeded serait levée ailleurs.
    app.state.limiter.enabled = False

    with TestClient(app) as test_client:
        yield test_client
        
    app.dependency_overrides.clear()
    # On réactive le limiter au cas où il serait utilisé dans un autre contexte
    app.state.limiter.enabled = True