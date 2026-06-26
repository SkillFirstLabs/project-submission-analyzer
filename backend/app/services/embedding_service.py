import os
import time
import logging
from langchain_google_genai import GoogleGenerativeAIEmbeddings

logger = logging.getLogger("project_analyzer")

def get_embedding_model():
    api_key = os.getenv("GOOGLE_API_KEY")
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=api_key,
    )