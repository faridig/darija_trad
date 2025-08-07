# tests/api/ia_api/locustfile.py

from locust import HttpUser, task, between
from dotenv import load_dotenv
import os
import random
import requests

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# ==============================================================================
# === LECTURE DES VARIABLES D'ENVIRONNEMENT ===
# ==============================================================================
USERNAME = os.getenv("ADMIN_USERNAME")
PASSWORD = os.getenv("ADMIN_PASSWORD")

# On lit l'URL de l'API de données depuis la même variable que le frontend
DATA_API_HOST = os.getenv("VITE_DATA_API_BASE_URL")

# Vérification : on s'assure que les variables nécessaires sont bien chargées
if not all([USERNAME, PASSWORD, DATA_API_HOST]):
    print("❌ ERREUR : Une ou plusieurs variables d'environnement sont manquantes.")
    print("   Veuillez vérifier votre fichier .env et vous assurer qu'il contient :")
    print("   - ADMIN_USERNAME")
    print("   - ADMIN_PASSWORD")
    print("   - VITE_DATA_API_BASE_URL")
    exit(1) # On arrête le script si la configuration est incomplète
# ==============================================================================

# Liste de phrases de test pour simuler une charge réaliste
TEST_PHRASES = [
    "Bonjour, comment ça va aujourd'hui ?",
    "Je voudrais un café s'il vous plaît.",
    "Où se trouve la gare la plus proche ?",
    "Quel temps fait-il dehors ?",
    "Merci beaucoup pour votre aide.",
    "Pourriez-vous m'indiquer le chemin pour aller au musée d'art moderne et contemporain ?",
    "Je cherche un bon restaurant qui sert des spécialités locales pas trop chères.",
    "Nous prévoyons de partir en vacances la semaine prochaine si la météo le permet.",
    "Le rapport analyse en détail les fluctuations du marché financier au cours du dernier trimestre.",
    "N'oubliez pas de vérifier que toutes les fenêtres sont bien fermées avant de quitter la maison.",
    "La conférence sur l'intelligence artificielle abordera les dernières avancées en matière de traitement du langage naturel.",
]

class UserBehavior(HttpUser):
    wait_time = between(1, 2)
    token = None

    def on_start(self):
        """
        S'exécute une fois par utilisateur virtuel au démarrage.
        S'authentifie via l'API de Données pour obtenir un token JWT.
        """
        print(f"Tentative de login sur la DATA-API à l'adresse : {DATA_API_HOST}")
        try:
            response = requests.post(
                f"{DATA_API_HOST}/login",
                data={
                    "username": USERNAME,
                    "password": PASSWORD
                },
                timeout=10
            )
            response.raise_for_status()  
            
            self.token = response.json()["access_token"]
            print("✅ Login sur la data-api réussi, token obtenu.")

        except requests.exceptions.RequestException as e:
            print(f"❌ Échec de login sur la data-api : {e}")
            self.token = None

    @task
    def generate_translation(self):
        """
        Tâche principale exécutée en boucle par chaque utilisateur virtuel.
        Envoie des requêtes de traduction à l'API d'IA (définie par --host).
        """
        if not self.token:
            print("Token manquant — requête de traduction sautée")
            return

        random_text = random.choice(TEST_PHRASES)

        payload = {
            "texte": random_text,
            "src_lang": "fra_Latn",
            "tgt_lang": "ary_Arab"
        }

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        self.client.post("/generer", json=payload, headers=headers, name="/generer")