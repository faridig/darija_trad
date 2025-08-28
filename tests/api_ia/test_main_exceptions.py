import pytest
from unittest.mock import patch
from api.ia_api.model import LLMTranslator

def test_validation_exception_handler_is_triggered(client):
    """
    Vérifie que le handler pour RequestValidationError est bien appelé
    en envoyant un payload qui viole une contrainte de type (longueur max).
    """
    long_text = "a" * 201
    response = client.post(
        "/generer",
        json={"texte": long_text, "src_lang": "fra_Latn", "tgt_lang": "ary_Arab"},
        headers={"Authorization": "Bearer fake-jwt-token"}
    )
    assert response.status_code == 422
    assert "String should have at most 200 characters" in response.json()["detail"][0]

# ===================================================================
# === NOUVEAU TEST POUR COUVRIR LE `if isinstance(exc, ValueError)`
# ===================================================================
def test_main_handler_catches_schema_value_error(client):
    """
    Vérifie que le gestionnaire global dans main.py attrape bien une ValueError
    levée par la validation du schéma Pydantic et la transforme en 422.
    Cela couvre les lignes 135-141.
    """
    # Ce payload envoie un texte vide, ce qui lève une ValueError dans schemas.py
    payload = {"texte": "", "src_lang": "fra_Latn", "tgt_lang": "ary_Arab"}
    response = client.post(
        "/generer", json=payload, headers={"Authorization": "Bearer fake-jwt-token"}
    )
    
    # On vérifie que le statut est bien 422, comme défini dans le handler
    assert response.status_code == 422
    # On vérifie que le message est bien celui de notre ValueError
    assert "Le texte doit contenir entre 1 et 200 mots" in response.json()["detail"]
# ===================================================================

def test_endpoint_handler_transforms_internal_exception_to_500(client):
    """
    (Ancien test renommé)
    Vérifie que le try/except à l'intérieur de l'endpoint `generer_texte`
    attrape bien les exceptions et les transforme en 500.
    """
    error_message = "Erreur d'exécution inattendue"
    with patch.object(LLMTranslator, 'traiter', side_effect=RuntimeError(error_message)):
        response = client.post(
            "/generer",
            json={"texte": "un texte valide", "src_lang": "fra_Latn", "tgt_lang": "ary_Arab"},
            headers={"Authorization": "Bearer fake-jwt-token"}
        )
        # L'endpoint attrape l'exception et la transforme en HTTPException(500)
        assert response.status_code == 500
        assert response.json()["detail"] == "Erreur interne du serveur"