from __future__ import annotations

from functools import lru_cache

from app.services.embeddings import EmbeddingsService
from app.services.llm import LLMService
from app.services.reranker import Reranker
from app.services.retrieval import RetrievalService
from app.services.vector_store import VectorStore


@lru_cache(maxsize=1)
def get_embeddings_service() -> EmbeddingsService:
    return EmbeddingsService()


@lru_cache(maxsize=1)
def get_vector_store() -> VectorStore:
    return VectorStore()


@lru_cache(maxsize=1)
def get_reranker() -> Reranker:
    return Reranker()


@lru_cache(maxsize=1)
def get_llm_service() -> LLMService:
    return LLMService()


@lru_cache(maxsize=1)
def get_retrieval_service() -> RetrievalService:
    return RetrievalService(
        embeddings=get_embeddings_service(),
        vector_store=get_vector_store(),
        reranker=get_reranker(),
    )
