from pydantic import BaseModel, ConfigDict, field_validator, constr
from typing import Literal, Optional
from datetime import datetime

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
    
class UserBase(BaseModel):
    """Schéma de base pour un utilisateur, contient les champs communs."""
    username: str = constr(strip_whitespace=True, min_length=3, max_length=50)

class UserCreate(UserBase):
    """Schéma pour la création d'un utilisateur. Attend un mot de passe."""
    password: str = constr(min_length=8)

class User(UserBase):
    """
    Schéma pour retourner un utilisateur depuis l'API.
    N'inclut JAMAIS le mot de passe.
    """
    id: int
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    # Permet de créer ce schéma Pydantic à partir d'un objet SQLAlchemy
    model_config = ConfigDict(from_attributes=True)
