"""Phase 05 smoke test — exercise the RAG pipeline on each tab.

Runs one sample query per tab, prints the generation + citations + cost.
Uses the scaffolded RAGEngine at apps/api/app/services/rag.py.

Env: pulls from apps/api/.env via python-dotenv.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO_ROOT / "apps" / "api" / ".env", override=True)

from app.models.schemas import ToneDial  # noqa: E402
from app.services.rag import RAGEngine  # noqa: E402


async def smoke_one(engine: RAGEngine, tab: str, query: str, user_payload: str, *, use_haiku: bool = False) -> None:
    print(f"\n{'='*80}\nTAB: {tab}  MODEL: {'haiku' if use_haiku else 'sonnet'}\nQUERY: {query}\n{'='*80}")
    model = None
    if use_haiku:
        import os
        model = os.environ.get("ANTHROPIC_MODEL_UTILITY", "claude-haiku-4-5-20251001")

    registers = {
        "content": ["comedic", "reflective", "informative"],
        "ad": ["comedic", "informative"],
        "qa": ["reflective", "informative", "comedic"],
    }[tab]

    result = await engine.generate(
        tab=tab,
        query=query,
        user_payload=user_payload,
        tone=ToneDial(roast_level=0.5, chaos=0.5, depth=0.5, hinglish_ratio=0.5),
        model=model,
        retrieval_top_k=6,  # lower during dev to save tokens
        exemplars_k=4,
        exemplar_registers=registers,
        max_tokens=1200,
    )

    print(f"\n--- OUTPUT ({len(result.text)} chars) ---\n{result.text[:3000]}")
    print(f"\n--- CITATIONS ({len(result.citations)} chunks, max_sim={result.max_similarity:.3f}) ---")
    for i, c in enumerate(result.citations[:6], 1):
        ts = f" @{int(c.start_seconds)}s" if c.start_seconds else ""
        print(f"  [{i}] score={c.score:.3f}  {c.source}/{c.video_id}{ts}  {c.title[:60] if c.title else ''}")

    cost = result.total_cost_usd
    # Haiku pricing override (rough):
    if use_haiku:
        cost = (
            result.input_tokens * 1.0 / 1_000_000
            + result.output_tokens * 5.0 / 1_000_000
            + result.cache_read_tokens * 0.08 / 1_000_000
            + result.cache_creation_tokens * 1.25 / 1_000_000
        )

    print(
        f"\n--- USAGE --- input={result.input_tokens} output={result.output_tokens} "
        f"cache_read={result.cache_read_tokens} cache_write={result.cache_creation_tokens}  "
        f"cost≈${cost:.4f}"
    )


async def main() -> None:
    engine = RAGEngine()

    await smoke_one(
        engine,
        "content",
        "AI is replacing everyone's jobs and we should be scared",
        (
            "Format: 60-second reel. Take: hook the viewer with why this fear is overblown, "
            "pivot to the one thing that actually matters for creators right now."
        ),
        use_haiku=True,  # cheap pipeline validation
    )

    await smoke_one(
        engine,
        "ad",
        "a neobank that does investing for Gen Z",
        (
            "Brand: Stonks Neobank. Product: one-tap SIP + stock fractional investing for 18-25 year olds. "
            "Duration: 30 seconds. Language: Hinglish. Cast: just Tanmay. "
            "Brief: We want to feel fun-not-preachy, demystify investing."
        ),
        use_haiku=True,
    )

    await smoke_one(
        engine,
        "qa",
        "what does Tanmay think about mental health and therapy",
        "Question: What does Tanmay think about mental health and therapy?",
        use_haiku=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
