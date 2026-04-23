"""Stamp every Qdrant chunk with is_tanmay based on tanmay_speakers.json.

For each video: issue two targeted set_payload calls per video —
  1. {video_id==vid, speaker==tanmay_id}  -> is_tanmay=true
  2. {video_id==vid, speaker!=tanmay_id}  -> is_tanmay=false

If the video's Tanmay speaker is null (guest contexts where he wasn't confidently found),
all chunks get is_tanmay=false.
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

load_dotenv(REPO_ROOT / "apps" / "api" / ".env", override=True)

from qdrant_client import AsyncQdrantClient  # noqa: E402
from qdrant_client.http import models as qm  # noqa: E402


COLLECTION = os.environ.get("QDRANT_COLLECTION", "tanmay_chunks")
LOG_PATH = DATA / "logs" / "mark_tanmay.log"


def log(msg: str) -> None:
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with LOG_PATH.open("a") as f:
        f.write(line + "\n")


async def main() -> None:
    speakers = json.loads((DATA / "tanmay_speakers.json").read_text())
    client = AsyncQdrantClient(
        url=os.environ.get("QDRANT_URL", "http://localhost:6333"),
        api_key=os.environ.get("QDRANT_API_KEY") or None,
    )

    total_videos = len(speakers)
    log(f"START — {total_videos} videos")

    for i, (vid, info) in enumerate(speakers.items(), start=1):
        tanmay_spk = info.get("speaker")
        base_filter = qm.FieldCondition(key="video_id", match=qm.MatchValue(value=vid))

        if tanmay_spk is None:
            # All chunks for this video: is_tanmay=false
            await client.set_payload(
                collection_name=COLLECTION,
                payload={"is_tanmay": False, "tanmay_speaker": None, "tanmay_confidence": info.get("confidence")},
                points=qm.Filter(must=[base_filter]),
            )
        else:
            # Matching speaker: true
            await client.set_payload(
                collection_name=COLLECTION,
                payload={"is_tanmay": True, "tanmay_speaker": tanmay_spk, "tanmay_confidence": info.get("confidence")},
                points=qm.Filter(must=[base_filter, qm.FieldCondition(key="speaker", match=qm.MatchValue(value=tanmay_spk))]),
            )
            # Non-matching speakers: false
            await client.set_payload(
                collection_name=COLLECTION,
                payload={"is_tanmay": False, "tanmay_speaker": tanmay_spk, "tanmay_confidence": info.get("confidence")},
                points=qm.Filter(
                    must=[base_filter],
                    must_not=[qm.FieldCondition(key="speaker", match=qm.MatchValue(value=tanmay_spk))],
                ),
            )
        if i % 20 == 0 or i == total_videos:
            log(f"  [{i}/{total_videos}]")

    # Tally: count chunks by is_tanmay
    counts = await client.count(collection_name=COLLECTION, count_filter=qm.Filter(must=[qm.FieldCondition(key="is_tanmay", match=qm.MatchValue(value=True))]))
    total = await client.count(collection_name=COLLECTION)
    log(f"DONE — tanmay_chunks: {counts.count} / {total.count} total")


if __name__ == "__main__":
    asyncio.run(main())
