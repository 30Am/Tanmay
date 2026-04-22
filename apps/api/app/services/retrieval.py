from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import Chunk, ContentFormat
from app.services.embeddings import EmbeddingsService
from app.services.reranker import Reranker
from app.services.vector_store import VectorStore

log = get_logger(__name__)


@dataclass
class RetrievalResult:
    chunks: list[Chunk]
    max_similarity: float
    below_threshold: bool


class RetrievalService:
    def __init__(
        self,
        embeddings: EmbeddingsService,
        vector_store: VectorStore,
        reranker: Reranker,
    ) -> None:
        self.embeddings = embeddings
        self.vector_store = vector_store
        self.reranker = reranker
        s = get_settings()
        self.top_candidates = s.retrieval_top_k_candidates
        self.top_final = s.retrieval_top_k_final
        self.confidence_threshold = s.retrieval_confidence_threshold

    async def retrieve(
        self,
        query: str,
        *,
        format_filter: list[ContentFormat] | None = None,
        exclude_sponsored: bool = False,
        top_k_final: int | None = None,
    ) -> RetrievalResult:
        vector = await self.embeddings.embed_query(query)
        candidates = await self.vector_store.search(
            vector,
            limit=self.top_candidates,
            format_filter=format_filter,
            exclude_sponsored=exclude_sponsored,
        )
        max_sim = max((c.score or 0.0 for c in candidates), default=0.0)
        reranked = await self.reranker.rerank(query, candidates, top_n=top_k_final or self.top_final)
        return RetrievalResult(
            chunks=reranked,
            max_similarity=max_sim,
            below_threshold=max_sim < self.confidence_threshold,
        )

    async def multi_query_retrieve(
        self,
        queries: list[str],
        *,
        top_k_final: int | None = None,
    ) -> RetrievalResult:
        seen: dict[str, Chunk] = {}
        max_sim = 0.0
        for q in queries:
            result = await self.retrieve(q, top_k_final=self.top_candidates)
            max_sim = max(max_sim, result.max_similarity)
            for c in result.chunks:
                if c.chunk_id not in seen or (c.score or 0) > (seen[c.chunk_id].score or 0):
                    seen[c.chunk_id] = c
        merged = sorted(seen.values(), key=lambda c: c.score or 0.0, reverse=True)
        reranked = await self.reranker.rerank(queries[0], merged, top_n=top_k_final or self.top_final)
        return RetrievalResult(
            chunks=reranked,
            max_similarity=max_sim,
            below_threshold=max_sim < self.confidence_threshold,
        )

    async def style_exemplars(self, query: str, format_filter: list[ContentFormat], limit: int = 5) -> list[Chunk]:
        vector = await self.embeddings.embed_query(query)
        return await self.vector_store.search(
            vector,
            limit=limit,
            collection=self.vector_store.exemplars_collection,
            format_filter=format_filter,
        )
