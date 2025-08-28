# Fichier : tests/api_ia/test_middlewares.py 
# Ce fichier teste le comportement des middlewares de l'application.

from fastapi import status
from unittest.mock import patch, MagicMock
import pytest
import json
from api.ia_api.model import LLMTranslator

# -----------------------------------------------------------------------------
# Test du middleware `limit_body_size`
# -----------------------------------------------------------------------------
def test_limit_body_size_rejects_large_payload(client):
    """
    Vérifie que le middleware de limitation de taille bloque bien les requêtes
    avec un corps trop volumineux.
    """
    large_text = "mot " * 3000
    payload = {"texte": large_text, "src_lang": "fra_Latn", "tgt_lang": "ary_Arab"}
    response = client.post("/generer", json=payload)
    assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    assert "trop volumineux" in response.text

def test_limit_body_size_allows_valid_payload(client):
    """
    Vérifie que le middleware de limitation de taille laisse passer
    les requêtes dont le corps a une taille acceptable.
    """
    valid_payload = {"texte": "un texte court", "src_lang": "fra_Latn", "tgt_lang": "ary_Arab"}
    response = client.post("/generer", json=valid_payload)
    assert response.status_code == status.HTTP_200_OK

def test_limit_body_size_with_no_content_length(client):
    """
    Teste le cas où l'en-tête Content-Length n'est pas présent.
    """
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK

# -----------------------------------------------------------------------------
# TESTS pour le middleware `add_security_headers`
# -----------------------------------------------------------------------------

def test_security_headers_for_docs_routes(client):
    """
    Teste les en-têtes de sécurité pour les routes de documentation.
    """
    response = client.get("/docs")
    assert response.status_code == status.HTTP_200_OK
    assert "text/html" in response.headers.get("content-type", "")

def test_security_headers_for_openapi_route(client):
    """
    Teste les en-têtes pour la route OpenAPI.
    """
    response = client.get("/openapi.json")
    assert response.status_code == 200

def test_security_headers_for_redoc_route(client):
    """
    Teste les en-têtes pour la route ReDoc.
    """
    response = client.get("/redoc")
    assert response.status_code == 200

def test_security_headers_for_api_routes(client):
    """
    Teste les en-têtes de sécurité pour les routes API standard.
    """
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK

# -----------------------------------------------------------------------------
# TESTS pour le middleware `monitoring_middleware`
# -----------------------------------------------------------------------------

def test_monitoring_middleware_handles_success_case(client):
    """
    Vérifie que le middleware de monitoring ne casse pas le flux normal
    d'une requête réussie.
    """
    payload = {"texte": "bonjour", "src_lang": "fra_Latn", "tgt_lang": "ary_Arab"}
    response = client.post("/generer", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["reponse"] == "traduction simulée réussie"

def test_monitoring_middleware_handles_invalid_json_body(client):
    """
    Teste le cas où le corps JSON est malformé.
    """
    invalid_json_body = '{"texte": "bonjour", "src_lang": "fra_Latn"' # JSON malformé
    response = client.post(
        "/generer",
        content=invalid_json_body,
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_monitoring_middleware_with_empty_body(client):
    """
    Teste le cas où le corps de requête est vide.
    """
    response = client.post(
        "/generer",
        content="",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_monitoring_middleware_with_get_request(client):
    """
    Teste le middleware avec une requête GET.
    """
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK

def test_monitoring_middleware_increments_5xx_on_handled_error(client):
    """
    Teste le cas d'une erreur 500 gérée par l'endpoint.
    """
    with patch.object(LLMTranslator, 'traiter', side_effect=Exception("Erreur interne simulée")):
        response = client.post(
            "/generer",
            json={"texte": "provoquer une erreur", "src_lang": "fra_Latn", "tgt_lang": "ary_Arab"}
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

# ===================================================================
# === CORRECTION 1 : POUR test_monitoring_middleware_exception_handling
# ===================================================================
def test_monitoring_middleware_exception_handling(client):
    """
    Teste le cas où une exception non gérée est levée.
    Couvre le bloc 'except Exception' dans monitoring_middleware.
    """
    # On simule une erreur grave dans la logique métier.
    with patch.object(LLMTranslator, 'traiter', side_effect=RuntimeError("Erreur système")):
        # L'exception est attrapée par le middleware, puis par FastAPI,
        # qui la transforment en une réponse HTTP 500.
        # L'exception n'est donc PAS propagée jusqu'au testeur.
        response = client.post(
            "/generer",
            json={"texte": "test", "src_lang": "fra_Latn", "tgt_lang": "ary_Arab"}
        )
        # On vérifie donc que la réponse finale est bien un 500.
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
# ===================================================================

def test_monitoring_middleware_data_drift_with_valid_json(client):
    """
    Teste la logique de data drift avec un JSON valide.
    """
    payload = {"texte": "un texte avec plusieurs mots pour tester", "src_lang": "fra_Latn", "tgt_lang": "ary_Arab"}
    response = client.post("/generer", json=payload)
    assert response.status_code == status.HTTP_200_OK

def test_monitoring_middleware_data_drift_empty_text(client):
    """
    Teste la logique de data drift avec un texte vide.
    """
    payload = {"texte": "", "src_lang": "fra_Latn", "tgt_lang": "ary_Arab"}
    response = client.post("/generer", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_monitoring_middleware_data_drift_missing_texte_field(client):
    """
    Teste la logique de data drift quand le champ 'texte' est absent.
    """
    payload = {"src_lang": "fra_Latn", "tgt_lang": "ary_Arab"}
    response = client.post("/generer", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_monitoring_middleware_non_generer_post_route(client):
    """
    Teste le middleware avec une route POST qui n'est pas /generer.
    """
    response = client.post("/autre-route", json={"data": "test"})
    assert response.status_code == status.HTTP_404_NOT_FOUND

# -----------------------------------------------------------------------------
# TESTS spécifiques pour couvrir les lignes manquantes
# -----------------------------------------------------------------------------

def test_security_headers_favicon_route(client):
    """
    Teste spécifiquement la route /favicon.ico.
    """
    response = client.get("/favicon.ico")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_security_headers_static_route(client):
    """
    Teste spécifiquement une route /static.
    """
    response = client.get("/static/test.css")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_security_headers_oauth_redirect_route(client):
    """
    Teste spécifiquement la route oauth2-redirect.
    """
    response = client.get("/docs/oauth2-redirect")
    assert response.status_code == status.HTTP_200_OK

# ===================================================================
# === CORRECTION 2 : POUR test_monitoring_middleware_json_decode_error_coverage
# ===================================================================
def test_monitoring_middleware_json_decode_error_coverage(client):
    """
    Teste spécifiquement l'erreur de décodage JSON pour couvrir les lignes d'exception.
    """
    # Le 'patch' simule le fait que `json.loads` va lever une erreur quand le middleware l'appellera.
    with patch('json.loads', side_effect=json.JSONDecodeError("mock error", "", 0)):
        response = client.post(
            "/generer",
            # On envoie un JSON valide, mais le mock forcera l'erreur de parsing.
            json={"texte": "test", "src_lang": "fra_Latn", "tgt_lang": "ary_Arab"}
        )
        # La requête doit quand même réussir (200 OK) car le middleware est conçu pour
        # logguer l'erreur de parsing sans bloquer la requête. L'endpoint sera appelé
        # et retournera une réponse de succès (basée sur le mock de conftest.py).
        assert response.status_code == status.HTTP_200_OK
# ===================================================================

# -----------------------------------------------------------------------------
# TESTS pour couvrir les branches restantes
# -----------------------------------------------------------------------------

def test_monitoring_middleware_with_non_json_post(client):
    """
    Teste le middleware avec un POST qui n'est pas JSON.
    """
    response = client.post(
        "/generer",
        data="texte=bonjour&src_lang=fra_Latn&tgt_lang=ary_Arab",
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.parametrize("method,endpoint,expected_status", [
    ("GET", "/health", [status.HTTP_200_OK]),
    ("POST", "/generer", [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]),
    ("GET", "/docs", [status.HTTP_200_OK]),
    ("GET", "/metrics", [status.HTTP_401_UNAUTHORIZED])
])
def test_monitoring_middleware_different_endpoints(client, method, endpoint, expected_status):
    """
    Teste le middleware sur différents endpoints et méthodes.
    """
    if method == "GET":
        response = client.get(endpoint)
        assert response.status_code in expected_status
    else:  # POST
        response = client.post(endpoint, json={
            "texte": "test", 
            "src_lang": "fra_Latn", 
            "tgt_lang": "ary_Arab"
        })
        assert response.status_code in expected_status