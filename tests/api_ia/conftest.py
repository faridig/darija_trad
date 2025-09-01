# Fichier : tests/api_ia/conftest.py
"""
Configuration et fixtures pour les tests de l'API IA.
Ce module contient les fixtures partagées pour les tests de l'API FastAPI.
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

# Désactiver le rate limiting pour tous les tests afin d'éviter que les
# tests rapides ne soient bloqués inutilement.
app.state.limiter = None

# Définir des variables d'environnement de test pour s'assurer que les
# tests ne dépendent pas d'un fichier .env local.
os.environ["ADMIN_USERNAME"] = "test_admin"
os.environ["ADMIN_PASSWORD"] = "test_password"

# REMARQUE : Il n'est pas nécessaire de réappliquer les middlewares ici.
# L'objet `app` importé depuis `main.py` est déjà entièrement configuré
# avec tous ses middlewares. Ajouter `app.middleware(...)` ici est redondant
# et peut causer des problèmes d'importation.

# ==============================================================================
# === FIXTURES PYTEST ==========================================================
# ==============================================================================

@pytest.fixture(autouse=True)
def prevent_network_calls(monkeypatch):
    """
    Fixture auto-exécutée qui empêche tous les appels réseau sortants
    en simulant la méthode `requests.post`. 
    
    Cette fixture est automatiquement utilisée par tous les tests du module
    pour isoler les tests de l'API sans dépendre de services externes.
    
    Args:
        monkeypatch: Fixture pytest pour modifier le comportement des objets.
    """
    class MockResponse:
        """Classe de simulation d'une réponse HTTP pour les tests."""
        
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data
            
        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.exceptions.HTTPError(f"Error {self.status_code}")

    def mock_post(*args, **kwargs):
        """Fonction simulée pour remplacer `requests.post`."""
        if "inputs" in kwargs.get("json", {}):
            return MockResponse([{"translation_text": "traduction simulée réussie"}], 200)
        return MockResponse(None, 200)

    # Remplacer `requests.post` par notre fonction simulée.
    monkeypatch.setattr(requests, "post", mock_post)


@pytest.fixture
def client():
    """
    Fixture qui crée un client de test FastAPI.
    
    Cette fixture initialise un client de test pour l'application FastAPI
    et remplace la dépendance de vérification JWT par une version simulée
    pour éviter de dépendre d'un système d'authentification réel.
    
    Yields:
        TestClient: Un client de test FastAPI prêt à l'emploi.
    """
    def fake_verify_jwt_token():
        """Simule une vérification de token JWT toujours réussie."""
        return {"username": "testuser", "sub": "testuser"}
    
    # Remplacer la dépendance de sécurité le temps du test.
    app.dependency_overrides[core_auth.verify_jwt_token] = fake_verify_jwt_token
    
    with TestClient(app) as test_client:
        yield test_client
        
    # Nettoyer les "overrides" après la fin du test pour ne pas affecter d'autres tests.
    app.dependency_overrides.clear()