# tests/api_ia/locustfile.py

from locust import HttpUser, task, between
from dotenv import load_dotenv
import os
import json

# Charger les variables depuis .env
load_dotenv()
USERNAME = os.getenv("ADMIN_USERNAME")
PASSWORD = os.getenv("ADMIN_PASSWORD")

class UserBehavior(HttpUser):
    wait_time = between(1, 2)
    token = None

    def on_start(self):
        """Authentifie l'utilisateur et récupère un JWT valide."""
        # --- DÉBUT DE LA CORRECTION ---
        # On passe les données directement comme un formulaire encodé,
        # et on enlève l'en-tête Content-Type car le client le mettra automatiquement.
        response = self.client.post(
            "/login",
            data={
                "username": USERNAME,
                "password": PASSWORD
            }
            # Il n'est généralement pas nécessaire de spécifier le header Content-Type
            # car le client `requests` (utilisé par Locust) est assez intelligent
            # pour le mettre à `application/x-www-form-urlencoded` quand on passe un dict à `data`.
        )
        # --- FIN DE LA CORRECTION ---

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

        payload = {
            "texte": "je veux manger un couscous",
            "src_lang": "fra_Latn",
            "tgt_lang": "ary_Arab"
        }

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        # Pour les requêtes JSON, on utilise l'argument `json` et non `data`
        self.client.post("/generer", json=payload, headers=headers)