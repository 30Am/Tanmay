from __future__ import annotations

import json
import re

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from langfuse import get_client

from app.core.logging import get_logger
from app.models.schemas import (
    Citation,
    ContentGenerateRequest,
    ContentGenerateResponse,
    Platform,
)
from app.routers.dependencies import get_rag_engine
from app.services.persona import get_content_format_rules
from app.services.rag import RAGEngine

log = get_logger(__name__)
router = APIRouter(prefix="/generate", tags=["content"])


SECTION_RE = re.compile(r"^\s*#{1,3}\s*\d*[\.\)]?\s*(SCRIPT|DESCRIPTION|RATIONALE)\b.*$", re.I | re.M)

# Structural anchors injected at the top of the user message to reinforce the system-prompt
# format rules. These explicit reminders dramatically improve model compliance with structure.
FORMAT_ANCHOR: dict[str, str] = {
    "reel": (
        "REQUIRED STRUCTURE: Shot-by-shot REEL script. HOOK line (one unexpected line, first 2-3s) "
        "→ short punchy body lines (max 8-10 words each, one beat per line) → hard CLOSE punchline. "
        "NO paragraph prose inside the SCRIPT section."
    ),
    "youtube_short": (
        "REQUIRED STRUCTURE: Shot-by-shot YOUTUBE SHORT script. HOOK line (one unexpected line, first 2-3s) "
        "→ short punchy body lines (max 8-10 words each, one beat per line) → hard CLOSE punchline. "
        "NO paragraph prose inside the SCRIPT section."
    ),
    "talking_head": (
        "REQUIRED STRUCTURE: Direct-to-camera TALKING HEAD script. Conversational paragraphs only "
        "(NOT beat-by-beat lines). OPEN → BODY (3-4 paragraphs with [beat] markers) → sharp CLOSE line."
    ),
    "long_podcast": (
        "REQUIRED STRUCTURE: PODCAST segment. COLD OPEN → ENERGY RAMP → MAIN SEGMENT → CLOSE/TEASE. "
        "Longer paragraphs, podcast host energy, co-host name-drops, allow tangents."
    ),
    "thread": (
        "REQUIRED STRUCTURE: TWITTER THREAD only. Output numbered tweets EXACTLY like this:\n"
        "1/\n[tweet text ≤280 chars]\n\n2/\n[tweet text ≤280 chars]\n\n3/\n...\n\n"
        "Minimum 8 tweets. Each tweet ≤280 characters. Each tweet standalone. "
        "NO paragraph prose. NO running narrative. ONLY numbered tweets."
    ),
    "stage": (
        "REQUIRED STRUCTURE: STAND-UP STAGE BIT with these labeled sections inside SCRIPT:\n"
        "PREMISE:\n[text]\n\nSETUP:\n[text]\n\nFIRST PUNCHLINE:\n[text]\n\n"
        "ESCALATION:\n[text]\n\nCALLBACK:\n[text]\n\nTAG (optional):\n[text]\n"
        "Use those exact labels. DO NOT write a continuous monologue."
    ),
    "monologue": (
        "REQUIRED STRUCTURE: Long-form MONOLOGUE — single unbroken arc with planted callback. "
        "No section labels inside the text. PLANT early → DEVELOP → ESCALATE → PAY OFF the plant. "
        "Paragraph breaks between beat-shifts. [beat] for delivery pauses."
    ),
    "explainer": (
        "REQUIRED STRUCTURE: EXPLAINER with these flowing sections inside SCRIPT:\n"
        "HOOK → WHAT IS IT → WHY IT MATTERS → HOW IT WORKS → TANMAY'S TAKE.\n"
        "Paragraph prose, educational progression, plain-language analogies."
    ),
    "interview": (
        "REQUIRED STRUCTURE: INTERVIEW DIALOGUE. Every line must be labeled:\n"
        "TANMAY: [line]\nGUEST: [line]\n\nMinimum 8 TANMAY + 8 GUEST exchanges. "
        "NO paragraph prose. NO narration. ONLY labeled speaker dialogue."
    ),
    "reaction": (
        "REQUIRED STRUCTURE: REACTION video. Alternate EXACTLY like:\n"
        "[CLIP/MOMENT: description]\nTANMAY: [reaction]\n\n[CLIP/MOMENT: description]\nTANMAY: [reaction]\n\n"
        "Start with TANMAY: intro. Minimum 5 clip-reaction pairs. NO paragraph prose."
    ),
}

_LANGUAGE_INSTRUCTIONS: dict[str, str] = {
    "hinglish": (
        "LANGUAGE: Hinglish — natural English-Hindi code-switching in Tanmay's voice. "
        "Switch to Hindi words, phrases, and connectors where they land harder or feel more natural. "
        "Don't force Hindi in every sentence — let it fall organically."
    ),
    "english": (
        "LANGUAGE: English only — write the ENTIRE script in English. "
        "No Hindi or Devanagari words at all. Keep Tanmay's voice but in pure English. "
        "Occasional transliterated Indian cultural references (bhai, yaar as exclamations) are fine, "
        "but no Hindi sentences or phrases."
    ),
    "hindi": (
        "LANGUAGE: Hindi only — write the ENTIRE script in Hindi. "
        "Use natural conversational Hindi (not formal/shuddh), exactly how Tanmay would speak on stage "
        "or in a casual video. Roman script is fine if that's more natural for the format. "
        "No English sentences — English brand names or tech terms (e.g. 'AI', 'startup') are fine as-is."
    ),
}


def _build_language_instruction(language: str) -> str:
    return _LANGUAGE_INSTRUCTIONS.get(language, "")


def _parse_sections(text: str) -> dict[str, str]:
    """Split the model output into {script, description, rationale}.

    Tolerates markdown headings, numbered sections, or plain labels. Falls back to
    returning the whole text under "script" if nothing parses.
    """
    matches = list(SECTION_RE.finditer(text))
    out: dict[str, str] = {"script": "", "description": "", "rationale": ""}
    if not matches:
        out["script"] = text.strip()
        return out
    for i, m in enumerate(matches):
        label = m.group(1).lower()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[label] = text[start:end].strip()
    return out


def _infer_platform(source: str) -> Platform:
    if source in {"honestly", "overpowered", "sheet"}:
        return Platform.YOUTUBE
    return Platform.OTHER


@router.post("/content", response_model=ContentGenerateResponse)
async def generate_content(
    req: ContentGenerateRequest,
    rag: RAGEngine = Depends(get_rag_engine),
) -> ContentGenerateResponse:
    lf = get_client()
    with lf.start_as_current_observation(
        name="content",
        as_type="span",
        input={"idea": req.idea, "format": req.format, "length_s": req.target_length_seconds, "language": req.language},
    ):
        format_rules = get_content_format_rules(req.format)
        anchor = FORMAT_ANCHOR.get(req.format, "")
        language_instruction = _build_language_instruction(req.language)
        user_payload = "\n\n".join(filter(None, [
            anchor,
            language_instruction,
            f"IDEA: {req.idea}",
            f"FORMAT: {req.format}",
            f"LANGUAGE: {req.language}",
            f"TARGET LENGTH: {req.target_length_seconds} seconds",
        ]))
        result = await rag.generate(
            tab="content",
            query=req.idea,
            user_payload=user_payload,
            tone=req.tone,
            format_rules=format_rules,
            retrieval_top_k=8,
            exemplars_k=4,
            exemplar_registers=["comedic", "reflective", "informative"],
            max_tokens=2000,
        )
        sections = _parse_sections(result.text)
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
        log.info(
            "content_generated",
            idea=req.idea[:80],
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            max_similarity=round(result.max_similarity, 3),
        )
        response = ContentGenerateResponse(
            script=sections["script"] or result.text,
            description=sections["description"],
            rationale=sections["rationale"],
            citations=citations,
        )
        lf.update_current_span(output={"citations": len(citations), "cost_usd": round(result.total_cost_usd, 5)})
        return response


@router.post("/content/stream")
async def generate_content_stream(
    req: ContentGenerateRequest,
    rag: RAGEngine = Depends(get_rag_engine),
) -> StreamingResponse:
    lf = get_client()
    format_rules = get_content_format_rules(req.format)
    anchor = FORMAT_ANCHOR.get(req.format, "")
    language_instruction = _build_language_instruction(req.language)
    user_payload = "\n\n".join(filter(None, [
        anchor,
        language_instruction,
        f"IDEA: {req.idea}",
        f"FORMAT: {req.format}",
        f"LANGUAGE: {req.language}",
        f"TARGET LENGTH: {req.target_length_seconds} seconds",
    ]))

    async def event_stream():
        with lf.start_as_current_observation(
            name="content-stream",
            as_type="span",
            input={"idea": req.idea, "format": req.format, "length_s": req.target_length_seconds},
        ):
            async for token, result in rag.stream_generate(
                tab="content",
                query=req.idea,
                user_payload=user_payload,
                tone=req.tone,
                format_rules=format_rules,
                retrieval_top_k=8,
                exemplars_k=4,
                exemplar_registers=["comedic", "reflective", "informative"],
                max_tokens=2000,
            ):
                if token is not None:
                    yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"
                else:
                    sections = _parse_sections(result.text)
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
                    done_payload = {
                        "type": "done",
                        "script": sections["script"] or result.text,
                        "description": sections["description"],
                        "rationale": sections["rationale"],
                        "citations": [c.model_dump() for c in citations],
                    }
                    yield f"data: {json.dumps(done_payload)}\n\n"
                    lf.update_current_span(output={"citations": len(citations), "cost_usd": round(result.total_cost_usd, 5)})
                    log.info(
                        "content_streamed",
                        idea=req.idea[:80],
                        input_tokens=result.input_tokens,
                        output_tokens=result.output_tokens,
                        max_similarity=round(result.max_similarity, 3),
                    )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
