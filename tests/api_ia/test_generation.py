import pytest
from fastapi import status

def test_generate_text_success(client):
    """
    Teste que l'endpoint /generer retourne une réponse réussie (200 OK)
    lorsque le texte fourni est valide.
    
    Args:
        client: Le client de test pour faire des requêtes HTTP
    """
    # Préparer les données d'entrée pour l'API
    payload = {"texte": "Bonjour le monde"}
    
    # Envoyer une requête POST à l'endpoint /generer avec le payload
    response = client.post("/generer", json=payload)
    
    # Vérifier que le code de statut est 200 OK
    assert response.status_code == status.HTTP_200_OK
    
    # Vérifier que la réponse JSON correspond à la traduction simulée attendue
    assert response.json() == {"reponse": "traduction simulée réussie"}


def test_generate_text_validation_error(client):
    """
    Teste que l'endpoint /generer retourne une erreur de validation (422)
    lorsque le texte fourni est vide.
    
    Args:
        client: Le client de test pour faire des requêtes HTTP
    """
    # Envoyer une requête POST avec un texte vide pour déclencher une erreur de validation
    response = client.post("/generer", json={"texte": ""})
    
    # Vérifier que le code de statut est 422 Unprocessable Entity
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY