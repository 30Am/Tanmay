"""Tone-dial calibration — does ToneDial actually move outputs?

Generates the same content-tab prompt at 4 dial settings (low/high for each of the 4
dimensions, plus a baseline) and prints the first 500 chars of each output side-by-side
so you can eyeball whether the dial is doing anything.

Uses Haiku to keep cost ~$0.05.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO_ROOT / "apps" / "api" / ".env", override=True)

from app.models.schemas import ToneDial  # noqa: E402
from app.services.rag import RAGEngine  # noqa: E402


QUERY = "Elon Musk launched another AI product this week and everyone's losing their minds"
USER_PAYLOAD = (
    "Format: 30-second reel. Take: is this one actually different, or more hype? "
    "Land a clean punchline."
)

DIALS = {
    "baseline": ToneDial(roast_level=0.5, chaos=0.5, depth=0.5, hinglish_ratio=0.5),
    "roast-high": ToneDial(roast_level=0.9, chaos=0.5, depth=0.5, hinglish_ratio=0.5),
    "roast-low": ToneDial(roast_level=0.1, chaos=0.5, depth=0.5, hinglish_ratio=0.5),
    "chaos-high": ToneDial(roast_level=0.5, chaos=0.9, depth=0.5, hinglish_ratio=0.5),
    "chaos-low": ToneDial(roast_level=0.5, chaos=0.1, depth=0.5, hinglish_ratio=0.5),
    "depth-high": ToneDial(roast_level=0.5, chaos=0.5, depth=0.9, hinglish_ratio=0.5),
    "hinglish-high": ToneDial(roast_level=0.5, chaos=0.5, depth=0.5, hinglish_ratio=0.9),
    "hinglish-low": ToneDial(roast_level=0.5, chaos=0.5, depth=0.5, hinglish_ratio=0.1),
}


async def run_one(engine: RAGEngine, label: str, tone: ToneDial) -> str:
    result = await engine.generate(
        tab="content",
        query=QUERY,
        user_payload=USER_PAYLOAD,
        tone=tone,
        model=os.environ.get("ANTHROPIC_MODEL_UTILITY", "claude-haiku-4-5-20251001"),
        retrieval_top_k=5,
        exemplars_k=4,
        exemplar_registers=["comedic", "roast", "informative"],
        max_tokens=600,
    )
    print(f"\n{'#' * 70}")
    print(f"# {label:12s}  tone: roast={tone.roast_level} chaos={tone.chaos} depth={tone.depth} hi={tone.hinglish_ratio}")
    print(f"# cost≈${(result.input_tokens * 1.0 + result.output_tokens * 5.0) / 1_000_000:.4f}")
    print(f"{'#' * 70}")
    # Grab just the script portion if the output has sections
    txt = result.text.strip()
    print(txt[:900])
    return txt


async def main() -> None:
    engine = RAGEngine()
    for label, tone in DIALS.items():
        await run_one(engine, label, tone)


if __name__ == "__main__":
    asyncio.run(main())
