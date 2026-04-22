"""Retag every Qdrant chunk with the improved Gemini prompt.

Scrolls all points in `tanmay_chunks`, re-sends text through Tagger, and set_payloads the
new {topic_tags, register, language_mix, entities, sentiment}. Other payload fields (text,
speaker, video_id, is_tanmay, etc.) are preserved.

Env:
  CONCURRENCY=10    parallel Gemini calls
  LIMIT=N           retag first N points only (probe mode)
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

DATA = Path(__file__).parent
REPO_ROOT = DATA.parent
sys.path.insert(0, str(REPO_ROOT))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO_ROOT / "apps" / "api" / ".env", override=False)

from qdrant_client import AsyncQdrantClient  # noqa: E402

from packages.ingestion.pipeline.tagger import Tagger  # noqa: E402

COLLECTION = os.environ.get("QDRANT_COLLECTION", "tanmay_chunks")
CONCURRENCY = int(os.environ.get("CONCURRENCY", "10"))
LIMIT = int(os.environ.get("LIMIT", "0"))
LOG_PATH = DATA / "logs" / "retag.log"


def log(msg: str) -> None:
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with LOG_PATH.open("a") as f:
        f.write(line + "\n")


async def main() -> None:
    if not os.environ.get("GOOGLE_API_KEY"):
        log("ERROR: GOOGLE_API_KEY not set")
        sys.exit(2)

    client = AsyncQdrantClient(url=os.environ.get("QDRANT_URL", "http://localhost:6333"))
    tagger = Tagger()

    # Scroll all points
    points: list[tuple[str, str]] = []  # (point_id, text)
    offset = None
    while True:
        pts, offset = await client.scroll(
            collection_name=COLLECTION,
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        for p in pts:
            points.append((str(p.id), p.payload.get("text") or ""))
        if offset is None:
            break

    if LIMIT:
        points = points[:LIMIT]
    total = len(points)
    log(f"START — total={total} concurrency={CONCURRENCY}")

    sem = asyncio.Semaphore(CONCURRENCY)
    from collections import Counter
    registers: Counter[str] = Counter()
    done = 0

    async def process(pid: str, text: str) -> None:
        nonlocal done
        async with sem:
            tags = await tagger.tag(text)
        await client.set_payload(
            collection_name=COLLECTION,
            payload={
                "topic_tags": tags.get("topic_tags", []),
                "register": tags.get("register", "comedic"),
                "language_mix": tags.get("language_mix", {"hi": 0.5, "en": 0.5}),
                "entities": tags.get("entities", []),
                "sentiment": tags.get("sentiment", 0.0),
            },
            points=[pid],
        )
        registers[tags.get("register", "comedic")] += 1
        done += 1
        if done % 100 == 0 or done == total:
            log(f"  [{done}/{total}] registers={dict(registers)}")

    await asyncio.gather(*(process(pid, text) for pid, text in points))
    log(f"DONE — registers={dict(registers)}")


if __name__ == "__main__":
    asyncio.run(main())
