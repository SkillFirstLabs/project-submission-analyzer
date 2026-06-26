import time
import logging
from typing import List
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from app.services.embedding_service import get_embedding_model

logger = logging.getLogger("project_analyzer")

MAX_RETRIES = 8
INITIAL_BACKOFF = 10  # seconds
BATCH_DELAY = 4  # seconds between batches

def build_vector_store(chunks: List[dict]) -> FAISS:
    """
    Takes code chunks, creates embeddings, and stores them in an in-memory FAISS index.
    Includes retry logic with exponential backoff for rate limiting.
    Processes documents in batches with delays to respect API rate limits.
    """
    embedding_model = get_embedding_model()
    
    documents = [
        Document(
            page_content=chunk["text"],
            metadata={
                "relative_path": chunk["relative_path"],
                "filename": chunk["filename"],
                "chunk_index": chunk["chunk_index"],
            }
        )
        for chunk in chunks
    ]
    
    total_docs = len(documents)
    logger.info(f"Starting embedding of {total_docs} documents")
    
    # Use batch size of 20 with delays to stay within rate limits
    batch_size = 20
    vector_store = None
    total_batches = (len(documents) + batch_size - 1) // batch_size
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        batch_num = i // batch_size + 1
        retries = 0
        
        while retries < MAX_RETRIES:
            try:
                if vector_store is None:
                    vector_store = FAISS.from_documents(batch, embedding_model)
                else:
                    batch_store = FAISS.from_documents(batch, embedding_model)
                    vector_store.merge_from(batch_store)
                logger.info(f"Embedded batch {batch_num}/{total_batches} ({len(batch)} docs)")
                break
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    retries += 1
                    wait_time = INITIAL_BACKOFF * (2 ** (retries - 1))
                    # Cap wait time at 120 seconds
                    wait_time = min(wait_time, 120)
                    logger.warning(f"Rate limited on batch {batch_num}/{total_batches}, retry {retries}/{MAX_RETRIES} in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    raise
        else:
            raise RuntimeError(f"Failed to embed batch {batch_num} after {MAX_RETRIES} retries due to rate limiting. Please try again later or use an API key with higher quota.")
        
        # Delay between batches to avoid hitting rate limits
        if i + batch_size < len(documents):
            time.sleep(BATCH_DELAY)
    
    logger.info(f"Successfully embedded all {total_docs} documents")
    return vector_store

def semantic_search(vector_store: FAISS, query: str, top_k: int = 8) -> List[Document]:
    """
    Runs a similarity search against the vector store.
    """
    return vector_store.similarity_search(query, k=top_k)
