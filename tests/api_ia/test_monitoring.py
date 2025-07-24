# tests/api_ia/test_monitoring.py

import pytest
from unittest.mock import patch

from api.ia_api.model import LLMTranslator
from api.ia_api.routers.monitoring import verify_jwt_token, security # Importer pour le patch
from fastapi import HTTPException


# ----------------------------------------------------

def test_health_success(client):
    """
    Test du "happy path" de /health : tout fonctionne.
    Ce test existait déjà.
    """
    r = client.get("/health", headers={"Authorization": "Bearer fake-jwt-token"})
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "healthy"
    assert "timestamp" in j

def test_health_unauthorized(client):
    """
    Test que /health est bien protégé par JWT.
    Ce test existait déjà.
    """
    # Forcer l'échec de la dépendance JWT
    def fake_fail_jwt(credentials=None):
        raise HTTPException(status_code=401, detail="unauth")
    
    # Remplacer la dépendance dans l'app
    client.app.dependency_overrides[verify_jwt_token] = fake_fail_jwt

    r = client.get("/health")
    assert r.status_code == 401

    # Important : nettoyer l'override après le test
    client.app.dependency_overrides.pop(verify_jwt_token, None)


def test_metrics_basic_auth_failure(client, basic_auth_header):
    """
    Test que /metrics rejette les mauvais identifiants.
    Ce test existait déjà.
    """
    headers = basic_auth_header("admin", "badpass")
    r = client.get("/metrics", headers=headers)
    assert r.status_code == 401

#  tests pour augmenter la couverture
# ====================================================

#  Test 1 : Couvrir le cas d'échec du health check
# -----------------------------------------------------------
def test_health_failure_on_model_error(client):
    """
    Vérifie que /health renvoie bien un statut 500 si le modèle lève une exception.
    Ce test va couvrir le bloc `except Exception as e:` dans la fonction `health_check`.
    """
    # On utilise "patch" pour remplacer temporairement la méthode `traiter` de la classe LLMTranslator.
    # `side_effect` permet de déclencher une exception quand la méthode est appelée.
    with patch.object(LLMTranslator, 'traiter', side_effect=Exception("Erreur modèle simulée")):
        response = client.get("/health", headers={"Authorization": "Bearer fake-jwt-token"})
        
        # On vérifie que le serveur a bien renvoyé une erreur 500 et le bon message.
        assert response.status_code == 500
        assert response.json() == {"detail": "Service unavailable"}


#  Test 2 : Couvrir le cas de Basic Auth avec mauvais utilisateur
# -----------------------------------------------------------
def test_metrics_basic_auth_bad_username(client, basic_auth_header):
    """
    Vérifie que /metrics rejette un mauvais nom d'utilisateur.
    Le test existant vérifiait un mauvais mot de passe. Celui-ci s'assure que
    la condition `if not (username_ok and password_ok):` est bien testée pour les deux cas.
    """
    headers = basic_auth_header("bad_user", "password")
    response = client.get("/metrics", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

# Test 3 : Couvrir le cas où le corps de la requête est vide
# -----------------------------------------------------------
def test_monitoring_middleware_with_empty_body(client):
    """
    Vérifie que le middleware gère correctement une requête POST à /generer
    sans aucun corps de requête.
    Ce test couvre le `if body:` dans `monitoring_middleware`.
    """
    response = client.post(
        "/generer",
        content=None, # On envoie un corps vide
        headers={"Authorization": "Bearer fake-jwt-token"}
    )
    # FastAPI va retourner une erreur 422 car le corps est requis, mais
    # l'important est que le middleware n'ait pas planté.
    assert response.status_code == 422


#  Test 4 : Couvrir le cas où le corps de la requête est mal formé
# -----------------------------------------------------------
def test_monitoring_middleware_with_bad_json(client):
    """
    Vérifie que le middleware gère une requête avec du JSON invalide.
    Ce test couvre le bloc `except Exception as e:` dans la partie
    de parsing du corps de la requête dans `monitoring_middleware`.
    """
    response = client.post(
        "/generer",
        content='{"texte": "ceci n\'est pas du json valide,}', # JSON malformé
        headers={
            "Authorization": "Bearer fake-jwt-token",
            "Content-Type": "application/json"
        }
    )
    # FastAPI devrait retourner une erreur 422. Notre but est de vérifier
    # que le middleware a bien intercepté l'erreur de parsing sans crasher.
    assert response.status_code == 422

