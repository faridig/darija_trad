# tests/data/test_data_quality.py

import pytest
import json
import os

# ---------------------------------------------------------------------------
# CONFIGURATION DES TESTS
# ---------------------------------------------------------------------------

# Fichier de données à tester. C'est l'artefact généré par l'étape d'export.
DATA_ARTIFACT_PATH = "all_translations_dataset.jsonl"

# Ensemble des codes de langue valides attendus dans le fichier (format NLLB).
VALID_LANG_CODES = {"fra_Latn", "eng_Latn", "ary_Arab"}

# Longueur maximale autorisée pour un texte (en nombre de mots).
MAX_TEXT_LENGTH_WORDS = 200

# ---------------------------------------------------------------------------
# FIXTURE PYTEST : CHARGEMENT DES DONNÉES
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def corpus_data():
    """
    Fixture Pytest qui charge les données depuis l'artefact JSONL.
    Le scope="module" signifie qu'il ne sera chargé qu'une seule fois
    pour tous les tests de ce fichier, optimisant la performance.
    """
    if not os.path.exists(DATA_ARTIFACT_PATH):
        pytest.fail(
            f"ERREUR : Le fichier de données à tester '{DATA_ARTIFACT_PATH}' est introuvable. "
            f"Assurez-vous que l'étape 'export_dataset.py' a bien été exécutée avant les tests."
        )
    
    with open(DATA_ARTIFACT_PATH, "r", encoding="utf-8") as f:
        # Charge chaque ligne comme un objet JSON distinct (format JSON Lines).
        return [json.loads(line) for line in f]

# ---------------------------------------------------------------------------
# SÉRIE DE TESTS DE QUALITÉ
# ---------------------------------------------------------------------------

def test_data_structure_is_valid(corpus_data):
    """
    Vérifie que chaque ligne a la structure de base attendue :
    un dictionnaire contenant une clé "translation".
    """
    for i, item in enumerate(corpus_data):
        assert isinstance(item, dict), f"La ligne {i} n'est pas un dictionnaire JSON valide."
        assert "translation" in item, f"La clé 'translation' est manquante à la ligne {i}."
        assert isinstance(item["translation"], dict), f"La valeur de 'translation' n'est pas un dictionnaire à la ligne {i}."

def test_no_empty_or_whitespace_text(corpus_data):
    """
    Vérifie qu'il n'y a pas de textes vides ou contenant uniquement des espaces.
    """
    for i, item in enumerate(corpus_data):
        translation_dict = item.get("translation", {})
        assert len(translation_dict) > 0, f"Le dictionnaire 'translation' est vide à la ligne {i}."
        
        for lang, text in translation_dict.items():
            assert text and text.strip(), f"Texte vide ou composé d'espaces trouvé pour la langue '{lang}' à la ligne {i}."

def test_language_codes_are_valid(corpus_data):
    """
    Vérifie que tous les codes de langue utilisés sont dans la liste autorisée.
    """
    for i, item in enumerate(corpus_data):
        lang_keys = item.get("translation", {}).keys()
        for lang_code in lang_keys:
            assert lang_code in VALID_LANG_CODES, f"Code langue invalide '{lang_code}' trouvé à la ligne {i}."

def test_text_length_is_within_limits(corpus_data):
    """
    Vérifie qu'aucun texte ne dépasse la longueur maximale autorisée.
    """
    for i, item in enumerate(corpus_data):
        for lang, text in item.get("translation", {}).items():
            word_count = len(text.strip().split())
            assert word_count <= MAX_TEXT_LENGTH_WORDS, (
                f"Texte trop long ({word_count} mots) pour la langue '{lang}' à la ligne {i}. "
                f"Extrait : '{text[:70]}...'"
            )