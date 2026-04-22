from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from app.core.logging import get_logger
from app.models.schemas import Citation, ContentGenerateRequest, ContentFormat, Platform
from app.routers.dependencies import get_llm_service, get_retrieval_service
from app.services.llm import LLMService
from app.services.persona import build_system_prompt, format_chunks, format_exemplars
from app.services.retrieval import RetrievalService

log = get_logger(__name__)
router = APIRouter(prefix="/generate", tags=["content"])


CONTENT_FORMAT_RULES = """\
OUTPUT FORMAT: Return three clearly separated sections, each prefixed exactly:

### SCRIPT
The on-camera script, written to be spoken aloud. Stage directions in [brackets].

### DESCRIPTION
2-3 sentence post description suited to the platform (YouTube/Reel/Thread).

### RATIONALE
3-5 bullets on what creative choices you made and why — the "how Tanmay would think about it" note.
"""


def _format_filter(fmt: str) -> list[ContentFormat]:
    mapping = {
        "long_podcast": [ContentFormat.LONG_PODCAST, ContentFormat.INTERVIEW],
        "reel": [ContentFormat.REEL],
        "thread": [ContentFormat.THREAD, ContentFormat.TWEET],
        "stage": [ContentFormat.STAGE],
    }
    return mapping.get(fmt, [])


@router.post("/content")
async def generate_content(
    req: ContentGenerateRequest,
    llm: LLMService = Depends(get_llm_service),
    retrieval: RetrievalService = Depends(get_retrieval_service),
) -> EventSourceResponse:
    fmt_filter = _format_filter(req.format)

    retrieval_result = await retrieval.retrieve(
        req.idea,
        format_filter=fmt_filter,
        exclude_sponsored=True,
    )
    exemplars = await retrieval.style_exemplars(req.idea, format_filter=fmt_filter, limit=5)

    system = build_system_prompt(
        tab="content_generation",
        format_rules=CONTENT_FORMAT_RULES,
        tone=req.tone,
    )

    user_payload = "\n\n".join(
        [
            format_chunks(retrieval_result.chunks),
            format_exemplars(exemplars),
            f"IDEA: {req.idea}",
            f"FORMAT: {req.format}",
            f"TARGET LENGTH: {req.target_length_seconds} seconds",
        ]
    )

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

    async def event_stream() -> AsyncIterator[dict[str, str]]:
        yield {
            "event": "citations",
            "data": json.dumps([c.model_dump(mode="json") for c in citations]),
        }
        async for token in llm.stream(
            system=system,
            messages=[{"role": "user", "content": user_payload}],
            temperature=0.8,
        ):
            yield {"event": "token", "data": token}
        yield {"event": "done", "data": ""}

    return EventSourceResponse(event_stream())
