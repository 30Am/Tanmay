"""Golden-set evaluator for TanmayGPT — Phase 09.

Runs a curated golden set of prompts through the live API, computes
style-match scores (generated output vs real Tanmay corpus via Voyage-3 +
Qdrant), and writes a JSON report + human-readable summary.

Style-match score: embed the generated output → query Qdrant for top-5 most
similar Tanmay chunks → mean cosine similarity of top-3 matches.
Threshold ≥ 0.38 = PASS  (calibrated from blind_test_results.json baseline).

Usage (from repo root):
    uv run --directory apps/api python scripts/eval.py
    uv run --directory apps/api python scripts/eval.py --tab qa --n 10
    uv run --directory apps/api python scripts/eval.py --tab all --out scripts/results/my_run.json

Options:
    --tab   qa | content | ad | all   Tab(s) to evaluate (default: all)
    --n     int                       Max prompts per tab (default: all defined)
    --out   path                      Output path (default: scripts/results/eval_<ts>.json)
    --url   str                       API base URL (default: http://localhost:8000)
    --threshold float                 Style-match pass threshold (default: 0.38)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO_ROOT / "apps" / "api" / ".env", override=True)

import httpx  # noqa: E402
import voyageai  # noqa: E402
from qdrant_client import AsyncQdrantClient  # noqa: E402
from qdrant_client.http import models as qm  # noqa: E402

VOYAGE_MODEL = "voyage-3"
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "tanmay_chunks")
STYLE_MATCH_THRESHOLD = 0.38
TOP_K_RERANK = 5   # Qdrant neighbours to fetch for scoring
TOP_K_SCORE = 3    # average the top-N of those for the final score

# ---------------------------------------------------------------------------
# Golden prompts — 15 per tab (extend to 100 for full Phase 09 panel)
# ---------------------------------------------------------------------------

GOLDEN_QA: list[str] = [
    "what does Tanmay think about consistency in content creation",
    "how does Tanmay approach failure and bouncing back",
    "what is Tanmay's take on the Indian comedy scene",
    "what does Tanmay say about mental health and therapy",
    "how does Tanmay feel about social media and its impact on creators",
    "what does Tanmay think about money and financial success",
    "what is Tanmay's advice for young content creators in India",
    "how does Tanmay handle criticism and negative comments online",
    "what does Tanmay think about competition in the creator economy",
    "how does Tanmay feel about quitting something and pivoting",
    "what is Tanmay's view on hard work versus smart work",
    "what does Tanmay say about discipline and maintaining a routine",
    "what is Tanmay's perspective on fame and popularity",
    "how does Tanmay approach personal growth and self-improvement",
    "what does Tanmay think about taking risks in your career",
]

GOLDEN_CONTENT: list[dict] = [
    {"idea": "why most people quit before they see results", "format": "60-second reel", "target_length_seconds": 60},
    {"idea": "the real cost of comparison on social media", "format": "YouTube short", "target_length_seconds": 55},
    {"idea": "why being cringe is actually a superpower", "format": "stand-up bit", "target_length_seconds": 90},
    {"idea": "how to deal with creative blocks when you have a deadline", "format": "reel", "target_length_seconds": 60},
    {"idea": "the uncomfortable truth about overnight success", "format": "talking head", "target_length_seconds": 75},
    {"idea": "why your parents don't understand the creator economy and that's okay", "format": "comedic monologue", "target_length_seconds": 90},
    {"idea": "what nobody tells you about going viral", "format": "YouTube short", "target_length_seconds": 55},
    {"idea": "the difference between being busy and being productive", "format": "reel", "target_length_seconds": 60},
    {"idea": "why AI won't replace people who understand people", "format": "talking head", "target_length_seconds": 75},
    {"idea": "how to stop overthinking and just ship the content", "format": "motivational bit", "target_length_seconds": 60},
    {"idea": "the one thing every successful creator does that nobody talks about", "format": "YouTube short", "target_length_seconds": 55},
    {"idea": "why feedback from your audience matters more than you think", "format": "reel", "target_length_seconds": 60},
    {"idea": "how to find your niche without losing yourself", "format": "reflective monologue", "target_length_seconds": 80},
    {"idea": "the truth about collaboration in the Indian creator space", "format": "comedic take", "target_length_seconds": 70},
    {"idea": "why showing up every day beats waiting for inspiration", "format": "reel", "target_length_seconds": 60},
]

GOLDEN_AD: list[dict] = [
    {
        "product_name": "Zepto",
        "product_description": "10-minute grocery delivery app, instant essentials at your door",
        "target_audience": "urban Indians 22-35 who hate running errands",
        "duration_seconds": 30,
    },
    {
        "product_name": "Notion",
        "product_description": "all-in-one workspace for notes, tasks, wikis, and databases",
        "target_audience": "Indian creators and startup founders",
        "duration_seconds": 30,
    },
    {
        "product_name": "Lenskart",
        "product_description": "affordable premium eyewear delivered home with free home trial",
        "target_audience": "working professionals 25-40",
        "duration_seconds": 30,
    },
    {
        "product_name": "boAt Airdopes",
        "product_description": "wireless earbuds with 40-hour battery and active noise cancellation",
        "target_audience": "young Indians 18-28 who commute daily",
        "duration_seconds": 30,
    },
    {
        "product_name": "Razorpay",
        "product_description": "payment gateway for Indian startups and freelancers",
        "target_audience": "indie founders and freelancers",
        "duration_seconds": 30,
    },
    {
        "product_name": "Swiggy Instamart",
        "product_description": "midnight snack and grocery delivery in under 15 minutes",
        "target_audience": "college students and night owls in metro cities",
        "duration_seconds": 30,
    },
    {
        "product_name": "Skillshare",
        "product_description": "online learning platform for creative and professional skills",
        "target_audience": "Indian creators and career-switchers 20-35",
        "duration_seconds": 30,
    },
    {
        "product_name": "Cred",
        "product_description": "credit card bill payment app with rewards for on-time payers",
        "target_audience": "creditworthy urban Indians 25-40",
        "duration_seconds": 30,
    },
    {
        "product_name": "Headspace",
        "product_description": "guided meditation and sleep app",
        "target_audience": "burnt-out professionals and stressed students",
        "duration_seconds": 30,
    },
    {
        "product_name": "Figma",
        "product_description": "collaborative design tool for UI/UX designers and product teams",
        "target_audience": "Indian designers and product managers",
        "duration_seconds": 30,
    },
]

GOLDEN: dict[str, list] = {
    "qa": GOLDEN_QA,
    "content": GOLDEN_CONTENT,
    "ad": GOLDEN_AD,
}


# ---------------------------------------------------------------------------
# Style-match scoring helpers
# ---------------------------------------------------------------------------

def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


async def style_match_score(
    text: str,
    voyage: voyageai.AsyncClient,
    qdrant: AsyncQdrantClient,
) -> float:
    """Embed `text`, query Qdrant for top-K Tanmay chunks, return mean of top-3 cosines."""
    if not text.strip():
        return 0.0

    # Embed the generated text as a document (not a query)
    embed_resp = await voyage.embed([text[:4000]], model=VOYAGE_MODEL, input_type="document")
    vec = embed_resp.embeddings[0]

    result = await qdrant.query_points(
        collection_name=QDRANT_COLLECTION,
        query=vec,
        limit=TOP_K_RERANK,
        query_filter=qm.Filter(must=[qm.FieldCondition(key="is_tanmay", match=qm.MatchValue(value=True))]),
        with_payload=False,
        with_vectors=True,
    )
    if not result.points:
        return 0.0

    sims = sorted(
        [_cosine(vec, p.vector) for p in result.points if p.vector],  # type: ignore[arg-type]
        reverse=True,
    )
    return round(sum(sims[: TOP_K_SCORE]) / min(TOP_K_SCORE, len(sims)), 4)


# ---------------------------------------------------------------------------
# Per-tab API callers
# ---------------------------------------------------------------------------

async def eval_qa(
    client: httpx.AsyncClient,
    question: str,
    voyage: voyageai.AsyncClient,
    qdrant: AsyncQdrantClient,
    *,
    api_url: str,
) -> dict:
    resp = await client.post(
        f"{api_url}/generate/qa",
        json={"question": question},
        timeout=60,
    )
    data = resp.json()
    status = data.get("status", "error")
    answer = data.get("answer") or ""
    max_sim = data.get("max_similarity", 0.0)

    if status == "answered" and answer:
        score = await style_match_score(answer, voyage, qdrant)
    else:
        score = 0.0

    return {
        "tab": "qa",
        "input": {"question": question},
        "status": status,
        "max_similarity": max_sim,
        "style_match_score": score,
        "pass": score >= STYLE_MATCH_THRESHOLD and status == "answered",
        "output_preview": answer[:200] if answer else data.get("reason", ""),
    }


async def eval_content(
    client: httpx.AsyncClient,
    prompt: dict,
    voyage: voyageai.AsyncClient,
    qdrant: AsyncQdrantClient,
    *,
    api_url: str,
) -> dict:
    resp = await client.post(
        f"{api_url}/generate/content",
        json={
            "idea": prompt["idea"],
            "format": prompt["format"],
            "target_length_seconds": prompt["target_length_seconds"],
        },
        timeout=90,
    )
    data = resp.json()
    script = data.get("script") or ""

    if script:
        score = await style_match_score(script, voyage, qdrant)
    else:
        score = 0.0

    return {
        "tab": "content",
        "input": prompt,
        "status": "generated" if script else "error",
        "style_match_score": score,
        "pass": score >= STYLE_MATCH_THRESHOLD and bool(script),
        "output_preview": script[:200],
    }


async def eval_ad(
    client: httpx.AsyncClient,
    prompt: dict,
    voyage: voyageai.AsyncClient,
    qdrant: AsyncQdrantClient,
    *,
    api_url: str,
) -> dict:
    resp = await client.post(
        f"{api_url}/generate/ad",
        json={
            "product_name": prompt["product_name"],
            "product_description": prompt["product_description"],
            "target_audience": prompt.get("target_audience", "general Indian urban 18-35"),
            "duration_seconds": prompt.get("duration_seconds", 30),
            "language": "english",
            "cast": [],
            "celebrities": [],
        },
        timeout=90,
    )

    if resp.status_code == 422:
        return {
            "tab": "ad",
            "input": prompt,
            "status": "refused_brand_safety",
            "style_match_score": 0.0,
            "pass": False,
            "output_preview": str(resp.json().get("detail", "")),
        }

    data = resp.json()
    hook = data.get("hook", "")
    scenes = data.get("scenes") or []
    ad_text = hook + " " + " ".join(
        line for s in scenes for line in (s.get("lines") or [])
    )

    if ad_text.strip():
        score = await style_match_score(ad_text, voyage, qdrant)
    else:
        score = 0.0

    return {
        "tab": "ad",
        "input": prompt,
        "status": "generated" if ad_text.strip() else "error",
        "style_match_score": score,
        "pass": score >= STYLE_MATCH_THRESHOLD and bool(ad_text.strip()),
        "output_preview": (hook + " " + " ".join(
            line for s in scenes[:2] for line in (s.get("lines") or [])[:2]
        ))[:200],
    }


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

async def run_eval(
    *,
    tabs: list[str],
    n: int,
    api_url: str,
    threshold: float,
    out_path: Path,
) -> None:
    global STYLE_MATCH_THRESHOLD
    STYLE_MATCH_THRESHOLD = threshold

    voyage = voyageai.AsyncClient(api_key=os.environ["VOYAGE_API_KEY"])
    qdrant = AsyncQdrantClient(url=QDRANT_URL)

    all_results: list[dict] = []
    tab_stats: dict[str, dict] = {}

    async with httpx.AsyncClient() as client:
        for tab in tabs:
            prompts = GOLDEN[tab][:n]
            results: list[dict] = []

            print(f"\n{'='*70}")
            print(f"TAB: {tab.upper()}  ({len(prompts)} prompts)")
            print(f"{'='*70}")

            for i, prompt in enumerate(prompts, 1):
                label = prompt if isinstance(prompt, str) else prompt.get("idea") or prompt.get("product_name", "")
                print(f"  [{i:02d}/{len(prompts):02d}] {label[:60]}", end=" ... ", flush=True)

                try:
                    if tab == "qa":
                        r = await eval_qa(client, prompt, voyage, qdrant, api_url=api_url)
                    elif tab == "content":
                        r = await eval_content(client, prompt, voyage, qdrant, api_url=api_url)
                    else:
                        r = await eval_ad(client, prompt, voyage, qdrant, api_url=api_url)

                    flag = "✓ PASS" if r["pass"] else "✗ FAIL"
                    print(f"{flag}  style={r['style_match_score']:.3f}")
                    results.append(r)

                except Exception as exc:
                    print(f"ERROR: {exc}")
                    results.append({
                        "tab": tab,
                        "input": prompt,
                        "status": "exception",
                        "style_match_score": 0.0,
                        "pass": False,
                        "error": str(exc),
                        "output_preview": "",
                    })

            passed = sum(1 for r in results if r["pass"])
            scores = [r["style_match_score"] for r in results if r["style_match_score"] > 0]
            avg_score = sum(scores) / len(scores) if scores else 0.0
            pass_rate = passed / len(results) if results else 0.0

            tab_stats[tab] = {
                "total": len(results),
                "passed": passed,
                "failed": len(results) - passed,
                "pass_rate": round(pass_rate, 3),
                "avg_style_match": round(avg_score, 4),
                "threshold": threshold,
            }

            print(f"\n  → {passed}/{len(results)} passed  |  avg style-match: {avg_score:.3f}")
            all_results.extend(results)

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print("EVAL SUMMARY")
    print(f"{'='*70}")
    total_pass = sum(s["passed"] for s in tab_stats.values())
    total_all = sum(s["total"] for s in tab_stats.values())
    for tab, s in tab_stats.items():
        print(f"  {tab.upper():8s}  pass={s['passed']}/{s['total']}  "
              f"pass_rate={s['pass_rate']:.0%}  avg_style={s['avg_style_match']:.3f}")
    print(f"{'─'*70}")
    print(f"  OVERALL   pass={total_pass}/{total_all}  "
          f"pass_rate={total_pass/total_all:.0%}" if total_all else "  (no results)")

    # ── Write output ─────────────────────────────────────────────────────────
    report = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "api_url": api_url,
        "threshold": threshold,
        "tabs_evaluated": tabs,
        "summary": tab_stats,
        "results": all_results,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nWrote {len(all_results)} results → {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="TanmayGPT golden-set evaluator")
    parser.add_argument("--tab", default="all", choices=["qa", "content", "ad", "all"],
                        help="Tab to evaluate (default: all)")
    parser.add_argument("--n", type=int, default=9999,
                        help="Max prompts per tab (default: all defined in golden set)")
    parser.add_argument("--out", default=None,
                        help="Output JSON path (default: scripts/results/eval_<ts>.json)")
    parser.add_argument("--url", default="http://localhost:8000",
                        help="API base URL (default: http://localhost:8000)")
    parser.add_argument("--threshold", type=float, default=0.38,
                        help="Style-match pass threshold (default: 0.38)")
    args = parser.parse_args()

    tabs = ["qa", "content", "ad"] if args.tab == "all" else [args.tab]

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path(args.out) if args.out else REPO_ROOT / "scripts" / "results" / f"eval_{ts}.json"

    asyncio.run(run_eval(
        tabs=tabs,
        n=args.n,
        api_url=args.url.rstrip("/"),
        threshold=args.threshold,
        out_path=out_path,
    ))


if __name__ == "__main__":
    main()
