# # api/ia_api/routers/generation.py

# """
# Ce module définit le routeur FastAPI pour les fonctionnalités liées à l'IA,
# principalement le point d'entrée pour la traduction de texte.
# """

# from fastapi import APIRouter, Depends, HTTPException, status
# from ..schemas import TexteInput, TexteOutput
# from ..model import LLMTranslator
# from database.core.auth import verify_jwt_token

# # Crée un routeur FastAPI. Cela permet de regrouper les routes liées à l'IA
# # et de les inclure dans l'application principale (main.py).
# # Le tag "IA" sera utilisé pour le regroupement dans la documentation Swagger.
# router = APIRouter(tags=["IA"])

# # Instanciation globale du traducteur.
# # Le traducteur est créé une seule fois au démarrage de l'application pour des raisons d'efficacité.
# # Il sera réutilisé pour chaque requête, évitant ainsi de recharger des configurations
# # ou des modèles à chaque appel.
# translator = LLMTranslator()

# # Déclare un endpoint qui répond aux requêtes HTTP POST sur le chemin "/generer".
# # - response_model=TexteOutput : Indique à FastAPI que la réponse doit suivre la structure du schéma TexteOutput.
# #   Cela garantit une réponse bien formée et l'inclut dans la documentation OpenAPI.
# # - status_code=status.HTTP_200_OK : Définit le code de statut HTTP par défaut en cas de succès.
# @router.post(
#     "/generer",
#     response_model=TexteOutput,
#     status_code=status.HTTP_200_OK
# )
# def generer_texte(
#     input: TexteInput,
#     utilisateur=Depends(verify_jwt_token)
# ):
#     """
#     Endpoint principal pour effectuer une traduction.

#     Cette fonction est protégée et nécessite un token JWT valide pour être exécutée.
#     Elle reçoit le texte et les langues, délègue la traduction au service `LLMTranslator`,
#     et retourne le résultat formaté.

#     Args:
#         input (TexteInput): Le corps de la requête, validé par Pydantic.
#                             Il contient le texte à traduire ainsi que les langues source et cible.
#         utilisateur (dict): Le résultat de la dépendance `verify_jwt_token`.
#                             Si le token est invalide, une exception 401 est levée et ce code n'est jamais atteint.
#                             La variable n'est pas utilisée directement, mais sa présence déclenche la vérification.

#     Raises:
#         HTTPException: Leve une erreur 500 si la traduction échoue pour une raison quelconque.

#     Returns:
#         TexteOutput: Un objet contenant le texte traduit dans le champ "reponse".
#     """
       
#     # Capture de manière sécurisée toute exception inattendue pouvant survenir
#     # lors de l'appel au service de traduction (ex: erreur réseau, API externe en panne).
#     try:
#         # Délègue la logique de traduction au service `translator`.
#         # C'est ici que l'appel à l'API externe (Hugging Face) est effectué.
#         reponse = translator.traiter(
#             input.texte,
#             src_lang=input.src_lang,
#             tgt_lang=input.tgt_lang
#         )
#         # Construit la réponse en utilisant le schéma Pydantic `TexteOutput`.
#         # FastAPI s'occupera de la sérialisation en JSON.
#         return TexteOutput(reponse=reponse)
#     except Exception as e:
#         # On log l'erreur côté serveur pour le débogage, mais on ne l'expose jamais au client.
#         print(f"Une erreur interne est survenue: {e}")

#         # Renvoie une erreur HTTP 500 générique au client.
#         # C'est une bonne pratique de sécurité pour ne pas divulguer les détails
#         # de l'implémentation interne en cas de défaillance.
#         raise HTTPException(status_code=500, detail="Erreur interne du serveur")

# api/ia_api/routers/generation.py

"""
Ce module définit le routeur FastAPI pour les fonctionnalités liées à l'IA,
principalement le point d'entrée pour la traduction de texte.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from ..schemas import TexteInput, TexteOutput
from ..model import LLMTranslator
from database.core.auth import verify_jwt_token
from ..limiter import limiter

# Crée un routeur FastAPI. Cela permet de regrouper les routes liées à l'IA
# et de les inclure dans l'application principale (main.py).
# Le tag "IA" sera utilisé pour le regroupement dans la documentation Swagger.
router = APIRouter(tags=["IA"])


# Instanciation globale du traducteur.
# Le traducteur est créé une seule fois au démarrage de l'application pour des raisons d'efficacité.
# Il sera réutilisé pour chaque requête, évitant ainsi de recharger des configurations
# ou des modèles à chaque appel.
translator = LLMTranslator()

# Déclare un endpoint qui répond aux requêtes HTTP POST sur le chemin "/generer".
# - response_model=TexteOutput : Indique à FastAPI que la réponse doit suivre la structure du schéma TexteOutput.
#   Cela garantit une réponse bien formée et l'inclut dans la documentation OpenAPI.
# - status_code=status.HTTP_200_OK : Définit le code de statut HTTP par défaut en cas de succès.
@router.post(
    "/generer",
    response_model=TexteOutput,
    status_code=status.HTTP_200_OK
)
@limiter.limit("29/minute")  # 9 requêtes par minute par IP
def generer_texte(
    request: Request,  # Ajout de request pour le rate limiting
    input: TexteInput,
    utilisateur=Depends(verify_jwt_token)
):
    """
    Endpoint principal pour effectuer une traduction.

    Cette fonction est protégée et nécessite un token JWT valide pour être exécutée.
    Elle reçoit le texte et les langues, délègue la traduction au service `LLMTranslator`,
    et retourne le résultat formaté.

    Args:
        request (Request): La requête HTTP (requis pour le rate limiting)
        input (TexteInput): Le corps de la requête, validé par Pydantic.
                            Il contient le texte à traduire ainsi que les langues source et cible.
        utilisateur (dict): Le résultat de la dépendance `verify_jwt_token`.
                            Si le token est invalide, une exception 401 est levée et ce code n'est jamais atteint.
                            La variable n'est pas utilisée directement, mais sa présence déclenche la vérification.

    Raises:
        HTTPException: Leve une erreur 500 si la traduction échoue pour une raison quelconque.

    Returns:
        TexteOutput: Un objet contenant le texte traduit dans le champ "reponse".
    """
       
    # Capture de manière sécurisée toute exception inattendue pouvant survenir
    # lors de l'appel au service de traduction (ex: erreur réseau, API externe en panne).
    try:
        # Délègue la logique de traduction au service `translator`.
        # C'est ici que l'appel à l'API externe (Hugging Face) est effectué.
        reponse = translator.traiter(
            input.texte,
            src_lang=input.src_lang,
            tgt_lang=input.tgt_lang
        )
        # Construit la réponse en utilisant le schéma Pydantic `TexteOutput`.
        # FastAPI s'occupera de la sérialisation en JSON.
        return TexteOutput(reponse=reponse)
    except Exception as e:
        # On log l'erreur côté serveur pour le débogage, mais on ne l'expose jamais au client.
        print(f"Une erreur interne est survenue: {e}")

        # Renvoie une erreur HTTP 500 générique au client.
        # C'est une bonne pratique de sécurité pour ne pas divulguer les détails
        # de l'implémentation interne en cas de défaillance.
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")