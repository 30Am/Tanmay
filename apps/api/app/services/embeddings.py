from __future__ import annotations

import voyageai

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)


class EmbeddingsService:
    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.voyage_model
        self.dim = settings.voyage_dim
        self._client = voyageai.AsyncClient(api_key=settings.voyage_api_key) if settings.voyage_api_key else None

    async def embed_query(self, text: str) -> list[float]:
        if self._client is None:
            log.warning("voyage_api_key not set, returning zero vector")
            return [0.0] * self.dim
        result = await self._client.embed([text], model=self.model, input_type="query")
        return result.embeddings[0]

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if self._client is None:
            log.warning("voyage_api_key not set, returning zero vectors")
            return [[0.0] * self.dim for _ in texts]
        result = await self._client.embed(texts, model=self.model, input_type="document")
        return result.embeddings
