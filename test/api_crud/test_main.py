# test/api_crud/test_main.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, MetaData, Table
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

from api.data_api.main import app, get_db
from passlib.context import CryptContext

# Load environment variables
load_dotenv()

# Setup DB with Supabase
SQLALCHEMY_DATABASE_URL = os.getenv("SUPABASE_URL")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

metadata = MetaData()

# Table translations
translations = Table(
    "translations",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("source_lang", String(2), nullable=False),
    Column("source_text", Text, nullable=False),
    Column("target_lang", String(2), nullable=False),
    Column("target_text", Text, nullable=False)
)

# Table users
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String, unique=True, nullable=False),
    Column("hashed_password", Text, nullable=False),
    Column("is_admin", Boolean, default=False)
)

# Create tables if they don't exist
metadata.create_all(bind=engine)

# 🔐 Ajouter un utilisateur admin
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_context.hash("password")
with engine.begin() as conn:
    # Check if admin user exists
    result = conn.execute(users.select().where(users.c.username == "admin")).fetchone()
    if not result:
        conn.execute(users.insert().values(username="admin", hashed_password=hashed, is_admin=True))

# Overriding DB
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

# === FIXTURE POUR TOKEN JWT ===
@pytest.fixture
def auth_headers(client):
    """Effectue un login et retourne les headers avec JWT."""
    login_payload = {"username": "admin", "password": "password"}  # valeurs définies dans .env
    response = client.post("/login", data=login_payload)
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# === FIXTURE POUR DONNÉES DE TEST ===
@pytest.fixture
def sample_translation_data():
    return {
        "source_lang": "fr",
        "source_text": "Bonjour",
        "target_lang": "dr",
        "target_text": "السلام عليكم"
    }

# === TEST: CREATE ===
def test_create_translation(client, auth_headers, sample_translation_data):
    """Test de création d'une traduction"""
    response = client.post("/translations", json=sample_translation_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["source_lang"] == sample_translation_data["source_lang"]
    assert data["target_lang"] == sample_translation_data["target_lang"]
    assert data["source_text"] == sample_translation_data["source_text"]
    assert data["target_text"] == sample_translation_data["target_text"]
    assert "id" in data
    assert data["id"] > 0

# === TEST: GET ALL ===
def test_get_all_translations(client, auth_headers, sample_translation_data):
    """Test de récupération de toutes les traductions"""
    client.post("/translations", json=sample_translation_data, headers=auth_headers)
    
    response = client.get("/translations", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

# === TEST: GET BY ID ===
def test_get_translation_by_id(client, auth_headers, sample_translation_data):
    """Test de récupération d'une traduction par ID"""
    create_response = client.post("/translations", json=sample_translation_data, headers=auth_headers)
    assert create_response.status_code == 200
    created_id = create_response.json()["id"]
    
    response = client.get(f"/translations/{created_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_id

# === TEST: UPDATE ===
def test_update_translation(client, auth_headers, sample_translation_data):
    """Test de mise à jour d'une traduction"""
    create_response = client.post("/translations", json=sample_translation_data, headers=auth_headers)
    assert create_response.status_code == 200
    created_id = create_response.json()["id"]
    
    update_payload = {
        "source_lang": "fr",
        "source_text": "Merci",
        "target_lang": "dr",
        "target_text": "شكرا"
    }

    response = client.put(f"/translations/{created_id}", json=update_payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["source_text"] == update_payload["source_text"]
    assert data["target_text"] == update_payload["target_text"]

# === TEST: DELETE ===
def test_delete_translation(client, auth_headers, sample_translation_data):
    """Test de suppression d'une traduction"""
    create_response = client.post("/translations", json=sample_translation_data, headers=auth_headers)
    assert create_response.status_code == 200
    created_id = create_response.json()["id"]
    
    response = client.delete(f"/translations/{created_id}", headers=auth_headers)
    assert response.status_code == 200

    get_response = client.get(f"/translations/{created_id}", headers=auth_headers)
    assert get_response.status_code == 404

# === TEST: ERREURS (ressource inexistante) ===
def test_get_nonexistent_translation(client, auth_headers):
    response = client.get("/translations/99999", headers=auth_headers)
    assert response.status_code == 404

def test_update_nonexistent_translation(client, auth_headers, sample_translation_data):
    response = client.put("/translations/99999", json=sample_translation_data, headers=auth_headers)
    assert response.status_code == 404

def test_delete_nonexistent_translation(client, auth_headers):
    response = client.delete("/translations/99999", headers=auth_headers)
    assert response.status_code == 404
