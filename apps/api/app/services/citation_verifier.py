"""Citation verifier — for each sentence in the model's answer, determine which retrieved
chunk(s) support it. Strips unsupported claims.

Runs on Haiku 4.5 with Anthropic tool_use so the verdict is schema-constrained. Cheap:
answer + ~8 chunks is typically 2-4K input tokens.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any

from anthropic import AsyncAnthropic

from app.services.rag import RetrievedChunk

ANTHROPIC_UTILITY = os.environ.get("ANTHROPIC_MODEL_UTILITY", "claude-haiku-4-5-20251001")


@dataclass
class VerifiedClaim:
    claim: str
    citation_indices: list[int] = field(default_factory=list)  # 1-based, matching chunks list order
    supported: bool = False


@dataclass
class VerifierResult:
    cleaned_answer: str  # answer with unsupported claims stripped
    claims: list[VerifiedClaim]
    n_supported: int
    n_unsupported: int
    input_tokens: int = 0
    output_tokens: int = 0


VERIFIER_TOOL = {
    "name": "report_claim_support",
    "description": (
        "Report which factual claims in the answer are supported by the retrieved chunks. "
        "Use this exactly once after reviewing every sentence. Ignore opinion/framing "
        "sentences with no factual content — only report things that can be right or wrong."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "claim": {
                            "type": "string",
                            "description": "The factual sentence verbatim from the answer.",
                        },
                        "citation_indices": {
                            "type": "array",
                            "items": {"type": "integer", "minimum": 1},
                            "description": (
                                "1-based indices into the retrieved-chunks list that "
                                "directly support this claim. Empty if no chunk supports it."
                            ),
                        },
                        "supported": {
                            "type": "boolean",
                            "description": "True iff at least one chunk directly supports this claim.",
                        },
                    },
                    "required": ["claim", "citation_indices", "supported"],
                },
            },
        },
        "required": ["claims"],
    },
}


VERIFIER_SYSTEM = """You are a fact-checking auditor for a RAG system.

You receive an ANSWER and a numbered list of RETRIEVED CHUNKS that the answer was supposed
to draw from. For each factual statement in the answer, you decide whether it is directly
supported by one or more of the chunks.

Rules:
- A claim is SUPPORTED only when the content is actually in the chunk — not just plausible.
- Paraphrased claims are fine if the chunk says the same thing in different words.
- Do NOT fact-check opinions, jokes, or rhetorical framing — only statements that assert
  something factual about Tanmay's views, experiences, or the world.
- If a claim blends a supported fact with unsupported additions, mark it unsupported.
- Cite ALL chunks that support a claim, not just the best one.

Report via the report_claim_support tool. Only use that tool — no prose response."""


async def verify_citations(
    *,
    answer: str,
    chunks: list[RetrievedChunk],
    anthropic: AsyncAnthropic | None = None,
) -> VerifierResult:
    if not answer or not chunks:
        return VerifierResult(cleaned_answer=answer or "", claims=[], n_supported=0, n_unsupported=0)

    client = anthropic or AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    chunks_text = "\n\n".join(
        f"[{i}] source={c.source} title={c.title or ''}\n{c.text}"
        for i, c in enumerate(chunks, start=1)
    )
    user_message = f"ANSWER:\n{answer}\n\n---\nRETRIEVED CHUNKS:\n{chunks_text}"

    response = await client.messages.create(
        model=ANTHROPIC_UTILITY,
        system=VERIFIER_SYSTEM,
        messages=[{"role": "user", "content": user_message}],
        tools=[VERIFIER_TOOL],
        tool_choice={"type": "tool", "name": VERIFIER_TOOL["name"]},
        max_tokens=2000,
        temperature=0.0,
    )

    tool_input: dict[str, Any] = {}
    for block in response.content:
        if block.type == "tool_use" and block.name == VERIFIER_TOOL["name"]:
            tool_input = dict(block.input)
            break

    raw_claims = tool_input.get("claims") or []
    claims: list[VerifiedClaim] = []
    for c in raw_claims:
        claims.append(
            VerifiedClaim(
                claim=c.get("claim", ""),
                citation_indices=list(c.get("citation_indices") or []),
                supported=bool(c.get("supported")),
            )
        )

    # Build cleaned answer: remove sentences corresponding to unsupported factual claims.
    # Sentence matching is fuzzy — we compare normalized text.
    unsupported_texts = [_normalize(c.claim) for c in claims if not c.supported]
    cleaned = _strip_unsupported(answer, unsupported_texts)

    usage = response.usage
    return VerifierResult(
        cleaned_answer=cleaned,
        claims=claims,
        n_supported=sum(1 for c in claims if c.supported),
        n_unsupported=sum(1 for c in claims if not c.supported),
        input_tokens=getattr(usage, "input_tokens", 0),
        output_tokens=getattr(usage, "output_tokens", 0),
    )


def _normalize(s: str) -> str:
    s = re.sub(r"[\s\n\t]+", " ", s).strip().lower()
    s = re.sub(r"[^\w\s]", "", s)
    return s


def _strip_unsupported(answer: str, unsupported_normalized: list[str]) -> str:
    """Rebuild the answer, dropping sentences whose normalized form matches any
    unsupported-claim text."""
    if not unsupported_normalized:
        return answer

    # Keep paragraphs and sentence structure reasonable — split on sentence boundaries
    # that preserve the delimiter.
    parts = re.split(r"(?<=[.!?])\s+", answer)
    kept: list[str] = []
    for part in parts:
        norm = _normalize(part)
        # Drop if exact match, or if the normalized form clearly contains the unsupported claim.
        if any(u and (u == norm or u in norm) for u in unsupported_normalized):
            continue
        kept.append(part)
    return " ".join(kept).strip()
