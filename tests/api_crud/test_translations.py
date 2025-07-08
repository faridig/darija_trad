

def test_create_translation(client, auth_headers, sample_translation_data):
    response = client.post(
        "/translations",
        json=sample_translation_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    for field in ["source_lang", "source_text", "target_lang", "target_text"]:
        assert data[field] == sample_translation_data[field]

def test_get_all_translations(client, auth_headers, sample_translation_data):
    client.post("/translations", json=sample_translation_data, headers=auth_headers)
    response = client.get("/translations", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

def test_get_translation_by_id(client, auth_headers, sample_translation_data):
    create_res = client.post("/translations", json=sample_translation_data, headers=auth_headers)
    created_id = create_res.json()["id"]
    response = client.get(f"/translations/{created_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == created_id

def test_update_translation(client, auth_headers, sample_translation_data):
    create_res = client.post("/translations", json=sample_translation_data, headers=auth_headers)
    created_id = create_res.json()["id"]
    update_payload = {
        "source_lang": "fr",
        "source_text": "Merci",
        "target_lang": "dr",
        "target_text": "شكرا"
    }
    response = client.put(
        f"/translations/{created_id}",
        json=update_payload,
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["source_text"] == "Merci"
    assert response.json()["target_text"] == "شكرا"

def test_delete_translation(client, auth_headers, sample_translation_data):
    create_res = client.post("/translations", json=sample_translation_data, headers=auth_headers)
    created_id = create_res.json()["id"]
    del_res = client.delete(f"/translations/{created_id}", headers=auth_headers)
    assert del_res.status_code == 200

    # vérification qu'on ne peut plus le récupérer
    get_res = client.get(f"/translations/{created_id}", headers=auth_headers)
    assert get_res.status_code == 404

def test_get_nonexistent_translation(client, auth_headers):
    response = client.get("/translations/9999", headers=auth_headers)
    assert response.status_code == 404

def test_update_nonexistent_translation(client, auth_headers, sample_translation_data):
    response = client.put("/translations/9999", json=sample_translation_data, headers=auth_headers)
    assert response.status_code == 404

def test_delete_nonexistent_translation(client, auth_headers):
    response = client.delete("/translations/9999", headers=auth_headers)
    assert response.status_code == 404
