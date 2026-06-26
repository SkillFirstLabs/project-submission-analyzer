"""
Lightweight RAG over the skill catalog.

Rather than pulling in a heavy framework, we embed each catalog skill once
(skill_name + category), cache the vectors in memory, and expose a
retrieve() function that returns the top-N most relevant catalog skills
for a chunk of code text. This is passed to the Skill Extractor agent as
grounding context — it can ONLY suggest skills that come back from this
index, which enforces the "only suggest skills that exist in the catalog"
rule structurally, not just via prompting.
"""
from __future__ import annotations
import json
import os
from typing import List, Dict, Any
import numpy as np
from openai import OpenAI

_EMBED_MODEL = "text-embedding-3-small"


class SkillCatalogIndex:
    def __init__(self, catalog_path: str, client: OpenAI):
        self.client = client
        with open(catalog_path, "r", encoding="utf-8") as f:
            self.catalog: List[Dict[str, Any]] = json.load(f)
        if not self.catalog:
            raise ValueError("Skill catalog is empty or invalid.")
        self._embeddings: np.ndarray | None = None
        self._build_index()

    def _embed_texts(self, texts: List[str]) -> np.ndarray:
        resp = self.client.embeddings.create(model=_EMBED_MODEL, input=texts)
        vecs = [d.embedding for d in resp.data]
        return np.array(vecs, dtype=np.float32)

    def _build_index(self) -> None:
        texts = [
            f"{item['skill_name']} ({item.get('category', 'General')})"
            for item in self.catalog
        ]
        self._embeddings = self._embed_texts(texts)
        # normalize for cosine similarity via dot product
        norms = np.linalg.norm(self._embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1e-8
        self._embeddings = self._embeddings / norms

    def retrieve(self, code_text: str, top_k: int = 15) -> List[Dict[str, Any]]:
        """Return the top_k catalog skills most relevant to the given code text."""
        if not code_text.strip():
            return self.catalog[:top_k]

        query_vec = self._embed_texts([code_text[:8000]])[0]
        qnorm = np.linalg.norm(query_vec)
        if qnorm > 0:
            query_vec = query_vec / qnorm

        sims = self._embeddings @ query_vec
        top_k = min(top_k, len(self.catalog))
        top_idx = np.argsort(-sims)[:top_k]
        return [self.catalog[i] for i in top_idx]

    def all_skills(self) -> List[Dict[str, Any]]:
        return self.catalog

    def get_by_id(self, skill_id: str) -> Dict[str, Any] | None:
        for item in self.catalog:
            if item["skill_id"] == skill_id:
                return item
        return None

    def get_by_name(self, skill_name: str) -> Dict[str, Any] | None:
        lname = skill_name.lower().strip()
        for item in self.catalog:
            if item["skill_name"].lower() == lname:
                return item
        return None


_index_singleton: SkillCatalogIndex | None = None


def get_skill_index(client: OpenAI) -> SkillCatalogIndex:
    global _index_singleton
    if _index_singleton is None:
        catalog_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skill_catalog.json")
        _index_singleton = SkillCatalogIndex(catalog_path, client)
    return _index_singleton
