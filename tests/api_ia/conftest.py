import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

from api.ia_api.main import app
from api.ia_api.routers import auth as auth_router, monitoring as mon_router
import database.core.db as core_db
import database.core.auth as core_auth
from api.ia_api.model import LLMTranslator

@pytest.fixture(autouse=True)
def stub_env_and_dependencies(monkeypatch):
    # 1) Variables pour /metrics
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "password")
    # Override des constantes du module monitoring
    monkeypatch.setattr(mon_router, "ADMIN_USERNAME", "admin")
    monkeypatch.setattr(mon_router, "ADMIN_PASSWORD", "password")

    # 2) Stub de authenticate_user & create_access_token
    def fake_auth(username, password, db):
        return {"username": username} if (username, password) == ("admin", "password") else None

    def fake_token(data, expires_delta=None):
        return "fake-jwt-token"

    monkeypatch.setattr(auth_router, "authenticate_user", fake_auth)
    monkeypatch.setattr(auth_router, "create_access_token", fake_token)

    # 3) Stub de verify_jwt_token pour toute l'app
    def fake_verify_jwt_token(credentials=None):
        return {"username": "admin"}

    app.dependency_overrides[core_auth.verify_jwt_token] = fake_verify_jwt_token

    # 4) Stub de la méthode traiter de LLMTranslator (génération & health)
    def fake_traduction(self, texte, src_lang=None, tgt_lang=None):
        print("[MOCK] Traduction simulée")
        return f"translated:{texte}"


    monkeypatch.setattr(LLMTranslator, "traiter", fake_traduction)

@pytest.fixture(scope="function")
def test_db_engine():
    # SQLite in-memory pour /login
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE
            )
        """))
        pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed = pwd_ctx.hash("password")
        conn.execute(text("""
            INSERT INTO users (username, hashed_password, is_admin)
            VALUES (:u, :p, 1)
        """), {"u": "admin", "p": hashed})
    return engine

@pytest.fixture(scope="function")
def client(test_db_engine):
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

    app.dependency_overrides[core_db.get_db] = override_get_db

    client = TestClient(app)
    yield client

    # Nettoyage des overrides
    app.dependency_overrides.clear()
