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
    1. Désactiver le rate limiting en remplaçant le limiteur par un mock complet.
    2. Empêcher les appels réseau sortants en simulant `requests.post`.
    """
    # --- 1. Désactivation robuste du Rate Limiting ---
    class MockLimiter:
        """
        Un faux limiteur qui ne fait rien mais qui est suffisamment complet
        pour ne pas planter le gestionnaire d'erreurs de slowapi.
        """
        def __init__(self, key_func):
            # L'attribut 'enabled' est vérifié par le middleware.
            self.enabled = False
        
        # Le décorateur @limiter.limit est remplacé par une fonction qui ne fait rien.
        def limit(self, limit_string):
            def decorator(func):
                return func
            return decorator

        # ================================================================
        # ===> CORRECTION APPLIQUÉE ICI <=================================
        # ================================================================
        # On ajoute la méthode que le gestionnaire d'erreurs de slowapi
        # s'attend à trouver. Elle prend la réponse et la retourne sans la modifier.
        def _inject_headers(self, response, current_limit):
            return response
        # ================================================================

    # On remplace l'instance du limiteur DANS LE MODULE OÙ IL EST DÉFINI (`limiter.py`).
    monkeypatch.setattr('api.ia_api.limiter.limiter', MockLimiter(key_func=None))
    
    # On met aussi à jour l'état de l'application avec le même mock.
    app.state.limiter = MockLimiter(key_func=None)

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
    
    with TestClient(app) as test_client:
        yield test_client
        
    app.dependency_overrides.clear()