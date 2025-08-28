# Fichier : tests/api_ia/test_middlewares.py (Version Finale Complète et Commentée)
# Ce fichier teste le comportement des middlewares de l'application.

from fastapi import status, Request
from fastapi.responses import Response
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
import json
from api.ia_api.model import LLMTranslator
# On importe directement les middlewares pour pouvoir les tester de manière isolée (unitaire).
from api.ia_api.middlewares import add_security_headers, monitoring_middleware

# -----------------------------------------------------------------------------
# Test du middleware `limit_body_size`
# -----------------------------------------------------------------------------

def test_limit_body_size_rejects_large_payload(client):
    """
    Vérifie que le middleware de limitation de taille bloque bien les requêtes
    avec un corps trop volumineux (cas d'échec).
    """
    # On crée un payload qui dépasse la limite de 10 Ko définie dans le middleware.
    large_text = "mot " * 3000
    payload = {
        "texte": large_text,
        "src_lang": "fra_Latn",
        "tgt_lang": "ary_Arab"
    }
    
    response = client.post("/generer", json=payload)
    
    # On s'attend à recevoir une erreur 413 "Payload Too Large".
    assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    assert "trop volumineux" in response.text

def test_limit_body_size_allows_valid_payload(client):
    """
    Vérifie que le middleware de limitation de taille laisse passer les requêtes
    dont le corps a une taille acceptable (cas de succès).
    """
    # Ce payload est bien en dessous de la limite de 10 Ko.
    valid_payload = {
        "texte": "un texte court",
        "src_lang": "fra_Latn",
        "tgt_lang": "ary_Arab"
    }
    
    response = client.post("/generer", json=valid_payload)
    
    # Le test crucial est de vérifier que la requête n'a PAS été bloquée (code 200 OK).
    assert response.status_code == status.HTTP_200_OK

def test_limit_body_size_with_no_content_length(client):
    """
    Vérifie le cas où l'en-tête Content-Length n'est pas présent (ex: requête GET).
    Ce test couvre la branche où `content_length` est None dans le middleware.
    """
    response = client.get("/health")
    # La requête doit passer sans erreur.
    assert response.status_code == status.HTTP_200_OK

# -----------------------------------------------------------------------------
# TESTS pour le middleware `add_security_headers`
# -----------------------------------------------------------------------------

def test_security_headers_for_api_routes(client):
    """
    Vérifie que les en-têtes de sécurité stricts sont appliqués aux routes API standard.
    Ce test couvre la branche `else` du middleware (lignes après 79).
    """
    response = client.get("/health")
    assert "Strict-Transport-Security" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"

# ===================================================================
# === CORRECTION 1 : TEST UNITAIRE POUR add_security_headers
# ===================================================================
@pytest.mark.asyncio
async def test_add_security_headers_applies_correct_policy_for_docs():
    """
    Teste de manière isolée que le middleware `add_security_headers` applique
    la bonne politique de sécurité pour une route de documentation.
    Ce test couvre spécifiquement les lignes 52-79 (la branche `if`).
    """
    # 1. On simule un objet `request` dont le chemin correspond à la condition.
    mock_request = MagicMock(spec=Request)
    mock_request.url.path = "/docs"

    # 2. On simule la fonction `call_next` pour qu'elle retourne une réponse de base.
    mock_response = Response(status_code=200)
    mock_call_next = AsyncMock(return_value=mock_response)

    # 3. On appelle le middleware directement avec nos objets simulés.
    response = await add_security_headers(mock_request, mock_call_next)

    # 4. On vérifie que l'en-tête spécifique à la branche 'if' a bien été ajouté.
    assert "Content-Security-Policy" in response.headers
    assert "cdn.jsdelivr.net" in response.headers["Content-Security-Policy"]
# ===================================================================

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
    Teste le cas où le corps JSON est malformé, pour couvrir le `except`
    du parsing JSON dans le middleware.
    """
    invalid_json_body = '{"texte": "bonjour"' # JSON intentionnellement cassé
    response = client.post(
        "/generer",
        content=invalid_json_body,
        headers={"Content-Type": "application/json"}
    )
    # FastAPI intercepte cette erreur en amont et renvoie un 422.
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_monitoring_middleware_increments_5xx_on_handled_error(client):
    """
    Teste qu'une erreur 500 gérée par l'endpoint est bien comptabilisée.
    Ce test couvre la condition `if response.status_code >= 500`.
    """
    # On simule une erreur qui se produit dans la logique de l'endpoint.
    with patch.object(LLMTranslator, 'traiter', side_effect=Exception("Erreur interne simulée")):
        response = client.post(
            "/generer",
            json={"texte": "provoquer une erreur", "src_lang": "fra_Latn", "tgt_lang": "ary_Arab"}
        )
        # L'endpoint attrape l'erreur et renvoie une HTTPException 500.
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

# ===================================================================
# === CORRECTION 2 : TEST UNITAIRE POUR monitoring_middleware
# ===================================================================
@pytest.mark.asyncio
async def test_monitoring_middleware_catches_unhandled_exception():
    """
    Teste de manière isolée que le middleware attrape bien une exception
    non gérée provenant de la chaîne d'appel (par exemple, une panne).
    Ce test couvre spécifiquement le bloc `except Exception as e:` (lignes 168-177).
    """
    # 1. On simule un objet `request` simple.
    mock_request = MagicMock(spec=Request)
    mock_request.method = "POST"
    mock_request.url.path = "/generer"
    # Le `body()` doit être un `async def` qui retourne des bytes.
    mock_request.body = AsyncMock(return_value=b'{}')

    # 2. On simule `call_next` pour qu'il LÈVE une exception, simulant une panne grave.
    mock_call_next = AsyncMock(side_effect=RuntimeError("Panne simulée"))

    # 3. On appelle le middleware et on s'attend à ce qu'il propage l'exception
    #    après l'avoir logguée et comptabilisée.
    with pytest.raises(RuntimeError, match="Panne simulée"):
        await monitoring_middleware(mock_request, mock_call_next)
# ===================================================================