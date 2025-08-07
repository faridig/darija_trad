# tests/api_ia/test_middlewares.py
from unittest.mock import patch
from api.ia_api.model import LLMTranslator
import pytest



# ────────────────────────────────────────────────────────────────────────────────
# Middleware 2 : Limitation de taille du body
# ────────────────────────────────────────────────────────────────────────────────
def test_limit_body_size_rejects_large_payload(client): # <--- Ajoutez "client" ici
    texte = "mot " * 3000  # 15KB environ
    payload = {
        "texte": texte,
        "src_lang": "fra_Latn",
        "tgt_lang": "ary_Arab"
    }

    response = client.post(
        "/generer",
        json=payload,
        headers={"Authorization": "Bearer fake-jwt-token"}
    )
    assert response.status_code == 413
    assert "trop volumineux" in response.text


# ────────────────────────────────────────────────────────────────────────────────
# Middleware 3 : Monitoring Prometheus
# ────────────────────────────────────────────────────────────────────────────────
def test_monitoring_middleware_success_metrics_update(client): # <--- Ajoutez "client" ici
    payload = {
        "texte": "bonjour",
        "src_lang": "fra_Latn",
        "tgt_lang": "ary_Arab"
    }
    response = client.post(
        "/generer",
        json=payload,
        headers={"Authorization": "Bearer fake-jwt-token"}
    )
    assert response.status_code == 200
    assert response.json()["reponse"] == "translated:bonjour"

# Vous pouvez garder cette fonction d'aide locale ou la déplacer dans utils.py
def basic_auth_header(user: str, pwd: str) -> dict:
    import base64
    token = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

def test_metrics_basic_auth_success(client): # <--- Ajoutez "client" ici
    client.post(
        "/generer",
        json={"texte": "test"},
        headers={"Authorization": "Bearer fake-jwt-token"}
    )
    headers = basic_auth_header("admin", "password")
    r = client.get("/metrics", headers=headers)
    assert r.status_code == 200
    text = r.text
    assert "api_requests_total" in text
    assert "data_drift_text_length" in text

