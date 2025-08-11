# Fichier : tests/api_ia/test_generation.py (Simplifié)

import pytest
from fastapi import status

def test_generate_text_success(client):
    payload = {"texte": "Bonjour le monde"}
    response = client.post("/generer", json=payload)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"reponse": "traduction simulée réussie"}

def test_generate_text_validation_error(client):
    response = client.post("/generer", json={"texte": ""})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY