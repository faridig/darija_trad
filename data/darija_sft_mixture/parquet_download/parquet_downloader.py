import os
import logging
from io import BytesIO
from dotenv import load_dotenv
from huggingface_hub import hf_hub_download
from azure.storage.blob import BlobServiceClient
import requests

class DarijaParquetUploader:
    """
    Télécharge dynamiquement les fichiers Parquet du dataset Darija
    depuis Hugging Face et les envoie directement sur Azure Blob Storage.
    """

    def __init__(self):
        # 1. Charger les variables d'environnement
        load_dotenv()

        self.hf_token = os.getenv("HUGGINGFACE_TOKEN")
        self.dataset_id = "MBZUAI-Paris/Darija-SFT-Mixture"

        self.azure_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.azure_container_name = os.getenv("AZURE_CONTAINER_NAME")
        print("Connection string Azure :", self.azure_connection_string)

        # 2. Initialiser le client Azure
        self.blob_service_client = BlobServiceClient.from_connection_string(self.azure_connection_string)
        self.container_client = self.blob_service_client.get_container_client(self.azure_container_name)

        # 3. Logger
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def get_parquet_files(self):
        """
        Récupère la liste réelle des fichiers .parquet depuis la section 'siblings'.
        """
        api_url = f"https://huggingface.co/api/datasets/{self.dataset_id}"
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        response = requests.get(api_url, headers=headers)
        info = response.json()

        # Filtrer les vrais fichiers .parquet dans 'siblings'
        parquet_files = [
            f["rfilename"] for f in info.get("siblings", [])
            if f["rfilename"].endswith(".parquet")
        ]

        return parquet_files


    def stream_to_azure(self, file_name):
        """
        Télécharge un fichier Parquet en mémoire et l'envoie sur Azure Blob Storage.
        """
        self.logger.info(f"📥 Téléchargement et envoi de {file_name}")

        # Télécharger dans un flux mémoire
        file_stream = BytesIO()
        local_path = hf_hub_download(
            repo_id=self.dataset_id,
            filename=file_name,
            repo_type="dataset",
            token=self.hf_token
        )
        with open(local_path, "rb") as f:
            file_stream.write(f.read())
        file_stream.seek(0)

        # Envoi sur Azure
        blob_client = self.container_client.get_blob_client(file_name)
        blob_client.upload_blob(file_stream, overwrite=True)

        self.logger.info(f"✅ {file_name} envoyé sur Azure avec succès.")

    def run(self):
        """
        Orchestration : récupère la liste des fichiers et les envoie sur Azure.
        """
        self.logger.info("🚀 Démarrage du transfert des fichiers Parquet")
        files = self.get_parquet_files()
        for file_name in files:
            self.stream_to_azure(file_name)
        self.logger.info("🎉 Tous les fichiers ont été transférés.")


# Point d'entrée
if __name__ == "__main__":
    uploader = DarijaParquetUploader()
    uploader.run()
