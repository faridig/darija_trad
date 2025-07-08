import sys
from pathlib import Path

# Ajouter la racine du projet au PYTHONPATH pour que les imports fonctionnent
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
