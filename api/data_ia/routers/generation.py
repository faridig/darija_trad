from fastapi import APIRouter, Depends
from ...core.auth import verify_jwt_token
from ..schemas import TexteInput, TexteOutput
from ..model import modele

router = APIRouter(tags=["IA"])

@router.post("/generer", response_model=TexteOutput)
def generer_texte(input: TexteInput, utilisateur=Depends(verify_jwt_token)):
    reponse = modele.traiter(input.texte)
    return TexteOutput(reponse=reponse)
