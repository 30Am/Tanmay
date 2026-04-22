from __future__ import annotations

from typing import Any

import structlog

from packages.ingestion.celery_app import celery_app

log = structlog.get_logger(__name__)


@celery_app.task(
    name="packages.ingestion.workers.twitter.ingest_source",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def ingest_source(self: Any, source: dict[str, Any]) -> dict[str, int]:
    """Pull tweets via Apify Tweet Scraper actor, persist raw, enqueue processing.

    For threads, reassemble child tweets into a single document before chunking.
    """
    log.info("twitter_ingest_stub", source_id=source.get("source_id"))
    return {"enqueued": 0}
