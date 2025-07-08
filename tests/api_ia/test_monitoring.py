import base64
from database.core.auth import verify_jwt_token
from fastapi import HTTPException
from tests.api_ia.utils import basic_auth_header




def test_health_success(client):
    r = client.get("/health", headers={"Authorization": "Bearer fake-jwt-token"})
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "healthy"
    assert "timestamp" in j

def test_health_unauthorized(client):
    # Forcer échec de la dépendance JWT
    def fake_fail(creds=None):
        raise HTTPException(status_code=401, detail="unauth")
    client.app.dependency_overrides[verify_jwt_token] = fake_fail

    r = client.get("/health")
    assert r.status_code == 401

    # Restauration
    client.app.dependency_overrides.pop(verify_jwt_token)


def test_metrics_basic_auth_failure(client):
    headers = basic_auth_header("admin", "badpass")
    r = client.get("/metrics", headers=headers)
    assert r.status_code == 401
