"""Phase 01 collector: metadata (yt-dlp) + transcripts (youtube-transcript-api).

For each manifest entry, fetch:
  - raw/{source}/{vid}/{vid}.info.json  (full yt-dlp metadata, no subtitle calls)
  - raw/{source}/{vid}/{vid}.{lang}.json (transcript: list of {start, duration, text})

Resumable: skips entries that already have both files (or a .no_transcript marker).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import warnings
from pathlib import Path
from typing import Any

warnings.filterwarnings("ignore")

SKIP_TRANSCRIPTS = os.environ.get("SKIP_TRANSCRIPTS") == "1"

if not SKIP_TRANSCRIPTS:
    from youtube_transcript_api import YouTubeTranscriptApi  # noqa: E402
    from youtube_transcript_api._errors import (  # noqa: E402
        NoTranscriptFound,
        TranscriptsDisabled,
        VideoUnavailable,
    )

DATA = Path(__file__).parent
RAW = DATA / "raw"
LOGS = DATA / "logs"
LOGS.mkdir(exist_ok=True)

PREF_LANGS = ["en", "hi", "en-US", "en-GB", "en-IN"]


def log(line: str) -> None:
    with (LOGS / "collect.log").open("a") as f:
        f.write(f"{time.strftime('%H:%M:%S')} {line}\n")
    print(line, flush=True)


def fetch_metadata(vid: str, out_dir: Path) -> bool:
    out = out_dir / f"{vid}.info.json"
    if out.exists():
        return True
    try:
        proc = subprocess.run(
            [
                "yt-dlp",
                "--skip-download",
                "--write-info-json",
                "--no-write-subs",
                "--no-write-auto-subs",
                "--no-warnings",
                "--no-progress",
                "--retries",
                "3",
                "--socket-timeout",
                "60",
                "--ignore-no-formats-error",  # get info.json even on live/restricted formats
                "-o",
                str(out_dir / "%(id)s.%(ext)s"),
                f"https://www.youtube.com/watch?v={vid}",
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )
        if proc.returncode != 0:
            log(f"  meta-fail {vid}: {proc.stderr.strip().splitlines()[-1] if proc.stderr else '?'}")
            return False
        return out.exists()
    except subprocess.TimeoutExpired:
        log(f"  meta-timeout {vid}")
        return False


def fetch_transcript(api: YouTubeTranscriptApi, vid: str, out_dir: Path) -> str | None:
    """Return lang of saved transcript, or None if unavailable."""
    marker = out_dir / ".no_transcript"
    # skip if already have any .{lang}.json
    existing = list(out_dir.glob(f"{vid}.*.json"))
    existing = [p for p in existing if not p.name.endswith(".info.json")]
    if existing:
        return existing[0].stem.rsplit(".", 1)[-1]
    if marker.exists():
        return None

    try:
        lst = api.list(vid)
    except (TranscriptsDisabled, VideoUnavailable) as e:
        log(f"  no-transcript {vid}: {type(e).__name__}")
        marker.touch()
        return None
    except Exception as e:
        log(f"  list-error {vid}: {type(e).__name__}: {e}")
        return None

    # Choose best transcript: prefer manual over auto, prefer PREF_LANGS order.
    manual = [t for t in lst if not t.is_generated]
    auto = [t for t in lst if t.is_generated]

    def pick(candidates: list) -> Any:
        for lang in PREF_LANGS:
            for t in candidates:
                if t.language_code == lang:
                    return t
        return candidates[0] if candidates else None

    chosen = pick(manual) or pick(auto)
    if chosen is None:
        log(f"  no-usable-transcript {vid}")
        marker.touch()
        return None

    try:
        fetched = chosen.fetch()
    except Exception as e:
        log(f"  fetch-error {vid} [{chosen.language_code}]: {type(e).__name__}: {e}")
        return None

    out = out_dir / f"{vid}.{chosen.language_code}.json"
    payload = {
        "video_id": vid,
        "language_code": chosen.language_code,
        "language": chosen.language,
        "is_generated": chosen.is_generated,
        "snippets": [
            {"start": s.start, "duration": s.duration, "text": s.text}
            for s in fetched.snippets
        ],
    }
    out.write_text(json.dumps(payload, ensure_ascii=False))
    return chosen.language_code


def main() -> None:
    manifest = json.loads((DATA / "manifest.json").read_text())
    api = None if SKIP_TRANSCRIPTS else YouTubeTranscriptApi()

    total = len(manifest)
    results = {"meta_ok": 0, "meta_fail": 0, "tx_ok": 0, "tx_none": 0}

    log(f"START pass: SKIP_TRANSCRIPTS={SKIP_TRANSCRIPTS} total={total}")

    for i, entry in enumerate(manifest, start=1):
        source = entry["source"]
        vid = entry["video_id"]
        out_dir = RAW / source / vid
        out_dir.mkdir(parents=True, exist_ok=True)

        log(f"[{i}/{total}] {source}/{vid} — {(entry.get('title') or '')[:60]}")

        if fetch_metadata(vid, out_dir):
            results["meta_ok"] += 1
        else:
            results["meta_fail"] += 1

        if not SKIP_TRANSCRIPTS:
            lang = fetch_transcript(api, vid, out_dir)
            if lang:
                results["tx_ok"] += 1
            else:
                results["tx_none"] += 1

        time.sleep(1.0)  # gentle pacing between videos

    log(f"DONE: {results}")


if __name__ == "__main__":
    main()
