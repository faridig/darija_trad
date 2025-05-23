import os
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
import time
import openpyxl
import json

# Charger les variables d'environnement
load_dotenv()

class GenerateurQuestions:
    def __init__(self):
        """Initialise le client OpenAI et charge la clé API depuis le fichier .env."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("La clé API OpenAI n'est pas définie dans le fichier .env")
        self.client = OpenAI(api_key=api_key)

    def generer_questions(self, langue: str, nombre_questions: int = 1000) -> list:
        """
        Génère des questions ou affirmations touristiques dans la langue spécifiée.
        
        Args:
            langue: 'fr' pour français ou 'en' pour anglais.
            nombre_questions: nombre total de questions à générer.
        
        Returns:
            Liste de questions/affirmations.
        """
        questions = []
        batch_size = 20  # Nombre de questions par requête
        nombre_batches = (nombre_questions + batch_size - 1) // batch_size

        # Prompt amélioré selon la langue avec contraintes de contenu et de style
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

        for i in range(nombre_batches):
            print(f"\n🔄 Génération du batch {i+1}/{nombre_batches}")
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Tu es un expert en tourisme au Maroc."},
                        {"role": "user", "content": prompts[langue].format(batch_size=min(batch_size, nombre_questions - len(questions)))}
                    ],
                    temperature=0.8,
                    max_tokens=2000
                )
                # Extraire les questions de la réponse
                nouvelles_questions = response.choices[0].message.content.strip().split('\n')
                nouvelles_questions = [q.strip() for q in nouvelles_questions if q.strip()]
                questions.extend(nouvelles_questions)
                print(f"✅ {len(nouvelles_questions)} questions générées")
                time.sleep(2)  # Pause entre les requêtes
            except Exception as e:
                print(f"❌ Erreur lors de la génération : {str(e)}")
                continue

        return questions[:nombre_questions]

    def determiner_type(self, texte: str) -> str:
        """
        Détermine si le texte est une question ou une affirmation.
        
        Args:
            texte: Le texte à analyser.
            
        Returns:
            'Question' ou 'Affirmation'.
        """
        mots_interrogatifs = ['comment', 'pourquoi', 'quand', 'où', 'qui', 'quel', 'quelle', 'quels', 'quelles', 
                              'combien', 'est-ce', 'what', 'why', 'when', 'where', 'who', 'which', 'how', 'can', 'could']
        texte_lower = texte.lower()
        if ('?' in texte or
            any(texte_lower.startswith(mot) for mot in mots_interrogatifs) or
            any(f" {mot} " in texte_lower for mot in mots_interrogatifs)):
            return 'Question'
        return 'Affirmation'

    def sauvegarder_xlsx(self, questions: list, langue: str):
        """
        Sauvegarde les questions dans un fichier XLSX.
        
        Args:
            questions: Liste des questions/affirmations à sauvegarder.
            langue: 'fr' pour français ou 'en' pour anglais.
        """
        noms_fichiers = {
            'fr': 'questions_fr_maroc.xlsx',
            'en': 'questions_en_morocco.xlsx'
        }
        df = pd.DataFrame({
            'id': range(1, len(questions) + 1),
            'Questions ou Affirmations': questions,
            'langue': [langue] * len(questions)
        })
        chemin_fichier = os.path.join(os.path.dirname(__file__), noms_fichiers[langue])
        with pd.ExcelWriter(chemin_fichier, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Questions')
            worksheet = writer.sheets['Questions']
            worksheet.column_dimensions['A'].width = 10
            worksheet.column_dimensions['B'].width = 60
            worksheet.column_dimensions['C'].width = 15
            worksheet.auto_filter.ref = worksheet.dimensions
            for cell in worksheet[1]:
                cell.font = openpyxl.styles.Font(bold=True)
                cell.fill = openpyxl.styles.PatternFill(start_color="E0E0E0", end_color="E0E0E0", fill_type="solid")
        print(f"\n✅ Questions et affirmations sauvegardées dans {noms_fichiers[langue]}")

def main():
    generateur = GenerateurQuestions()
    
    print("\n🇫🇷 Génération des questions en français...")
    questions_fr = generateur.generer_questions('fr')
    generateur.sauvegarder_xlsx(questions_fr, 'fr')
    
    print("\n🇬🇧 Génération des questions en anglais...")
    questions_en = generateur.generer_questions('en')
    generateur.sauvegarder_xlsx(questions_en, 'en')

if __name__ == "__main__":
    main()
