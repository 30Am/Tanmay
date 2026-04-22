from __future__ import annotations

from pathlib import Path

from packages.ingestion.celery_app import celery_app
from packages.ingestion.config import load_registry

REGISTRY_PATH = Path(__file__).resolve().parents[3] / "config" / "sources.yaml"


PLATFORM_TASKS: dict[str, str] = {
    "youtube": "packages.ingestion.workers.youtube.ingest_source",
    "x": "packages.ingestion.workers.twitter.ingest_source",
    "linkedin": "packages.ingestion.workers.linkedin.ingest_source",
    "instagram": "packages.ingestion.workers.instagram.ingest_source",
    "podcast": "packages.ingestion.workers.podcast.ingest_source",
}


@celery_app.task(name="packages.ingestion.workers.dispatcher.dispatch_all")
def dispatch_all() -> dict[str, int]:
    registry = load_registry(REGISTRY_PATH)
    dispatched = 0
    skipped = 0
    for source in registry.enabled_sources():
        task_name = PLATFORM_TASKS.get(source.platform.value)
        if not task_name:
            skipped += 1
            continue
        celery_app.send_task(task_name, kwargs={"source": source.model_dump()})
        dispatched += 1
    return {"dispatched": dispatched, "skipped": skipped}


@celery_app.task(name="packages.ingestion.workers.dispatcher.dispatch_one")
def dispatch_one(source_id: str) -> str:
    registry = load_registry(REGISTRY_PATH)
    for source in registry.sources:
        if source.source_id == source_id:
            task_name = PLATFORM_TASKS.get(source.platform.value)
            if not task_name:
                return f"no-worker-for-{source.platform.value}"
            celery_app.send_task(task_name, kwargs={"source": source.model_dump()})
            return f"dispatched:{source_id}"
    return f"not-found:{source_id}"
