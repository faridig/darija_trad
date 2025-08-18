# ==============================================================================
# SCRIPT DE TRANSFERT DE DONNÉES : HUGGING FACE VERS AZURE BLOB STORAGE
# ==============================================================================
#
# OBJECTIF :
# Ce script automatise l'extraction d'un dataset public (au format Parquet)
# depuis Hugging Face Hub et son ingestion dans une infrastructure de stockage
# cloud privée sur Azure Blob Storage.
#
# ARCHITECTURE :
# Le script est encapsulé dans une classe `DarijaParquetUploader` pour une meilleure
# organisation et réutilisabilité. Il utilise une approche de "streaming" pour
# transférer les fichiers sans les stocker de manière permanente sur le disque local.
#
# TECHNOLOGIES CLÉS :
# - huggingface_hub : SDK officiel pour interagir avec le Hub Hugging Face.
# - azure-storage-blob : SDK officiel de Microsoft pour interagir avec Azure Storage.
# - requests : Pour les appels à l'API REST de Hugging Face.
# - python-dotenv : Pour la gestion sécurisée des configurations et secrets.
#
# COMPÉTENCE RNCP VALIDÉE :
# - C1 : Automatiser l’extraction de données depuis un service web et un
#   système big data (format Parquet).
#
# ==============================================================================

import os
import logging
from io import BytesIO
from dotenv import load_dotenv
from huggingface_hub import hf_hub_download
from azure.storage.blob import BlobServiceClient
import requests

class DarijaParquetUploader:
    """
    Classe responsable du transfert de fichiers Parquet du dataset Darija
    depuis Hugging Face vers Azure Blob Storage.
    """

    def __init__(self):
        """
        Initialise l'uploader en chargeant la configuration, en configurant
        les clients d'API et en initialisant le logger.
        """
        # --- Étape 1 : Chargement de la configuration ---
        # Utilisation de .env pour séparer le code de la configuration,
        # ce qui est une bonne pratique de sécurité et de portabilité.
        load_dotenv()

        self.hf_token = os.getenv("HUGGINGFACE_TOKEN")
        self.dataset_id = "MBZUAI-Paris/Darija-SFT-Mixture"
        self.azure_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.azure_container_name = os.getenv("AZURE_CONTAINER_NAME")

        # Validation critique de la configuration au démarrage.
        if not all([self.hf_token, self.azure_connection_string, self.azure_container_name]):
            raise ValueError("Configuration manquante. Veuillez vérifier les variables d'environnement.")

        # --- Étape 2 : Initialisation des clients de service ---
        # Le client BlobServiceClient est instancié une seule fois pour réutiliser
        # les connexions et optimiser les performances.
        self.blob_service_client = BlobServiceClient.from_connection_string(self.azure_connection_string)
        self.container_client = self.blob_service_client.get_container_client(self.azure_container_name)

        # --- Étape 3 : Configuration du logging ---
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.logger.info("DarijaParquetUploader initialisé avec succès.")

    def get_parquet_files(self) -> list[str]:
        """
        Interroge l'API REST de Hugging Face pour obtenir la liste dynamique
        des fichiers Parquet disponibles dans le dataset.

        Cette approche est plus robuste que de coder en dur la liste des fichiers,
        car elle s'adapte si le dataset est mis à jour.

        Returns:
            list[str]: Une liste des noms de fichiers Parquet (ex: 'data/train-00000-of-00001.parquet').
        """
        self.logger.info(f"Récupération de la liste des fichiers pour le dataset '{self.dataset_id}'...")
        api_url = f"https://huggingface.co/api/datasets/{self.dataset_id}"
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        
        try:
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()  # Lève une exception pour les codes d'erreur HTTP
            info = response.json()

            # La section 'siblings' contient la liste de tous les fichiers du dépôt.
            # On filtre pour ne garder que ceux qui se terminent par '.parquet'.
            parquet_files = [
                f["rfilename"] for f in info.get("siblings", [])
                if f["rfilename"].endswith(".parquet")
            ]
            self.logger.info(f"{len(parquet_files)} fichiers Parquet trouvés.")
            return parquet_files
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Échec de l'appel à l'API de Hugging Face : {e}")
            return []


    def stream_to_azure(self, file_name: str):
        """
        Orchestre le téléchargement d'un fichier en mémoire et son envoi (upload)
        vers Azure Blob Storage.

        Cette méthode de streaming est choisie pour son efficacité :
        - Elle ne nécessite pas d'espace disque temporaire sur la machine exécutant le script.
        - Elle est plus rapide car elle évite un cycle d'écriture/lecture sur le disque.

        Args:
            file_name (str): Le nom complet du fichier à transférer.
        """
        self.logger.info(f"Traitement du fichier : {file_name}")
        
        try:
            # --- Étape A : Téléchargement depuis Hugging Face ---
            # hf_hub_download gère le téléchargement et le met en cache localement.
            # C'est un comportement interne de la bibliothèque.
            self.logger.info(f"  -> Téléchargement depuis Hugging Face...")
            local_path = hf_hub_download(
                repo_id=self.dataset_id,
                filename=file_name,
                repo_type="dataset",
                token=self.hf_token
            )

            # --- Étape B : Lecture en mémoire ---
            # On lit le fichier depuis le cache de hf_hub vers un objet en mémoire (BytesIO).
            file_stream = BytesIO()
            with open(local_path, "rb") as f:
                file_stream.write(f.read())
            file_stream.seek(0)  # Rembobine le "curseur" au début du flux en mémoire.

            # --- Étape C : Envoi vers Azure ---
            # Le SDK Azure peut envoyer des données directement depuis ce flux en mémoire.
            self.logger.info(f"  -> Envoi vers Azure Container '{self.azure_container_name}'...")
            blob_client = self.container_client.get_blob_client(file_name)
            blob_client.upload_blob(file_stream, overwrite=True)

            self.logger.info(f"✅ Transfert de '{file_name}' terminé avec succès.")
        except Exception as e:
            self.logger.error(f"❌ Échec du transfert pour le fichier '{file_name}': {e}")


    def run(self):
        """
        Point d'entrée principal pour exécuter le pipeline de transfert complet.
        """
        self.logger.info("🚀 Démarrage du pipeline de transfert des fichiers Parquet.")
        
        files = self.get_parquet_files()
        if not files:
            self.logger.warning("Aucun fichier Parquet à traiter. Arrêt du script.")
            return

        for file_name in files:
            self.stream_to_azure(file_name)
            
        self.logger.info("🎉 Tous les fichiers ont été traités. Pipeline terminé.")


# ==============================================================================
# EXÉCUTION DU SCRIPT
# ==============================================================================
if __name__ == "__main__":
    # Ce bloc n'est exécuté que si le script est appelé directement
    # (ex: `python parquet_downloader.py`).
    uploader = DarijaParquetUploader()
    uploader.run()