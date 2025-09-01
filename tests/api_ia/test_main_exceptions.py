import pytest
from unittest.mock import patch
from fastapi import Request
from fastapi.responses import JSONResponse
from api.ia_api.model import LLMTranslator
from database.core.db import get_db
from api.ia_api.main import all_exception_handler


def test_validation_exception_handler_is_triggered(client):
    """
    Test d'intégration qui vérifie que le handler automatique de FastAPI pour
    RequestValidationError est correctement déclenché.
    
    Scénario : Envoi d'un payload qui viole les contraintes de validation Pydantic.
    Résultat attendu : Code 422 (Unprocessable Entity) avec détails de l'erreur.
    
    Ce test couvre le cas où Pydantic intercepte une erreur de validation avant
    même que la requête n'atteigne le handler personnalisé.
    """
    # Crée un texte qui dépasse la limite de 200 caractères définie dans le modèle Pydantic
    long_text = "a" * 201 
    
    # Envoie une requête POST avec le texte trop long
    response = client.post(
        "/generer",
        json={"texte": long_text},
        headers={"Authorization": "Bearer fake-jwt-token"}
    )
    
    # Vérifications :
    assert response.status_code == 422  # Code d'erreur de validation
    assert "String should have at most 200 characters" in response.json()["detail"][0]  # Message d'erreur spécifique


def test_all_exception_handler_catches_value_error(client):
    """
    Test d'intégration qui vérifie le comportement du handler personnalisé
    lorsqu'un ValueError est levé pendant le traitement.
    
    Scénario : Simulation d'une ValueError dans la méthode 'traiter' du traducteur.
    Résultat attendu : Le handler personnalisé intercepte l'erreur et retourne un code 500.
    
    Ce test couvre la branche du handler qui capture spécifiquement les ValueError.
    """
    # Mock de la méthode 'traiter' pour simuler une ValueError
    with patch.object(LLMTranslator, 'traiter', side_effect=ValueError("Erreur de valeur simulée")):
        payload = {"texte": "un texte valide"}
        response = client.post(
            "/generer", json=payload, headers={"Authorization": "Bearer fake-jwt-token"}
        )

        # Vérification : Le handler doit retourner 500 pour les ValueError
        assert response.status_code == 500


def test_all_exception_handler_reraises_other_exceptions(client):
    """
    Test d'intégration qui vérifie que le handler personnalisé laisse passer
    les exceptions non gérées (autres que ValueError).
    
    Scénario : Simulation d'une RuntimeError dans la méthode 'traiter'.
    Résultat attendu : FastAPI intercepte l'exception et retourne un code 500 générique.
    
    Ce test couvre la branche du handler qui relance les exceptions non gérées.
    """
    error_message = "Erreur d'exécution inattendue"
    # Mock de la méthode 'traiter' pour simuler une RuntimeError
    with patch.object(LLMTranslator, 'traiter', side_effect=RuntimeError(error_message)):
        response = client.post(
            "/generer", json={"texte": "un texte valide"}, headers={"Authorization": "Bearer fake-jwt-token"}
        )
        # Vérification : FastAPI doit retourner 500 pour les exceptions non gérées
        assert response.status_code == 500
        # Note : En production, FastAPI masque les détails des erreurs 500 pour des raisons de sécurité


@pytest.mark.asyncio
async def test_all_exception_handler_directly():
    """
    Test unitaire direct du handler d'exceptions personnalisé.
    
    Ce test appelle directement le handler sans passer par l'application FastAPI,
    permettant de tester les deux branches de manière isolée :
    1. Capture des ValueError et retour d'une réponse JSON 422
    2. Relance des autres exceptions pour traitement par FastAPI
    
    Méthode : Test asynchrone avec objets Request simulés.
    """
    # Test de la branche ValueError
    request = Request(scope={"type": "http"})  # Crée une requête HTTP simulée
    exc = ValueError("Erreur de valeur")  # Exception de type ValueError
    
    # Appel direct du handler
    response = await all_exception_handler(request, exc)
    
    # Vérifications pour ValueError :
    assert isinstance(response, JSONResponse)  # Doit retourner une réponse JSON
    assert response.status_code == 422  # Code spécifique pour les erreurs de validation
    assert "Erreur de valeur" in response.body.decode()  # Message d'erreur dans le corps
    
    # Test de la branche autres exceptions
    request = Request(scope={"type": "http"})  # Nouvelle requête simulée
    exc = RuntimeError("Erreur runtime")  # Exception de type RuntimeError
    
    # Vérification que l'exception est relancée (non capturée par le handler)
    with pytest.raises(RuntimeError, match="Erreur runtime"):
        await all_exception_handler(request, exc)