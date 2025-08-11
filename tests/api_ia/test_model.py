# Fichier : tests/api_ia/test_model.py
import pytest
from unittest.mock import patch, Mock
import requests

from api.ia_api.model import LLMTranslator

# On définit des variables "factices" pour les tests
DUMMY_URL = "https://fake.endpoint.url"
DUMMY_TOKEN = "hf_faketoken"

@pytest.fixture
def mock_env(monkeypatch):
    """Fixture pour simuler les variables d'environnement nécessaires."""
    monkeypatch.setenv("HF_INFERENCE_ENDPOINT_URL", DUMMY_URL)
    monkeypatch.setenv("HF_TOKEN_AI", DUMMY_TOKEN)

def test_translator_initialization_success(mock_env):
    """Vérifie que le traducteur s'initialise correctement avec les variables d'env."""
    try:
        translator = LLMTranslator()
        assert translator.api_url == DUMMY_URL
        assert translator.api_token == DUMMY_TOKEN
    except ValueError:
        pytest.fail("L'initialisation de LLMTranslator a échoué alors que les variables d'env sont présentes.")

def test_translator_initialization_failure():
    """Vérifie que le traducteur lève une erreur si les variables d'env sont manquantes."""
    with pytest.raises(ValueError, match="sont requises"):
        LLMTranslator()

@patch('requests.post')
def test_traiter_success(mock_post, mock_env):
    """
    Vérifie le cas nominal : l'API HF répond correctement.
    Cela couvre la majorité du code de la méthode `traiter`.
    """
    # On configure le mock pour simuler une réponse réussie de l'API
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"translation_text": "Salam Alikoum"}]
    # On fait en sorte que `requests.post` retourne notre fausse réponse
    mock_post.return_value = mock_response

    translator = LLMTranslator()
    result = translator.traiter("Bonjour", "fra_Latn", "ary_Arab")

    assert result == "Salam Alikoum"
    # On vérifie que `requests.post` a été appelé avec la bonne URL, les bons headers et le bon payload
    mock_post.assert_called_once_with(
        DUMMY_URL,
        headers={"Authorization": f"Bearer {DUMMY_TOKEN}"},
        json={
            "inputs": "Bonjour",
            "parameters": {"src_lang": "fra_Latn", "tgt_lang": "ary_Arab"}
        },
        timeout=30
    )

@patch('requests.post')
def test_traiter_http_error(mock_post, mock_env):
    """
    Vérifie que la gestion d'erreur HTTP fonctionne.
    Cela couvre le `response.raise_for_status()` et le `except requests.exceptions.RequestException`.
    """
    # On simule une réponse d'erreur 500 (serveur en panne)
    mock_post.side_effect = requests.exceptions.RequestException("Server Error")
    
    translator = LLMTranslator()
    
    # On s'attend à ce que notre code lève une ConnectionError
    with pytest.raises(ConnectionError, match="Le service de traduction est actuellement indisponible."):
        translator.traiter("test", "fra_Latn", "ary_Arab")

@patch('requests.post')
def test_traiter_unexpected_response_format(mock_post, mock_env):
    """
    Vérifie la gestion d'un format de réponse JSON inattendu.
    Cela couvre le `if translation is not None` et l'erreur levée ensuite.
    """
    # On simule une réponse avec un format incorrect (pas de 'translation_text')
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"wrong_key": "some_value"}]
    mock_post.return_value = mock_response
    
    translator = LLMTranslator()

    with pytest.raises(ConnectionError, match="Format de réponse inattendu"):
        translator.traiter("test", "fra_Latn", "ary_Arab")