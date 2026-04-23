"""RAG orchestrator — query → retrieve → exemplars → generate.

Direct adapter against Phase 03's Qdrant payload (source/video_id/is_tanmay/register),
bypassing the scaffolded Chunk/Platform/Format enum schema that doesn't match our data.
Used by both the FastAPI routers and the standalone smoke/eval scripts.

Models:
  - Generation: Claude Sonnet 4.6 (primary). Claude Haiku 4.5 for utility passes.
  - Embeddings: Voyage-3 (1024d).
  - Rerank: Cohere Rerank 3 if COHERE_API_KEY set; otherwise returns top-N by similarity.

Prompt caching: the stable persona + format prefix is sent with cache_control=ephemeral.
Minimum 1024 input tokens to cache — our persona prefix is ~1.1K so it qualifies for
Sonnet; for Haiku the minimum is higher (2K) so caching may only kick in with exemplars
appended.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from anthropic import AsyncAnthropic
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qm

import voyageai

from app.services.persona import (
    TAB_FORMAT_RULES,
    build_cached_system,
    format_chunks,
    format_exemplars,
)

# Env + defaults
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "tanmay_chunks")
QDRANT_EXEMPLARS = os.environ.get("QDRANT_EXEMPLARS_COLLECTION", "tanmay_exemplars")
VOYAGE_MODEL = os.environ.get("VOYAGE_MODEL", "voyage-3")
ANTHROPIC_PRIMARY = os.environ.get("ANTHROPIC_MODEL_PRIMARY", "claude-sonnet-4-5-20250929")
ANTHROPIC_UTILITY = os.environ.get("ANTHROPIC_MODEL_UTILITY", "claude-haiku-4-5-20251001")


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    score: float
    source: str
    video_id: str
    title: str | None
    url: str
    start_seconds: float | None
    end_seconds: float | None
    register: str | None
    is_tanmay: bool
    topic_tags: list[str]

    def as_payload_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "url": self.url,
            "source": self.source,
            "video_id": self.video_id,
            "start_seconds": self.start_seconds,
            "register": self.register,
            "title": self.title,
        }


@dataclass
class GenerationResult:
    text: str
    citations: list[RetrievedChunk]
    max_similarity: float
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int

    @property
    def total_cost_usd(self) -> float:
        """Rough cost estimate using Sonnet 4.6 rates. Override for Haiku."""
        return (
            self.input_tokens * 3.0 / 1_000_000
            + self.output_tokens * 15.0 / 1_000_000
            + self.cache_creation_tokens * 3.75 / 1_000_000
            + self.cache_read_tokens * 0.30 / 1_000_000
        )


class RAGEngine:
    def __init__(self) -> None:
        self.voyage = voyageai.AsyncClient(api_key=os.environ["VOYAGE_API_KEY"])
        self.anthropic = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.qdrant = AsyncQdrantClient(url=QDRANT_URL)

    async def embed_query(self, query: str) -> list[float]:
        r = await self.voyage.embed([query], model=VOYAGE_MODEL, input_type="query")
        return r.embeddings[0]

    async def retrieve(
        self,
        query: str,
        *,
        limit: int = 12,
        tanmay_only: bool = False,
        register_any: list[str] | None = None,
        collection: str | None = None,
    ) -> list[RetrievedChunk]:
        vec = await self.embed_query(query)
        must = []
        if tanmay_only:
            must.append(qm.FieldCondition(key="is_tanmay", match=qm.MatchValue(value=True)))
        if register_any:
            must.append(qm.FieldCondition(key="register", match=qm.MatchAny(any=register_any)))
        qfilter = qm.Filter(must=must) if must else None

        result = await self.qdrant.query_points(
            collection_name=collection or QDRANT_COLLECTION,
            query=vec,
            limit=limit,
            query_filter=qfilter,
            with_payload=True,
            with_vectors=False,
        )
        return [self._to_chunk(p) for p in result.points]

    async def retrieve_exemplars(
        self,
        query: str,
        *,
        limit: int = 5,
        register_any: list[str] | None = None,
    ) -> list[RetrievedChunk]:
        return await self.retrieve(
            query,
            limit=limit,
            tanmay_only=False,  # exemplars collection is already Tanmay-only
            register_any=register_any,
            collection=QDRANT_EXEMPLARS,
        )

    @staticmethod
    def _to_chunk(point: Any) -> RetrievedChunk:
        p = point.payload or {}
        return RetrievedChunk(
            chunk_id=p.get("chunk_id") or str(point.id),
            text=p.get("text") or "",
            score=point.score or 0.0,
            source=p.get("source") or "",
            video_id=p.get("video_id") or "",
            title=p.get("title"),
            url=p.get("url") or "",
            start_seconds=p.get("start_seconds"),
            end_seconds=p.get("end_seconds"),
            register=p.get("register"),
            is_tanmay=bool(p.get("is_tanmay")),
            topic_tags=p.get("topic_tags") or [],
        )

    async def generate(
        self,
        *,
        tab: str,
        query: str,
        user_payload: str | None = None,
        tone: Any = None,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.8,
        retrieval_top_k: int = 12,
        exemplars_k: int = 5,
        exemplar_registers: list[str] | None = None,
        tanmay_only_retrieval: bool = True,
    ) -> GenerationResult:
        # Retrieve context + exemplars in parallel.
        import asyncio

        retrieval_task = self.retrieve(
            query,
            limit=retrieval_top_k,
            tanmay_only=tanmay_only_retrieval,
        )
        exemplars_task = self.retrieve_exemplars(
            query,
            limit=exemplars_k,
            register_any=exemplar_registers,
        )
        chunks, exemplars = await asyncio.gather(retrieval_task, exemplars_task)

        max_sim = max((c.score for c in chunks), default=0.0)

        # Build system blocks (cached prefix + dynamic tone).
        system_blocks = build_cached_system(tab=tab, tone=tone)

        # The retrieved context + exemplars + user query go in the USER message.
        user_sections = []
        user_sections.append(format_chunks([c.as_payload_dict() for c in chunks]))
        if exemplars:
            user_sections.append(format_exemplars([{"text": e.text} for e in exemplars]))
        user_sections.append(f"USER INPUT:\n{user_payload or query}")
        user_message = "\n\n".join(user_sections)

        response = await self.anthropic.messages.create(
            model=model or ANTHROPIC_PRIMARY,
            system=system_blocks,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        text = "".join(b.text for b in response.content if b.type == "text")

        usage = response.usage
        return GenerationResult(
            text=text,
            citations=chunks,
            max_similarity=max_sim,
            input_tokens=getattr(usage, "input_tokens", 0),
            output_tokens=getattr(usage, "output_tokens", 0),
            cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
            cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
        )
