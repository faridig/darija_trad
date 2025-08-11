# Fichier : tests/api_ia/conftest.py (Correction finale)

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from api.ia_api.main import app
import database.core.auth as core_auth

@pytest.fixture(autouse=True, scope="session")
def mock_llm_translator_globally():
    """
    Patche la classe LLMTranslator à sa source pour TOUS les tests de la session.
    """
    # --- LA CORRECTION EST ICI ---
    # On patche la classe là où elle est définie ('api.ia_api.model') et non où elle est importée.
    with patch('api.ia_api.model.LLMTranslator') as MockedTranslator:
        instance = MockedTranslator.return_value
        instance.traiter.return_value = "traduction simulée réussie"
        yield

@pytest.fixture
def client():
    """Crée un client de test FastAPI."""
    def fake_verify_jwt_token():
        return {"username": "testuser", "sub": "testuser"}
    app.dependency_overrides[core_auth.verify_jwt_token] = fake_verify_jwt_token
    
    with TestClient(app) as test_client:
        yield test_client
        
    app.dependency_overrides.clear()