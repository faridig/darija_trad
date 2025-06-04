import pytest

# Le client est maintenant fourni par conftest.py

# === TEST: CREATE ===
def test_create_translation(client, sample_translation_data):
    """Test de création d'une traduction"""
    response = client.post("/translations", json=sample_translation_data)
    assert response.status_code == 200
    data = response.json()
    assert data["source_lang"] == sample_translation_data["source_lang"]
    assert data["target_lang"] == sample_translation_data["target_lang"]
    assert data["source_text"] == sample_translation_data["source_text"]
    assert data["target_text"] == sample_translation_data["target_text"]
    assert "id" in data
    assert data["id"] > 0


# === TEST: GET ALL ===
def test_get_all_translations(client, sample_translation_data):
    """Test de récupération de toutes les traductions"""
    # Créer d'abord une traduction pour s'assurer qu'il y en a au moins une
    client.post("/translations", json=sample_translation_data)
    
    response = client.get("/translations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


# === TEST: GET BY ID ===
def test_get_translation_by_id(client, sample_translation_data):
    """Test de récupération d'une traduction par ID"""
    # Créer d'abord une traduction
    create_response = client.post("/translations", json=sample_translation_data)
    assert create_response.status_code == 200
    created_id = create_response.json()["id"]
    
    # Récupérer par ID
    response = client.get(f"/translations/{created_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_id
    assert data["source_lang"] == sample_translation_data["source_lang"]
    assert data["source_text"] == sample_translation_data["source_text"]


# === TEST: UPDATE ===
def test_update_translation(client, sample_translation_data):
    """Test de mise à jour d'une traduction"""
    # Créer d'abord une traduction
    create_response = client.post("/translations", json=sample_translation_data)
    assert create_response.status_code == 200
    created_id = create_response.json()["id"]
    
    # Préparer les données de mise à jour
    update_payload = {
        "source_lang": "fr",
        "source_text": "Merci",
        "target_lang": "ar",
        "target_text": "شكرا"
    }

    # Effectuer la mise à jour
    response = client.put(f"/translations/{created_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_id
    assert data["source_text"] == update_payload["source_text"]
    assert data["target_text"] == update_payload["target_text"]


# === TEST: DELETE ===
def test_delete_translation(client, sample_translation_data):
    """Test de suppression d'une traduction"""
    # Créer d'abord une traduction
    create_response = client.post("/translations", json=sample_translation_data)
    assert create_response.status_code == 200
    created_id = create_response.json()["id"]
    
    # Supprimer la traduction
    response = client.delete(f"/translations/{created_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_id

    # Vérifier qu'elle a bien été supprimée
    get_response = client.get(f"/translations/{created_id}")
    assert get_response.status_code == 404


# === TEST: ERREURS ===
def test_get_nonexistent_translation(client):
    """Test de récupération d'une traduction inexistante"""
    response = client.get("/translations/99999")
    assert response.status_code == 404

def test_update_nonexistent_translation(client, sample_translation_data):
    """Test de mise à jour d'une traduction inexistante"""
    response = client.put("/translations/99999", json=sample_translation_data)
    assert response.status_code == 404

def test_delete_nonexistent_translation(client):
    """Test de suppression d'une traduction inexistante"""
    response = client.delete("/translations/99999")
    assert response.status_code == 404
