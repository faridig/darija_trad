# api/ia_api/schemas.py

from enum import Enum
from pydantic import BaseModel, Field, model_validator
import re

class LangCode(str, Enum):
    fra_Latn = "fra_Latn"
    eng_Latn = "eng_Latn"
    ary_Arab = "ary_Arab"

class TexteInput(BaseModel):
    texte: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Texte à traduire (1 à 200 mots)"
    )
    src_lang: LangCode = Field(
        default=LangCode.fra_Latn,
        description="Code langue source (fra_Latn, eng_Latn ou ary_Arab)"
    )
    tgt_lang: LangCode = Field(
        default=LangCode.ary_Arab,
        description="Code langue cible (fra_Latn, eng_Latn ou ary_Arab)"
    )

    @model_validator(mode="after")
    def check_text_and_script(cls, model):
        texte = model.texte.strip()
        src   = model.src_lang

        # 1) Vérifier le nombre de mots
        n_mots = len(texte.split())
        if not 1 <= n_mots <= 200:
            raise ValueError(f"Le texte doit contenir entre 1 et 200 mots (actuellement {n_mots}).")

        # 2) Validation du script selon src_lang
        if src in (LangCode.fra_Latn, LangCode.eng_Latn):
            # On n’autorise que les lettres latines (A-Z, a-z) + étendues accentuées + chiffres + ponctuation
            pattern = re.compile(r'^[A-Za-zÀ-ÖØ-öø-ž0-9 ,\.\?!\'"-]+$')
            msg = "lettres latines (A-Z, a-z, accents), chiffres, espaces, , . ? ! ' \" -"
        else:  # ary_Arab
            pattern = re.compile(r'^[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF0-9 ,\.\?!\'"-]+$')
            msg = "lettres arabes, chiffres, espaces, , . ? ! ' \" -"

        if not pattern.match(texte):
            raise ValueError(f"Caractères interdits détectés pour {src.value} : autorisez {msg}.")

        return model

    class Config:
        json_schema_extra = {
            "example": {
                "texte": "je veux manger",
                "src_lang": "fra_Latn",
                "tgt_lang": "ary_Arab"
            }
        }

class TexteOutput(BaseModel):
    reponse: str
