"""Automated blind-test proxy — how close are generated outputs to real Tanmay voice?

We can't run a real fan-panel blind test yet, so this is a cheap automated proxy:

  1. Pick 10 real Tanmay chunks from voice_corpus.json (high-register, Tanmay-only).
  2. For each, extract its topic_tags + truncated opening as a "prompt that could have
     plausibly generated this".
  3. Generate a short content-tab piece with persona v1 + Haiku 4.5.
  4. Embed both the generated output and the real chunk (Voyage-3 query embeddings).
  5. Compute cosine similarity — voice_match_score.
  6. Baseline: compare each real chunk against a RANDOM Tanmay chunk on a different topic.
     Generated should score noticeably higher than random-Tanmay baseline if voice is
     holding up.

Outputs:
  data/blind_test_results.json — per-sample: real chunk, prompt, generated output,
  voice_match_score, random_baseline_score, delta.

Cost: ~$0.15 (10 Haiku generations + Voyage embeddings are free on free tier).
"""
from __future__ import annotations

import asyncio
import json
import os
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO_ROOT / "apps" / "api" / ".env", override=True)

import voyageai  # noqa: E402

from app.models.schemas import ToneDial  # noqa: E402
from app.services.rag import RAGEngine  # noqa: E402

DATA = Path(__file__).parent
CORPUS_PATH = DATA / "voice_corpus.json"
OUT_PATH = DATA / "blind_test_results.json"
N_SAMPLES = 10
random.seed(7)


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def build_prompt_from(chunk: dict) -> tuple[str, str]:
    """Turn a real chunk into a plausible content-tab prompt."""
    topic = (chunk.get("topic_tags") or ["something tanmay talks about"])[0]
    # user_payload kept short — user intent, not a rewrite request
    query = f"{topic}"
    user_payload = (
        f"Format: 45-60 second reel.\n"
        f"Topic: {topic}.\n"
        f"Take: whatever angle Tanmay would most naturally take on this. "
        f"Keep it punchy. One clean punchline."
    )
    return query, user_payload


async def main() -> None:
    corpus = json.loads(CORPUS_PATH.read_text())
    # Only comedic/reflective (Tab 1 most common registers)
    pool = [c for c in corpus if c.get("register") in ("comedic", "reflective")]
    samples = random.sample(pool, k=min(N_SAMPLES, len(pool)))

    engine = RAGEngine()
    voyage = voyageai.AsyncClient(api_key=os.environ["VOYAGE_API_KEY"])

    results = []
    for i, real in enumerate(samples, start=1):
        query, user_payload = build_prompt_from(real)
        print(f"\n[{i}/{len(samples)}] register={real['register']}  topic_tags={real.get('topic_tags', [])[:3]}")
        result = await engine.generate(
            tab="content",
            query=query,
            user_payload=user_payload,
            tone=ToneDial(roast_level=0.5, chaos=0.5, depth=0.5, hinglish_ratio=0.5),
            model=os.environ.get("ANTHROPIC_MODEL_UTILITY", "claude-haiku-4-5-20251001"),
            retrieval_top_k=6,
            exemplars_k=4,
            exemplar_registers=[real["register"], "comedic"],
            max_tokens=900,
        )
        # Take just the SCRIPT section if present (skip RATIONALE/DESCRIPTION)
        gen_text = result.text
        if "RATIONALE" in gen_text.upper():
            # truncate to pre-rationale for fair comparison
            idx = gen_text.upper().find("RATIONALE")
            gen_text = gen_text[:idx].strip()
        gen_text = gen_text[:1500]  # bound length

        # Pick a random Tanmay chunk different from `real` as baseline
        other = random.choice([c for c in corpus if c["chunk_id"] != real["chunk_id"]])

        # Embed all three (real, generated, random-baseline) in one Voyage call
        resp = await voyage.embed(
            [real["text"], gen_text, other["text"]],
            model="voyage-3",
            input_type="document",
        )
        real_vec, gen_vec, other_vec = resp.embeddings

        voice_match = cosine(real_vec, gen_vec)
        random_baseline = cosine(real_vec, other_vec)

        print(f"  voice_match={voice_match:.3f}  random_baseline={random_baseline:.3f}  delta={voice_match - random_baseline:+.3f}")
        results.append(
            {
                "chunk_id": real["chunk_id"],
                "register": real["register"],
                "topic_tags": real.get("topic_tags"),
                "query": query,
                "real_text_preview": real["text"][:200],
                "generated_text": gen_text,
                "voice_match_score": round(voice_match, 4),
                "random_baseline_score": round(random_baseline, 4),
                "delta": round(voice_match - random_baseline, 4),
                "usage": {
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                },
            }
        )

    OUT_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False))

    # Aggregate
    avg_match = sum(r["voice_match_score"] for r in results) / len(results)
    avg_baseline = sum(r["random_baseline_score"] for r in results) / len(results)
    avg_delta = sum(r["delta"] for r in results) / len(results)
    positive_delta = sum(1 for r in results if r["delta"] > 0)
    print()
    print(f"=== AGGREGATE ({len(results)} samples) ===")
    print(f"avg voice_match_score:     {avg_match:.3f}")
    print(f"avg random_baseline_score: {avg_baseline:.3f}")
    print(f"avg delta (persona lift):  {avg_delta:+.3f}")
    print(f"positive-delta samples:    {positive_delta}/{len(results)}")
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
