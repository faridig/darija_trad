from pydantic import BaseModel, ConfigDict, field_validator, constr
from typing import Literal

# Langues supportées : fr = français, en = anglais, dr = darija
LangCode = Literal["fr", "en", "dr"]

class TranslationBase(BaseModel):
    source_lang: LangCode
    source_text: constr(min_length=1, max_length=500)
    target_lang: LangCode
    target_text: constr(min_length=1, max_length=500)

    @field_validator("target_lang")
    @classmethod
    def source_diff_target(cls, v, info):
        """
        Valide que la langue source et la langue cible sont différentes.
        """
        if v == info.data.get("source_lang"):
            raise ValueError("La langue source et la langue cible doivent être différentes.")
        return v

class TranslationCreate(TranslationBase):
    """
    Données requises pour créer une traduction.
    """
    pass

class TranslationUpdate(TranslationBase):
    """
    Données requises pour mettre à jour une traduction.
    """
    pass

class Translation(TranslationBase):
    """
    Modèle de traduction retourné par l'API, incluant l'ID.
    """
    id: int
    model_config = ConfigDict(from_attributes=True)
