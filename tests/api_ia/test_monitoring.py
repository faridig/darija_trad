# Fichier : tests/api_ia/test_monitoring.py (Version mise à jour)

import pytest
from unittest.mock import patch
from fastapi import status
from api.ia_api.model import LLMTranslator

def test_health_success(client):
    """Vérifie le cas nominal de /health."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

def test_health_failure_on_model_error(client):
    """Vérifie que /health renvoie 500 si le traducteur échoue."""
    # On surcharge le mock global juste pour ce test
    with patch('api.ia_api.routers.generation.translator.traiter', side_effect=Exception("Erreur modèle simulée")):
        response = client.get("/health")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json() == {"detail": "Service unavailable"}

def test_metrics_basic_auth_failure(client, basic_auth_header):
    """Vérifie que /metrics rejette les mauvais identifiants."""
    headers = basic_auth_header("admin", "badpass")
    response = client.get("/metrics", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED