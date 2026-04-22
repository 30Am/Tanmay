from __future__ import annotations

from typing import Any

import structlog

from packages.ingestion.celery_app import celery_app

log = structlog.get_logger(__name__)


@celery_app.task(
    name="packages.ingestion.workers.youtube.ingest_source",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def ingest_source(self: Any, source: dict[str, Any]) -> dict[str, int]:
    """Expand a YouTube channel into videos, fetch transcript or audio, enqueue processing.

    Implementation plan:
      1. Use yt-dlp --flat-playlist to list videos for the channel URL.
      2. For each video id, check if already ingested (Postgres lookup by source_id).
      3. Try youtube-transcript-api first; if missing, download audio with yt-dlp and enqueue
         the Deepgram transcription task.
      4. Upload raw transcript + manifest to R2 under sources/<source_id>/<video_id>/.
      5. Enqueue `pipeline.process.process_transcript` for downstream chunking.
    """
    log.info("youtube_ingest_stub", source_id=source.get("source_id"))
    # TODO: implement — this is the scaffold.
    return {"enqueued": 0}
