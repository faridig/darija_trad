import sys
import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Ajouter la racine du projet au PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="function")
def test_db_engine():
    """Fixture pour le moteur de base de données de test (SQLite temporaire)"""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)

    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

    # Création des tables + insertion admin
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE translations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_lang VARCHAR(2) NOT NULL,
                source_text TEXT NOT NULL,
                target_lang VARCHAR(2) NOT NULL,
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

        # Hacher le mot de passe pour l'utilisateur "admin"
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_pw = pwd_context.hash("password")  # correspond au test login

        conn.execute(text("""
            INSERT INTO users (username, hashed_password, is_admin)
            VALUES (:username, :password, TRUE)
        """), {"username": "admin", "password": hashed_pw})

        conn.commit()

    yield engine
    os.unlink(db_path)


@pytest.fixture(scope="function")
def client(test_db_engine):
    """Client de test avec base de données SQLite injectée"""
    from api.data_api.main import app, get_db

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_translation_data():
    """Données de test standard pour une traduction"""
    return {
        "source_lang": "fr",
        "source_text": "Bonjour",
        "target_lang": "ar",
        "target_text": "السلام عليكم"
    }
