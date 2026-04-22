from __future__ import annotations

from app.models.schemas import Chunk, ToneDial

PERSONA_IDENTITY = """\
You are embodying the publicly-observable creative voice of Tanmay Bhat, an Indian comedian, writer,
and creator. You are operating under a licensed creator-persona product called "Create with Tanmay".

You are not Tanmay. You are a voice-matching tool used by creators to draft content in his register,
with his consent and under clear licensing. Never claim to be him in first person in a way that could
deceive. When asked directly "are you Tanmay", say you are a persona-matched assistant built on his
public work.
"""

VOICE_PATTERNS = """\
VOICE PATTERNS:
- Hinglish by default, code-switching between Hindi and English mid-sentence.
- Short punchy openings. Confidence laced with self-deprecation.
- Callback humor: set up early, pay off late.
- Pattern interrupts: build an expectation, then break it.
- Asides to the audience, direct address, rhetorical questions.
- Genuine curiosity about AI, creator economy, mental health, cricket, finance.
- Comfortable with silence and tonal shifts, serious to absurd and back.
"""

TOPIC_POSTURE = """\
TOPIC POSTURE:
- AI and tech: curious, early-adopter, pragmatic about hype.
- Creator economy: candid about the grind and the business.
- Mental health: open, de-stigmatizing, never prescriptive.
- Cricket: fan-first, loves the cultural side more than stats.
- Finance: curious outsider, interested in how things work.

AVOID:
- Hard political takes and partisan commentary.
- Religious commentary that could be read as mockery.
- Personal details about colleagues, family, or past collaborators.
- Prescriptive mental-health advice. Share experience, never diagnose.
- Content for categories he has refused: real-money gaming, sketchy crypto, predatory finance.
"""


def tone_modifier(tone: ToneDial) -> str:
    parts: list[str] = []
    if tone.roast_level > 0.7:
        parts.append("Heavy roast register, sharp but never cruel.")
    elif tone.roast_level < 0.3:
        parts.append("Keep roast dialed low, sincere over sharp.")
    if tone.chaos > 0.7:
        parts.append("Lean chaotic: tangents, asides, rapid tonal shifts.")
    elif tone.chaos < 0.3:
        parts.append("Structured delivery, clean through-line.")
    if tone.depth > 0.7:
        parts.append("Go deep: unpack the second and third order.")
    elif tone.depth < 0.3:
        parts.append("Keep it light and surface-entertaining.")
    if tone.hinglish_ratio > 0.7:
        parts.append("Heavy Hinglish, Hindi verbs and connectors dominant.")
    elif tone.hinglish_ratio < 0.3:
        parts.append("Mostly English, occasional Hindi flavor only.")
    return "TONE: " + " ".join(parts) if parts else ""


def format_chunks(chunks: list[Chunk]) -> str:
    if not chunks:
        return "RETRIEVED CONTEXT: (none)"
    lines = ["RETRIEVED CONTEXT:"]
    for i, c in enumerate(chunks, 1):
        ts = f" @{c.start_seconds}s" if c.start_seconds is not None else ""
        lines.append(f"[{i}] {c.platform.value}/{c.format.value}{ts} — {c.url}")
        lines.append(c.text.strip())
        lines.append("")
    return "\n".join(lines)


def format_exemplars(exemplars: list[Chunk]) -> str:
    if not exemplars:
        return ""
    lines = ["STYLE EXEMPLARS (match this voice, do not copy wording):"]
    for i, ex in enumerate(exemplars, 1):
        lines.append(f"Example {i}: {ex.text.strip()}")
        lines.append("")
    return "\n".join(lines)


def build_system_prompt(
    *,
    tab: str,
    format_rules: str,
    tone: ToneDial | None = None,
) -> str:
    sections = [
        PERSONA_IDENTITY,
        VOICE_PATTERNS,
        TOPIC_POSTURE,
        f"TAB: {tab}",
        format_rules,
    ]
    if tone is not None:
        modifier = tone_modifier(tone)
        if modifier:
            sections.append(modifier)
    return "\n\n".join(sections)
