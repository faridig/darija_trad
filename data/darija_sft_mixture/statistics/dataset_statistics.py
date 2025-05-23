import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
import requests

class DarijaStatsAPI:
    """
    Classe pour récupérer et analyser les statistiques du dataset Darija
    via l'API Hugging Face, et les sauvegarder en JSON.
    """

    def __init__(self, stats_dir: Path):
        load_dotenv()
        self.token = os.getenv('HUGGINGFACE_TOKEN')

        self.dataset_id = "MBZUAI-Paris/Darija-SFT-Mixture"
        self.api_url = f"https://huggingface.co/api/datasets/{self.dataset_id}"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }

        self.stats_dir = stats_dir
        self.logger = logging.getLogger(__name__)

    def get_dataset_info(self):
        response = requests.get(self.api_url, headers=self.headers)
        info = response.json()

        files_url = f"{self.api_url}/parquet"
        files_response = requests.get(files_url, headers=self.headers)
        info['files'] = files_response.json() if files_response.status_code == 200 else []

        return info

    def prepare_stats(self, info):
        card_data = info.get('cardData', {})

        return {
            "dataset": {
                "nom": info.get('id'),
                "auteur": info.get('author'),
                "description": info.get('description', ''),
                "licence": card_data.get('license'),
                "mis_à_jour": info.get('lastModified'),
                "accès_restreint": info.get('gated', False),
                "désactivé": info.get('disabled', False),
                "popularité": {
                    "téléchargements": info.get('downloads', 0),
                    "likes": info.get('likes', 0)
                },
                "tags": info.get('tags', []),
                "métriques": card_data.get('metrics', [])
            },
            "contenu": {
                "tâches": card_data.get('task_categories', []),
                "taille": card_data.get('size_categories', []),
                "format": "Parquet",
                "fichiers": {
                    "nombre": len(info.get('files', [])),
                    "liste": info.get('files', [])
                },
                "fichiers_raw": info.get('siblings', [])
            }
        }

    def save_results(self, stats):
        stats_file = self.stats_dir / "dataset_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        self.logger.info("Statistiques sauvegardées en JSON")
        return True

    def run(self):
        self.logger.info("Analyse des statistiques du dataset")
        info = self.get_dataset_info()
        stats = self.prepare_stats(info)
        return self.save_results(stats)

# Point d'entrée
if __name__ == "__main__":
    output_dir = Path(".")
    output_dir.mkdir(parents=True, exist_ok=True)
    api = DarijaStatsAPI(output_dir)
    api.run()
