from pydantic import BaseModel

class TexteInput(BaseModel):
    texte: str

class TexteOutput(BaseModel):
    reponse: str
