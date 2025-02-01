from typing import Dict
import httpx
from ..config import get_settings

class BluDeltaService:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.bludelta_service_url
        
    async def analyze_document(self, doc_id: str, prompt: str) -> Dict:
        """
        Send document to BluDeltaService for analysis
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/analyze",
                json={
                    "doc_id": doc_id,
                    "prompt": prompt
                },
                headers={"Authorization": f"Bearer {self.settings.bludelta_api_key}"}
            )
            response.raise_for_status()
            return response.json()

    async def get_document_info(self, doc_id: str) -> Dict:
        """
        Get document metadata from BluDeltaService
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/documents/{doc_id}",
                headers={"Authorization": f"Bearer {self.settings.bludelta_api_key}"}
            )
            response.raise_for_status()
            return response.json() 