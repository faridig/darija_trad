def test_login_success(client):
    response = client.post(
        "/login",
        data={"username": "admin", "password": "password"}
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"

def test_login_failure(client):
    response = client.post(
        "/login",
        data={"username": "admin", "password": "wrong"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Identifiants invalides"

def test_me_endpoint(client, auth_headers):
    response = client.get("/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"username": "admin"}
