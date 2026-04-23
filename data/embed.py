"""Phase 03 — Chunk + tag + embed + upsert to Qdrant.

For each video with a provider_raw.json, run:
  1. Extract word-level Deepgram words
  2. Semantic chunk with speaker + pause awareness (chunker.py)
  3. Tag each chunk via Gemini 2.5 Flash-Lite (tagger.py)
  4. Embed batch via Voyage-3 (embedder.py)
  5. Upsert into Qdrant collection `tanmay_chunks` with full payload

Idempotent: marks `raw/<source>/<video_id>/.phase03_done` on success; skips on re-run.

Env (loaded from apps/api/.env automatically):
  GOOGLE_API_KEY, VOYAGE_API_KEY, QDRANT_URL
  GEMINI_CONCURRENCY=10   parallel Gemini tag calls
  VOYAGE_BATCH=32         Voyage embeddings per request
  LIMIT=N                 process first N videos only (for probe runs)
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

DATA = Path(__file__).parent
REPO_ROOT = DATA.parent
sys.path.insert(0, str(REPO_ROOT))

# Load apps/api/.env into os.environ before importing pipeline modules.
from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO_ROOT / "apps" / "api" / ".env", override=True)

from packages.ingestion.pipeline.chunker import Word, chunk_transcript  # noqa: E402
from packages.ingestion.pipeline.embedder import EmbeddedChunk, Embedder, QdrantUpserter  # noqa: E402
from packages.ingestion.pipeline.tagger import Tagger  # noqa: E402

RAW = DATA / "raw"
LOG_PATH = DATA / "logs" / "embed.log"
STATE_PATH = DATA / "logs" / "embed_state.json"

GEMINI_CONCURRENCY = int(os.environ.get("GEMINI_CONCURRENCY", "10"))
VOYAGE_BATCH = int(os.environ.get("VOYAGE_BATCH", "32"))
LIMIT = int(os.environ.get("LIMIT", "0"))


def log(msg: str) -> None:
    stamp = time.strftime("%H:%M:%S")
    line = f"{stamp} {msg}"
    print(line, flush=True)
    with LOG_PATH.open("a") as f:
        f.write(line + "\n")


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"completed": [], "total_chunks": 0}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2))


def extract_words(provider_raw: dict) -> list[Word]:
    dg = provider_raw.get("results", {}).get("channels", [{}])[0]
    alt = dg.get("alternatives", [{}])[0]
    return [
        Word(
            text=w.get("punctuated_word") or w["word"],
            start=w["start"],
            end=w["end"],
            speaker=w.get("speaker"),
        )
        for w in alt.get("words", [])
    ]


async def process_video(entry: dict, tagger: Tagger, embedder: Embedder, upserter: QdrantUpserter, sem: asyncio.Semaphore) -> int:
    vid = entry["video_id"]
    src = entry["source"]
    vid_dir = RAW / src / vid
    done_marker = vid_dir / ".phase03_done"
    if done_marker.exists():
        return -1  # signal "skip"

    raw_path = vid_dir / "provider_raw.json"
    transcript_path = vid_dir / "transcript.json"
    if not raw_path.exists():
        log(f"  skip {src}/{vid}: no provider_raw.json")
        return 0

    raw = json.loads(raw_path.read_text())
    words = extract_words(raw)
    if not words:
        log(f"  skip {src}/{vid}: zero words")
        return 0

    source_id = f"{src}_{vid}"
    chunks = chunk_transcript(source_id, words)
    if not chunks:
        log(f"  skip {src}/{vid}: zero chunks")
        return 0

    # Metadata from transcript.json (language) + index entry.
    transcript = json.loads(transcript_path.read_text()) if transcript_path.exists() else {}
    video_meta = {
        "source": src,
        "video_id": vid,
        "title": entry.get("title"),
        "url": entry.get("webpage_url") or entry.get("url") or f"https://www.youtube.com/watch?v={vid}",
        "upload_date": entry.get("upload_date"),
        "duration_s": entry.get("duration_s"),
        "channel": entry.get("channel"),
        "language": transcript.get("language"),
    }

    # Tag each chunk in parallel, bounded.
    async def tag_one(text: str) -> dict:
        async with sem:
            return await tagger.tag(text)

    tags = await asyncio.gather(*(tag_one(c.text) for c in chunks))

    # Embed in batches.
    vectors: list[list[float]] = []
    for i in range(0, len(chunks), VOYAGE_BATCH):
        batch = chunks[i : i + VOYAGE_BATCH]
        vecs = await embedder.embed([c.text for c in batch])
        vectors.extend(vecs)

    payloads = []
    assert len(chunks) == len(tags) == len(vectors)
    for c, t, v in zip(chunks, tags, vectors):
        payloads.append(
            EmbeddedChunk(
                chunk_id=c.chunk_id,
                vector=v,
                payload={
                    **video_meta,
                    "source_id": c.source_id,
                    "text": c.text,
                    "start_seconds": c.start_seconds,
                    "end_seconds": c.end_seconds,
                    "speaker": c.speaker,
                    "speakers": c.speakers,
                    **t,
                },
            )
        )
    await upserter.upsert(payloads)
    done_marker.touch()
    log(f"DONE  {src}/{vid} — {len(chunks)} chunks, dom_speakers={sorted({p.payload['speaker'] for p in payloads if p.payload['speaker'] is not None})}")
    return len(chunks)


async def main() -> None:
    # Basic env validation.
    for k in ("GOOGLE_API_KEY", "VOYAGE_API_KEY"):
        if not os.environ.get(k):
            log(f"ERROR: {k} not set")
            sys.exit(2)

    state = load_state()
    completed = set(state.get("completed", []))

    idx = json.loads((DATA / "index.json").read_text())
    entries = list(idx.values()) if isinstance(idx, dict) else idx
    entries = [e for e in entries if e.get("video_id")]
    entries.sort(key=lambda e: e.get("duration_s") or 0)  # short first for fast feedback
    if LIMIT:
        entries = entries[:LIMIT]

    tagger = Tagger()
    embedder = Embedder()
    upserter = QdrantUpserter()
    await upserter.ensure_collection()
    sem = asyncio.Semaphore(GEMINI_CONCURRENCY)

    log(
        f"START pipeline — total={len(entries)} gemini_concurrency={GEMINI_CONCURRENCY} "
        f"voyage_batch={VOYAGE_BATCH} already_done={len(completed)}"
    )

    running_chunks = state.get("total_chunks", 0)
    for i, e in enumerate(entries, start=1):
        vid = e["video_id"]
        if vid in completed:
            continue
        try:
            n = await process_video(e, tagger, embedder, upserter, sem)
        except Exception as exc:  # noqa: BLE001
            log(f"  ERROR {e['source']}/{vid}: {type(exc).__name__} {str(exc)[:200]}")
            continue
        if n == -1:
            completed.add(vid)
            continue
        if n > 0:
            running_chunks += n
            completed.add(vid)
            state["completed"] = sorted(completed)
            state["total_chunks"] = running_chunks
            save_state(state)
        if i % 10 == 0 or i == len(entries):
            log(f"  [{i}/{len(entries)}] done={len(completed)} total_chunks={running_chunks}")

    log(f"DONE pipeline — {len(completed)} videos processed, {running_chunks} chunks in Qdrant")


if __name__ == "__main__":
    asyncio.run(main())
