# Fichier : tests/api_ia/test_monitoring.py (Version Corrigée)
"""
Ce module contient les tests pour les endpoints de monitoring de l'API:
- /health : vérifie l'état de santé de l'application et ses dépendances
- /metrics : fournit des métriques sur l'application (protégé par authentification)

Ces tests permettent de s'assurer que le monitoring fonctionne correctement
dans différents scénarios (succès et échecs).
"""

import pytest
from fastapi import status
import requests  # Nécessaire pour simuler les exceptions réseau
import base64    # Nécessaire pour l'authentification Basic
from unittest.mock import patch, MagicMock
import os

# --- Tests pour /health ---

def test_health_success(client):
    """
    Vérifie le cas nominal de l'endpoint /health.
    
    Ce test s'assure que lorsque tous les services sont disponibles:
    - Le code de statut HTTP est 200 OK
    - Le JSON retourné contient "healthy" comme statut
    - Un timestamp est présent dans la réponse
    
    Le mock global dans conftest.py simule un appel réseau réussi vers l'API externe.
    """
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"  # Vérifie que le statut est bien "healthy"
    assert "timestamp" in data  # Vérifie qu'un timestamp est présent dans la réponse

def test_health_failure_on_model_error(client, monkeypatch):
    """
    Vérifie que /health renvoie 500 si l'appel réseau vers l'API externe échoue.
    
    Ce test simule une panne de l'API externe en remplaçant le comportement
    de requests.post par une fonction qui lève une exception.
    
    On s'attend à:
    - Un code de statut HTTP 500
    - Un message d'erreur indiquant que le service est indisponible
    """
    # On surcharge le mock global de 'requests.post' pour qu'il lève une exception
    def mock_post_error(*args, **kwargs):
        raise requests.exceptions.RequestException("Erreur réseau simulée")
    
    monkeypatch.setattr(requests, "post", mock_post_error)  # Remplace la fonction requests.post par notre mock
    
    response = client.get("/health")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "Service unavailable"}  # Vérifie le message d'erreur exact

# --- Tests pour /metrics ---

# Fonction d'aide pour créer le header d'authentification Basic
def basic_auth_header(user: str, pwd: str) -> dict:
    """
    Crée un header d'authentification Basic à partir d'un nom d'utilisateur et mot de passe.
    
    Args:
        user (str): Nom d'utilisateur
        pwd (str): Mot de passe
        
    Returns:
        dict: Un dictionnaire contenant l'en-tête Authorization avec la valeur encodée en Base64
    """
    token = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

def test_metrics_basic_auth_failure_wrong_password(client):
    """
    Vérifie que /metrics rejette un mot de passe incorrect.
    
    Ce test tente d'accéder à l'endpoint /metrics avec un nom d'utilisateur
    valide mais un mot de passe incorrect, et vérifie que l'accès est refusé.
    """
    headers = basic_auth_header("admin", "bad_password")  # Utilise un mot de passe incorrect
    response = client.get("/metrics", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED  # Vérifie que l'accès est refusé

def test_metrics_basic_auth_failure_wrong_user(client):
    """
    Vérifie que /metrics rejette un nom d'utilisateur incorrect.
    
    Ce test tente d'accéder à l'endpoint /metrics avec un nom d'utilisateur
    invalide et vérifie que l'accès est refusé même si le format de l'authentification est correct.
    """
    headers = basic_auth_header("bad_user", "password")  # Utilise un nom d'utilisateur incorrect
    response = client.get("/metrics", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED  # Vérifie que l'accès est refusé

def test_metrics_no_auth(client):
    """
    Vérifie que /metrics rejette une requête sans authentification.
    
    Ce test s'assure que l'endpoint /metrics n'est pas accessible
    sans fournir d'en-tête d'authentification.
    """
    response = client.get("/metrics")  # Pas d'en-tête d'authentification fourni
    assert response.status_code == status.HTTP_401_UNAUTHORIZED  # Vérifie que l'accès est refusé

def test_metrics_success_with_correct_credentials(client, monkeypatch):
    """
    Vérifie que /metrics retourne les métriques Prometheus avec des identifiants corrects.
    
    Ce test couvre la ligne 106 (return PlainTextResponse) et s'assure que l'endpoint
    fonctionne correctement avec les bonnes credentials.
    """
    # Mock direct des variables dans le module monitoring
    with patch('api.ia_api.routers.monitoring.ADMIN_USERNAME', 'test_admin'), \
         patch('api.ia_api.routers.monitoring.ADMIN_PASSWORD', 'test_password'):
        
        # Mock de generate_latest pour retourner un contenu de test
        mock_metrics_content = "# HELP test_metric A test metric\n# TYPE test_metric counter\ntest_metric 1\n"
        
        with patch('api.ia_api.routers.monitoring.generate_latest', return_value=mock_metrics_content.encode()):
            headers = basic_auth_header("test_admin", "test_password")  # Utilise les credentials de test
            response = client.get("/metrics", headers=headers)
            
            assert response.status_code == status.HTTP_200_OK
            assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"
            assert mock_metrics_content in response.text

def test_health_check_exception_logging(client, monkeypatch):
    """
    Vérifie que l'exception dans health_check est correctement loggée.
    
    Ce test couvre la ligne 167 (logger.error) et s'assure que les erreurs
    sont bien enregistrées dans les logs.
    """
    # Mock pour faire échouer l'appel au traducteur
    def mock_traiter_error(*args, **kwargs):
        raise Exception("Erreur de connexion simulée")
    
    # Mock du logger pour capturer l'appel à error
    with patch('api.ia_api.routers.monitoring.logger') as mock_logger:
        # Mock direct de la méthode traiter du translator
        from api.ia_api.routers.monitoring import translator
        original_traiter = translator.traiter
        translator.traiter = mock_traiter_error
        
        try:
            response = client.get("/health")
            
            # Vérifie que l'erreur a été loggée
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "Health check failed" in call_args
            assert "Erreur de connexion simulée" in call_args
            
            # Vérifie que la réponse est une erreur 500
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert response.json() == {"detail": "Service unavailable"}
        finally:
            # Restaure la méthode originale
            translator.traiter = original_traiter
            
def test_liveness_check(client):
    """
    Teste l'endpoint /healthz (liveness probe).
    
    Ce test couvre la ligne 106 (return {"status": "ok"}) et s'assure que
    l'endpoint de vivacité fonctionne correctement.
    """
    response = client.get("/healthz")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}