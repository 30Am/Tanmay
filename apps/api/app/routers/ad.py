from __future__ import annotations

import re
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse

from langfuse import get_client

from app.core.logging import get_logger
from app.models.schemas import (
    AdGenerateRequest,
    AdGenerateResponse,
    AdQualityScores,
    AdScene,
    Citation,
    Platform,
    ToneDial,
)
from app.routers.dependencies import get_rag_engine
from app.services.ad_export import EXPORTERS
from app.services.ad_validate import WORDS_PER_SECOND, validate_ad
from app.services.brand_safety import check_product
from app.services.persona import (
    get_category_idiom,
    get_placement_pacing,
)
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
    lf = get_client()
    with lf.start_as_current_observation(
        name="ad",
        as_type="span",
        input={"product": req.product_name, "duration_s": req.duration_seconds, "language": req.language},
    ):
        return await _generate_ad_inner(req, format, rag, lf)


def _apply_brand_voice_override(tone: ToneDial, tags: list[str]) -> tuple[ToneDial, list[str]]:
    """Clamp tone sliders when brand-voice tags conflict with defaults.

    Returns (possibly-adjusted tone, list of overrides applied).
    Premium and cant_do_humor both cap roast+chaos low. educational caps depth high.
    family_safe_only caps roast low. minimal caps chaos low.
    """
    applied: list[str] = []
    r, c, d, h = tone.roast_level, tone.chaos, tone.depth, tone.hinglish_ratio

    if "premium" in tags:
        if r > 0.35:
            r = 0.25; applied.append("premium→roast≤0.25")
        if c > 0.35:
            c = 0.25; applied.append("premium→chaos≤0.25")
    if "cant_do_humor" in tags:
        if r > 0.2:
            r = 0.1; applied.append("cant_do_humor→roast≤0.1")
        if c > 0.3:
            c = 0.2; applied.append("cant_do_humor→chaos≤0.2")
    if "family_safe_only" in tags and r > 0.5:
        r = 0.4; applied.append("family_safe_only→roast≤0.4")
    if "minimal" in tags and c > 0.3:
        c = 0.2; applied.append("minimal→chaos≤0.2")
    if "educational" in tags and d < 0.5:
        d = 0.6; applied.append("educational→depth≥0.6")

    return ToneDial(roast_level=r, chaos=c, depth=d, hinglish_ratio=h), applied


def _gather_text(response: AdGenerateResponse) -> str:
    """Flatten the full ad output to one string for keyword / regex checks."""
    parts = [response.title, response.hook, response.cta, response.strategy_rationale]
    for s in response.scenes:
        parts.extend([s.setting, s.direction, *s.characters, *s.lines])
    return "\n".join(p for p in parts if p)


def _check_do_not_say(response: AdGenerateResponse, terms: list[str]) -> list[str]:
    """Return the banned terms that appear in the output (case-insensitive, word-boundary)."""
    if not terms:
        return []
    haystack = _gather_text(response)
    hits: list[str] = []
    for term in terms:
        t = term.strip()
        if not t:
            continue
        pattern = r"\b" + re.escape(t) + r"\b"
        if re.search(pattern, haystack, flags=re.IGNORECASE):
            hits.append(t)
    return hits


def _check_proof_point(response: AdGenerateResponse, proof: str | None) -> bool | None:
    """Best-effort substring match on 4+ consecutive word-tokens of the proof point.

    Returns None if no proof_point supplied, True if a meaningful chunk appears
    in the output, False otherwise.
    """
    if not proof:
        return None
    haystack = _gather_text(response).lower()
    tokens = [t for t in re.findall(r"\w+", proof.lower()) if len(t) > 2]
    if not tokens:
        return None
    # require a 4-word contiguous window; fall back to 3 if the proof is short
    window = 4 if len(tokens) >= 5 else max(2, len(tokens) - 1)
    for i in range(len(tokens) - window + 1):
        phrase = r"\W+".join(re.escape(t) for t in tokens[i : i + window])
        if re.search(phrase, haystack):
            return True
    return False


async def _judge_quality(rag: RAGEngine, req, response: AdGenerateResponse) -> AdQualityScores | None:
    """Haiku-based post-gen rubric — scores 1-5 on 5 dimensions. Best-effort."""
    from app.services.rag import ANTHROPIC_UTILITY

    ad_json = response.model_dump(mode="json", exclude={"quality", "citations", "do_not_say_hits", "proof_point_found"})
    brief = {
        "product_name": req.product_name,
        "product_description": req.product_description,
        "audience": req.target_audience,
        "industry": req.industry,
        "campaign_goal": req.campaign_goal,
        "proof_point": req.proof_point,
        "positioning": req.positioning,
        "brand_voice_tags": req.brand_voice_tags,
        "placement": req.placement,
    }
    system = (
        "You are a strict ad-critic. Score an ad against its brief on 5 dimensions, 1-5 integer each. "
        "Be honest — 3 = adequate, 5 = exceptional. Return ONLY a JSON object with this exact shape: "
        '{"on_brand": int, "proof_point_present": int, "audience_match": int, '
        '"hook_strength": int, "no_tanmay_leak": int, "notes": "one sentence"}'
    )
    import json as _json

    prompt = (
        "BRIEF:\n" + _json.dumps(brief, indent=2, ensure_ascii=False)
        + "\n\nAD:\n" + _json.dumps(ad_json, indent=2, ensure_ascii=False)
        + "\n\nScoring guide:\n"
        "- on_brand: fits the industry/positioning/voice (1=off-brand, 5=could run tomorrow).\n"
        "- proof_point_present: if brief has a proof_point, is it anchored in the ad? "
        "(1=missing; 5=cleanly embedded in a scene). If brief has none, score 3 by default.\n"
        "- audience_match: does register and reference-set match the audience? (1=mismatch, 5=bullseye).\n"
        "- hook_strength: does the first beat earn the next 5 seconds? (1=forgettable, 5=scroll-stopping).\n"
        "- no_tanmay_leak: 5 if no mention of Tanmay Bhat by name anywhere; drop one point per leak."
    )
    try:
        resp = await rag.anthropic.messages.create(
            model=ANTHROPIC_UTILITY,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.0,
        )
        raw = "".join(b.text for b in resp.content if b.type == "text").strip()
        # The model may wrap in ```json — strip fences.
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw).strip()
        data = _json.loads(raw)
        return AdQualityScores(**data)
    except Exception as exc:
        log.warning("ad_judge_failed", error=str(exc))
        return None


async def _generate_ad_inner(req, format, rag, lf):  # type: ignore[no-untyped-def]
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

    # ── Brand-voice override: clamp conflicting tone slider values ───────────
    effective_tone, overrides_applied = _apply_brand_voice_override(req.tone, req.brand_voice_tags)

    # ── Placement-driven pacing ─────────────────────────────────────────────
    pacing = get_placement_pacing(req.placement)
    # Use placement's WPS when specified; otherwise fall back to language default.
    wps = pacing.words_per_second if req.placement else WORDS_PER_SECOND[req.language]
    target_words = int(req.duration_seconds * wps)

    # ── Phase 1: Pattern analysis from Tanmay's real ad corpus ──────────────
    # Retrieve the most semantically similar past Tanmay ads, then use Haiku
    # to extract actionable storytelling patterns. This analysis is injected
    # into Phase 2 so the generation model replicates observed patterns, not
    # just the manually-coded persona rules.
    ad_corpus_query = f"{req.product_name}: {req.product_description}"
    if req.target_audience:
        ad_corpus_query += f". Target audience: {req.target_audience}"

    ad_corpus_chunks = await rag.retrieve_ad_corpus(
        ad_corpus_query,
        limit=5,
        has_celebrities=bool(req.celebrities) if req.celebrities else None,
        industry=req.industry,
    )

    pattern_analysis = await rag.analyze_ad_patterns(
        ad_corpus_chunks,
        product_name=req.product_name,
        product_description=req.product_description,
        has_celebrities=bool(req.celebrities),
    )

    n_corpus = len(ad_corpus_chunks)
    log.info(
        "ad_pattern_analysis",
        product=req.product_name,
        corpus_ads_retrieved=n_corpus,
        analysis_chars=len(pattern_analysis),
        industry=req.industry,
    )

    # ── Phase 2: Build user payload with pattern analysis injected ───────────
    cast_block = "\n".join([f"- {c.name} ({c.role or 'character'})" for c in req.cast]) or "(none specified)"

    if req.celebrities:
        celeb_instruction = (
            "CELEBRITY CAMEOS (MANDATORY — each must appear in at least one scene with actual spoken lines):\n"
            + "\n".join(f"- {c}: write a dedicated scene or moment that plays to their known public persona, "
                        f"has them interact with the ad's protagonist (from CAST, or a generic character "
                        f"fitted to the AUDIENCE — NOT Tanmay), and involves the product naturally."
                        for c in req.celebrities)
        )
    else:
        celeb_instruction = "CELEBRITY CAMEOS: none"

    # ── Tone calibration block ────────────────────────────────────────────────
    tone = effective_tone
    tone_parts: list[str] = []
    if tone.roast_level > 0.7:
        tone_parts.append("ROAST HIGH: very witty, sharp punchlines, playful mockery of the product/situation — the comedy is the hook")
    elif tone.roast_level > 0.4:
        tone_parts.append("ROAST MED: light humor, relatable jokes — funny but not edgy")
    else:
        tone_parts.append("ROAST LOW: warm and sincere tone — minimal jokes, let the story do the work")

    if tone.chaos > 0.7:
        tone_parts.append("CHAOS HIGH: unpredictable structure, comedic tangents welcome, lots of unexpected beats")
    elif tone.chaos > 0.4:
        tone_parts.append("CHAOS MED: some surprise moments but overall coherent arc")
    else:
        tone_parts.append("CHAOS LOW: tight clean script, no tangents, every line earns its place")

    if tone.depth > 0.7:
        tone_parts.append("DEPTH HIGH: dig into second-order insights, the product solves something real — show the insight")
    elif tone.depth > 0.4:
        tone_parts.append("DEPTH MED: one genuine insight mixed with entertainment")
    else:
        tone_parts.append("DEPTH LOW: pure entertainment, surface-level fun — don't make it heavy")

    if tone.hinglish_ratio > 0.7:
        tone_parts.append("HINGLISH HIGH: heavy slang throughout — Hindi verbs, colloquial phrases, bhai/yaar/bro freely")
    elif tone.hinglish_ratio > 0.4:
        tone_parts.append("HINGLISH MED: natural code-switching, Hindi where it punches harder")
    else:
        tone_parts.append("HINGLISH LOW: mostly English, very light Hindi flavoring only")

    tone_block = "TONE CALIBRATION (follow these precisely):\n" + "\n".join(f"- {t}" for t in tone_parts)

    # ── Category idiom, placement pacing, proof-point rule, do-not-say ────────
    idiom = get_category_idiom(req.industry)
    category_block = f"{idiom}\n\n" if idiom else ""

    placement_block = (
        "PLACEMENT CONSTRAINTS:\n"
        f"- Placement: {req.placement or 'unspecified'}\n"
        f"- Hook must land within {pacing.hook_seconds:.1f}s.\n"
        f"- Target pacing: ~{pacing.words_per_second:.1f} words/sec.\n"
        f"- Scene budget: at most {pacing.max_scenes} scenes.\n"
        f"- {pacing.notes}\n"
    )

    proof_block = (
        f"PROOF POINT (MUST appear verbatim or with minimal paraphrase in scene 2 or 3):\n"
        f"  \"{req.proof_point}\"\n"
        if req.proof_point
        else ""
    )

    positioning_block = f"POSITIONING: {req.positioning}\n" if req.positioning else ""
    competitor_block = (
        f"COMPETITOR / DISPLACES: {req.competitor} — contrast implicitly; never name-drop.\n"
        if req.competitor
        else ""
    )
    campaign_goal_block = (
        f"CAMPAIGN GOAL: {req.campaign_goal} — "
        + {
            "awareness": "lean emotion + memorability; a soft CTA is fine.",
            "consideration": "build trust with a proof beat; the CTA nudges exploration, not purchase.",
            "conversion": "the CTA is a hard action (sign up / download / order). Remove all ambiguity.",
            "relaunch": "acknowledge the audience's past expectation; show what's different now.",
            "feature_drop": "front-load the new feature in the hook; everything else supports it.",
        }.get(req.campaign_goal or "", "")
        + "\n"
        if req.campaign_goal
        else ""
    )
    stage_block = f"PRODUCT STAGE: {req.product_stage}\n" if req.product_stage else ""
    voice_tags_block = (
        f"BRAND VOICE TAGS: {', '.join(req.brand_voice_tags)}\n"
        if req.brand_voice_tags
        else ""
    )
    do_not_say_block = (
        "DO NOT SAY (banned words/phrases — never include any of these in any scene, line, or CTA):\n"
        + "\n".join(f"  - {t}" for t in req.do_not_say)
        + "\n"
        if req.do_not_say
        else ""
    )

    # Prepend pattern analysis block when available — this is the key upgrade.
    pattern_block = (
        f"STORYTELLING PATTERN ANALYSIS\n"
        f"(extracted from {n_corpus} sample ads most similar to this brief — "
        f"replicate these patterns, not just the persona rules):\n\n"
        f"{pattern_analysis}\n\n"
        f"{'─' * 60}\n"
        if pattern_analysis
        else ""
    )

    payload_lines: list[str] = [
        pattern_block,
        category_block,
        tone_block,
        "",
        placement_block,
        "AD BRIEF:",
        f"PRODUCT: {req.product_name}",
        f"DESCRIPTION: {req.product_description}",
        f"INDUSTRY: {req.industry or 'unspecified'}",
        positioning_block.rstrip(),
        campaign_goal_block.rstrip(),
        competitor_block.rstrip(),
        stage_block.rstrip(),
        voice_tags_block.rstrip(),
        f"AUDIENCE: {req.target_audience or 'general Indian urban 18-35'}",
        f"DURATION: {req.duration_seconds}s (target ~{target_words} words in {req.language})",
        f"LANGUAGE: {req.language}",
        f"CAST:\n{cast_block}",
        celeb_instruction,
        proof_block.rstrip(),
        do_not_say_block.rstrip(),
        f"NOTES: {req.notes or '(none)'}",
        "",
        "Call emit_ad_script with the final ad. Total scene durations must sum to the",
        f"requested DURATION {req.duration_seconds}s within ±2s tolerance.",
    ]
    # Drop empty slots so optional blocks that weren't populated don't leave gaps.
    user_payload = "\n".join(line for line in payload_lines if line)

    tool_input, result = await rag.generate_with_tool(
        tab="ad",
        query=f"{req.product_name}: {req.product_description}",
        tool_name=AD_TOOL_NAME,
        tool_description=AD_TOOL_DESCRIPTION,
        tool_schema=AD_TOOL_SCHEMA,
        user_payload=user_payload,
        tone=effective_tone,
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

    # ── Post-gen audits ──────────────────────────────────────────────────────
    response.do_not_say_hits = _check_do_not_say(response, req.do_not_say)
    response.proof_point_found = _check_proof_point(response, req.proof_point)
    response.quality = await _judge_quality(rag, req, response)

    lf.update_current_span(output={
        "valid": validation.ok,
        "flags": merged_flags,
        "cost_usd": round(result.total_cost_usd, 5),
        "corpus_ads_used": n_corpus,
        "pattern_analysis_chars": len(pattern_analysis),
        "brand_voice_overrides": overrides_applied,
        "do_not_say_hits": response.do_not_say_hits,
        "proof_point_found": response.proof_point_found,
        "quality_total": response.quality.total if response.quality else None,
    })
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
        corpus_ads_used=n_corpus,
        industry=req.industry,
        placement=req.placement,
        overrides=overrides_applied,
        dns_hits=len(response.do_not_say_hits),
        proof_found=response.proof_point_found,
        quality_total=response.quality.total if response.quality else None,
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
            "X-Ad-Quality-Total": str(response.quality.total) if response.quality else "na",
            "X-Ad-DNS-Hits": ";".join(response.do_not_say_hits) or "none",
            "X-Ad-Proof-Found": {True: "true", False: "false", None: "na"}[response.proof_point_found],
        },
    )
