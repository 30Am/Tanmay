from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.logging import get_logger
from app.models.schemas import Citation, Platform, QaConfidence, QaRequest, QaResponse
from app.routers.dependencies import get_rag_engine
from app.services.rag import RAGEngine

log = get_logger(__name__)
router = APIRouter(prefix="/generate", tags=["qa"])


SENSITIVE_KEYWORDS = [
    "vote for",
    "religion",
    "hindu vs",
    "muslim vs",
    "suicide",
    "self harm",
    "diagnose",
    "should i take",
]

CONFIDENCE_THRESHOLD = 0.35  # cosine similarity — retrieved chunks below this = refuse


def _is_sensitive(question: str) -> bool:
    q = question.lower()
    return any(k in q for k in SENSITIVE_KEYWORDS)


def _infer_platform(source: str) -> Platform:
    if source in {"honestly", "overpowered", "sheet"}:
        return Platform.YOUTUBE
    return Platform.OTHER


@router.post("/qa", response_model=QaResponse)
async def qa(
    req: QaRequest,
    rag: RAGEngine = Depends(get_rag_engine),
) -> QaResponse:
    if _is_sensitive(req.question):
        return QaResponse(
            status=QaConfidence.REFUSED_SENSITIVE,
            reason=(
                "This touches a topic Tanmay avoids speaking on publicly — "
                "politics, religion, mental-health prescriptions. "
                "Refusing rather than putting words in his mouth."
            ),
        )

    # Peek at retrieval before paying for generation
    chunks = await rag.retrieve(req.question, limit=8, tanmay_only=True)
    max_sim = max((c.score for c in chunks), default=0.0)

    if not chunks or max_sim < CONFIDENCE_THRESHOLD:
        return QaResponse(
            status=QaConfidence.REFUSED_LOW_CONFIDENCE,
            reason="Tanmay hasn't spoken publicly on this — refusing rather than fabricating.",
            max_similarity=max_sim,
        )

    result = await rag.generate(
        tab="qa",
        query=req.question,
        user_payload=f"QUESTION: {req.question}",
        retrieval_top_k=8,
        exemplars_k=3,
        exemplar_registers=["reflective", "informative", "comedic"],
        max_tokens=900,
        temperature=0.4,
        tanmay_only_retrieval=True,
    )

    citations = [
        Citation(
            source_id=c.chunk_id,
            url=c.url,
            platform=_infer_platform(c.source),
            title=c.title,
            timestamp_seconds=int(c.start_seconds) if c.start_seconds is not None else None,
            excerpt=c.text[:240],
        )
        for c in result.citations
    ]

    log.info(
        "qa_answered",
        question=req.question[:80],
        max_sim=round(result.max_similarity, 3),
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )
    return QaResponse(
        status=QaConfidence.ANSWERED,
        answer=result.text,
        citations=citations,
        max_similarity=result.max_similarity,
    )
