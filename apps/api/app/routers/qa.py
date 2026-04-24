from __future__ import annotations

import os

from fastapi import APIRouter, Depends

from langfuse import get_client

from app.core.logging import get_logger
from app.models.schemas import (
    Citation,
    Platform,
    QaConfidence,
    QaRequest,
    QaResponse,
    VerifiedClaim,
)
from app.routers.dependencies import get_rag_engine
from app.services.citation_verifier import verify_citations
from app.services.persona import build_cached_system, format_chunks
from app.services.rag import RAGEngine

log = get_logger(__name__)
router = APIRouter(prefix="/generate", tags=["qa"])


SENSITIVE_KEYWORDS = [
    "vote for",
    "religion",
    "hindu vs",
    "muslim vs",
    "suicid",       # catches: suicide, suicidal, suicidality
    "self harm",
    "self-harm",
    "diagnose",
    "should i take",
    "kashmir",
    "ram mandir",
    "ayodhya",
    "caa ",         # Citizenship Amendment Act (trailing space avoids "because")
    "nrc ",
    "article 370",
    "partition",
    "pakistan vs",
    "india vs pakistan",
]

CONFIDENCE_THRESHOLD = 0.35  # RRF-fused max-similarity threshold


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
    lf = get_client()
    with lf.start_as_current_observation(name="qa", as_type="span", input={"question": req.question}):
        return await _qa_inner(req, rag, lf)


async def _qa_inner(req: QaRequest, rag: RAGEngine, lf) -> QaResponse:  # type: ignore[no-untyped-def]
    if _is_sensitive(req.question):
        return QaResponse(
            status=QaConfidence.REFUSED_SENSITIVE,
            reason=(
                "This touches a topic Tanmay avoids speaking on publicly — "
                "politics, religion, mental-health prescriptions. "
                "Refusing rather than putting words in his mouth."
            ),
        )

    # 1. Paraphrase the question (Haiku) + multi-query retrieve with RRF fusion.
    paraphrases = await rag.paraphrase_query(req.question, n=2)
    all_queries = [req.question, *paraphrases]
    chunks, max_sim = await rag.multi_query_retrieve(
        all_queries,
        limit=8,
        tanmay_only=True,
    )

    if not chunks or max_sim < CONFIDENCE_THRESHOLD:
        return QaResponse(
            status=QaConfidence.REFUSED_LOW_CONFIDENCE,
            reason="Tanmay hasn't spoken publicly on this — refusing rather than fabricating.",
            max_similarity=max_sim,
            paraphrases_used=paraphrases,
        )

    # 2. Generate — pass the pre-fetched multi-query chunks through instead of re-retrieving.
    #    We reuse format_chunks + build_cached_system directly to avoid a second retrieval call.
    system_blocks = build_cached_system(tab="qa")
    exemplars = await rag.retrieve_exemplars(
        req.question,
        limit=3,
        register_any=["reflective", "informative", "comedic"],
    )

    from app.services.persona import format_exemplars

    user_sections = [format_chunks([c.as_payload_dict() for c in chunks])]
    if exemplars:
        user_sections.append(format_exemplars([{"text": e.text} for e in exemplars]))
    user_sections.append(f"QUESTION: {req.question}")
    user_message = "\n\n".join(user_sections)

    primary_model = os.environ.get("ANTHROPIC_MODEL_PRIMARY", "claude-sonnet-4-5-20250929")
    gen_response = await rag.anthropic.messages.create(
        model=primary_model,
        system=system_blocks,
        messages=[{"role": "user", "content": user_message}],
        max_tokens=900,
        temperature=0.4,
    )
    answer_text = "".join(b.text for b in gen_response.content if b.type == "text")

    # 3. Verify citations.
    verifier = await verify_citations(answer=answer_text, chunks=chunks, anthropic=rag.anthropic)

    # 4. Build the public response.
    citations = [
        Citation(
            source_id=c.chunk_id,
            url=c.url,
            platform=_infer_platform(c.source),
            title=c.title,
            timestamp_seconds=int(c.start_seconds) if c.start_seconds is not None else None,
            excerpt=c.text[:240],
        )
        for c in chunks
    ]

    verified_claims_out = [
        VerifiedClaim(
            claim=vc.claim,
            citation_indices=vc.citation_indices,
            supported=vc.supported,
        )
        for vc in verifier.claims
    ]

    lf.update_current_span(output={
        "status": "answered",
        "max_similarity": round(max_sim, 4),
        "n_supported": verifier.n_supported,
        "n_unsupported": verifier.n_unsupported,
        "citations": len(chunks),
    })
    log.info(
        "qa_answered",
        question=req.question[:80],
        max_sim=round(max_sim, 3),
        gen_in=getattr(gen_response.usage, "input_tokens", 0),
        gen_out=getattr(gen_response.usage, "output_tokens", 0),
        verifier_in=verifier.input_tokens,
        verifier_out=verifier.output_tokens,
        n_supported=verifier.n_supported,
        n_unsupported=verifier.n_unsupported,
    )
    return QaResponse(
        status=QaConfidence.ANSWERED,
        answer=verifier.cleaned_answer or answer_text,
        citations=citations,
        max_similarity=max_sim,
        verified_claims=verified_claims_out,
        n_supported=verifier.n_supported,
        n_unsupported=verifier.n_unsupported,
        paraphrases_used=paraphrases,
    )
