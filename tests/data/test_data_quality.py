import sys
import os
import pytest

# Pour pouvoir faire import depuis data/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data")))
from normalise_data import get_clean_data

CODES_LANGS = {"fr", "en", "dr"}

def test_no_empty_fields():
    data = get_clean_data()
    for i, item in enumerate(data):
        assert item["source_text"], f"Texte source vide à la ligne {i}"
        assert item["target_text"], f"Texte cible vide à la ligne {i}"

def test_lang_codes_valid():
    data = get_clean_data()
    for i, item in enumerate(data):
        assert item["source_lang"] in CODES_LANGS, f"Code langue source inconnu : {item['source_lang']} à la ligne {i}"
        assert item["target_lang"] in CODES_LANGS, f"Code langue cible inconnu : {item['target_lang']} à la ligne {i}"

def test_no_long_texts():
    data = get_clean_data()
    for i, item in enumerate(data):
        assert len(item["source_text"].split()) <= 200, f"Texte source trop long à la ligne {i}"
        assert len(item["target_text"].split()) <= 200, f"Texte cible trop long à la ligne {i}"
