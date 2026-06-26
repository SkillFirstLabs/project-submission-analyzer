import os
import logging
import requests
from typing import List
from langchain_core.embeddings import Embeddings

logger = logging.getLogger("project_analyzer")

class CohereEmbeddings(Embeddings):
    def __init__(self, api_key: str, model: str = "embed-english-v3.0"):
        self.api_key = api_key
        self.model = model
        self.url = "https://api.cohere.com/v1/embed"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        batch_size = 90
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            payload = {
                "texts": batch,
                "model": self.model,
                "input_type": "search_document"
            }
            try:
                response = requests.post(self.url, headers=self.headers, json=payload, timeout=180)
                response.raise_for_status()
                data = response.json()
                embeddings.extend(data["embeddings"])
            except Exception as e:
                logger.error(f"Cohere embedding documents error: {e}")
                raise
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        payload = {
            "texts": [text],
            "model": self.model,
            "input_type": "search_query"
        }
        try:
            response = requests.post(self.url, headers=self.headers, json=payload, timeout=180)
            response.raise_for_status()
            data = response.json()
            return data["embeddings"][0]
        except Exception as e:
            logger.error(f"Cohere embedding query error: {e}")
            raise

def get_embedding_model():
    api_key = os.getenv("COHERE_API_KEY")
    return CohereEmbeddings(
        model="embed-english-v3.0",
        api_key=api_key,
    )