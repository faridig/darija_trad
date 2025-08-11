# Fichier : tests/api_ia/test_generation.py (Version mise à jour)

import pytest
from fastapi import status

def test_generate_text_success(client):
    payload = {"texte": "Bonjour le monde"}
    response = client.post("/generer", json=payload)
    
    # L'appel réseau est maintenant simulé par conftest.py
    assert response.status_code == status.HTTP_200_OK
    # On vérifie que la réponse est bien celle de notre mock global
    assert response.json() == {"reponse": "traduction simulée réussie"}

def test_generate_text_validation_error(client):
    # Ce test ne change pas, il teste la validation Pydantic
    response = client.post("/generer", json={"texte": ""})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY