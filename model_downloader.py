# model_downloader.py (or at the top of main.py)
import os
import zipfile
from azure.storage.blob import BlobServiceClient

expected_model_folders = [
    "ai4bharatIndicBERTv2-alpha-SentimentClassification",
    "cardiffnlptwitter-xlm-roberta-base-sentiment",
    "cis-lmuglotlid",
    "oleksiizirka-xlm-roberta-toxicity-classifier"
]

def all_models_present():
    return all(os.path.isdir(folder) for folder in expected_model_folders)

def download_and_unzip_models():
    AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    CONTAINER_NAME = 'ml-models'
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)
    for blob in container_client.list_blobs():
        zip_path = blob.name
        with open(zip_path, 'wb') as f:
            f.write(container_client.download_blob(blob).readall())
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall('.')  # Extract to root
        os.remove(zip_path)

# In your main.py (where FastAPI app is defined)
from fastapi import FastAPI

app = FastAPI()

@app.on_event('startup')
async def startup_event():
    if not all_models_present():
        download_and_unzip_models()
