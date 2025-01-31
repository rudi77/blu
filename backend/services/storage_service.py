from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv

load_dotenv()

class AzureStorageService:
    def __init__(self):
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME")

    async def upload_document(self, file_content: bytes, filename: str) -> str:
        """
        Upload document to Azure Blob Storage
        """
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=filename
        )
        await blob_client.upload_blob(file_content, overwrite=True)
        return blob_client.url

    async def get_document(self, filename: str) -> bytes:
        """
        Retrieve document from Azure Blob Storage
        """
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=filename
        )
        return await blob_client.download_blob().readall() 