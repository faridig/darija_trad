# Fichier : api/data_api/schemas.py (Version Corrigée avec Exemples en Arabe)

from pydantic import BaseModel, ConfigDict, field_validator, constr
from typing import Literal, Optional
from datetime import datetime

# --- Définition des Types Personnalisés ---
# On définit ici un type `LangCode` qui ne peut accepter que ces trois valeurs.
# Pydantic et FastAPI l'utiliseront pour la validation automatique.
LangCode = Literal["fr", "en", "dr"]

# ==============================================================================
# === SCHÉMAS POUR LES TRADUCTIONS ===
# ==============================================================================

class TranslationBase(BaseModel):
    """
    Ce schéma de base définit les champs communs à toutes les opérations
    sur une traduction. Il sert de fondation pour les autres schémas.
    """
    source_lang: LangCode
    # `constr` permet d'ajouter des contraintes : ici, une longueur min/max.
    source_text: constr(min_length=1, max_length=500)
    target_lang: LangCode
    target_text: constr(min_length=1, max_length=500)

    # --- Validateur personnalisé ---
    @field_validator("target_lang")
    @classmethod
    def source_diff_target(cls, v, info):
        """
        Cette fonction de validation métier s'assure qu'on ne peut pas
        soumettre une traduction d'une langue vers elle-même.
        Pydantic l'exécute automatiquement.
        """
        if v == info.data.get("source_lang"):
            raise ValueError("La langue source et la langue cible doivent être différentes.")
        return v

# --- Schémas Spécifiques qui héritent de TranslationBase ---

class TranslationCreate(TranslationBase):
    """
    Ce schéma est utilisé pour la validation des données lors de la CRÉATION
    d'une traduction (endpoint `POST /translations`). Il hérite de toutes
    les règles de TranslationBase.
    """
    # ================================================================
    # ===> AJOUT D'UN EXEMPLE POUR LA DOCUMENTATION OPENAPI <=========
    # ================================================================
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_lang": "fr",
                "source_text": "Où est la gare, s'il vous plaît ?",
                "target_lang": "dr",
                "target_text": "فين كاينة المحطة عافاك؟"
            }
        }
    )
    # ================================================================


class TranslationUpdate(TranslationBase):
    """
    Ce schéma est utilisé pour la validation des données lors de la MISE À JOUR
    d'une traduction (endpoint `PUT /translations/{id}`).
    """
    # ================================================================
    # ===> AJOUT D'UN EXEMPLE POUR LA DOCUMENTATION OPENAPI <=========
    # ================================================================
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_lang": "en",
                "source_text": "Thank you very much",
                "target_lang": "dr",
                "target_text": "شكرا بزاف"
            }
        }
    )
    # ================================================================


class Translation(TranslationBase):
    """
    Ce schéma définit la structure des données qui sont RETOURNÉES par l'API.
    Il inclut l'ID de la traduction, qui est généré par la base de données.
    """
    id: int
    # Permet à Pydantic de créer ce schéma à partir d'un objet de base de données (SQLAlchemy).
    model_config = ConfigDict(from_attributes=True)
    
# ==============================================================================
# === SCHÉMAS POUR LES UTILISATEURS ===
# ==============================================================================

class UserBase(BaseModel):
    """Schéma de base pour un utilisateur, contient les champs communs."""
    username: str = constr(strip_whitespace=True, min_length=3, max_length=50)

class UserCreate(UserBase):
    """
    Schéma pour la CRÉATION d'un utilisateur (endpoint `POST /register`).
    Il attend un mot de passe avec une longueur minimale de 8 caractères.
    """
    password: str = constr(min_length=8)

    # ================================================================
    # ===> AJOUT D'UN EXEMPLE POUR LA DOCUMENTATION OPENAPI <=========
    # ================================================================
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "nouveau_user",
                "password": "motdepassesecurise"
            }
        }
    )
    # ================================================================


class User(UserBase):
    """
    Schéma pour les données d'utilisateur RETOURNÉES par l'API.
    Il est conçu pour la sécurité : il n'inclut JAMAIS le mot de passe,
    même pas le hash.
    """
    id: int
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)