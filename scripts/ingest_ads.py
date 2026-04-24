#!/usr/bin/env python3
"""Ingest data/tanmay_ads.json into the Qdrant 'tanmay_ads' collection.

Each ad is stored as a single point whose text is the full script.
Metadata kept in payload for filtering and display.

Usage:
    cd /path/to/Tanmaygpt
    uv run python scripts/ingest_ads.py                   # uses .env
    uv run python scripts/ingest_ads.py --qdrant-url http://...  # override
    uv run python scripts/ingest_ads.py --reset           # drop+recreate collection first
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import hashlib
from pathlib import Path

# Load .env from apps/api
env_path = Path(__file__).parent.parent / "apps" / "api" / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

import voyageai
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qm

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
VOYAGE_API_KEY = os.environ["VOYAGE_API_KEY"]
VOYAGE_MODEL = os.environ.get("VOYAGE_MODEL", "voyage-3")
COLLECTION = "tanmay_ads"
VECTOR_SIZE = 1024
DATA_PATH = Path(__file__).parent.parent / "data" / "tanmay_ads.json"


def chunk_id_for(ad: dict) -> str:
    """Stable deterministic ID based on brand + script hash."""
    content = f"{ad['brand']}:{ad['script']}"
    return hashlib.sha256(content.encode()).hexdigest()[:24]


async def main(qdrant_url: str, reset: bool) -> None:
    ads = json.loads(DATA_PATH.read_text())
    print(f"Loaded {len(ads)} ads from {DATA_PATH}")

    voyage = voyageai.AsyncClient(api_key=VOYAGE_API_KEY)
    qdrant = AsyncQdrantClient(url=qdrant_url)

    # Create (or reset) collection
    collections = await qdrant.get_collections()
    existing = {c.name for c in collections.collections}

    if COLLECTION in existing and reset:
        await qdrant.delete_collection(COLLECTION)
        print(f"Dropped collection '{COLLECTION}'")
        existing.discard(COLLECTION)

    if COLLECTION not in existing:
        await qdrant.create_collection(
            collection_name=COLLECTION,
            vectors_config=qm.VectorParams(size=VECTOR_SIZE, distance=qm.Distance.COSINE),
        )
        print(f"Created collection '{COLLECTION}'")
    else:
        print(f"Collection '{COLLECTION}' already exists — upserting")

    # Embed all scripts in one batch (Voyage supports up to 128 per call)
    scripts = [ad["script"] for ad in ads]
    print(f"Embedding {len(scripts)} scripts with {VOYAGE_MODEL}…")
    result = await voyage.embed(scripts, model=VOYAGE_MODEL, input_type="document")
    embeddings = result.embeddings
    print(f"Got {len(embeddings)} embeddings")

    # Build Qdrant points
    points = []
    for ad, vec in zip(ads, embeddings):
        cid = chunk_id_for(ad)
        payload = {
            "chunk_id": cid,
            "ad_id": ad["ad_id"],
            "brand": ad["brand"],
            "product_category": ad["product_category"],
            "year": ad.get("year"),
            "duration_seconds": ad.get("duration_seconds"),
            "platform": ad.get("platform", "youtube"),
            "celebrities": ad.get("celebrities", []),
            "text": ad["script"],
            "hook": ad.get("hook", ""),
            "cta": ad.get("cta", ""),
            "cynicism_beat": ad.get("cynicism_beat", ""),
            "setup_summary": ad.get("setup_summary", ""),
            "notes": ad.get("notes", ""),
            "url": ad.get("url", ""),
            # Fields used by _to_chunk in RAGEngine
            "source": "tanmay_ads",
            "video_id": ad["ad_id"],
            "title": f"{ad['brand']} ad",
            "start_seconds": None,
            "end_seconds": None,
            "register": "comedic",
            "is_tanmay": True,
            "topic_tags": [ad["product_category"], "ad", "sponsored"] + (
                ["celebrity_cameo"] if ad.get("celebrities") else []
            ),
        }
        points.append(
            qm.PointStruct(
                id=int(cid[:8], 16),   # numeric ID from first 8 hex chars
                vector=vec,
                payload=payload,
            )
        )

    # Upsert
    op = await qdrant.upsert(collection_name=COLLECTION, points=points)
    print(f"Upserted {len(points)} ads → status: {op.status}")

    # Quick sanity check
    count = await qdrant.count(COLLECTION)
    print(f"Collection '{COLLECTION}' now has {count.count} points")
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Tanmay ad corpus into Qdrant")
    parser.add_argument("--qdrant-url", default=QDRANT_URL)
    parser.add_argument("--reset", action="store_true", help="Drop and recreate collection first")
    args = parser.parse_args()
    asyncio.run(main(args.qdrant_url, args.reset))
