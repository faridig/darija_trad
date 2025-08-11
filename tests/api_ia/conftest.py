# Fichier : tests/api_ia/conftest.py (Version Corrigée)

import pytest
from fastapi.testclient import TestClient

from api.ia_api.main import app
import database.core.auth as core_auth

@pytest.fixture(autouse=True)
def stub_env_and_dependencies(monkeypatch):
    """
    Ce fixture simule les dépendances externes pour isoler nos tests.
    """
    # 1) Simulation de la validation de token pour toutes les routes protégées.
    def fake_verify_jwt_token():
        return {"username": "testuser", "sub": "testuser"}
    app.dependency_overrides[core_auth.verify_jwt_token] = fake_verify_jwt_token
    
    # 2) ON SUPPRIME LE MONKEYPATCH DE LLMTranslator.traiter
    #    Chaque test gérera maintenant sa propre simulation si nécessaire.

@pytest.fixture(scope="function")
def client():
    """
    Crée un client de test pour l'application.
    """
    with TestClient(app) as test_client:
        yield test_client

    # Nettoyage des simulations de dépendances
    app.dependency_overrides.clear()