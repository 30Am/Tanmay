"""Pull the strongest-voice Tanmay chunks from Qdrant for Phase 04 voice analysis.

Filter: is_tanmay=true, tanmay_confidence=high, register in {comedic, roast, reflective, sincere},
length 300-2500 chars. Rank by length (more voice per chunk) + tag count.

Output: data/voice_corpus.json — list of {chunk_id, text, register, topic_tags, url, start_seconds,
end_seconds, source, video_id, title}.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

DATA = Path(__file__).parent
REPO_ROOT = DATA.parent
sys.path.insert(0, str(REPO_ROOT))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO_ROOT / "apps" / "api" / ".env", override=False)

from qdrant_client import AsyncQdrantClient  # noqa: E402
from qdrant_client.http import models as qm  # noqa: E402

COLLECTION = os.environ.get("QDRANT_COLLECTION", "tanmay_chunks")
OUT_PATH = DATA / "voice_corpus.json"
REGISTER_CAPS = {"comedic": 40, "roast": 17, "reflective": 30, "sincere": 7}
MIN_LEN, MAX_LEN = 300, 2500


async def main() -> None:
    client = AsyncQdrantClient(url=os.environ.get("QDRANT_URL", "http://localhost:6333"))
    buckets: dict[str, list[tuple[float, dict]]] = defaultdict(list)
    offset = None
    scanned = 0
    while True:
        pts, offset = await client.scroll(
            collection_name=COLLECTION,
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=False,
            scroll_filter=qm.Filter(
                must=[
                    qm.FieldCondition(key="is_tanmay", match=qm.MatchValue(value=True)),
                    qm.FieldCondition(key="tanmay_confidence", match=qm.MatchValue(value="high")),
                ],
            ),
        )
        for p in pts:
            scanned += 1
            reg = p.payload.get("register")
            if reg not in REGISTER_CAPS:
                continue
            txt = p.payload.get("text") or ""
            if not (MIN_LEN <= len(txt) <= MAX_LEN):
                continue
            score = len(txt) / 1000.0 + 0.1 * len(p.payload.get("topic_tags") or [])
            buckets[reg].append((score, p.payload))
        if offset is None:
            break

    selected: list[dict] = []
    for reg, cap in REGISTER_CAPS.items():
        top = sorted(buckets.get(reg, []), key=lambda x: -x[0])[:cap]
        selected.extend(pl for _, pl in top)
        print(f"{reg}: {len(top)}/{cap} selected (from {len(buckets.get(reg, []))} candidates)")

    keep_fields = ("chunk_id", "text", "register", "topic_tags", "url", "start_seconds",
                   "end_seconds", "source", "video_id", "title", "language_mix", "entities",
                   "sentiment")
    out = [{k: pl.get(k) for k in keep_fields} for pl in selected]
    OUT_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nscanned={scanned} selected={len(out)} -> {OUT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
