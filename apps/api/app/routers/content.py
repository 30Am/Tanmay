from __future__ import annotations

import re

from fastapi import APIRouter, Depends

from app.core.logging import get_logger
from app.models.schemas import (
    Citation,
    ContentGenerateRequest,
    ContentGenerateResponse,
    Platform,
)
from app.routers.dependencies import get_rag_engine
from app.services.rag import RAGEngine

log = get_logger(__name__)
router = APIRouter(prefix="/generate", tags=["content"])


SECTION_RE = re.compile(r"^\s*#{1,3}\s*\d*[\.\)]?\s*(SCRIPT|DESCRIPTION|RATIONALE)\b.*$", re.I | re.M)


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
    user_payload = (
        f"IDEA: {req.idea}\n"
        f"FORMAT: {req.format}\n"
        f"TARGET LENGTH: {req.target_length_seconds} seconds"
    )
    result = await rag.generate(
        tab="content",
        query=req.idea,
        user_payload=user_payload,
        tone=req.tone,
        retrieval_top_k=8,
        exemplars_k=4,
        exemplar_registers=["comedic", "reflective", "informative"],
        max_tokens=1400,
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
    return ContentGenerateResponse(
        script=sections["script"] or result.text,
        description=sections["description"],
        rationale=sections["rationale"],
        citations=citations,
    )
