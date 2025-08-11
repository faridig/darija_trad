# Fichier : tests/api_ia/test_middlewares.py (Version finale)
# Ce fichier teste le comportement des middlewares de l'application.

from fastapi import status

# -----------------------------------------------------------------------------
# Test du middleware `limit_body_size`
# -----------------------------------------------------------------------------
def test_limit_body_size_rejects_large_payload(client):
    """
    Vérifie que le middleware de limitation de taille bloque bien les requêtes
    avec un corps trop volumineux.
    """
    # On crée un payload qui dépasse la limite de 10 Ko
    large_text = "mot " * 3000
    payload = {
        "texte": large_text,
        "src_lang": "fra_Latn",
        "tgt_lang": "ary_Arab"
    }
    
    response = client.post("/generer", json=payload)
    
    # On s'attend à recevoir une erreur 413 "Payload Too Large"
    assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    assert "trop volumineux" in response.text

# -----------------------------------------------------------------------------
# Test du middleware `monitoring_middleware`
# -----------------------------------------------------------------------------
def test_monitoring_middleware_handles_success_case(client):
    """
    Vérifie que le middleware de monitoring ne casse pas le flux normal
    d'une requête réussie. C'est un test de non-régression.
    """
    payload = {
        "texte": "bonjour",
        "src_lang": "fra_Latn",
        "tgt_lang": "ary_Arab"
    }
    response = client.post("/generer", json=payload)
    
    # On s'assure que la réponse est toujours 200 OK
    assert response.status_code == status.HTTP_200_OK
    # On vérifie que la réponse est bien celle du mock configuré dans conftest.py
    assert response.json()["reponse"] == "traduction simulée réussie"