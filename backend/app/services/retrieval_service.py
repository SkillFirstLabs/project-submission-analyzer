from typing import List
from langchain_community.vectorstores import FAISS
from app.services.vector_store import semantic_search

def retrieve_context(vector_store: FAISS, queries: List[str], top_k: int = 5) -> str:
    """
    Runs multiple queries against the vector store, deduplicates matching chunks,
    and returns a formatted context string.
    """
    seen = set()
    all_docs = []
    
    for query in queries:
        results = semantic_search(vector_store, query, top_k=top_k)
        for doc in results:
            key = f"{doc.metadata['relative_path']}:{doc.metadata['chunk_index']}"
            if key not in seen:
                seen.add(key)
                all_docs.append(doc)
                
    context_parts = [doc.page_content for doc in all_docs]
    return "\n\n---\n\n".join(context_parts)
