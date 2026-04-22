"""End-to-end processing task.

Given raw content (transcript words or post text) + source metadata, run:
  chunk → tag → embed → upsert.

Invoked by platform workers once the raw text is available in R2.
"""
from __future__ import annotations

import asyncio
from typing import Any

import structlog

from packages.ingestion.celery_app import celery_app
from packages.ingestion.pipeline.chunker import Word, chunk_post, chunk_transcript
from packages.ingestion.pipeline.embedder import EmbeddedChunk, Embedder, QdrantUpserter
from packages.ingestion.pipeline.tagger import Tagger

log = structlog.get_logger(__name__)


async def _run(raw: dict[str, Any]) -> int:
    source_id = raw["source_id"]
    metadata = raw["metadata"]
    kind = raw["kind"]

    if kind == "transcript":
        words = [Word(**w) for w in raw["words"]]
        chunks = chunk_transcript(source_id, words)
    else:
        chunks = chunk_post(source_id, raw["text"])

    if not chunks:
        log.info("no_chunks", source_id=source_id)
        return 0

    tagger = Tagger()
    tags = await asyncio.gather(*(tagger.tag(c.text) for c in chunks))

    embedder = Embedder()
    vectors = await embedder.embed([c.text for c in chunks])

    upserter = QdrantUpserter()
    await upserter.ensure_collection()

    payloads: list[EmbeddedChunk] = []
    for c, t, v in zip(chunks, tags, vectors, strict=True):
        payloads.append(
            EmbeddedChunk(
                chunk_id=c.chunk_id,
                vector=v,
                payload={
                    "source_id": c.source_id,
                    "text": c.text,
                    "start_seconds": c.start_seconds,
                    "end_seconds": c.end_seconds,
                    **metadata,
                    **t,
                },
            )
        )
    await upserter.upsert(payloads)
    log.info("processed", source_id=source_id, chunks=len(chunks))
    return len(chunks)


@celery_app.task(
    name="packages.ingestion.pipeline.process.process_raw",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def process_raw(self: Any, raw: dict[str, Any]) -> dict[str, int]:
    count = asyncio.run(_run(raw))
    return {"chunks": count}
