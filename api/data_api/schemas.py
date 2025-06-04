from pydantic import BaseModel, ConfigDict, field_validator, constr
from typing import Literal

LangCode = Literal["fr", "en", "dr"]

class TranslationBase(BaseModel):
    source_lang: LangCode
    source_text: constr(min_length=1, max_length=500)
    target_lang: LangCode
    target_text: constr(min_length=1, max_length=500)

    @field_validator('target_lang')
    @classmethod
    def source_diff_target(cls, v, info):
        if v == info.data.get("source_lang"):
            raise ValueError("La langue source et la langue cible doivent être différentes.")
        return v

class TranslationCreate(TranslationBase):
    pass

class TranslationUpdate(TranslationBase):
    pass

class Translation(TranslationBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

