# Fichier : tests/api_ia/conftest.py (Version finale et robuste)

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# On importe les modules que nous allons surcharger ou utiliser
from api.ia_api.main import app
import database.core.auth as core_auth

@pytest.fixture(autouse=True, scope="session")
def mock_llm_translator_globally():
    """
    Ce fixture s'exécute une seule fois pour toute la session de test.
    Il remplace la classe LLMTranslator partout où elle est importée
    par un mock, empêchant tout appel réseau réel.
    """
    with patch('api.ia_api.routers.generation.LLMTranslator') as MockedTranslator:
        # On configure le mock pour qu'il se comporte comme la vraie classe
        instance = MockedTranslator.return_value
        instance.traiter.return_value = "traduction simulée réussie"
        yield

@pytest.fixture
def client():
    """
    Crée un client de test FastAPI pour chaque test.
    """
    # On surcharge la dépendance de vérification JWT pour tous les tests
    def fake_verify_jwt_token():
        return {"username": "testuser", "sub": "testuser"}
    app.dependency_overrides[core_auth.verify_jwt_token] = fake_verify_jwt_token
    
    with TestClient(app) as test_client:
        yield test_client
        
    # Nettoyage des surcharges après chaque test
    app.dependency_overrides.clear()