#!/usr/bin/env python3
"""
Download audio from all Moonshot Vimeo ads and transcribe with Deepgram.
Outputs an enriched tanmay_ads.json ready to ingest into Qdrant.

Usage:
    cd /path/to/Tanmaygpt
    uv run --project apps/api python scripts/scrape_moonshot_ads.py
    uv run --project apps/api python scripts/scrape_moonshot_ads.py --workers 4
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

import httpx

# ── Config ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
ENV_PATH = ROOT / "apps" / "api" / ".env"

# Load .env
for line in ENV_PATH.read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())

DEEPGRAM_API_KEY = os.environ["DEEPGRAM_API_KEY"]
PROJECTS_FILE = DATA_DIR / "moonshot_projects.json"
OUTPUT_FILE = DATA_DIR / "tanmay_ads.json"
AUDIO_DIR = Path(tempfile.gettempdir()) / "moonshot_audio"
AUDIO_DIR.mkdir(exist_ok=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

def vimeo_id_valid(vimeo_id: str) -> bool:
    """Return True only for plain numeric IDs (not full MP4 URLs)."""
    return bool(re.match(r"^\d{7,12}$", str(vimeo_id).strip()))


def download_audio(vimeo_id: str) -> Path | None:
    """Download best audio for a Vimeo ID. Returns path or None on failure."""
    out = AUDIO_DIR / f"{vimeo_id}.m4a"
    if out.exists() and out.stat().st_size > 10_000:
        return out  # already cached

    result = subprocess.run(
        [
            "yt-dlp",
            "-f", "bestaudio[ext=m4a]/bestaudio",
            "--output", str(AUDIO_DIR / "%(id)s.%(ext)s"),
            "--no-playlist",
            "--quiet",
            f"https://vimeo.com/{vimeo_id}",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    # yt-dlp may rename the extension
    for ext in ("m4a", "webm", "opus", "mp3", "ogg"):
        candidate = AUDIO_DIR / f"{vimeo_id}.{ext}"
        if candidate.exists():
            return candidate
    print(f"  [WARN] audio download failed for {vimeo_id}: {result.stderr[:200]}")
    return None


async def transcribe_deepgram(audio_path: Path, client: httpx.AsyncClient) -> str:
    """Transcribe an audio file using Deepgram Nova-3 and return raw transcript text."""
    audio_bytes = audio_path.read_bytes()
    # Detect mime type from extension
    ext = audio_path.suffix.lstrip(".")
    mime = {
        "m4a": "audio/mp4",
        "webm": "audio/webm",
        "opus": "audio/ogg",
        "mp3": "audio/mpeg",
        "ogg": "audio/ogg",
    }.get(ext, "audio/mp4")

    resp = await client.post(
        "https://api.deepgram.com/v1/listen",
        params={
            "model": "nova-2",
            "smart_format": "true",
            "punctuate": "true",
            "paragraphs": "false",
            "detect_language": "true",   # auto-detect Hindi vs English vs Hinglish
            "diarize": "false",
        },
        headers={
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": mime,
        },
        content=audio_bytes,
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    try:
        transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]
        return transcript.strip()
    except (KeyError, IndexError):
        return ""


def build_ad_entry(project: dict, transcript: str) -> dict:
    """Build a tanmay_ads.json entry from project metadata + transcript."""
    title = project["title"].strip()
    brand = project["brand"].strip()
    vimeo_id = str(project["vimeo_id"]).strip()

    # Infer celebrities from title
    celeb_patterns = [
        "Rahul Dravid", "Ranveer Singh", "Deepika Padukone", "Alia Bhatt",
        "Shah Rukh Khan", "Virat Kohli", "MS Dhoni", "MC Stan", "Diljit Dosanjh",
        "Vicky Kaushal", "Sachin Tendulkar", "Glenn McGrath", "Yuvraj Singh",
        "Arjun Kapoor", "Karan Johar", "Madhuri Dixit", "Sonu Nigam", "Shaan",
        "Udit Narayan", "Alka Yagnik", "Anil Kapoor", "Govinda", "Daler Mehndi",
        "Bappi Lahiri", "Karisma Kapoor", "Leander Paes", "Ravi Shastri",
        "Jim Sarbh", "Neeraj Chopra", "Kapil Dev", "Warner", "Rajamouli",
        "Johnny Sins", "Peyush Bansal", "Rishabh Pant", "Vikrant Massey",
        "Anupam Mittal", "Vishwanathan Anand",
    ]
    celebrities = [c for c in celeb_patterns if c.lower() in title.lower()]

    # Infer product category from brand
    category_map = {
        "CRED": "fintech",
        "Meesho": "ecommerce",
        "Boldcare": "health_wellness",
        "Subway": "food_qsr",
        "Lenskart": "eyewear_retail",
        "Shark Tank": "reality_tv_promo",
        "Firebolt": "consumer_electronics",
        "Shaadi": "matrimony",
        "MMT": "travel",
        "Vadilal": "ice_cream_fmcg",
        "Hotstar": "ott_streaming",
        "Swiggy": "food_delivery",
        "Campus Shoes": "footwear",
        "Dr. Agarwals Eye Hospital": "healthcare",
        "Mokobara": "travel_luggage",
        "Muthoot Fincorp": "gold_finance",
        "Aspora": "tech_hardware",
        "Call Me Chunky": "fashion",
        "Wildstone": "personal_care",
        "Oyo": "hospitality",
    }
    product_category = category_map.get(brand, "brand_advertising")

    # Use summary from CMS if meaningful, else derive from title
    summary = project.get("summary", "").strip()
    if not summary or summary in (".", ""):
        summary = ""

    return {
        "ad_id": f"moonshot_{project['id']:03d}",
        "brand": brand,
        "product_category": product_category,
        "year": 2024,
        "duration_seconds": None,   # unknown without video metadata
        "platform": "youtube",
        "url": f"https://vimeo.com/{vimeo_id}",
        "celebrities": celebrities,
        "script": transcript,
        "hook": transcript[:150] if transcript else "",
        "setup_summary": summary,
        "product_reveal_line": "",
        "cynicism_beat": "",
        "cta": "",
        "notes": f"Real Moonshot ad. Vimeo: {vimeo_id}. Title: {title}",
        "source": "moonshot_vimeo",
    }


# ── Main ─────────────────────────────────────────────────────────────────────

async def process_project(
    project: dict,
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
) -> dict | None:
    vimeo_id = str(project["vimeo_id"]).strip()
    title = project["title"].strip()

    if not vimeo_id_valid(vimeo_id):
        print(f"  [SKIP] {title} — not a plain Vimeo ID ({vimeo_id[:40]})")
        return None

    print(f"  [DL]   {title} ({vimeo_id})")
    audio_path = await asyncio.get_event_loop().run_in_executor(
        None, download_audio, vimeo_id
    )
    if not audio_path:
        print(f"  [FAIL] {title} — audio download failed")
        return None

    async with sem:
        print(f"  [TX]   {title} — transcribing {audio_path.stat().st_size // 1024}KB")
        try:
            transcript = await transcribe_deepgram(audio_path, client)
        except Exception as exc:
            print(f"  [FAIL] {title} — transcription error: {exc}")
            return None

    if not transcript:
        print(f"  [SKIP] {title} — empty transcript")
        return None

    print(f"  [OK]   {title} — {len(transcript)} chars")
    return build_ad_entry(project, transcript)


async def main(workers: int) -> None:
    projects = json.loads(PROJECTS_FILE.read_text())
    print(f"Loaded {len(projects)} projects from {PROJECTS_FILE}")

    # Load existing handcrafted ads so we preserve them
    existing_ads: list[dict] = []
    if OUTPUT_FILE.exists():
        existing_ads = json.loads(OUTPUT_FILE.read_text())
        # Keep only handcrafted (non-moonshot) entries
        existing_ads = [a for a in existing_ads if a.get("source") != "moonshot_vimeo"]
        print(f"Keeping {len(existing_ads)} existing handcrafted entries")

    sem = asyncio.Semaphore(workers)   # limit concurrent Deepgram calls
    async with httpx.AsyncClient() as client:
        tasks = [process_project(p, client, sem) for p in projects]
        results = await asyncio.gather(*tasks)

    new_ads = [r for r in results if r]
    print(f"\nTranscribed {len(new_ads)}/{len(projects)} ads successfully")

    all_ads = existing_ads + new_ads
    OUTPUT_FILE.write_text(json.dumps(all_ads, indent=2, ensure_ascii=False))
    print(f"Wrote {len(all_ads)} total entries to {OUTPUT_FILE}")

    # Print summary by brand
    from collections import Counter
    brands = Counter(a["brand"] for a in new_ads)
    print("\nBreakdown by brand:")
    for brand, count in brands.most_common():
        print(f"  {brand}: {count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape and transcribe Moonshot ads")
    parser.add_argument("--workers", type=int, default=5, help="Concurrent Deepgram calls")
    args = parser.parse_args()
    asyncio.run(main(args.workers))
