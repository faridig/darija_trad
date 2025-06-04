import sys
import os
import tempfile
from pathlib import Path

# Ajouter la racine du projet au PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="function")
def test_db_engine():
    """Fixture pour le moteur de base de données de test"""
    # Créer un fichier SQLite temporaire
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    # Créer la table avec SQL brut
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
        conn.commit()
    
    yield engine
    
    # Nettoyer le fichier temporaire
    os.unlink(db_path)

@pytest.fixture(scope="function")
def client(test_db_engine):
    """Fixture pour le client de test avec base de données persistante"""
    from api.data_api.main import app, get_db
    
    # Créer le sessionmaker une seule fois par test
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    
    # Override de la dépendance get_db
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Nettoyer les overrides après le test
    app.dependency_overrides.clear()

@pytest.fixture
def sample_translation_data():
    """Fixture pour des données de test"""
    return {
        "source_lang": "fr",
        "source_text": "Bonjour",
        "target_lang": "ar", 
        "target_text": "السلام عليكم"
    } 