from __future__ import annotations

from functools import lru_cache

from app.services.rag import RAGEngine


@lru_cache(maxsize=1)
def get_rag_engine() -> RAGEngine:
    return RAGEngine()
