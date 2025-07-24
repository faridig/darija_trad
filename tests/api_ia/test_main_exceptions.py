import pytest
from unittest.mock import patch
from api.ia_api.model import LLMTranslator

# Ce test va couvrir le handler pour RequestValidationError (ligne 77)
def test_validation_exception_handler_is_triggered(client):
    """
    Vérifie que le handler pour RequestValidationError est bien appelé
    en envoyant un payload qui viole les règles du schéma.
    """
    # Le schéma TexteInput requiert entre 1 et 200 mots. Envoyons plus de 200.
    long_text = "mot " * 201 
    
    response = client.post(
        "/generer",
        json={"texte": long_text},
        headers={"Authorization": "Bearer fake-jwt-token"}
    )
    
    # On vérifie que le statut est bien 422
    assert response.status_code == 422
    
    # On vérifie que le corps de la réponse contient le message d'erreur de Pydantic,
    # prouvant que notre handler personnalisé a bien formaté la réponse.
    assert "Le texte doit contenir entre 1 et 200 mots" in response.json()["detail"][0]


def test_all_exception_handler_catches_value_error(client):
    """
    Vérifie que le handler global intercepte un ValueError qui ne viendrait pas de Pydantic.
    """
    with patch.object(LLMTranslator, 'traiter', side_effect=ValueError("Erreur de valeur simulée")):
        payload = {"texte": "un texte valide"}
        response = client.post(
            "/generer", json=payload, headers={"Authorization": "Bearer fake-jwt-token"}
        )
        # L'exception est interceptée et notre handler la transforme en 422
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