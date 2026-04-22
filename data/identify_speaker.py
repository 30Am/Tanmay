"""Phase 03 addendum — identify which Deepgram speaker-id is Tanmay Bhat per video.

For each video we have speaker-id 0, 1, 2, ... assigned by Deepgram per utterance. We need
to know which ID is Tanmay so retrieval can filter to Tanmay-only chunks.

Strategy: for each speaker, sample ~150 words of their speech (from three evenly-spaced
points), send all speakers' samples to Gemini 2.5 Flash-Lite with channel context, ask
which ID is Tanmay. Output JSON is schema-enforced.

Writes `data/tanmay_speakers.json`:
  {video_id: {speaker: int|null, confidence: "low"|"medium"|"high", reasoning: "..."}}

Idempotent: skips videos already in the output file.
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

from google import genai  # noqa: E402
from google.genai import types  # noqa: E402

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
CONCURRENCY = int(os.environ.get("CONCURRENCY", "10"))
RAW = DATA / "raw"
OUT_PATH = DATA / "tanmay_speakers.json"
LOG_PATH = DATA / "logs" / "identify_speaker.log"

SYSTEM = """You identify which speaker-id in a multi-speaker transcript is Tanmay Bhat.

Context on Tanmay Bhat:
- Indian comedian, writer, podcaster, former All India Bakchod (AIB) co-founder.
- Hosts "Honestly by Tanmay Bhat" (podcasts, long-form interviews, YouTube streams on finance/startups).
- Frequently guests on "Overpowered" and other shows.
- Speaks English-dominant Hinglish, self-deprecating humor, references his weight-loss journey, AIB history, cricket fandom, AI tools, creator economy, mental-health openness.
- When hosting he asks the bulk of the questions and steers the conversation.
- When guesting he's often asked about his own content, AIB, career pivots, AI.

Given excerpts labeled by speaker-id, decide which ID is Tanmay. If the context is weak or
he's probably not present, return null.

Return JSON:
{
  "speaker": <int or null>,
  "confidence": "low|medium|high",
  "reasoning": "<one sentence>"
}
"""

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "speaker": {"type": "integer", "nullable": True},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
        "reasoning": {"type": "string"},
    },
    "required": ["speaker", "confidence", "reasoning"],
}


def log(msg: str) -> None:
    stamp = time.strftime("%H:%M:%S")
    line = f"{stamp} {msg}"
    print(line, flush=True)
    with LOG_PATH.open("a") as f:
        f.write(line + "\n")


def sample_speakers(provider_raw_path: Path, per_speaker_budget: int = 150) -> dict[int, str]:
    raw = json.loads(provider_raw_path.read_text())
    words = raw.get("results", {}).get("channels", [{}])[0].get("alternatives", [{}])[0].get("words", [])
    # Group consecutive same-speaker runs; take three evenly-spaced windows per speaker.
    per_speaker: dict[int, list[str]] = {}
    for w in words:
        spk = w.get("speaker")
        if spk is None:
            continue
        per_speaker.setdefault(spk, []).append(w.get("punctuated_word") or w["word"])

    samples: dict[int, str] = {}
    for spk, wds in per_speaker.items():
        if len(wds) <= per_speaker_budget:
            samples[spk] = " ".join(wds)
            continue
        # Three windows of ~budget/3 from 15%, 45%, 75% positions — skips intros/outros.
        win = per_speaker_budget // 3
        n = len(wds)
        segs: list[str] = []
        for pos in (0.15, 0.45, 0.75):
            start = max(0, int(n * pos) - win // 2)
            segs.append(" ".join(wds[start : start + win]))
        samples[spk] = "\n…\n".join(segs)
    return samples


async def identify_one(client: genai.Client, entry: dict, sem: asyncio.Semaphore) -> tuple[str, dict | None]:
    vid = entry["video_id"]
    src = entry["source"]
    raw_path = RAW / src / vid / "provider_raw.json"
    if not raw_path.exists():
        return vid, None

    samples = sample_speakers(raw_path)
    if not samples:
        return vid, {"speaker": None, "confidence": "low", "reasoning": "no speaker-labeled words"}
    if len(samples) == 1:
        only = next(iter(samples))
        # Single-speaker video: assume Tanmay only on his own channel.
        if src == "honestly":
            return vid, {"speaker": only, "confidence": "high", "reasoning": "single speaker on Tanmay's own channel"}
        return vid, {"speaker": None, "confidence": "low", "reasoning": "single speaker on guest-context channel"}

    prompt_lines = [
        f"Channel: {src} ({entry.get('channel') or 'unknown'})",
        f"Video title: {entry.get('title') or '(untitled)'}",
        "",
        "Speaker excerpts:",
    ]
    for spk in sorted(samples.keys()):
        prompt_lines.append(f"\n=== speaker {spk} ===\n{samples[spk]}")

    prompt = "\n".join(prompt_lines)
    async with sem:
        try:
            resp = await client.aio.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM,
                    response_mime_type="application/json",
                    response_schema=RESPONSE_SCHEMA,
                    temperature=0.0,
                    max_output_tokens=400,
                ),
            )
            return vid, json.loads(resp.text)
        except Exception as exc:  # noqa: BLE001
            log(f"  err {vid}: {type(exc).__name__} {str(exc)[:160]}")
            return vid, None


async def main() -> None:
    if not os.environ.get("GOOGLE_API_KEY"):
        log("ERROR: GOOGLE_API_KEY not set")
        sys.exit(2)

    if OUT_PATH.exists():
        out: dict[str, dict] = json.loads(OUT_PATH.read_text())
    else:
        out = {}

    idx = json.loads((DATA / "index.json").read_text())
    entries = list(idx.values()) if isinstance(idx, dict) else idx
    entries = [e for e in entries if e.get("video_id") and e["video_id"] not in out]

    if not entries:
        log("all videos already identified — nothing to do")
        return

    log(f"START pipeline — total={len(entries)} concurrency={CONCURRENCY}")
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    sem = asyncio.Semaphore(CONCURRENCY)

    tasks = [identify_one(client, e, sem) for e in entries]
    counts = {"high": 0, "medium": 0, "low": 0, "null_speaker": 0, "error": 0}
    for i, coro in enumerate(asyncio.as_completed(tasks), start=1):
        vid, result = await coro
        if result is None:
            counts["error"] += 1
            continue
        out[vid] = result
        conf = result.get("confidence", "low")
        counts[conf] = counts.get(conf, 0) + 1
        if result.get("speaker") is None:
            counts["null_speaker"] += 1
        if i % 20 == 0 or i == len(entries):
            log(f"  [{i}/{len(entries)}] {counts}")
            OUT_PATH.write_text(json.dumps(out, indent=2))

    OUT_PATH.write_text(json.dumps(out, indent=2))
    log(f"DONE — {counts}")


if __name__ == "__main__":
    asyncio.run(main())
