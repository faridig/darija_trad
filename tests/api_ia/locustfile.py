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
        response = self.client.post(
            "/login",
            data={
                "username": USERNAME,
                "password": PASSWORD
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if response.status_code == 200:
            self.token = response.json()["access_token"]
        else:
            print(f"Échec de login ({response.status_code}): {response.text}")
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

        self.client.post("/generer", data=json.dumps(payload), headers=headers)
