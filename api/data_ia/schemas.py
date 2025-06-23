from pydantic import BaseModel, Field, validator
import re

class TexteInput(BaseModel):
    # On impose une longueur minimale de 1 et un maximum de 200 mots
    texte: str = Field(
        ..., 
        min_length=1, 
        max_length=200,
        description="Texte à traduire (1 à 200 mots, caractères limités)"
    )

    @validator('texte')
    def strip_and_validate_chars(cls, v: str) -> str:
        # 1) Strip des espaces autour
        v = v.strip()

        # 2) Vérifier qu'il ne dépasse pas 200 mots
        n_mots = len(v.split())
        if n_mots < 1 or n_mots > 200:
            raise ValueError(f"Le texte doit contenir entre 1 et 200 mots (actuellement {n_mots}).")

        # 3) Autoriser uniquement ces caractères : lettres (+accents), chiffres, espaces et ponctuation basique
        pattern = re.compile(r'^[\wÀ-ž0-9 ,\.\?!\'"-]+$')
        if not pattern.match(v):
            raise ValueError(
                "Caractères interdits détectés : n’autorisez que lettres, chiffres, espaces, "
                "virgule, point, ?, !, apostrophe, guillemet, tiret."
            )
        return v

class TexteOutput(BaseModel):
    reponse: str