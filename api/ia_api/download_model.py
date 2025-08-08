# api/ia_api/download_model.py
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import sys

# Le nom de votre modèle final et fusionné sur le Hub.
MERGED_MODEL_ID = "Farid59/nllb-darija-fr_eng"

def main():
    """
    Script pour télécharger et mettre en cache le modèle fusionné
    lors de la construction de l'image Docker.
    """
    print(f"--- Démarrage de la mise en cache du modèle fusionné ---")
    print(f"Modèle à télécharger : {MERGED_MODEL_ID}")

    try:
        # Télécharger et mettre en cache le tokenizer et le modèle.
        # Le simple fait de les charger les met dans le cache de Hugging Face.
        AutoTokenizer.from_pretrained(MERGED_MODEL_ID)
        AutoModelForSeq2SeqLM.from_pretrained(MERGED_MODEL_ID)

        print("--- Modèle et tokenizer mis en cache avec succès ---")

    except Exception as e:
        print(f"❌ Une erreur est survenue lors du téléchargement : {e}")
        # Quitte avec un code d'erreur pour faire échouer le build Docker
        sys.exit(1)

if __name__ == "__main__":
    main()