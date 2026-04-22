from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.logging import get_logger
from app.models.schemas import Citation, Platform, QaConfidence, QaRequest, QaResponse
from app.routers.dependencies import get_llm_service, get_retrieval_service
from app.services.llm import LLMService
from app.services.persona import build_system_prompt, format_chunks
from app.services.retrieval import RetrievalService

log = get_logger(__name__)
router = APIRouter(prefix="/generate", tags=["qa"])


QA_FORMAT_RULES = """\
OUTPUT FORMAT:
- Ground every factual claim in the RETRIEVED CONTEXT. Cite using [1], [2], ... matching the
  bracketed numbers in the context.
- Start the answer with a 1-sentence takeaway, then elaborate.
- 150-300 words.
- If the context does not support a specific claim, do not make it.
- If asked about sensitive topics (hard politics, religion, personal gossip, mental health prescriptions),
  politely decline and briefly explain why.
"""


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


def _is_sensitive(question: str) -> bool:
    q = question.lower()
    return any(k in q for k in SENSITIVE_KEYWORDS)


async def _paraphrase(llm: LLMService, question: str) -> list[str]:
    system = "Rewrite the user's question into 2 alternative phrasings that preserve meaning. Return one per line, no bullets."
    raw = await llm.complete(
        system=system,
        messages=[{"role": "user", "content": question}],
        model=llm.utility,
        temperature=0.3,
        max_tokens=200,
    )
    paraphrases = [line.strip() for line in raw.splitlines() if line.strip()][:2]
    return [question, *paraphrases]


@router.post("/qa", response_model=QaResponse)
async def qa(
    req: QaRequest,
    llm: LLMService = Depends(get_llm_service),
    retrieval: RetrievalService = Depends(get_retrieval_service),
) -> QaResponse:
    if _is_sensitive(req.question):
        return QaResponse(
            status=QaConfidence.REFUSED_SENSITIVE,
            reason="This touches a topic Tanmay avoids speaking on publicly (politics/religion/mental-health prescription).",
        )

    queries = await _paraphrase(llm, req.question)
    retrieval_result = await retrieval.multi_query_retrieve(queries)

    if retrieval_result.below_threshold or not retrieval_result.chunks:
        return QaResponse(
            status=QaConfidence.REFUSED_LOW_CONFIDENCE,
            reason="Tanmay hasn't spoken publicly on this — refusing rather than fabricating.",
            max_similarity=retrieval_result.max_similarity,
        )

    system = build_system_prompt(tab="qa", format_rules=QA_FORMAT_RULES)
    user_payload = "\n\n".join([format_chunks(retrieval_result.chunks), f"QUESTION: {req.question}"])

    answer = await llm.complete(
        system=system,
        messages=[{"role": "user", "content": user_payload}],
        temperature=0.4,
        max_tokens=900,
    )

    citations = [
        Citation(
            source_id=c.source_id,
            url=c.url,
            platform=c.platform if isinstance(c.platform, Platform) else Platform(c.platform),
            timestamp_seconds=c.start_seconds,
            excerpt=c.text[:240],
        )
        for c in retrieval_result.chunks
    ]

    return QaResponse(
        status=QaConfidence.ANSWERED,
        answer=answer,
        citations=citations,
        max_similarity=retrieval_result.max_similarity,
    )
