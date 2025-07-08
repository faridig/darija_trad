import pytest
from fastapi.testclient import TestClient
from api.ia_api.main import app

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
