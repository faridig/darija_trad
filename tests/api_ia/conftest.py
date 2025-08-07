import os
import pytest
from fastapi.testclient import TestClient

# --- IMPORTS DE L'APPLICATION ---
from api.ia_api.main import app
from api.ia_api.routers import monitoring as mon_router
from api.ia_api.model import LLMTranslator
import database.core.auth as core_auth




@pytest.fixture(autouse=True)
def stub_env_and_dependencies(monkeypatch):
    """
    Ce fixture s'exécute automatiquement pour chaque test.
    Il simule les dépendances externes pour isoler nos tests.
    """
    # 1) Simulation des variables d'environnement pour la route /metrics.
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
    
    # La simulation de `get_db` n'est plus nécessaire.


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