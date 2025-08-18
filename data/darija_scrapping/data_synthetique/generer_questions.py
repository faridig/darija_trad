# ==============================================================================
# SCRIPT DE GÉNÉRATION DE DONNÉES SYNTHÉTIQUES
# ==============================================================================
#
# OBJECTIF :
# Ce script crée un corpus de phrases sources de haute qualité et spécifiques
# à un domaine (le tourisme au Maroc). Il utilise un Grand Modèle de Langage (LLM)
# pour générer des questions et affirmations réalistes, qui serviront ensuite
# de base pour le processus de web scraping.
#
# TECHNOLOGIE CLÉ :
# - OpenAI API : Accès programmatique au modèle GPT-4o-mini pour la génération de texte.
# - Prompt Engineering : Conception soignée des instructions données au LLM pour
#   contrôler la qualité, le style et le contenu du texte généré.
# - Pandas & OpenPyXL : Pour structurer et sauvegarder les données générées
#   dans un format Excel propre et facilement utilisable.
#
# COMPÉTENCE RNCP VALIDÉE :
# - C1 : Ce script est une étape préliminaire cruciale à l'extraction de données.
#   Il démontre la capacité à construire un jeu de données source pertinent
#   avant même l'étape de scraping.
#
# ==============================================================================

import os
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
import time
import openpyxl

# Charger les variables d'environnement (notamment OPENAI_API_KEY)
load_dotenv()

class GenerateurQuestions:
    """
    Classe encapsulant la logique de génération de phrases via l'API OpenAI.
    """
    def __init__(self):
        """
        Initialise le client OpenAI et s'assure que la clé API est disponible.
        Lève une exception si la configuration est manquante pour un fail-fast propre.
        """
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("La clé API OpenAI n'est pas définie dans le fichier .env")
        self.client = OpenAI(api_key=api_key)

    def generer_questions(self, langue: str, nombre_questions: int = 1000) -> list:
        """
        Génère une liste de questions/affirmations en interagissant avec l'API OpenAI.
        Le processus est optimisé pour gérer un grand nombre de générations par lots.

        Args:
            langue (str): Code de la langue ('fr' ou 'en').
            nombre_questions (int): Le nombre total de phrases à générer.

        Returns:
            list: Une liste de chaînes de caractères, chaque chaîne étant une phrase générée.
        """
        questions = []
        batch_size = 20  # Nombre de phrases à demander par appel API pour optimiser les coûts et le temps.
        nombre_batches = (nombre_questions + batch_size - 1) // batch_size

        # --- Section de Prompt Engineering ---
        # La qualité de la sortie du LLM dépend directement de la qualité de l'entrée.
        # Ces prompts sont conçus pour être très spécifiques.
        prompts = {
            'fr': (
                "Génère {batch_size} questions ou affirmations variées et naturelles qu'un touriste français pourrait poser ou exprimer lors d'une visite au Maroc. "
                "Les phrases doivent couvrir divers aspects du tourisme (culture, transport, gastronomie, hébergement, prix, directions, etc.). "
                "Il est impératif que ces phrases respectent les us et coutumes du Maroc, en reconnaissant que le Sahara Occidental fait partie intégrante du Maroc et en respectant la monarchie marocaine. "
                "\n\nContrainte de style : "
                "Adopte un ton détendu, convivial et conversationnel, et n'hésite pas à intégrer une pointe d'humour lorsque cela est pertinent. "
                "Utilise un langage simple, direct et authentique, avec des expressions courantes. "
                "\n\nFormat de sortie : "
                "Ne renvoie qu'une liste de phrases, une par ligne, sans explications ni numérotation."
            ),
            'en': (
                "Generate {batch_size} varied and natural questions or statements that an English-speaking tourist might ask or express when visiting Morocco. "
                "The sentences should cover various aspects of tourism (culture, transportation, food, accommodation, prices, directions, etc.). "
                "It is essential that these sentences respect Moroccan customs, including recognizing that Western Sahara is an integral part of Morocco and respecting the Moroccan monarchy. "
                "\n\nStyle constraints: "
                "Adopt a relaxed, friendly and conversational tone, and feel free to include a touch of humor when appropriate. "
                "Use simple, direct, and authentic language with common expressions. "
                "\n\nOutput format: "
                "Return only a list of sentences, one per line, without explanations or numbering."
            )
        }
        # --- Fin de la section de Prompt Engineering ---

        # Boucle sur les lots pour atteindre le nombre total de questions souhaité.
        for i in range(nombre_batches):
            print(f"\n🔄 Génération du batch {i+1}/{nombre_batches} pour la langue '{langue}'")
            try:
                # Appel à l'API OpenAI
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini", # Choix d'un modèle rapide et efficace pour cette tâche.
                    messages=[
                        {"role": "system", "content": "Tu es un expert en tourisme au Maroc."},
                        {"role": "user", "content": prompts[langue].format(batch_size=min(batch_size, nombre_questions - len(questions)))}
                    ],
                    temperature=0.8, # Un peu de créativité, mais pas trop pour rester réaliste.
                    max_tokens=2000
                )
                
                # Traitement de la réponse brute de l'API
                nouvelles_questions = response.choices[0].message.content.strip().split('\n')
                # Nettoyage pour supprimer les lignes vides ou les artefacts potentiels.
                nouvelles_questions = [q.strip() for q in nouvelles_questions if q.strip()]
                
                questions.extend(nouvelles_questions)
                print(f"✅ {len(nouvelles_questions)} phrases générées avec succès.")
                
                # Pause de politesse pour respecter les limites de l'API et éviter les erreurs.
                time.sleep(2)
            except Exception as e:
                print(f"❌ Erreur lors de la génération du batch : {str(e)}")
                continue # En cas d'erreur sur un batch, on passe au suivant.

        return questions[:nombre_questions]

    def sauvegarder_xlsx(self, questions: list, langue: str):
        """
        Structure les données générées dans un DataFrame Pandas et les sauvegarde
        dans un fichier Excel formaté.

        Args:
            questions (list): La liste des phrases générées.
            langue (str): Le code de la langue pour nommer le fichier de sortie.
        """
        noms_fichiers = {
            'fr': 'questions_fr_maroc.xlsx',
            'en': 'questions_en_morocco.xlsx'
        }
        
        # Création d'un DataFrame structuré
        df = pd.DataFrame({
            'id': range(1, len(questions) + 1),
            'Questions ou Affirmations': questions,
            'langue': [langue] * len(questions)
        })
        
        # Sauvegarde et mise en forme du fichier Excel
        chemin_fichier = os.path.join(os.path.dirname(__file__), noms_fichiers[langue])
        with pd.ExcelWriter(chemin_fichier, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Questions')
            
            # Mise en forme pour une meilleure lisibilité
            worksheet = writer.sheets['Questions']
            worksheet.column_dimensions['A'].width = 10
            worksheet.column_dimensions['B'].width = 60
            worksheet.column_dimensions['C'].width = 15
            worksheet.auto_filter.ref = worksheet.dimensions
            for cell in worksheet[1]: # Mise en gras de la ligne d'en-tête
                cell.font = openpyxl.styles.Font(bold=True)
                cell.fill = openpyxl.styles.PatternFill(start_color="E0E0E0", end_color="E0E0E0", fill_type="solid")
                
        print(f"\n✅ Données sauvegardées et formatées dans : {noms_fichiers[langue]}")


def main():
    """
    Fonction principale qui orchestre le processus de génération pour chaque langue.
    """
    generateur = GenerateurQuestions()
    
    print("\n--- Démarrage de la génération de données synthétiques ---")
    
    # Génération pour le français
    print("\n🇫🇷 Génération des phrases en français...")
    questions_fr = generateur.generer_questions('fr')
    generateur.sauvegarder_xlsx(questions_fr, 'fr')
    
    # Génération pour l'anglais
    print("\n🇬🇧 Génération des phrases en anglais...")
    questions_en = generateur.generer_questions('en')
    generateur.sauvegarder_xlsx(questions_en, 'en')

# ==============================================================================
# POINT D'ENTRÉE DU SCRIPT
# ==============================================================================
if __name__ == "__main__":
    main()
    print("\n🎉 Processus de génération de données synthétiques terminé.")