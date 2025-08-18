# ==============================================================================
# SCRIPT D'ANALYSE PROGRAMMATIQUE DE DATASET HUGGING FACE
# ==============================================================================
#
# OBJECTIF :
# Ce script a pour but d'analyser les métadonnées d'un dataset hébergé sur
# Hugging Face de manière automatisée, avant de lancer un processus de
# téléchargement lourd. Il permet de valider la pertinence et la structure
# de la source de données en amont.
#
# TECHNOLOGIE CLÉ :
# - requests : Pour interagir avec l'API REST de Hugging Face.
# - Hugging Face Hub API : Utilisée pour récupérer les informations structurées
#   d'un dataset.
#
# COMPÉTENCE RNCP VALIDÉE :
# - C1 : Automatiser l’extraction de données depuis un service web (API REST).
#
# ==============================================================================

import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
import requests

class DarijaStatsAPI:
    """
    Classe encapsulant la logique pour récupérer et analyser les statistiques
    du dataset Darija via l'API Hugging Face, et les sauvegarder en JSON.
    """

    def __init__(self, stats_dir: Path):
        """
        Initialise le client d'API et la configuration.

        - Charge les variables d'environnement (notamment le token HF).
        - Définit les URL des endpoints de l'API à interroger.
        - Configure les en-têtes HTTP pour l'authentification.
        """
        load_dotenv()
        self.token = os.getenv('HUGGINGFACE_TOKEN')
        if not self.token:
            raise ValueError("Le token HUGGINGFACE_TOKEN est manquant dans le .env")

        self.dataset_id = "MBZUAI-Paris/Darija-SFT-Mixture"
        self.api_url = f"https://huggingface.co/api/datasets/{self.dataset_id}"
        
        # Les en-têtes sont nécessaires pour s'authentifier auprès de l'API HF.
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }

        self.stats_dir = stats_dir
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        self.logger = logging.getLogger(__name__)

    def get_dataset_info(self):
        """
        Effectue les appels à l'API Hugging Face pour collecter les métadonnées.
        
        Cette méthode interroge deux endpoints distincts :
        1. L'endpoint principal pour les informations générales (auteur, likes, etc.).
        2. L'endpoint '/parquet' pour obtenir la liste spécifique des fichiers Parquet.

        Returns:
            dict: Un dictionnaire contenant les informations fusionnées des deux appels API.
        """
        self.logger.info(f"Interrogation de l'API principale : {self.api_url}")
        response = requests.get(self.api_url, headers=self.headers)
        response.raise_for_status() # Lève une exception si l'appel échoue (ex: 404, 401)
        info = response.json()

        # Appel secondaire pour obtenir des détails sur les fichiers Parquet
        files_url = f"{self.api_url}/parquet"
        self.logger.info(f"Interrogation de l'API des fichiers : {files_url}")
        files_response = requests.get(files_url, headers=self.headers)
        
        # On ajoute la liste des fichiers au dictionnaire principal pour tout centraliser.
        # On gère le cas où l'appel échouerait pour ne pas faire planter le script.
        info['files'] = files_response.json() if files_response.status_code == 200 else []

        return info

    def prepare_stats(self, info: dict) -> dict:
        """
        Structure et formate les données brutes de l'API en un dictionnaire JSON
        clair et lisible.

        Args:
            info (dict): Les données brutes retournées par get_dataset_info().

        Returns:
            dict: Un dictionnaire structuré prêt à être sauvegardé en JSON.
        """
        card_data = info.get('cardData', {}) # La 'card' contient des métadonnées riches

        # Création d'une structure organisée pour le fichier de sortie
        return {
            "dataset": {
                "nom": info.get('id'),
                "auteur": info.get('author'),
                "description": info.get('description', ''),
                "licence": card_data.get('license'),
                "mis_à_jour": info.get('lastModified'),
                "popularité": {
                    "téléchargements": info.get('downloads', 0),
                    "likes": info.get('likes', 0)
                },
                "tags": info.get('tags', [])
            },
            "contenu": {
                "tâches": card_data.get('task_categories', []),
                "taille_catégorie": card_data.get('size_categories', []),
                "format_principal": "Parquet",
                "fichiers_parquet": {
                    "nombre": len(info.get('files', [])),
                    "liste": [f.get('filename') for f in info.get('files', [])]
                }
            }
        }

    def save_results(self, stats: dict) -> bool:
        """
        Sauvegarde le dictionnaire de statistiques formaté dans un fichier JSON.

        Args:
            stats (dict): Le dictionnaire retourné par prepare_stats().

        Returns:
            bool: True si la sauvegarde a réussi.
        """
        stats_file = self.stats_dir / "dataset_stats.json"
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                # ensure_ascii=False est important pour les descriptions contenant des accents
                json.dump(stats, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Statistiques sauvegardées avec succès dans : {stats_file}")
            return True
        except IOError as e:
            self.logger.error(f"Erreur lors de la sauvegarde du fichier JSON : {e}")
            return False

    def run(self):
        """
        Orchestre le processus complet : récupération, préparation, et sauvegarde.
        C'est la méthode publique principale de la classe.
        """
        self.logger.info("Démarrage de l'analyse des statistiques du dataset...")
        try:
            info = self.get_dataset_info()
            stats = self.prepare_stats(info)
            return self.save_results(stats)
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Échec de la communication avec l'API Hugging Face : {e}")
            return False
        except Exception as e:
            self.logger.error(f"Une erreur inattendue est survenue : {e}")
            return False

# ==============================================================================
# POINT D'ENTRÉE DU SCRIPT
# ==============================================================================
if __name__ == "__main__":
    # Ce bloc s'exécute uniquement lorsque le script est lancé directement.
    
    # Définir le répertoire de sortie
    output_dir = Path("./data/darija_sft_mixture/statistics")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Instancier et exécuter le processus
    api_analyzer = DarijaStatsAPI(output_dir)
    api_analyzer.run()