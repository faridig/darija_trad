def test_login_success(client):
    r = client.post("/login", data={"username": "admin", "password": "password"})
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"] == "fake-jwt-token"
    assert body["token_type"] == "bearer"

def test_login_bad_credentials(client):
    r = client.post("/login", data={"username": "admin", "password": "wrong"})
    assert r.status_code == 400

def test_me_endpoint(client):
    r = client.get(
        "/me",
        headers={"Authorization": "Bearer fake-jwt-token"}
    )
    assert r.status_code == 200
    assert r.json() == {"username": "admin"}
