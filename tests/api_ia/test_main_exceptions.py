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


# Ce test va couvrir le 'if isinstance(exc, ValueError):' dans all_exception_handler
def test_all_exception_handler_catches_value_error(client):
    """
    Vérifie que le handler global intercepte un ValueError qui ne viendrait pas de Pydantic.
    On simule cela en patchant la méthode `traiter` du modèle.
    """
    # On remplace la méthode `traiter` pour qu'elle lève un ValueError
    with patch.object(LLMTranslator, 'traiter', side_effect=ValueError("Erreur de valeur simulée")):
        payload = {"texte": "un texte valide qui passe la validation Pydantic"}
        
        response = client.post(
            "/generer",
            json=payload,
            headers={"Authorization": "Bearer fake-jwt-token"}
        )
        
        # On vérifie que le handler a renvoyé un 422 avec le message de l'erreur
        assert response.status_code == 422
        assert response.json() == {"detail": "Erreur de valeur simulée"}


# Ce test va couvrir le 'raise exc' dans all_exception_handler
def test_all_exception_handler_reraises_other_exceptions(client):
    """
    Vérifie que le handler global laisse passer (re-lève) les exceptions
    qu'il n'est pas censé gérer (tout ce qui n'est pas un ValueError).
    """
    # On simule une erreur d'exécution générique
    error_message = "Erreur d'exécution inattendue"
    with patch.object(LLMTranslator, 'traiter', side_effect=RuntimeError(error_message)):
        
        # Le TestClient de FastAPI va intercepter cette exception et la relancer.
        # On utilise `pytest.raises` pour confirmer que c'est bien le cas.
        with pytest.raises(RuntimeError, match=error_message):
            client.post(
                "/generer",
                json={"texte": "un texte valide"},
                headers={"Authorization": "Bearer fake-jwt-token"}
            )