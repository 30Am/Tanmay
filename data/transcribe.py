"""Phase 02 — Deepgram transcription pipeline.

Per video, streaming/delete:
  1. Download audio with yt-dlp → 32 kbps mono opus (~10 MB per hour)
  2. POST to Deepgram /v1/listen with nova-3 + diarize + smart_format + detect_language + utterances
  3. Save provider_raw.json (unmodified response) + transcript.json (normalized)
  4. Delete audio file
  5. Track cumulative billed minutes; hard-stop at BUDGET_MIN

Idempotent: skips videos that already have transcript.json. Safe to re-run.

Outputs:
  raw/<source>/<video_id>/provider_raw.json
  raw/<source>/<video_id>/transcript.json

Env:
  DEEPGRAM_API_KEY   (required)
  WORKERS            parallelism (default 5)
  BUDGET_USD         hard budget cap in dollars (default 30)
  RATE_PER_MIN       $/minute billed (default 0.0043 for Nova-3)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from typing import Any

import requests

DATA = Path(__file__).parent
RAW = DATA / "raw"
LOG_PATH = DATA / "logs" / "transcribe.log"
STATE_PATH = DATA / "logs" / "transcribe_state.json"

API_KEY = os.environ.get("DEEPGRAM_API_KEY") or ""
if not API_KEY:
    print("ERROR: DEEPGRAM_API_KEY not set", file=sys.stderr)
    sys.exit(2)

WORKERS = int(os.environ.get("WORKERS", "5"))
BUDGET_USD = float(os.environ.get("BUDGET_USD", "30"))
RATE_PER_MIN = float(os.environ.get("RATE_PER_MIN", "0.0043"))
BUDGET_MIN = BUDGET_USD / RATE_PER_MIN  # minutes of audio we can afford
COOKIES_BROWSER = os.environ.get("YTDLP_COOKIES_BROWSER", "").strip()  # e.g. "chrome", "safari", "firefox"

DEEPGRAM_URL = (
    "https://api.deepgram.com/v1/listen"
    "?model=nova-3"
    "&diarize=true"
    "&smart_format=true"
    "&detect_language=true"
    "&utterances=true"
    "&punctuate=true"
)

_state_lock = Lock()
_log_lock = Lock()
_billed_minutes = 0.0


def log(msg: str) -> None:
    stamp = time.strftime("%H:%M:%S")
    line = f"{stamp} {msg}"
    with _log_lock:
        print(line, flush=True)
        with LOG_PATH.open("a") as f:
            f.write(line + "\n")


def load_state() -> dict[str, Any]:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"billed_minutes": 0.0, "completed": [], "failed": []}


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2))


def download_audio(vid: str, url: str, out: Path) -> bool:
    """yt-dlp → 32 kbps mono opus in webm container, small + speech-grade."""
    cmd = [
        "yt-dlp",
        "--no-warnings",
        "--no-progress",
        "--retries",
        "5",
        "--socket-timeout",
        "60",
        "--sleep-requests",
        "2",
        "--sleep-interval",
        "3",
        "--max-sleep-interval",
        "8",
        "--ignore-no-formats-error",
        "-f",
        "bestaudio/best",
        "-x",
        "--audio-format",
        "opus",
        "--audio-quality",
        "32K",
        "--postprocessor-args",
        "-ac 1 -b:a 32k",
        "-o",
        str(out.with_suffix(".%(ext)s")),
    ]
    if COOKIES_BROWSER:
        cmd.extend(["--cookies-from-browser", COOKIES_BROWSER])
    cmd.append(url)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            log(f"  dl-fail {vid}: {r.stderr.strip().splitlines()[-1][:140]}")
            return False
    except subprocess.TimeoutExpired:
        log(f"  dl-timeout {vid}")
        return False
    return out.exists()


def deepgram_transcribe(vid: str, audio_path: Path) -> dict | None:
    """POST the audio file to Deepgram; return the parsed JSON response."""
    try:
        with audio_path.open("rb") as f:
            r = requests.post(
                DEEPGRAM_URL,
                headers={
                    "Authorization": f"Token {API_KEY}",
                    "Content-Type": "audio/ogg",
                },
                data=f,
                timeout=600,
            )
        if r.status_code != 200:
            log(f"  dg-fail {vid}: HTTP {r.status_code} {r.text[:160]}")
            return None
        return r.json()
    except Exception as e:  # noqa: BLE001
        log(f"  dg-error {vid}: {type(e).__name__} {str(e)[:160]}")
        return None


def normalize(vid: str, raw: dict, duration_s: float) -> dict:
    """Flatten Deepgram's response into our downstream-friendly shape."""
    channel = raw.get("results", {}).get("channels", [{}])[0]
    alt = channel.get("alternatives", [{}])[0]
    detected_language = channel.get("detected_language")
    language_confidence = channel.get("language_confidence")
    utterances = raw.get("results", {}).get("utterances", []) or []

    segments = []
    for u in utterances:
        segments.append(
            {
                "speaker": u.get("speaker"),
                "start": u.get("start"),
                "end": u.get("end"),
                "text": u.get("transcript") or "",
                "confidence": u.get("confidence"),
            }
        )

    return {
        "video_id": vid,
        "provider": "deepgram",
        "model": "nova-3",
        "duration_s": duration_s,
        "language": detected_language,
        "language_confidence": language_confidence,
        "full_text": alt.get("transcript") or "",
        "num_speakers": len({s["speaker"] for s in segments if s.get("speaker") is not None}),
        "segments": segments,
        "processed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


def process_one(entry: dict, state: dict) -> str:
    """Return status string: 'skip' | 'ok' | 'dl-fail' | 'dg-fail' | 'budget'."""
    global _billed_minutes
    vid = entry["video_id"]
    src = entry["source"]
    url = entry.get("webpage_url") or entry.get("url") or f"https://www.youtube.com/watch?v={vid}"
    duration_s = entry.get("duration_s") or 0
    out_dir = RAW / src / vid
    out_dir.mkdir(parents=True, exist_ok=True)
    transcript_path = out_dir / "transcript.json"
    raw_path = out_dir / "provider_raw.json"
    audio_path = out_dir / "audio.opus"

    if transcript_path.exists():
        return "skip"

    # Budget gate — check BEFORE downloading so we don't waste bandwidth.
    duration_min = duration_s / 60.0
    with _state_lock:
        if _billed_minutes + duration_min > BUDGET_MIN:
            log(f"  budget-skip {vid} ({duration_min:.1f} min would exceed cap)")
            (out_dir / ".budget_exceeded").touch()
            return "budget"

    log(f"START {src}/{vid} ({duration_min:.1f} min)")

    if not download_audio(vid, url, audio_path):
        return "dl-fail"

    size_mb = audio_path.stat().st_size / 1024 / 1024
    log(f"  audio {vid}: {size_mb:.1f} MB")

    raw = deepgram_transcribe(vid, audio_path)
    if raw is None:
        audio_path.unlink(missing_ok=True)
        return "dg-fail"

    raw_path.write_text(json.dumps(raw, ensure_ascii=False))
    normalized = normalize(vid, raw, duration_s)
    transcript_path.write_text(json.dumps(normalized, indent=2, ensure_ascii=False))

    # Delete audio immediately (disk-tight).
    audio_path.unlink(missing_ok=True)

    with _state_lock:
        _billed_minutes += duration_min
        state["billed_minutes"] = _billed_minutes
        state["completed"].append(vid)
        save_state(state)

    log(
        f"DONE  {src}/{vid} — {len(normalized['segments'])} seg, "
        f"{normalized['num_speakers']} spk, cum=${_billed_minutes * RATE_PER_MIN:.2f}"
    )
    return "ok"


def main() -> None:
    global _billed_minutes
    state = load_state()
    _billed_minutes = state.get("billed_minutes", 0.0)

    index = json.loads((DATA / "index.json").read_text())
    # index.json is a dict keyed by (source, video_id) or a list — handle both.
    if isinstance(index, dict):
        entries = list(index.values())
    else:
        entries = index

    # Filter to entries with a usable video_id; URL is derived from webpage_url or video_id.
    entries = [e for e in entries if e.get("video_id")]
    # Process shortest videos first — cheap failures, fast feedback, better budget efficiency.
    entries.sort(key=lambda e: e.get("duration_s") or 1e9)

    limit = int(os.environ.get("LIMIT", "0"))
    if limit:
        entries = entries[:limit]

    total = len(entries)
    log(
        f"START pipeline — total={total} workers={WORKERS} "
        f"budget=${BUDGET_USD:.0f} (~{BUDGET_MIN:.0f} min) already_billed=${_billed_minutes * RATE_PER_MIN:.2f}"
    )

    results = {"skip": 0, "ok": 0, "dl-fail": 0, "dg-fail": 0, "budget": 0}

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futs = {pool.submit(process_one, e, state): e for e in entries}
        for i, fut in enumerate(as_completed(futs), start=1):
            try:
                status = fut.result()
            except Exception as e:  # noqa: BLE001
                status = "dg-fail"
                log(f"  worker-exception: {e!r}")
            results[status] = results.get(status, 0) + 1
            if i % 10 == 0 or i == total:
                log(
                    f"  [{i}/{total}] running totals: {results} "
                    f"cost=${_billed_minutes * RATE_PER_MIN:.2f}"
                )

    log(f"DONE pipeline — {results} total_cost=${_billed_minutes * RATE_PER_MIN:.2f}")


if __name__ == "__main__":
    main()
