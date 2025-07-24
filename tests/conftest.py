import sys
from pathlib import Path
import pytest
import base64

# Ajouter la racine du projet au PYTHONPATH pour que les imports fonctionnent
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture
def basic_auth_header():
    """Fixture pour créer facilement un header d'authentification Basic."""
    def _basic_auth_header(user: str, pwd: str) -> dict:
        token = base64.b64encode(f"{user}:{pwd}".encode()).decode()
        return {"Authorization": f"Basic {token}"}
    return _basic_auth_header
