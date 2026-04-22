"""Voyage-3 embedder + Qdrant upsert."""
from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Any

import voyageai
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels


@dataclass
class EmbeddedChunk:
    chunk_id: str
    vector: list[float]
    payload: dict[str, Any]


class Embedder:
    def __init__(self) -> None:
        self.model = os.environ.get("VOYAGE_MODEL", "voyage-3")
        self.dim = int(os.environ.get("VOYAGE_DIM", "1024"))
        self._client = voyageai.AsyncClient(api_key=os.environ["VOYAGE_API_KEY"])

    async def embed(self, texts: list[str]) -> list[list[float]]:
        result = await self._client.embed(texts, model=self.model, input_type="document")
        return result.embeddings


class QdrantUpserter:
    def __init__(self) -> None:
        self.collection = os.environ.get("QDRANT_COLLECTION", "tanmay_chunks")
        self.dim = int(os.environ.get("VOYAGE_DIM", "1024"))
        self._client = AsyncQdrantClient(
            url=os.environ.get("QDRANT_URL", "http://localhost:6333"),
            api_key=os.environ.get("QDRANT_API_KEY") or None,
        )

    async def ensure_collection(self) -> None:
        exists = await self._client.collection_exists(self.collection)
        if not exists:
            await self._client.create_collection(
                collection_name=self.collection,
                vectors_config=qmodels.VectorParams(size=self.dim, distance=qmodels.Distance.COSINE),
            )

    async def upsert(self, chunks: list[EmbeddedChunk]) -> None:
        points = [
            qmodels.PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, c.chunk_id)),
                vector=c.vector,
                payload={**c.payload, "chunk_id": c.chunk_id},
            )
            for c in chunks
        ]
        await self._client.upsert(collection_name=self.collection, points=points, wait=True)
