# Fichier : tests/api_crud/test_auth.py (Version mise à jour)

import pytest
from fastapi import status

# --- Tests de Login (inchangés, déjà bons) ---

def test_login_success(client):
    response = client.post(
        "/login",
        data={"username": "admin", "password": "password"}
    )
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"

def test_login_failure_wrong_password(client):
    response = client.post(
        "/login",
        data={"username": "admin", "password": "wrong"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Identifiants invalides"

def test_login_failure_wrong_user(client):
    response = client.post(
        "/login",
        data={"username": "unknown", "password": "password"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Identifiants invalides"

def test_me_endpoint(client, auth_headers):
    response = client.get("/me", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"username": "admin"}

# --- NOUVEAUX TESTS pour /register ---

def test_register_success(client):
    """Vérifie une inscription réussie."""
    payload = {"username": "newuser", "password": "newpassword123"}
    response = client.post("/register", json=payload)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == "newuser"
    assert "id" in data
    # On s'assure que le mot de passe n'est jamais retourné
    assert "hashed_password" not in data
    assert "password" not in data

def test_register_failure_user_exists(client):
    """Vérifie que l'inscription échoue si l'utilisateur existe déjà."""
    payload = {"username": "admin", "password": "somepassword"} # "admin" existe déjà
    response = client.post("/register", json=payload)
    
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "existe déjà" in response.json()["detail"]

@pytest.mark.parametrize("payload", [
    {"username": "u", "password": "password123"}, # username trop court
    {"username": "user", "password": "pass"},     # password trop court
    {"password": "password123"},                  # username manquant
    {"username": "user"},                         # password manquant
])
def test_register_failure_invalid_payload(client, payload):
    """Vérifie que les contraintes de validation Pydantic sont respectées."""
    response = client.post("/register", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY