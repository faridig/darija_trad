# generation.py
from fastapi import APIRouter, Depends
from database.core.auth import verify_jwt_token
from ..schemas import TexteInput, TexteOutput

# Import différé pour éviter les circulaires
from ..model import LLMDarija  # Importez la classe, pas l'instance

router = APIRouter(tags=["IA"])

# Créez une instance locale (ou utilisez un singleton)
modele = LLMDarija("llm/nllb-darija-lora-model")  # Chemin à configurer proprement

@router.post("/generer", response_model=TexteOutput)
def generer_texte(input: TexteInput, utilisateur=Depends(verify_jwt_token)):
    reponse = modele.traiter(input.texte)
    return TexteOutput(reponse=reponse)