import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Column, Integer, String, Text, MetaData, Table
from sqlalchemy.orm import sessionmaker

from main import app
from db import Base
from schemas import TranslationCreate
from database.queries import TranslationQueries
from main import get_db

# Création de la base SQLite en mémoire
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# Session de test
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Déclaration de la table manuellement (si tu n'utilises pas SQLAlchemy ORM)
metadata = MetaData()

translations = Table(
    "translations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source_lang", String(2), nullable=False),
    Column("source_text", Text, nullable=False),
    Column("target_lang", String(2), nullable=False),
    Column("target_text", Text, nullable=False),
)

# Création de la table dans SQLite
metadata.create_all(bind=engine)


# Fonction pour injecter la session de test
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# On remplace la dépendance de la vraie BDD par la version test
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


# === TEST: CREATE ===
def test_create_translation():
    payload = {
        "source_lang": "fr",
        "source_text": "Bonjour",
        "target_lang": "ar",
        "target_text": "السلام عليكم"
    }

    response = client.post("/translations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["source_lang"] == "fr"
    assert data["target_lang"] == "ar"
    assert data["source_text"] == "Bonjour"
    assert data["target_text"] == "السلام عليكم"
    assert "id" in data
    return data["id"]


# === TEST: GET BY ID ===
def test_get_translation_by_id():
    created_id = test_create_translation()
    response = client.get(f"/translations/{created_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_id
    assert data["source_lang"] == "fr"


# === TEST: GET ALL ===
def test_get_all_translations():
    # Créer 2 traductions
    test_create_translation()
    test_create_translation()
    response = client.get("/translations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


# === TEST: UPDATE ===
def test_update_translation():
    created_id = test_create_translation()
    payload = {
        "source_lang": "fr",
        "source_text": "Merci",
        "target_lang": "ar",
        "target_text": "شكرا"
    }

    response = client.put(f"/translations/{created_id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["source_text"] == "Merci"
    assert data["target_text"] == "شكرا"


# === TEST: DELETE ===
def test_delete_translation():
    created_id = test_create_translation()
    response = client.delete(f"/translations/{created_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_id

    get_response = client.get(f"/translations/{created_id}")
    assert get_response.status_code == 404
