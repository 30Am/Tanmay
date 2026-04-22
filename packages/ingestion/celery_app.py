from __future__ import annotations

import os

from celery import Celery

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "tanmay_ingestion",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "packages.ingestion.workers.youtube",
        "packages.ingestion.workers.twitter",
        "packages.ingestion.workers.linkedin",
        "packages.ingestion.workers.instagram",
        "packages.ingestion.workers.podcast",
        "packages.ingestion.pipeline.process",
    ],
)

celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=60,
    task_time_limit=60 * 60,
    result_expires=7 * 24 * 3600,
    beat_schedule={
        "weekly-recrawl": {
            "task": "packages.ingestion.workers.dispatcher.dispatch_all",
            "schedule": 7 * 24 * 3600,
        },
    },
)
