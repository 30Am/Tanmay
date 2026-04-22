"""Semantic chunker for Tanmay transcripts and posts.

Strategy:
  * For transcripts (word-level): split on speaker changes and long pauses (>=1.2s) once the
    running chunk has reached MIN_TOKENS. Always split on MAX_TOKENS even mid-turn.
  * For posts (tweets, LI, IG captions): one chunk per post unless it exceeds MAX_TOKENS,
    in which case split on paragraph breaks.

The chunker is intentionally deterministic — same input yields same chunk_ids so re-runs
don't create vector-store duplicates.
"""
from __future__ import annotations

import hashlib
import re
from collections import Counter
from dataclasses import dataclass, field

import tiktoken

TOKENIZER = tiktoken.get_encoding("cl100k_base")
MIN_TOKENS = 400
MAX_TOKENS = 800
# Rough English: ~1.3 tokens per word. Use word counts as cheap proxy during accumulation,
# then the final chunk texts will land in the 400-800 token band.
MIN_WORDS = 300
MAX_WORDS = 600
PAUSE_THRESHOLD_S = 1.2


@dataclass
class Word:
    text: str
    start: float
    end: float
    speaker: int | None = None


@dataclass
class Chunk:
    chunk_id: str
    source_id: str
    text: str
    start_seconds: float | None
    end_seconds: float | None
    speaker: int | None = None
    speakers: list[int] = field(default_factory=list)


def _token_count(text: str) -> int:
    return len(TOKENIZER.encode(text))


def _hash_id(source_id: str, start: float | None, text: str) -> str:
    h = hashlib.sha1(f"{source_id}|{start}|{text[:200]}".encode()).hexdigest()[:16]
    return f"{source_id}_{h}"


def chunk_transcript(source_id: str, words: list[Word]) -> list[Chunk]:
    if not words:
        return []

    chunks: list[Chunk] = []
    buf: list[Word] = []

    def flush() -> None:
        if not buf:
            return
        text = " ".join(w.text for w in buf).strip()
        text = re.sub(r"\s+([,.!?;:])", r"\1", text)
        if text:
            spk_counts = Counter(w.speaker for w in buf if w.speaker is not None)
            dom = spk_counts.most_common(1)[0][0] if spk_counts else None
            chunks.append(
                Chunk(
                    chunk_id=_hash_id(source_id, buf[0].start, text),
                    source_id=source_id,
                    text=text,
                    start_seconds=buf[0].start,
                    end_seconds=buf[-1].end,
                    speaker=dom,
                    speakers=sorted(spk_counts.keys()),
                )
            )
        buf.clear()

    prev: Word | None = None
    for w in words:
        # Natural-boundary split: only fires after MIN_WORDS, so short turns don't shatter into tiny chunks.
        if buf and len(buf) >= MIN_WORDS and prev is not None:
            speaker_change = w.speaker is not None and prev.speaker is not None and w.speaker != prev.speaker
            pause = (w.start - prev.end) > PAUSE_THRESHOLD_S
            if speaker_change or pause:
                flush()

        buf.append(w)

        # Hard cap — never exceed MAX_WORDS, even mid-turn.
        if len(buf) >= MAX_WORDS:
            flush()
        prev = w

    flush()
    return chunks


def chunk_post(source_id: str, text: str) -> list[Chunk]:
    text = text.strip()
    if not text:
        return []
    if _token_count(text) <= MAX_TOKENS:
        return [
            Chunk(
                chunk_id=_hash_id(source_id, None, text),
                source_id=source_id,
                text=text,
                start_seconds=None,
                end_seconds=None,
            )
        ]
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[Chunk] = []
    buf: list[str] = []
    for p in paragraphs:
        candidate = "\n\n".join([*buf, p])
        if _token_count(candidate) > MAX_TOKENS and buf:
            joined = "\n\n".join(buf)
            chunks.append(
                Chunk(
                    chunk_id=_hash_id(source_id, None, joined),
                    source_id=source_id,
                    text=joined,
                    start_seconds=None,
                    end_seconds=None,
                )
            )
            buf = [p]
        else:
            buf.append(p)
    if buf:
        joined = "\n\n".join(buf)
        chunks.append(
            Chunk(
                chunk_id=_hash_id(source_id, None, joined),
                source_id=source_id,
                text=joined,
                start_seconds=None,
                end_seconds=None,
            )
        )
    return chunks
