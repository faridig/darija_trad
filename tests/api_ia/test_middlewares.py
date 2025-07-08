import base64
from fastapi.testclient import TestClient
from api.ia_api.main import app

client = TestClient(app)

# ────────────────────────────────────────────────────────────────────────────────
# Middleware 1 : Headers de sécurité HTTP
# ────────────────────────────────────────────────────────────────────────────────
def test_security_headers_on_api_routes():
    response = client.get("/health", headers={"Authorization": "Bearer fake-jwt-token"})
    assert response.status_code == 200
    headers = response.headers

    assert "Strict-Transport-Security" in headers
    assert "X-Frame-Options" in headers
    assert "Content-Security-Policy" in headers
    assert headers["X-Frame-Options"] == "DENY"

def test_swagger_headers_dev_friendly():
    response = client.get("/docs")
    headers = response.headers
    assert "Content-Security-Policy" in headers
    assert "cdn.jsdelivr.net" in headers["Content-Security-Policy"]


# ────────────────────────────────────────────────────────────────────────────────
# Middleware 2 : Limitation de taille du body
# ────────────────────────────────────────────────────────────────────────────────
def test_limit_body_size_rejects_large_payload():
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
def test_monitoring_middleware_success_metrics_update():
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

def basic_auth_header(user: str, pwd: str) -> dict:
    token = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

def test_metrics_basic_auth_success(client):
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
