from __future__ import annotations

import cohere

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import Chunk

log = get_logger(__name__)


class Reranker:
    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.cohere_rerank_model
        self._client = cohere.AsyncClientV2(api_key=settings.cohere_api_key) if settings.cohere_api_key else None

    async def rerank(self, query: str, chunks: list[Chunk], top_n: int) -> list[Chunk]:
        if self._client is None or not chunks:
            log.warning("cohere_api_key not set or empty chunks, returning head")
            return chunks[:top_n]
        response = await self._client.rerank(
            model=self.model,
            query=query,
            documents=[c.text for c in chunks],
            top_n=min(top_n, len(chunks)),
        )
        reranked: list[Chunk] = []
        for r in response.results:
            chunk = chunks[r.index]
            chunk.score = r.relevance_score
            reranked.append(chunk)
        return reranked
