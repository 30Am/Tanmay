from __future__ import annotations

import json
import re

from fastapi import APIRouter, Depends, HTTPException

from app.core.logging import get_logger
from app.models.schemas import (
    AdGenerateRequest,
    AdGenerateResponse,
    AdScene,
    Citation,
    Platform,
)
from app.routers.dependencies import get_rag_engine
from app.services.brand_safety import check_product
from app.services.rag import RAGEngine

log = get_logger(__name__)
router = APIRouter(prefix="/generate", tags=["ad"])


WORDS_PER_SECOND = {"hinglish": 2.3, "english": 2.6, "hindi": 2.0}


def _strip_fences(s: str) -> str:
    """Model sometimes wraps JSON in ```json fences; strip them for json.loads."""
    m = re.search(r"```(?:json)?\s*\n(.*?)\n```", s, re.DOTALL)
    return m.group(1) if m else s.strip()


def _infer_platform(source: str) -> Platform:
    if source in {"honestly", "overpowered", "sheet"}:
        return Platform.YOUTUBE
    return Platform.OTHER


@router.post("/ad", response_model=AdGenerateResponse)
async def generate_ad(
    req: AdGenerateRequest,
    rag: RAGEngine = Depends(get_rag_engine),
) -> AdGenerateResponse:
    safety = check_product(product_name=req.product_name, product_description=req.product_description)

    wps = WORDS_PER_SECOND[req.language]
    target_words = int(req.duration_seconds * wps)

    cast_block = "\n".join([f"- {c.name} ({c.role or 'character'})" for c in req.cast]) or "(none specified)"
    celeb_block = ", ".join(req.celebrities) or "(none)"

    user_payload = "\n".join(
        [
            f"PRODUCT: {req.product_name}",
            f"DESCRIPTION: {req.product_description}",
            f"AUDIENCE: {req.target_audience or 'general Indian urban 18-35'}",
            f"DURATION: {req.duration_seconds}s (target ~{target_words} words in {req.language})",
            f"LANGUAGE: {req.language}",
            f"CAST:\n{cast_block}",
            f"CELEBRITY CAMEOS: {celeb_block}",
            f"NOTES: {req.notes or '(none)'}",
        ]
    )

    result = await rag.generate(
        tab="ad",
        query=f"{req.product_name}: {req.product_description}",
        user_payload=user_payload,
        tone=None,
        retrieval_top_k=6,
        exemplars_k=4,
        exemplar_registers=["comedic", "informative"],
        max_tokens=2000,
        temperature=0.7,
    )

    try:
        data = json.loads(_strip_fences(result.text))
    except json.JSONDecodeError as exc:
        log.error("ad_json_parse_failed", error=str(exc), raw=result.text[:500])
        raise HTTPException(status_code=502, detail="Model did not return valid JSON.") from exc

    citations = [
        Citation(
            source_id=c.chunk_id,
            url=c.url,
            platform=_infer_platform(c.source),
            title=c.title,
            timestamp_seconds=int(c.start_seconds) if c.start_seconds is not None else None,
            excerpt=c.text[:240],
        )
        for c in result.citations[:5]
    ]

    scenes = [AdScene(**s) for s in data.get("scenes", [])]

    # Merge model-reported flags with brand-safety gate output
    model_flags = list(data.get("brand_safety_flags") or [])
    merged_flags = sorted(set(model_flags) | set(safety.flags))

    log.info(
        "ad_generated",
        product=req.product_name,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        flags=merged_flags,
    )
    return AdGenerateResponse(
        title=data.get("title", ""),
        hook=data.get("hook", ""),
        scenes=scenes,
        cta=data.get("cta", ""),
        strategy_rationale=data.get("strategy_rationale", ""),
        brand_safety_flags=merged_flags,
        citations=citations,
    )
