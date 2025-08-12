# tests/api/ia_api/locustfile.py

from locust import HttpUser, task, between
from dotenv import load_dotenv
import os
import random
import requests

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# ==============================================================================
# === LECTURE DES VARIABLES D'ENVIRONNEMENT (INCHANGÉ) ===
# ==============================================================================
USERNAME = os.getenv("ADMIN_USERNAME")
PASSWORD = os.getenv("ADMIN_PASSWORD")
DATA_API_HOST = os.getenv("VITE_DATA_API_BASE_URL")

if not all([USERNAME, PASSWORD, DATA_API_HOST]):
    print("❌ ERREUR : Variables d'environnement manquantes (ADMIN_USERNAME, ADMIN_PASSWORD, VITE_DATA_API_BASE_URL).")
    exit(1)
# ==============================================================================


PHRASES = [
    "Pourriez-vous m'indiquer " ,
    "Le rapport financier ",
    "N'oubliez surtout ",
]
# ==============================================================================


class UserBehavior(HttpUser):
    wait_time = between(1, 3) # J'ai légèrement augmenté le temps d'attente
    token = None

    def on_start(self):
        """S'authentifie pour obtenir un token JWT (INCHANGÉ)."""
        print(f"Tentative de login sur la DATA-API à l'adresse : {DATA_API_HOST}")
        try:
            response = requests.post(
                f"{DATA_API_HOST}/login",
                data={"username": USERNAME, "password": PASSWORD},
                timeout=10
            )
            response.raise_for_status()
            self.token = response.json()["access_token"]
            print("✅ Login sur la data-api réussi, token obtenu.")
        except requests.exceptions.RequestException as e:
            print(f"❌ Échec de login sur la data-api : {e}")
            self.token = None

    # === MODIFICATION : UNE SEULE TÂCHE FOCALISÉE SUR LE DATA DRIFT ===
    @task
    def generate_drift_translation(self):
        """
        Tâche unique : envoie en continu des requêtes avec des textes plus longs
        que la moyenne d'entraînement pour tester l'alerte DataDriftDetected.
        """
        if not self.token:
            print("Token manquant — requête de traduction sautée")
            return

        # On choisit aléatoirement une phrase longue
        random_long_text = random.choice(PHRASES)

        payload = {
            "texte": random_long_text,
            "src_lang": "fra_Latn",
            "tgt_lang": "ary_Arab"
        }

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        # On envoie la requête à l'API d'IA (définie par --host)
        self.client.post("/generer", json=payload, headers=headers, name="/generer [Drift]")