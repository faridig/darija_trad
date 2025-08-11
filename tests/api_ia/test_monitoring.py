# Fichier : tests/api_ia/test_monitoring.py (Version Corrigée et Complète)

import pytest
from fastapi import status
import requests  # Nécessaire pour simuler les exceptions réseau
import base64    # Nécessaire pour l'authentification Basic
from unittest.mock import patch

# --- Tests pour /health ---

def test_health_success(client):
    """
    Vérifie le cas nominal de /health.
    Le mock global dans conftest.py simule un appel réseau réussi.
    """
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

def test_health_failure_on_model_error(client, monkeypatch):
    """
    Vérifie que /health renvoie 500 si l'appel réseau vers l'API externe échoue.
    """
    # On surcharge le mock global de 'requests.post' pour qu'il lève une exception
    def mock_post_error(*args, **kwargs):
        raise requests.exceptions.RequestException("Erreur réseau simulée")
    
    monkeypatch.setattr(requests, "post", mock_post_error)
    
    response = client.get("/health")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Service unavailable"}

# --- Tests pour /metrics ---

# Fonction d'aide pour créer le header d'authentification Basic
def basic_auth_header(user: str, pwd: str) -> dict:
    token = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

def test_metrics_basic_auth_failure_wrong_password(client):
    """Vérifie que /metrics rejette un mot de passe incorrect."""
    headers = basic_auth_header("admin", "bad_password")
    response = client.get("/metrics", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_metrics_basic_auth_failure_wrong_user(client):
    """Vérifie que /metrics rejette un nom d'utilisateur incorrect."""
    headers = basic_auth_header("bad_user", "password")
    response = client.get("/metrics", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_metrics_no_auth(client):
    """Vérifie que /metrics rejette une requête sans authentification."""
    response = client.get("/metrics")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED