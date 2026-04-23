"""Build the Tanmay style-exemplar Qdrant collection.

After retag + mark_tanmay, pull the strongest-voice chunks — Tanmay-only, high-confidence,
comedic/roast/reflective register — and copy them into a separate Qdrant collection for
few-shot prompting in Phase 04+.

Target: ~200 exemplars, diverse across topics and registers.

Selection:
  must: is_tanmay == true, tanmay_confidence in {medium, high}
  bucket by register: comedic (up to 80), roast (up to 40), reflective (up to 60), sincere (up to 20)
  prefer longer chunks (more voice per chunk), cap chunk length reasonably.

Output collection: `tanmay_exemplars` (same vector dim as tanmay_chunks).
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

DATA = Path(__file__).parent
REPO_ROOT = DATA.parent
sys.path.insert(0, str(REPO_ROOT))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO_ROOT / "apps" / "api" / ".env", override=True)

from qdrant_client import AsyncQdrantClient  # noqa: E402
from qdrant_client.http import models as qm  # noqa: E402

SRC = os.environ.get("QDRANT_COLLECTION", "tanmay_chunks")
DST = os.environ.get("QDRANT_EXEMPLARS_COLLECTION", "tanmay_exemplars")
LOG_PATH = DATA / "logs" / "build_exemplars.log"

REGISTER_CAPS = {"comedic": 80, "roast": 40, "reflective": 60, "sincere": 20}
# informative intentionally excluded — it's common and not persona-distinctive.

MIN_TEXT_LEN = 300  # chars — skip very short chunks
MAX_TEXT_LEN = 2500  # chars — skip giant ones


def log(msg: str) -> None:
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with LOG_PATH.open("a") as f:
        f.write(line + "\n")


async def main() -> None:
    client = AsyncQdrantClient(url=os.environ.get("QDRANT_URL", "http://localhost:6333"))

    # Discover source vector dim.
    src_info = await client.get_collection(SRC)
    dim = src_info.config.params.vectors.size
    log(f"source={SRC} dim={dim} points={src_info.points_count}")

    # Scroll Tanmay-only chunks, bucket by register.
    buckets: dict[str, list[tuple[float, any]]] = defaultdict(list)  # register -> [(score, point)]
    offset = None
    total_scanned = 0
    while True:
        pts, offset = await client.scroll(
            collection_name=SRC,
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=True,
            scroll_filter=qm.Filter(
                must=[qm.FieldCondition(key="is_tanmay", match=qm.MatchValue(value=True))],
                must_not=[qm.FieldCondition(key="tanmay_confidence", match=qm.MatchValue(value="low"))],
            ),
        )
        for p in pts:
            total_scanned += 1
            reg = p.payload.get("register")
            if reg not in REGISTER_CAPS:
                continue
            txt = p.payload.get("text") or ""
            if not (MIN_TEXT_LEN <= len(txt) <= MAX_TEXT_LEN):
                continue
            # Score: prefer longer chunks (more voice density) with more topic tags.
            score = len(txt) / 1000.0 + 0.1 * len(p.payload.get("topic_tags") or [])
            buckets[reg].append((score, p))
        if offset is None:
            break

    log(f"scanned={total_scanned} candidates by register: {{r: len(v) for r, v in buckets.items()}}".replace("{{", "{").replace("}}", "}"))
    for r, v in buckets.items():
        log(f"  {r}: {len(v)} candidates")

    # Pick top-N per register.
    selected = []
    for reg, cap in REGISTER_CAPS.items():
        cands = sorted(buckets.get(reg, []), key=lambda x: -x[0])[:cap]
        selected.extend(p for _, p in cands)
        log(f"  selected {len(cands)}/{cap} from {reg}")
    log(f"total exemplars: {len(selected)}")

    # Create destination collection (drop + recreate for clean rebuilds).
    if await client.collection_exists(DST):
        await client.delete_collection(DST)
        log(f"dropped existing {DST}")
    await client.create_collection(
        collection_name=DST,
        vectors_config=qm.VectorParams(size=dim, distance=qm.Distance.COSINE),
    )
    log(f"created {DST} (dim={dim}, cosine)")

    # Upsert.
    points_to_upsert = [
        qm.PointStruct(id=str(p.id), vector=p.vector, payload=p.payload)
        for p in selected
    ]
    # Upsert in batches to avoid giant request.
    for i in range(0, len(points_to_upsert), 128):
        batch = points_to_upsert[i : i + 128]
        await client.upsert(collection_name=DST, points=batch, wait=True)
    log(f"DONE — upserted {len(points_to_upsert)} exemplars to {DST}")


if __name__ == "__main__":
    asyncio.run(main())
