import pytest
from unittest.mock import patch
from api.ia_api.model import LLMTranslator

# Ce test va couvrir le handler pour RequestValidationError (ligne 77)
def test_validation_exception_handler_is_triggered(client):
    """
    Vérifie que le handler pour RequestValidationError est bien appelé
    en envoyant un payload qui viole une règle de Pydantic.
    """
    # Ce texte viole la contrainte `max_length=200` de Pydantic
    long_text = "a" * 201 
    
    response = client.post(
        "/generer",
        json={"texte": long_text},
        headers={"Authorization": "Bearer fake-jwt-token"}
    )
    
    assert response.status_code == 422
    # On vérifie que le message d'erreur attendu est celui de Pydantic
    assert "String should have at most 200 characters" in response.json()["detail"][0]


def test_all_exception_handler_catches_value_error(client):
    """
    Vérifie que le handler global pour Exception intercepte bien un ValueError
    et le transforme en réponse 422.
    """
    with patch.object(LLMTranslator, 'traiter', side_effect=ValueError("Erreur de valeur simulée")):
        payload = {"texte": "un texte valide"}
        response = client.post(
            "/generer", json=payload, headers={"Authorization": "Bearer fake-jwt-token"}
        )
        # Maintenant, le handler @app.exception_handler(Exception) devrait 
        # intercepter le ValueError et renvoyer 422.
        assert response.status_code == 422
        assert response.json()["detail"] == "Erreur de valeur simulée"



def test_all_exception_handler_reraises_other_exceptions(client):
    """
    Vérifie que le handler global laisse FastAPI gérer les autres exceptions,
    ce qui résulte en une réponse 500.
    """
    error_message = "Erreur d'exécution inattendue"
    with patch.object(LLMTranslator, 'traiter', side_effect=RuntimeError(error_message)):
        response = client.post(
            "/generer", json={"texte": "un texte valide"}, headers={"Authorization": "Bearer fake-jwt-token"}
        )
        # FastAPI intercepte l'exception non gérée et renvoie une réponse 500
        assert response.status_code == 500
        # On ne peut pas vérifier le détail car en production FastAPI masque les erreurs 500
        # mais on peut vérifier le log si on capture les logs. Pour la couverture, ceci suffit.