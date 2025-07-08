# api/ia_api/routers/generation.py

from fastapi import APIRouter, Depends, HTTPException, status
from ..schemas import TexteInput, TexteOutput
from ..model import LLMTranslator
from database.core.auth import verify_jwt_token

router = APIRouter(tags=["IA"])

# Instanciation globale de notre traducteur
translator = LLMTranslator()

@router.post(
    "/generer",
    response_model=TexteOutput,
    status_code=status.HTTP_200_OK
)
def generer_texte(
    input: TexteInput,
    utilisateur=Depends(verify_jwt_token)
):
    try:
        reponse = translator.traiter(
            input.texte,
            src_lang=input.src_lang,
            tgt_lang=input.tgt_lang
        )
        return TexteOutput(reponse=reponse)
    except Exception:
        # Cachez les détails internes
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")
