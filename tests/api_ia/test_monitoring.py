import pytest
from unittest.mock import patch
from fastapi import status
import requests # Importez requests pour monkeypatcher

def test_health_success(client):
    """Vérifie le cas nominal de /health."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"

def test_health_failure_on_model_error(client, monkeypatch):
    """Vérifie que /health renvoie 500 si l'appel réseau échoue."""
    # On surcharge le mock global pour simuler une erreur réseau
    def mock_post_error(*args, **kwargs):
        raise requests.exceptions.RequestException("Erreur réseau simulée")
    
    monkeypatch.setattr(requests, "post", mock_post_error)
    
    response = client.get("/health")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Service unavailable"}


def test_metrics_basic_auth_failure(client, basic_auth_header):
    """Vérifie que /metrics rejette les mauvais identifiants."""
    headers = basic_auth_header("admin", "badpass")
    response = client.get("/metrics", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED