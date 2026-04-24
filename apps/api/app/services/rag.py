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
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any

import cohere
from anthropic import AsyncAnthropic
from langfuse import get_client, observe
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
QDRANT_ADS = os.environ.get("QDRANT_ADS_COLLECTION", "tanmay_ads")
VOYAGE_MODEL = os.environ.get("VOYAGE_MODEL", "voyage-3")
ANTHROPIC_PRIMARY = os.environ.get("ANTHROPIC_MODEL_PRIMARY", "claude-sonnet-4-5-20250929")
ANTHROPIC_UTILITY = os.environ.get("ANTHROPIC_MODEL_UTILITY", "claude-haiku-4-5-20251001")
COHERE_API_KEY = os.environ.get("COHERE_API_KEY", "")
COHERE_RERANK_MODEL = os.environ.get("COHERE_RERANK_MODEL", "rerank-v3.5")
# How many extra candidates to fetch before reranking; 3× is the sweet spot for quality/cost.
RERANK_FETCH_MULTIPLIER = 3


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
        self._cohere: cohere.AsyncClientV2 | None = (
            cohere.AsyncClientV2(api_key=COHERE_API_KEY) if COHERE_API_KEY else None
        )

    async def embed_query(self, query: str) -> list[float]:
        r = await self.voyage.embed([query], model=VOYAGE_MODEL, input_type="query")
        return r.embeddings[0]

    async def _rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_n: int,
    ) -> list[RetrievedChunk]:
        """Rerank chunks with Cohere Rerank-3.5 when COHERE_API_KEY is set.

        Falls back to top-N by vector similarity score when the key is absent.
        Chunks are returned in descending relevance order.
        """
        if not self._cohere or not chunks:
            return chunks[:top_n]
        try:
            result = await self._cohere.rerank(
                model=COHERE_RERANK_MODEL,
                query=query,
                documents=[c.text for c in chunks],
                top_n=top_n,
            )
            return [chunks[r.index] for r in result.results]
        except Exception:
            # Degrade gracefully — log and fall back to similarity order
            import logging
            logging.getLogger(__name__).warning("Cohere rerank failed, falling back to similarity order", exc_info=True)
            return chunks[:top_n]

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

    # Maps the AdGenerateRequest.industry enum to matching product_category
    # payload values observed in the tanmay_ads collection. The list captures
    # variants we've seen indexed; add more as the corpus grows.
    _INDUSTRY_TO_CATEGORIES: dict[str, list[str]] = {
        "fintech": ["fintech", "payments", "banking", "credit_card", "loans", "insurance"],
        "d2c": ["d2c", "apparel", "skincare_d2c", "food_d2c", "beverage_d2c"],
        "saas_b2b": ["saas", "saas_b2b", "developer_tools", "productivity"],
        "fmcg": ["fmcg", "ice_cream_fmcg", "snacks", "beverages", "household"],
        "beauty": ["beauty", "skincare", "haircare", "cosmetics", "fragrance"],
        "edtech": ["edtech", "education", "test_prep", "upskilling"],
        "auto": ["auto", "automotive", "two_wheeler", "four_wheeler", "ev"],
        "realty": ["realty", "real_estate", "housing"],
        "ott_media": ["ott", "ott_media", "streaming", "media"],
        "telecom": ["telecom", "mobile_plans", "isp"],
        "healthcare": ["healthcare", "health", "pharma", "diagnostics", "wellness"],
        "travel": ["travel", "hospitality", "hotels", "airlines", "aggregator"],
        "other": [],
    }

    async def retrieve_ad_corpus(
        self,
        query: str,
        *,
        limit: int = 5,
        has_celebrities: bool | None = None,  # kept for API compat; not used in filtering
        industry: str | None = None,
    ) -> list[RetrievedChunk]:
        """Retrieve the most relevant Tanmay ad scripts from the ad corpus collection.

        When `industry` is supplied, first tries a filtered search restricted to matching
        `product_category` values. If that returns < 2 results (the pool is too thin to be
        useful), falls back to an unfiltered search so the caller still has patterns to work
        with. Without `industry`, behaves exactly as before.
        """

        async def _unfiltered() -> list[RetrievedChunk]:
            vec = await self.embed_query(query)
            result = await self.qdrant.query_points(
                collection_name=QDRANT_ADS,
                query=vec,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )
            return [self._to_chunk(p) for p in result.points]

        try:
            if industry:
                categories = self._INDUSTRY_TO_CATEGORIES.get(industry, [])
                if categories:
                    vec = await self.embed_query(query)
                    cat_filter = qm.Filter(
                        must=[
                            qm.FieldCondition(
                                key="product_category",
                                match=qm.MatchAny(any=categories),
                            )
                        ]
                    )
                    result = await self.qdrant.query_points(
                        collection_name=QDRANT_ADS,
                        query=vec,
                        limit=limit,
                        query_filter=cat_filter,
                        with_payload=True,
                        with_vectors=False,
                    )
                    filtered = [self._to_chunk(p) for p in result.points]
                    if len(filtered) >= 2:
                        return filtered
                    # Too few category matches — fall through to unfiltered search
                    # so we still get *some* pattern data rather than none.
            return await _unfiltered()
        except Exception:
            import logging
            logging.getLogger(__name__).warning(
                "retrieve_ad_corpus failed — skipping pattern analysis",
                exc_info=True,
            )
            return []

    async def analyze_ad_patterns(
        self,
        ad_chunks: list[RetrievedChunk],
        *,
        product_name: str,
        product_description: str,
        has_celebrities: bool = False,
    ) -> str:
        """Analyze storytelling patterns from retrieved Tanmay ad scripts using Haiku.

        Returns a concise, actionable pattern analysis string that gets injected into
        the main generation prompt so the model can replicate the observed patterns.

        This is a fast Haiku call (~800ms). If it fails, returns an empty string so the
        caller can gracefully skip pattern injection.
        """
        if not ad_chunks:
            return ""

        # Format the ad scripts for analysis
        ad_texts: list[str] = []
        for i, chunk in enumerate(ad_chunks, 1):
            payload = chunk.as_payload_dict()
            brand = chunk.topic_tags[0] if chunk.topic_tags else "unknown"
            ad_texts.append(f"--- AD {i} (brand context: {brand}) ---\n{payload['text']}")
        ads_block = "\n\n".join(ad_texts)

        celeb_note = (
            "The new ad WILL have celebrity cameos. Pay special attention to how scenes with "
            "celebrities are structured — dialogue rhythm, who drives the joke, how the product "
            "is revealed through conversation rather than pitch."
            if has_celebrities
            else "The new ad has no celebrity cameos."
        )

        system = (
            "You are an expert analyst of comedic ad-making style. "
            "Your job is to extract actionable, TRANSFERABLE storytelling patterns from sample ads "
            "so a writer can replicate the same approach for a new brief — applying those patterns "
            "to ANY protagonist, not just the person who wrote the originals."
        )

        prompt = f"""\
You are about to analyze {len(ad_chunks)} sample ad scripts to extract storytelling patterns.

IMPORTANT: Phrase every pattern as a transferable writing move ("the hook opens with X",
"the narrator admits Y"). Do NOT phrase patterns as "Tanmay does X" and do NOT treat
Tanmay Bhat as a required character in the new ad — he is the writer, not the protagonist.
The new ad may feature completely different characters.

NEW AD BRIEF (what you're preparing patterns FOR):
Product: {product_name}
Description: {product_description}
{celeb_note}

SAMPLE AD SCRIPTS TO ANALYZE:
{ads_block}

Now extract the following patterns as actionable instructions for writing the new ad.
Be specific — quote exact structural moves, not vague advice like "be authentic".
Describe the NARRATOR / PROTAGONIST generically (not by any real person's name).

Write the analysis under these headers:

HOOK MECHANICS:
(How does the hook open? What sentence structures? What specific details ground it?)

SETUP CONSTRUCTION:
(What kind of personal failure/embarrassment from the protagonist sets up this category of product? How specific are the details? Any use of numbers?)

PRODUCT REVEAL TIMING & FRAMING:
(When does the product name appear? What exact phrase introduces it? How is audience cynicism pre-empted?)

VOICE & TONE REGISTER:
(Hinglish patterns observed. Sentence length rhythm. Specific filler words and when used.)

CTA STYLE:
(Exact CTA patterns. What makes them feel casual not corporate? Any callbacks to the setup?)

CELEB SCENE MECHANICS (if applicable):
(How is the celebrity introduced? Who holds the skeptic role — the protagonist, the celeb, or a third character? How does the product appear naturally in the dialogue?)

APPLICATION TO THIS BRIEF:
(2-3 sentences: given {product_name}, which specific patterns from the above ads apply most directly and why — stated generically, without naming Tanmay.)
"""

        try:
            response = await self.anthropic.messages.create(
                model=ANTHROPIC_UTILITY,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=900,
                temperature=0.3,
            )
            return "".join(b.text for b in response.content if b.type == "text").strip()
        except Exception:
            import logging
            logging.getLogger(__name__).warning("analyze_ad_patterns failed", exc_info=True)
            return ""

    async def paraphrase_query(self, question: str, *, n: int = 2) -> list[str]:
        """Generate `n` paraphrases of the user's question via Haiku.

        Returns the list WITHOUT the original — caller combines if needed.
        """
        system = (
            "Rewrite the user's question into {n} alternative phrasings that preserve meaning "
            "but use different vocabulary and sentence structure. Return one per line, no bullets, "
            "no numbering, no prose."
        ).format(n=n)
        response = await self.anthropic.messages.create(
            model=ANTHROPIC_UTILITY,
            system=system,
            messages=[{"role": "user", "content": question}],
            max_tokens=200,
            temperature=0.3,
        )
        text = "".join(b.text for b in response.content if b.type == "text")
        paraphrases = [line.strip() for line in text.splitlines() if line.strip()]
        return paraphrases[:n]

    async def multi_query_retrieve(
        self,
        queries: list[str],
        *,
        limit: int = 12,
        tanmay_only: bool = False,
        register_any: list[str] | None = None,
    ) -> tuple[list[RetrievedChunk], float]:
        """Retrieve for each query, fuse results with Reciprocal Rank Fusion (RRF).

        RRF score per chunk: sum over queries of 1 / (60 + rank). Chunks that surface on
        multiple queries get boosted. Returns (fused_chunks, max_similarity_seen).
        """
        import asyncio

        per_query = await asyncio.gather(
            *(self.retrieve(q, limit=limit, tanmay_only=tanmay_only, register_any=register_any) for q in queries)
        )

        rrf_score: dict[str, float] = {}
        best_chunk: dict[str, RetrievedChunk] = {}
        max_sim = 0.0
        RRF_K = 60  # standard RRF constant

        for chunks in per_query:
            for rank, c in enumerate(chunks):
                rrf_score[c.chunk_id] = rrf_score.get(c.chunk_id, 0.0) + 1.0 / (RRF_K + rank + 1)
                # Keep best-scoring version (for displaying similarity)
                if c.chunk_id not in best_chunk or (c.score > best_chunk[c.chunk_id].score):
                    best_chunk[c.chunk_id] = c
                max_sim = max(max_sim, c.score)

        fused = sorted(best_chunk.values(), key=lambda c: rrf_score[c.chunk_id], reverse=True)
        # Rerank the full fused pool (before slicing) using the first query as the signal.
        # This gives Cohere the most candidates to work with.
        reranked = await self._rerank(queries[0], fused, limit)
        return reranked, max_sim

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

    @observe(as_type="generation", capture_output=False)
    async def generate(
        self,
        *,
        tab: str,
        query: str,
        user_payload: str | None = None,
        tone: Any = None,
        format_rules: str | None = None,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.8,
        retrieval_top_k: int = 12,
        exemplars_k: int = 5,
        exemplar_registers: list[str] | None = None,
        tanmay_only_retrieval: bool = True,
    ) -> GenerationResult:
        # Retrieve context + exemplars in parallel.
        # Fetch RERANK_FETCH_MULTIPLIER × candidates so Cohere can rerank meaningfully.
        import asyncio

        fetch_limit = retrieval_top_k * RERANK_FETCH_MULTIPLIER if self._cohere else retrieval_top_k
        retrieval_task = self.retrieve(
            query,
            limit=fetch_limit,
            tanmay_only=tanmay_only_retrieval,
        )
        exemplars_task = self.retrieve_exemplars(
            query,
            limit=exemplars_k,
            register_any=exemplar_registers,
        )
        raw_chunks, exemplars = await asyncio.gather(retrieval_task, exemplars_task)
        max_sim = max((c.score for c in raw_chunks), default=0.0)
        chunks = await self._rerank(query, raw_chunks, retrieval_top_k)

        # Build system blocks (cached prefix + dynamic tone).
        system_blocks = build_cached_system(tab=tab, tone=tone, format_rules=format_rules)

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
        _in = getattr(usage, "input_tokens", 0)
        _out = getattr(usage, "output_tokens", 0)
        _cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
        _cache_create = getattr(usage, "cache_creation_input_tokens", 0) or 0
        result = GenerationResult(
            text=text,
            citations=chunks,
            max_similarity=max_sim,
            input_tokens=_in,
            output_tokens=_out,
            cache_read_tokens=_cache_read,
            cache_creation_tokens=_cache_create,
        )
        get_client().update_current_generation(
            name=f"claude/{tab}",
            model=model or ANTHROPIC_PRIMARY,
            usage_details={"input": _in, "output": _out, "cache_read": _cache_read, "cache_create": _cache_create},
            cost_details={"total": result.total_cost_usd},
            metadata={"tab": tab, "max_similarity": round(max_sim, 4), "chunks_retrieved": len(chunks)},
        )
        return result

    @observe(as_type="generation", capture_output=False)
    async def generate_with_tool(
        self,
        *,
        tab: str,
        query: str,
        tool_name: str,
        tool_description: str,
        tool_schema: dict[str, Any],
        user_payload: str | None = None,
        tone: Any = None,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        retrieval_top_k: int = 12,
        exemplars_k: int = 5,
        exemplar_registers: list[str] | None = None,
        tanmay_only_retrieval: bool = True,
        entity_boost_term: str | None = None,
    ) -> tuple[dict[str, Any], GenerationResult]:
        """Generate with Anthropic tool_use — model must emit tool input matching schema.

        Returns (tool_input_dict, GenerationResult). The tool_input is the schema-valid
        structured output; the GenerationResult carries citations + usage + cost.

        `entity_boost_term` re-ranks retrieved chunks by bumping any chunk whose `entities`
        payload contains that term (case-insensitive substring match). Useful for ad
        generation: boost chunks that have mentioned the brand/product category.
        """
        import asyncio

        fetch_limit = retrieval_top_k * RERANK_FETCH_MULTIPLIER if self._cohere else retrieval_top_k
        retrieval_task = self.retrieve(
            query,
            limit=fetch_limit,
            tanmay_only=tanmay_only_retrieval,
        )
        exemplars_task = self.retrieve_exemplars(
            query,
            limit=exemplars_k,
            register_any=exemplar_registers,
        )
        raw_chunks, exemplars = await asyncio.gather(retrieval_task, exemplars_task)

        if entity_boost_term:
            term = entity_boost_term.lower()

            def boost_score(c: RetrievedChunk) -> float:
                # RetrievedChunk doesn't carry entities, but topic_tags is a softer proxy
                for t in (c.topic_tags or []):
                    if term in t.lower():
                        return c.score + 0.15
                return c.score

            raw_chunks = sorted(raw_chunks, key=boost_score, reverse=True)

        max_sim = max((c.score for c in raw_chunks), default=0.0)
        chunks = await self._rerank(query, raw_chunks, retrieval_top_k)
        system_blocks = build_cached_system(tab=tab, tone=tone)

        user_sections = [format_chunks([c.as_payload_dict() for c in chunks])]
        if exemplars:
            user_sections.append(format_exemplars([{"text": e.text} for e in exemplars]))
        user_sections.append(f"USER INPUT:\n{user_payload or query}")
        user_message = "\n\n".join(user_sections)

        tool = {
            "name": tool_name,
            "description": tool_description,
            "input_schema": tool_schema,
        }

        response = await self.anthropic.messages.create(
            model=model or ANTHROPIC_PRIMARY,
            system=system_blocks,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=max_tokens,
            temperature=temperature,
            tools=[tool],
            tool_choice={"type": "tool", "name": tool_name},
        )

        tool_input: dict[str, Any] = {}
        text_parts: list[str] = []
        for block in response.content:
            if block.type == "tool_use" and block.name == tool_name:
                tool_input = dict(block.input)
            elif block.type == "text":
                text_parts.append(block.text)

        usage = response.usage
        _in = getattr(usage, "input_tokens", 0)
        _out = getattr(usage, "output_tokens", 0)
        _cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
        _cache_create = getattr(usage, "cache_creation_input_tokens", 0) or 0
        result = GenerationResult(
            text="".join(text_parts),
            citations=chunks,
            max_similarity=max_sim,
            input_tokens=_in,
            output_tokens=_out,
            cache_read_tokens=_cache_read,
            cache_creation_tokens=_cache_create,
        )
        get_client().update_current_generation(
            name=f"claude/{tab}",
            model=model or ANTHROPIC_PRIMARY,
            usage_details={"input": _in, "output": _out, "cache_read": _cache_read, "cache_create": _cache_create},
            cost_details={"total": result.total_cost_usd},
            metadata={"tab": tab, "tool": tool_name, "max_similarity": round(max_sim, 4)},
        )
        return tool_input, result

    async def stream_generate(
        self,
        *,
        tab: str,
        query: str,
        user_payload: str | None = None,
        tone: Any = None,
        format_rules: str | None = None,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.8,
        retrieval_top_k: int = 12,
        exemplars_k: int = 5,
        exemplar_registers: list[str] | None = None,
        tanmay_only_retrieval: bool = True,
    ) -> AsyncGenerator[tuple[str | None, GenerationResult | None], None]:
        """Stream text tokens then yield a final GenerationResult.

        Yields (token, None) for each text delta, then (None, result) when generation
        is complete. Retrieval runs upfront (blocking) before the first token is yielded.
        """
        import asyncio

        fetch_limit = retrieval_top_k * RERANK_FETCH_MULTIPLIER if self._cohere else retrieval_top_k
        retrieval_task = self.retrieve(query, limit=fetch_limit, tanmay_only=tanmay_only_retrieval)
        exemplars_task = self.retrieve_exemplars(query, limit=exemplars_k, register_any=exemplar_registers)
        raw_chunks, exemplars = await asyncio.gather(retrieval_task, exemplars_task)
        max_sim = max((c.score for c in raw_chunks), default=0.0)
        chunks = await self._rerank(query, raw_chunks, retrieval_top_k)
        system_blocks = build_cached_system(tab=tab, tone=tone, format_rules=format_rules)

        user_sections = [format_chunks([c.as_payload_dict() for c in chunks])]
        if exemplars:
            user_sections.append(format_exemplars([{"text": e.text} for e in exemplars]))
        user_sections.append(f"USER INPUT:\n{user_payload or query}")
        user_message = "\n\n".join(user_sections)

        full_text: list[str] = []
        lf = get_client()
        with lf.start_as_current_observation(name=f"claude/{tab}-stream", as_type="generation"):
            async with self.anthropic.messages.stream(
                model=model or ANTHROPIC_PRIMARY,
                system=system_blocks,
                messages=[{"role": "user", "content": user_message}],
                max_tokens=max_tokens,
                temperature=temperature,
            ) as stream:
                async for token in stream.text_stream:
                    full_text.append(token)
                    yield (token, None)

                final_msg = await stream.get_final_message()
                usage = final_msg.usage

            _in = getattr(usage, "input_tokens", 0)
            _out = getattr(usage, "output_tokens", 0)
            _cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
            _cache_create = getattr(usage, "cache_creation_input_tokens", 0) or 0
            result = GenerationResult(
                text="".join(full_text),
                citations=chunks,
                max_similarity=max_sim,
                input_tokens=_in,
                output_tokens=_out,
                cache_read_tokens=_cache_read,
                cache_creation_tokens=_cache_create,
            )
            lf.update_current_generation(
                model=model or ANTHROPIC_PRIMARY,
                usage_details={"input": _in, "output": _out, "cache_read": _cache_read, "cache_create": _cache_create},
                cost_details={"total": result.total_cost_usd},
                metadata={"tab": tab, "max_similarity": round(max_sim, 4), "chunks_retrieved": len(chunks)},
            )
            yield (None, result)
