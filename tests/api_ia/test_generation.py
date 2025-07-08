import pytest

def test_generate_text_success(client):
    payload = {"texte": "Bonjour le monde"}
    r = client.post(
        "/generer",
        json=payload,
        headers={"Authorization": "Bearer fake-jwt-token"}
    )
    assert r.status_code == 200
    assert r.json() == {"reponse": "translated:Bonjour le monde"}

def test_generate_text_validation_error(client):
    # Texte vide doit déclencher 422
    r = client.post(
        "/generer",
        json={"texte": ""},
        headers={"Authorization": "Bearer fake-jwt-token"}
    )
    assert r.status_code == 422
