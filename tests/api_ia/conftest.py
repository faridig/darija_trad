import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

from api.ia_api.main import app
# --- CORRECTION ---
# On ne peut plus importer 'auth' car il a été supprimé.
# On importe directement les dépendances que l'on veut simuler.
from api.ia_api.routers import monitoring as mon_router
import database.core.db as core_db
import database.core.auth as core_auth
from api.ia_api.model import LLMTranslator
# --- FIN DE LA CORRECTION ---


@pytest.fixture(autouse=True)
def stub_env_and_dependencies(monkeypatch):
    """
    Ce fixture s'exécute automatiquement pour chaque test.
    Il simule les dépendances externes pour isoler nos tests.
    """
    # 1) Variables d'environnement pour la route /metrics
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "password")
    # On modifie directement les constantes dans le module 'monitoring'
    monkeypatch.setattr(mon_router, "ADMIN_USERNAME", "admin")
    monkeypatch.setattr(mon_router, "ADMIN_PASSWORD", "password")

    # --- CORRECTION ---
    # 2) La logique de 'authenticate_user' et 'create_access_token' n'est plus
    #    dans l'API IA. Il n'y a donc plus rien à simuler ici concernant
    #    la création de token. On supprime les anciens mocks.
    # --- FIN DE LA CORRECTION ---

    # 3) Simulation de la validation de token pour toutes les routes protégées.
    #    Ceci est maintenant la seule simulation d'authentification nécessaire.
    def fake_verify_jwt_token(credentials=None):
        # On simule un utilisateur authentifié avec succès.
        return {"username": "testuser", "sub": "testuser"}

    app.dependency_overrides[core_auth.verify_jwt_token] = fake_verify_jwt_token

    # 4) Simulation de la méthode 'traiter' du modèle LLM pour que les tests
    #    soient rapides et ne dépendent pas du chargement d'un vrai modèle.
    def fake_traduction(self, texte, src_lang=None, tgt_lang=None):
        return f"translated:{texte}"

    monkeypatch.setattr(LLMTranslator, "traiter", fake_traduction)

# --- CORRECTION ---
# 5) La base de données n'est plus du tout utilisée par l'API IA.
#    Toute la logique de création de BDD de test, de session, et d'override de get_db
#    peut être supprimée car elle est devenue inutile.
# --- FIN DE LA CORRECTION ---

@pytest.fixture(scope="function")
def client():
    """
    Crée un client de test pour l'application.
    Ce client permet d'envoyer des requêtes HTTP à notre API en mémoire.
    """
    # On utilise un with TestClient(app) pour s'assurer que les événements
    # de démarrage et d'arrêt de l'application sont bien exécutés.
    with TestClient(app) as test_client:
        yield test_client

    # Nettoyage des simulations de dépendances après chaque test
    # pour garantir l'isolation des tests.
    app.dependency_overrides.clear()