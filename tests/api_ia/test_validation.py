import pytest
from fastapi.testclient import TestClient
from api.ia_api.main import app
from api.ia_api.schemas import TexteInput, LangCode
from pydantic import ValidationError

client = TestClient(app)

@pytest.mark.parametrize("texte, src, status", [
    ("тест", "fra_Latn", 422),     # cyrillique non autorisé en latin
    ("مرحبا", "fra_Latn", 422),    # arabe non autorisé en latin
    ("Hello", "eng_Latn", 200),    # latin autorisé en anglais
    ("مرحبا", "ary_Arab", 200),    # arabe autorisé en arabe
])
def test_script_validation(texte, src, status):
    payload = {"texte": texte, "src_lang": src, "tgt_lang": "fra_Latn"}
    r = client.post("/generer", json=payload,
                    headers={"Authorization": "Bearer fake-jwt-token"})
    assert r.status_code == status

# ===================================================================
# Tests sur la validation du nombre de mots
# ===================================================================

def test_texte_input_valid():
    """Vérifie qu'un texte valide passe la validation sans erreur."""
    try:
        TexteInput(texte="Bonjour le monde")
    except ValidationError:
        pytest.fail("TexteInput a levé une ValidationError inattendue pour un texte valide.")

def test_texte_input_too_short():
    """
    Vérifie qu'un texte avec 0 mot lève une erreur.
    Ce test couvre la borne inférieure de `if not 1 <= n_mots <= 200:`.
    """
    with pytest.raises(ValueError, match="Le texte doit contenir entre 1 et 200 mots"):
        # Un texte composé uniquement d'espaces aura 0 mot après strip().
        TexteInput(texte="   ")

def test_texte_input_too_long():
    """
    Vérifie qu'un texte avec plus de 200 mots lève une erreur.
    Ce test couvre la borne supérieure de `if not 1 <= n_mots <= 200:`.
    """
    long_text = "mot " * 201
    with pytest.raises(ValueError, match="Le texte doit contenir entre 1 et 200 mots"):
        TexteInput(texte=long_text)


# ===================================================================
# Tests sur la validation du script (caractères autorisés)
# ===================================================================

@pytest.mark.parametrize("texte, src, is_valid", [
    # Cas valides
    ("Bonjour le monde, comment ça va ?", LangCode.fra_Latn, True),
    ("Hello world!", LangCode.eng_Latn, True),
    ("مرحبا بالعالم", LangCode.ary_Arab, True),
    ("Test avec des chiffres 123", LangCode.fra_Latn, True),
    
    # Cas invalides
    ("тест cyrillique", LangCode.fra_Latn, False), # Cyrillique en source latine
    ("مرحبا arabe", LangCode.fra_Latn, False),    # Arabe en source latine
    ("Hello latin", LangCode.ary_Arab, False),    # Latin en source arabe
])
def test_script_validation(texte, src, is_valid):
    """
    Vérifie que la validation du script fonctionne pour différents cas.
    Ce test couvre les deux branches du `if src in (...)` et le `if not pattern.match(...)`.
    """
    if is_valid:
        try:
            TexteInput(texte=texte, src_lang=src)
        except ValueError:
            pytest.fail(f"Validation a échoué pour un cas valide : texte='{texte}', src='{src.value}'")
    else:
        with pytest.raises(ValueError, match="Caractères interdits détectés"):
            TexteInput(texte=texte, src_lang=src)
