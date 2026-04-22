from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException

from app.core.logging import get_logger
from app.models.schemas import AdGenerateRequest, AdGenerateResponse, AdScene, Citation, ContentFormat, Platform
from app.routers.dependencies import get_llm_service, get_retrieval_service
from app.services.brand_safety import check_product
from app.services.llm import LLMService
from app.services.persona import build_system_prompt, format_chunks, format_exemplars
from app.services.retrieval import RetrievalService

log = get_logger(__name__)
router = APIRouter(prefix="/generate", tags=["ad"])


WORDS_PER_SECOND = {"hinglish": 2.3, "english": 2.6, "hindi": 2.0}

AD_FORMAT_RULES = """\
OUTPUT FORMAT: Return strictly valid JSON matching this schema:

{
  "title": "short working title",
  "hook": "opening 3-5 second hook line",
  "scenes": [
    {
      "scene_number": 1,
      "setting": "where this takes place",
      "direction": "what happens, camera notes, vibe",
      "characters": ["Tanmay", "..."],
      "lines": ["line 1", "line 2"],
      "duration_seconds": 12
    }
  ],
  "cta": "final call to action",
  "strategy_rationale": "why this ad works for the product and audience in Tanmay's voice"
}

Do not wrap in markdown fences. Output JSON only.
"""


@router.post("/ad", response_model=AdGenerateResponse)
async def generate_ad(
    req: AdGenerateRequest,
    llm: LLMService = Depends(get_llm_service),
    retrieval: RetrievalService = Depends(get_retrieval_service),
) -> AdGenerateResponse:
    safety = check_product(product_name=req.product_name, product_description=req.product_description)

    wps = WORDS_PER_SECOND[req.language]
    target_words = int(req.duration_seconds * wps)

    retrieval_result = await retrieval.retrieve(
        f"{req.product_name}: {req.product_description}",
        format_filter=[ContentFormat.AD, ContentFormat.BRANDED],
    )
    exemplars = await retrieval.style_exemplars(
        req.product_description,
        format_filter=[ContentFormat.AD, ContentFormat.BRANDED],
        limit=5,
    )

    system = build_system_prompt(tab="ad_generation", format_rules=AD_FORMAT_RULES)

    cast_block = "\n".join([f"- {c.name} ({c.role or 'character'})" for c in req.cast]) or "(none specified)"
    celeb_block = ", ".join(req.celebrities) or "(none)"

    user_payload = "\n\n".join(
        [
            format_chunks(retrieval_result.chunks),
            format_exemplars(exemplars),
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

    raw = await llm.complete(
        system=system,
        messages=[{"role": "user", "content": user_payload}],
        temperature=0.7,
        max_tokens=4096,
    )

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        log.error("ad_json_parse_failed", error=str(exc), raw=raw[:500])
        raise HTTPException(status_code=502, detail="Model did not return valid JSON.") from exc

    citations = [
        Citation(
            source_id=c.source_id,
            url=c.url,
            platform=c.platform if isinstance(c.platform, Platform) else Platform(c.platform),
            timestamp_seconds=c.start_seconds,
            excerpt=c.text[:240],
        )
        for c in retrieval_result.chunks[:5]
    ]

    scenes = [AdScene(**s) for s in data.get("scenes", [])]

    return AdGenerateResponse(
        title=data.get("title", ""),
        hook=data.get("hook", ""),
        scenes=scenes,
        cta=data.get("cta", ""),
        strategy_rationale=data.get("strategy_rationale", ""),
        brand_safety_flags=safety.flags,
        citations=citations,
    )
