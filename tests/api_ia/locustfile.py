# tests/api_ia/locustfile.py

from locust import HttpUser, task, between
from dotenv import load_dotenv
import os
import random # <-- On importe le module 'random' pour faire un choix aléatoire

# Charger les variables depuis .env
load_dotenv()
USERNAME = os.getenv("ADMIN_USERNAME")
PASSWORD = os.getenv("ADMIN_PASSWORD")

# ==============================================================================
# ===> DÉBUT DE LA MODIFICATION <===
# ==============================================================================

# Création d'une liste de phrases de test de longueurs variées.
# Ces longueurs sont choisies pour correspondre à la distribution de vos données d'entraînement.
TEST_PHRASES = [
    # Phrases très courtes (autour de la médiane de 6 mots)
    "Bonjour, comment ça va aujourd'hui ?",      # 5 mots
    "Je voudrais un café s'il vous plaît.",     # 6 mots
    "Où se trouve la gare la plus proche ?",     # 7 mots
    "Quel temps fait-il dehors ?",              # 4 mots
    "Merci beaucoup pour votre aide.",          # 5 mots
    
    # Phrases de longueur moyenne (autour du 75ème percentile de 14 mots)
    "Pourriez-vous m'indiquer le chemin pour aller au musée d'art moderne et contemporain ?", # 13 mots
    "Je cherche un bon restaurant qui sert des spécialités locales pas trop chères.", # 12 mots
    "Nous prévoyons de partir en vacances la semaine prochaine si la météo le permet.", # 13 mots
    
    # Phrases plus longues (pour tester la "longue traîne")
    "Le rapport analyse en détail les fluctuations du marché financier au cours du dernier trimestre.", # 14 mots
    "N'oubliez pas de vérifier que toutes les fenêtres sont bien fermées avant de quitter la maison.", # 15 mots
    "La conférence sur l'intelligence artificielle abordera les dernières avancées en matière de traitement du langage naturel.", # 16 mots
]

# ==============================================================================
# ===> FIN DE LA MODIFICATION <===
# ==============================================================================


class UserBehavior(HttpUser):
    wait_time = between(1, 2)
    token = None

    def on_start(self):
        """Authentifie l'utilisateur et récupère un JWT valide."""
        # Note : Votre code de login est déjà correct, on ne le touche pas.
        response = self.client.post(
            "/login",
            data={
                "username": USERNAME,
                "password": PASSWORD
            }
        )

        if response.status_code == 200:
            self.token = response.json()["access_token"]
            print("✅ Login réussi, token obtenu.")
        else:
            print(f"❌ Échec de login ({response.status_code}): {response.text}")
            self.token = None

    @task
    def generate_translation(self):
        if not self.token:
            print("Token manquant — requête sautée")
            return

        # ==============================================================================
        # ===> DÉBUT DE LA MODIFICATION <===
        # ==============================================================================

        # Choisir une phrase au hasard depuis notre liste à chaque appel
        random_text = random.choice(TEST_PHRASES)

        payload = {
            "texte": random_text, # <-- On utilise la phrase aléatoire
            "src_lang": "fra_Latn",
            "tgt_lang": "ary_Arab"
        }
        
        # ==============================================================================
        # ===> FIN DE LA MODIFICATION <===
        # ==============================================================================

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        # Pour les requêtes JSON, on utilise l'argument `json` et non `data`
        self.client.post("/generer", json=payload, headers=headers)