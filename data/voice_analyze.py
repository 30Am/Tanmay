"""Analyze the voice corpus to extract patterns for the persona prompt.

Sends the full voice_corpus.json (94 chunks) to Gemini 2.5 Flash in one call (context is
easily under 20K tokens). Asks for a schema-constrained voice profile covering signature
phrases, sentence mechanics, opener/closer patterns, callback humor examples, and
self-deprecation examples. Each observation cites the chunk_ids that evidenced it — so the
persona prompt is traceable back to data.

Output: data/voice_profile.json
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

DATA = Path(__file__).parent
REPO_ROOT = DATA.parent
sys.path.insert(0, str(REPO_ROOT))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO_ROOT / "apps" / "api" / ".env", override=True)

from google import genai  # noqa: E402
from google.genai import types  # noqa: E402

MODEL = os.environ.get("GEMINI_PRO_MODEL", "gemini-2.5-flash")  # use Flash (not Lite) for better analysis
CORPUS_PATH = DATA / "voice_corpus.json"
OUT_PATH = DATA / "voice_profile.json"


SYSTEM = """You are a voice-pattern analyst. Given excerpts from the Indian comedian/creator
Tanmay Bhat's public content (podcast hosting, interviews, commentary), produce a dense,
evidence-grounded voice profile that another AI can use to mimic his register.

You must ground every observation in specific chunk_ids. Don't make claims you can't point to.
Be concrete — no generic creator-coach filler. Capture what is distinctive about HIS voice
vs. any generic Indian-English podcast host.

Focus on features a generation model needs:
- Lexical signatures: words/phrases he reaches for, code-switch anchors, filler habits.
- Sentence mechanics: length, rhythm, question-to-statement ratio, use of asides.
- Structural moves: openings, tangent patterns, callbacks, how he lands a beat.
- Self-deprecation and vulnerability patterns — how/when he turns it on himself.
- Roast technique: targets, escalation pattern, when he softens.
- Hinglish mechanics: Hindi tokens most commonly interleaved, code-switch triggers.
- Topic posture: what he engages deeply vs. glides past; recurring frames.
- What he avoids (from the corpus): topics/registers that are visibly absent.

Output JSON only, matching the provided schema."""


RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "signature_phrases": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "phrase": {"type": "string"},
                    "usage": {"type": "string", "description": "how and when he uses it"},
                    "evidence_chunk_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["phrase", "usage", "evidence_chunk_ids"],
            },
        },
        "sentence_mechanics": {
            "type": "object",
            "properties": {
                "typical_length": {"type": "string", "description": "short/mixed/long with rationale"},
                "rhythm": {"type": "string"},
                "question_to_statement": {"type": "string"},
                "asides_and_direct_address": {"type": "string"},
                "evidence_chunk_ids": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["typical_length", "rhythm", "question_to_statement", "asides_and_direct_address", "evidence_chunk_ids"],
        },
        "openers_and_transitions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "example_quote": {"type": "string"},
                    "evidence_chunk_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["pattern", "example_quote", "evidence_chunk_ids"],
            },
        },
        "callback_and_tangent_patterns": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "example_quote": {"type": "string"},
                    "evidence_chunk_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["pattern", "example_quote", "evidence_chunk_ids"],
            },
        },
        "self_deprecation": {
            "type": "object",
            "properties": {
                "style": {"type": "string"},
                "triggers": {"type": "string"},
                "example_quotes": {"type": "array", "items": {"type": "string"}},
                "evidence_chunk_ids": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["style", "triggers", "example_quotes", "evidence_chunk_ids"],
        },
        "roast_technique": {
            "type": "object",
            "properties": {
                "targets": {"type": "string"},
                "escalation_pattern": {"type": "string"},
                "when_he_softens": {"type": "string"},
                "example_quotes": {"type": "array", "items": {"type": "string"}},
                "evidence_chunk_ids": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["targets", "escalation_pattern", "when_he_softens", "example_quotes", "evidence_chunk_ids"],
        },
        "hinglish_mechanics": {
            "type": "object",
            "properties": {
                "ratio_estimate": {"type": "string"},
                "frequent_hindi_tokens": {"type": "array", "items": {"type": "string"}},
                "code_switch_triggers": {"type": "string"},
                "example_quotes": {"type": "array", "items": {"type": "string"}},
                "evidence_chunk_ids": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["ratio_estimate", "frequent_hindi_tokens", "code_switch_triggers", "example_quotes", "evidence_chunk_ids"],
        },
        "topic_posture": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "stance": {"type": "string"},
                    "evidence_chunk_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["topic", "stance", "evidence_chunk_ids"],
            },
        },
        "avoided_or_absent": {
            "type": "array",
            "items": {"type": "string"},
        },
        "overall_summary": {"type": "string", "description": "3-5 sentence voice summary"},
    },
    "required": [
        "signature_phrases", "sentence_mechanics", "openers_and_transitions",
        "callback_and_tangent_patterns", "self_deprecation", "roast_technique",
        "hinglish_mechanics", "topic_posture", "avoided_or_absent", "overall_summary",
    ],
}


async def main() -> None:
    corpus = json.loads(CORPUS_PATH.read_text())
    print(f"loaded {len(corpus)} chunks from {CORPUS_PATH.name}")

    # Format corpus for the prompt.
    parts = []
    for c in corpus:
        parts.append(
            f"=== chunk_id={c['chunk_id']}  register={c['register']}  source={c['source']}  ===\n{c['text']}\n"
        )
    corpus_text = "\n".join(parts)

    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    resp = await client.aio.models.generate_content(
        model=MODEL,
        contents=corpus_text,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM,
            response_mime_type="application/json",
            response_schema=RESPONSE_SCHEMA,
            temperature=0.2,
            max_output_tokens=16000,
        ),
    )
    raw = resp.text or ""
    (DATA / "voice_profile.raw.txt").write_text(raw)
    try:
        profile = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"JSON parse failed: {e}\nsaved raw to voice_profile.raw.txt ({len(raw)} chars)")
        print(f"last 200 chars of raw: {raw[-200:]}")
        raise
    OUT_PATH.write_text(json.dumps(profile, indent=2, ensure_ascii=False))
    # Summary print
    print(f"wrote {OUT_PATH.name}")
    print(f"  signature_phrases: {len(profile.get('signature_phrases', []))}")
    print(f"  openers/transitions: {len(profile.get('openers_and_transitions', []))}")
    print(f"  callback patterns: {len(profile.get('callback_and_tangent_patterns', []))}")
    print(f"  topic posture items: {len(profile.get('topic_posture', []))}")
    print("\n--- overall_summary ---")
    print(profile.get("overall_summary", ""))


if __name__ == "__main__":
    asyncio.run(main())
