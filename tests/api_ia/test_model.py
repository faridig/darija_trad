# Fichier : tests/api_ia/test_model.py (Version Corrigée)

import pytest
from unittest.mock import patch, Mock
import requests

from api.ia_api.model import LLMTranslator

# Les variables factices ne changent pas
DUMMY_URL = "https://fake.endpoint.url"
DUMMY_TOKEN_AI = "hf_faketoken_for_ai"

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("HF_INFERENCE_ENDPOINT_URL", DUMMY_URL)
    monkeypatch.setenv("HF_TOKEN_AI", DUMMY_TOKEN_AI)

# Les tests d'initialisation ne changent pas
def test_translator_initialization_success(mock_env):
    translator = LLMTranslator()
    assert translator.api_url == DUMMY_URL
    assert translator.api_token == DUMMY_TOKEN_AI

def test_translator_initialization_failure(monkeypatch):
    monkeypatch.delenv("HF_INFERENCE_ENDPOINT_URL", raising=False)
    monkeypatch.delenv("HF_TOKEN_AI", raising=False)
    with pytest.raises(ValueError, match="sont requises"):
        LLMTranslator()

@patch('api.ia_api.model.requests.post')
def test_traiter_success(mock_post, mock_env):
    """Vérifie le cas nominal : l'API HF répond correctement."""
    mock_response = Mock()
    mock_response.json.return_value = [{"translation_text": "Salam Alikoum"}]
    mock_post.return_value = mock_response

    translator = LLMTranslator()
    result = translator.traiter("Bonjour", "fra_Latn", "ary_Arab")

    assert result == "Salam Alikoum"
    
    mock_post.assert_called_once_with(
        DUMMY_URL,
        headers={
            "Authorization": f"Bearer {DUMMY_TOKEN_AI}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        json={
            "inputs": "Bonjour",
            "src_lang": "fra_Latn",
            "tgt_lang": "ary_Arab",
            "options": {"wait_for_model": True}
        },
        timeout=30
    )
    # ================================================================

# Les tests de gestion d'erreur ne changent pas
@patch('api.ia_api.model.requests.post')
def test_traiter_http_error(mock_post, mock_env):
    mock_post.side_effect = requests.exceptions.RequestException("Server Error")
    translator = LLMTranslator()
    with pytest.raises(ConnectionError, match="Le service de traduction externe est actuellement indisponible."):
        translator.traiter("test", "fra_Latn", "ary_Arab")

@patch('api.ia_api.model.requests.post')
def test_traiter_unexpected_response_format(mock_post, mock_env):
    mock_response = Mock()
    mock_response.json.return_value = [{"wrong_key": "some_value"}]
    mock_post.return_value = mock_response
    translator = LLMTranslator()
    with pytest.raises(ConnectionError, match="Format de réponse inattendu"):
        translator.traiter("test", "fra_Latn", "ary_Arab")