from __future__ import annotations

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import Chunk, ContentFormat, Platform

log = get_logger(__name__)


class VectorStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.collection = settings.qdrant_collection
        self.exemplars_collection = settings.qdrant_exemplars_collection
        self.dim = settings.voyage_dim
        self._client = AsyncQdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)

    async def ensure_collections(self) -> None:
        for name in (self.collection, self.exemplars_collection):
            exists = await self._client.collection_exists(name)
            if not exists:
                log.info("creating_qdrant_collection", name=name, dim=self.dim)
                await self._client.create_collection(
                    collection_name=name,
                    vectors_config=qmodels.VectorParams(size=self.dim, distance=qmodels.Distance.COSINE),
                )

    async def search(
        self,
        vector: list[float],
        *,
        limit: int,
        collection: str | None = None,
        format_filter: list[ContentFormat] | None = None,
        exclude_sponsored: bool = False,
    ) -> list[Chunk]:
        must: list[qmodels.Condition] = []
        if format_filter:
            must.append(
                qmodels.FieldCondition(
                    key="format",
                    match=qmodels.MatchAny(any=[f.value for f in format_filter]),
                )
            )
        if exclude_sponsored:
            # Unsponsored = sponsor field is null/absent. Keep only those rows.
            must.append(
                qmodels.IsNullCondition(is_null=qmodels.PayloadField(key="sponsor")),
            )

        qfilter = qmodels.Filter(must=must) if must else None

        results = await self._client.search(
            collection_name=collection or self.collection,
            query_vector=vector,
            limit=limit,
            query_filter=qfilter,
            with_payload=True,
        )
        return [self._to_chunk(r) for r in results]

    @staticmethod
    def _to_chunk(point: qmodels.ScoredPoint) -> Chunk:
        payload = point.payload or {}
        return Chunk(
            chunk_id=str(point.id),
            source_id=payload.get("source_id", ""),
            platform=Platform(payload.get("platform", "other")),
            format=ContentFormat(payload.get("format", "reel")),
            text=payload.get("text", ""),
            start_seconds=payload.get("start_seconds"),
            end_seconds=payload.get("end_seconds"),
            published_at=payload.get("published_at"),
            topic_tags=payload.get("topic_tags", []),
            register=payload.get("register"),
            language_mix=payload.get("language_mix", {}),
            url=payload.get("url", ""),
            score=point.score,
        )
