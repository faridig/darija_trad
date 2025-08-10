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


# === MODIFICATION : ON GARDE UNIQUEMENT LES PHRASES LONGUES ===
# Ces phrases, toutes de plus de 14 mots, sont conçues pour
# simuler un "data drift" en s'écartant des données d'entraînement courtes.
DRIFT_PHRASES = [
    "Pourriez-vous m'indiquer le chemin le plus rapide pour me rendre au musée d'art moderne et contemporain de la ville ?",
    "Le rapport financier analyse en détail les fluctuations importantes du marché des actions au cours du dernier trimestre fiscal de l'année.",
    "N'oubliez surtout pas de vérifier que toutes les lumières et les fenêtres sont bien fermées avant de quitter définitivement la maison.",
    "La conférence sur l'intelligence artificielle abordera les dernières avancées en matière de traitement avancé du langage naturel et de la vision par ordinateur.",
    "L'optimisation des chaînes logistiques mondiales représente un défi majeur pour les entreprises multinationales face aux tensions géopolitiques actuelles.",
    "Je suis à la recherche d'une solution logicielle capable d'intégrer de manière transparente notre système de gestion de la relation client avec notre plateforme d'e-commerce.",
    "Veuillez prendre en considération les implications éthiques et légales avant de déployer tout système de reconnaissance faciale dans les espaces publics.",
    "La mission spatiale a pour objectif principal d'étudier la composition atmosphérique des exoplanètes situées dans la zone habitable de leur étoile.",
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
        random_long_text = random.choice(DRIFT_PHRASES)

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