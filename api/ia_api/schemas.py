# Fichier : api/ia_api/schemas.py
# Rôle : Ce fichier définit les "schémas" de données pour l'API d'IA.
#        Utilisant Pydantic, il garantit que toutes les données entrantes (requêtes)
#        et sortantes (réponses) sont correctement formatées et validées.
#        C'est la première ligne de défense pour la qualité et la sécurité des données.

from enum import Enum
from pydantic import BaseModel, Field, model_validator
import re

class LangCode(str, Enum):
    """
    Définit les codes de langue exacts acceptés par l'API.
    
    L'utilisation d'une `Enum` (énumération) garantit que seules ces valeurs
    précises sont considérées comme valides par Pydantic, évitant ainsi les
    erreurs de frappe ou les codes non supportés par le modèle de traduction.
    Les codes sont ceux attendus par le modèle NLLB.
    """
    fra_Latn = "fra_Latn" # Français, script Latin
    eng_Latn = "eng_Latn" # Anglais, script Latin
    ary_Arab = "ary_Arab" # Arabe Marocain (Darija), script Arabe

class TexteInput(BaseModel):
    """
    Schéma de validation pour le corps de la requête de l'endpoint `/generer`.
    
    Ce modèle Pydantic est utilisé par FastAPI pour automatiquement valider
    et parser le JSON reçu lors d'un appel `POST /generer`. Si les données
    ne correspondent pas à cette structure ou violent une contrainte, FastAPI
    renverra automatiquement une erreur HTTP 422.
    """
    # Champ pour le texte à traduire.
    # `...` signifie que ce champ est obligatoire.
    texte: str = Field(
        ...,
        min_length=1,     # Le texte ne peut pas être vide.
        max_length=200,   # Limite la longueur pour des raisons de performance et de coût.
        description="Texte à traduire (1 à 200 mots)"
    )
    
    # Champ pour la langue source du texte.
    # `default` indique la valeur utilisée si le client ne fournit pas ce champ.
    src_lang: LangCode = Field(
        default=LangCode.fra_Latn,
        description="Code langue source (fra_Latn, eng_Latn ou ary_Arab)"
    )
    
    # Champ pour la langue cible de la traduction.
    tgt_lang: LangCode = Field(
        default=LangCode.ary_Arab,
        description="Code langue cible (fra_Latn, eng_Latn ou ary_Arab)"
    )

    @model_validator(mode="after")
    def check_text_and_script(cls, model):
        """
        Validateur personnalisé exécuté après la validation standard de Pydantic.
        
        Cette fonction ajoute deux règles de validation métier plus complexes :
        1. Elle vérifie que le nombre de mots se situe dans une plage acceptable.
        2. Elle s'assure que les caractères du texte correspondent au script
           attendu pour la langue source déclarée (ex: pas de caractères arabes
           si la langue source est `fra_Latn`).

        Args:
            model (TexteInput): L'instance du modèle Pydantic en cours de validation.

        Raises:
            ValueError: Si une des règles de validation métier échoue.

        Returns:
            TexteInput: Le modèle validé.
        """
        # On retire les espaces superflus en début et fin de chaîne.
        texte = model.texte.strip()
        src   = model.src_lang

        # --- Règle 1 : Vérifier le nombre de mots ---
        # `texte.split()` découpe la chaîne en une liste de mots.
        n_mots = len(texte.split())
        if not 1 <= n_mots <= 200:
            # Si la condition n'est pas respectée, on lève une exception qui
            # sera interceptée par FastAPI et retournée au client.
            raise ValueError(f"Le texte doit contenir entre 1 et 200 mots (actuellement {n_mots}).")

        # --- Règle 2 : Validation du script (alphabet) en fonction de la langue source ---
        if src in (LangCode.fra_Latn, LangCode.eng_Latn):
            # Expression régulière pour le script Latin :
            # Accepte les lettres de a-z, A-Z, les caractères accentués courants,
            # les chiffres, et une liste de signes de ponctuation.
            pattern = re.compile(r'^[A-Za-zÀ-ÖØ-öø-ž0-9 ,\.\?!\'"-]+$')
            msg = "lettres latines (A-Z, a-z, accents), chiffres, espaces, , . ? ! ' \" -"
        else:  # Cas `ary_Arab`
            # Expression régulière pour le script Arabe :
            # Accepte les caractères de la plage Unicode arabe, les chiffres,
            # et la même ponctuation.
            pattern = re.compile(r'^[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF0-9 ,\.\?!\'"-]+$')
            msg = "lettres arabes, chiffres, espaces, , . ? ! ' \" -"

        # On teste si le texte correspond au pattern défini.
        if not pattern.match(texte):
            raise ValueError(f"Caractères interdits détectés pour {src.value} : autorisez {msg}.")

        # Si toutes les validations passent, on retourne le modèle.
        return model

    # Configuration Pydantic pour enrichir la documentation OpenAPI (Swagger UI).
    model_config = {
        "json_schema_extra": {
            # Fournit un exemple concret qui sera affiché dans la documentation,
            # ce qui facilite grandement le test de l'API.
            "example": {
                "texte": "je veux manger",
                "src_lang": "fra_Latn",
                "tgt_lang": "ary_Arab"
            }
        }
    }

class TexteOutput(BaseModel):
    """
    Schéma de validation pour la réponse de l'endpoint `/generer`.
    
    Ce modèle garantit que la réponse de l'API est toujours un JSON
    structuré contenant une clé "reponse" avec une chaîne de caractères.
    """
    reponse: str