# api/data_ia/routers/generation.py

from fastapi import APIRouter, Depends, HTTPException, status
from database.core.auth import verify_jwt_token
from ..schemas import TexteInput, TexteOutput
from ..model import LLMDarija

router = APIRouter(tags=["IA"])

# Instance du modèle
modele = LLMDarija()

@router.post(
    "/generer",
    response_model=TexteOutput,
    status_code=status.HTTP_200_OK
)
def generer_texte(input: TexteInput, utilisateur=Depends(verify_jwt_token)):
    """
    Point de terminaison pour générer une traduction.
    L'input est déjà validé par Pydantic (min/max mots, caractères autorisés).
    """
    try:
        reponse = modele.traiter(input.texte)
        return TexteOutput(reponse=reponse)
    except Exception:
        # Pas de fuite d'info interne
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")
