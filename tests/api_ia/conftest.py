import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# --- IMPORTS DE L'APPLICATION ---
from api.ia_api.main import app
from api.ia_api.routers import monitoring as mon_router
from api.ia_api.model import LLMTranslator
import database.core.db as core_db
import database.core.auth as core_auth

# ==============================================================================
# ===> CORRECTION : Restauration d'une base de données de test en mémoire <===
# ==============================================================================
# Même si l'API IA n'utilise plus la BDD pour sa logique métier, certaines routes
# (comme /health dans sa version actuelle) ont encore la dépendance `Depends(get_db)`.
# Pour que les tests ne plantent pas en essayant de se connecter à une vraie BDD,
# nous fournissons une fausse BDD en mémoire (SQLite) uniquement pour la durée des tests.

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Crée une session de base de données de test."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# ==============================================================================
# ===> FIN DE LA CORRECTION <===
# ==============================================================================


@pytest.fixture(autouse=True)
def stub_env_and_dependencies(monkeypatch):
    """
    Ce fixture s'exécute automatiquement pour chaque test.
    Il simule les dépendances externes pour isoler nos tests.
    """
    # 1) Simulation des variables d'environnement pour la route /metrics
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "password")
    monkeypatch.setattr(mon_router, "ADMIN_USERNAME", "admin")
    monkeypatch.setattr(mon_router, "ADMIN_PASSWORD", "password")

    # 2) Simulation de la validation de token pour toutes les routes protégées.
    def fake_verify_jwt_token():
        return {"username": "testuser", "sub": "testuser"}
    app.dependency_overrides[core_auth.verify_jwt_token] = fake_verify_jwt_token

    # 3) Simulation de la méthode 'traiter' du modèle LLM pour des tests rapides.
    def fake_traduction(self, texte, src_lang=None, tgt_lang=None):
        return f"translated:{texte}"
    monkeypatch.setattr(LLMTranslator, "traiter", fake_traduction)
    
    # 4) On applique l'override de la base de données pour tous les tests.
    app.dependency_overrides[core_db.get_db] = override_get_db


@pytest.fixture(scope="function")
def client():
    """
    Crée un client de test pour l'application.
    Ce client permet d'envoyer des requêtes HTTP à notre API en mémoire.
    """
    with TestClient(app) as test_client:
        yield test_client

    # Nettoyage des simulations de dépendances après chaque test
    # pour garantir l'isolation des tests.
    app.dependency_overrides.clear()