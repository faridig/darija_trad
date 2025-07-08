import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

from api.data_api.main import app
from database.core.db import get_db

@pytest.fixture(scope="function")
def test_db_engine(tmp_path):
    # Base SQLite éphémère dans tmp_path
    db_file = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False}
    )
    # Création des tables
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE translations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_lang TEXT NOT NULL,
                source_text TEXT NOT NULL,
                target_lang TEXT NOT NULL,
                target_text TEXT NOT NULL
            )
        """))
        conn.execute(text("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE
            )
        """))
        # Insertion d'un utilisateur admin
        pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed = pwd_ctx.hash("password")
        conn.execute(text("""
            INSERT INTO users (username, hashed_password, is_admin)
            VALUES (:username, :password, 1)
        """), {"username": "admin", "password": hashed})
    return engine

@pytest.fixture(scope="function")
def client(test_db_engine):
    # Override de la dépendance get_db pour utiliser SQLite
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine
    )
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    yield client

    # Nettoyage des overrides
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers(client):
    # Obtention du JWT via /login
    response = client.post(
        "/login",
        data={"username": "admin", "password": "password"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_translation_data():
    return {
        "source_lang": "fr",
        "source_text": "Bonjour",
        "target_lang": "dr",
        "target_text": "سلام"
    }

