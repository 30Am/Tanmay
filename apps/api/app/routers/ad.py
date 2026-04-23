from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app.core.logging import get_logger
from app.models.schemas import (
    AdGenerateRequest,
    AdGenerateResponse,
    AdScene,
    Citation,
    Platform,
)
from app.routers.dependencies import get_rag_engine
from app.services.ad_export import EXPORTERS
from app.services.ad_validate import WORDS_PER_SECOND, validate_ad
from app.services.brand_safety import check_product
from app.services.rag import RAGEngine

log = get_logger(__name__)
router = APIRouter(prefix="/generate", tags=["ad"])


AD_TOOL_NAME = "emit_ad_script"
AD_TOOL_DESCRIPTION = (
    "Emit the final ad as a structured object. Use this exactly once to return the "
    "ad script — do NOT produce any prose response alongside."
)
AD_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Short working title (≤8 words)."},
        "hook": {"type": "string", "description": "Opening 3-5 second hook line."},
        "scenes": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "properties": {
                    "scene_number": {"type": "integer", "minimum": 1},
                    "setting": {"type": "string"},
                    "direction": {"type": "string"},
                    "characters": {"type": "array", "items": {"type": "string"}},
                    "lines": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                    "duration_seconds": {"type": "integer", "minimum": 1},
                },
                "required": ["scene_number", "setting", "direction", "characters", "lines", "duration_seconds"],
            },
        },
        "cta": {"type": "string"},
        "strategy_rationale": {
            "type": "string",
            "description": "2-3 sentences on why this angle for this brand/audience.",
        },
        "brand_safety_flags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Categories like 'real_money_gaming', 'predatory_finance'. Empty if none.",
        },
    },
    "required": ["title", "hook", "scenes", "cta", "strategy_rationale", "brand_safety_flags"],
}


def _infer_platform(source: str) -> Platform:
    if source in {"honestly", "overpowered", "sheet"}:
        return Platform.YOUTUBE
    return Platform.OTHER


@router.post("/ad")
async def generate_ad(
    req: AdGenerateRequest,
    format: Literal["json", "md", "fountain"] = Query(default="json", description="Response format."),
    rag: RAGEngine = Depends(get_rag_engine),
):
    # Pre-gate brand-safety — refuse without ever calling the LLM on publicly-refused categories.
    safety = check_product(product_name=req.product_name, product_description=req.product_description)
    if not safety.ok:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "refused_brand_safety",
                "flags": safety.flags,
                "reason": (
                    "Category Tanmay has publicly refused. Pipeline will not generate an ad "
                    "for: " + ", ".join(safety.flags)
                ),
            },
        )

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
            "",
            "Call emit_ad_script with the final ad. Total scene durations must sum to the",
            f"requested DURATION {req.duration_seconds}s within ±2s tolerance.",
        ]
    )

    tool_input, result = await rag.generate_with_tool(
        tab="ad",
        query=f"{req.product_name}: {req.product_description}",
        tool_name=AD_TOOL_NAME,
        tool_description=AD_TOOL_DESCRIPTION,
        tool_schema=AD_TOOL_SCHEMA,
        user_payload=user_payload,
        tone=None,
        retrieval_top_k=6,
        exemplars_k=4,
        exemplar_registers=["comedic", "informative"],
        max_tokens=2400,
        temperature=0.7,
        entity_boost_term=req.product_name.split()[0] if req.product_name else None,
    )

    if not tool_input:
        log.error("ad_tool_emit_missing", text_fallback=result.text[:300])
        raise HTTPException(status_code=502, detail="Model did not emit the ad tool.")

    # Validate duration/wordcount sanity.
    validation = validate_ad(
        scenes=tool_input.get("scenes") or [],
        target_duration_s=req.duration_seconds,
        language=req.language,
    )

    # Build the response model. Brand-safety flags come from the deterministic gate PLUS
    # anything the model flagged (merged + deduped).
    model_flags = list(tool_input.get("brand_safety_flags") or [])
    merged_flags = sorted(set(model_flags) | set(safety.flags))

    try:
        scenes = [AdScene(**s) for s in tool_input.get("scenes", [])]
    except Exception as exc:  # pydantic validation
        log.error("ad_scene_parse_failed", error=str(exc), scenes=tool_input.get("scenes"))
        raise HTTPException(status_code=502, detail=f"Scene schema mismatch: {exc}") from exc

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

    response = AdGenerateResponse(
        title=tool_input.get("title", ""),
        hook=tool_input.get("hook", ""),
        scenes=scenes,
        cta=tool_input.get("cta", ""),
        strategy_rationale=tool_input.get("strategy_rationale", ""),
        brand_safety_flags=merged_flags,
        citations=citations,
    )

    log.info(
        "ad_generated",
        product=req.product_name,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        flags=merged_flags,
        valid=validation.ok,
        duration_actual=validation.total_scene_duration_s,
        duration_target=validation.target_duration_s,
        words_actual=validation.total_words,
        words_target=validation.target_words,
    )

    if format in ("md", "fountain"):
        exporter = EXPORTERS[format]
        media_type = "text/markdown" if format == "md" else "text/x-fountain"
        return PlainTextResponse(content=exporter(response), media_type=media_type)

    # JSON response — attach validation metadata via response headers so we don't mutate
    # the public AdGenerateResponse shape.
    from fastapi.responses import JSONResponse

    return JSONResponse(
        content=response.model_dump(mode="json"),
        headers={
            "X-Ad-Valid": "true" if validation.ok else "false",
            "X-Ad-Duration": str(validation.total_scene_duration_s),
            "X-Ad-Words": str(validation.total_words),
            "X-Ad-Validation-Issues": ";".join(i.code for i in validation.issues) or "none",
        },
    )
