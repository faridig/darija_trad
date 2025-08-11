# Fichier : tests/api_ia/test_middlewares.py (Version Corrigée)

from fastapi import status
import base64

# Middleware 2 : Limitation de taille du body (ce test est déjà correct)
def test_limit_body_size_rejects_large_payload(client):
    texte = "mot " * 3000
    payload = {
        "texte": texte,
        "src_lang": "fra_Latn",
        "tgt_lang": "ary_Arab"
    }
    response = client.post("/generer", json=payload)
    assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    assert "trop volumineux" in response.text

# Middleware 3 : Monitoring Prometheus
def test_monitoring_middleware_success_metrics_update(client):
    payload = {
        "texte": "bonjour",
        "src_lang": "fra_Latn",
        "tgt_lang": "ary_Arab"
    }
    response = client.post("/generer", json=payload)
    
    assert response.status_code == status.HTTP_200_OK
    # --- CORRECTION N°1 ---
    # On met à jour l'assertion pour correspondre au mock global de conftest.py
    assert response.json()["reponse"] == "traduction simulée réussie"

# Fonction d'aide pour l'authentification Basic
def basic_auth_header(user: str, pwd: str) -> dict:
    token = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

# --- CORRECTION N°2 ---
# On utilise monkeypatch pour simuler les variables d'environnement
def test_metrics_basic_auth_success(client, monkeypatch):
    # Simulation des variables d'environnement pour ce test
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "password")

    # On fait un appel à une route pour générer des métriques
    client.post("/generer", json={"texte": "test"})
    
    # On utilise les mêmes identifiants pour s'authentifier
    headers = basic_auth_header("admin", "password")
    response = client.get("/metrics", headers=headers)
    
    # Le test devrait maintenant passer
    assert response.status_code == status.HTTP_200_OK
    text = response.text
    assert "api_requests_total" in text
    assert "data_drift_text_length" in text