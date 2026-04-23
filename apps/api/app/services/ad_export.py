"""Export an ad response to Markdown or Fountain (screenplay) format.

Markdown: human-readable, good for sharing a link.
Fountain: industry-standard plaintext screenplay format — opens in Highland, Slugline,
Final Draft, and most script tools.

PDF is deliberately NOT handled server-side — the frontend (Phase 08) will render from
the structured response via print-to-PDF to keep server deps lean.
"""
from __future__ import annotations

from app.models.schemas import AdGenerateResponse


def to_markdown(ad: AdGenerateResponse) -> str:
    lines: list[str] = [f"# {ad.title}", ""]
    if ad.hook:
        lines.extend([f"**Hook:** {ad.hook}", ""])

    for s in ad.scenes:
        lines.append(f"## Scene {s.scene_number} — {s.setting} ({s.duration_seconds}s)")
        if s.direction:
            lines.extend([f"*Direction:* {s.direction}", ""])
        if s.characters:
            lines.append(f"*Cast:* {', '.join(s.characters)}")
            lines.append("")
        for line in s.lines:
            lines.append(f"> {line}")
        lines.append("")

    if ad.cta:
        lines.extend(["## CTA", ad.cta, ""])

    if ad.strategy_rationale:
        lines.extend(["## Strategy rationale", ad.strategy_rationale, ""])

    if ad.brand_safety_flags:
        lines.extend(["## Brand safety flags", ""])
        for f in ad.brand_safety_flags:
            lines.append(f"- `{f}`")
        lines.append("")

    if ad.citations:
        lines.extend(["## Citations", ""])
        for i, c in enumerate(ad.citations, 1):
            ts = f" @{c.timestamp_seconds}s" if c.timestamp_seconds is not None else ""
            title = c.title or "(untitled)"
            lines.append(f"{i}. [{title}]({c.url}){ts} — {c.excerpt[:120]}…")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _primary_speaker(characters: list[str]) -> str:
    """Best effort: pick the first character, uppercase for Fountain."""
    return (characters[0].strip().upper() if characters else "TANMAY")


def to_fountain(ad: AdGenerateResponse) -> str:
    """Emit a minimal Fountain document — title page + scene headings + action +
    character cues + dialogue.

    Fountain spec: https://fountain.io/syntax/
    """
    out: list[str] = []

    # Title page
    out.append(f"Title: {ad.title}")
    out.append("Author: Create with Tanmay (auto-drafted)")
    out.append("Draft date: auto")
    out.append("")  # blank line terminates title page

    for s in ad.scenes:
        # Scene heading — Fountain uses INT./EXT.; we don't know which, use "INT." as safe default
        slug = f"INT. {s.setting.upper()} — DAY" if s.setting else f"INT. SCENE {s.scene_number}"
        out.append(slug)
        out.append("")

        if s.direction:
            out.append(s.direction)
            out.append("")

        speaker = _primary_speaker(s.characters)
        for line in s.lines:
            out.append(speaker)
            out.append(line)
            out.append("")

        out.append(f"[[Scene duration: {s.duration_seconds}s]]")
        out.append("")

    if ad.cta:
        out.append("CUT TO:")
        out.append("")
        out.append("INT. CTA — DAY")
        out.append("")
        out.append(_primary_speaker([]))
        out.append(ad.cta)
        out.append("")

    # Notes block for metadata + citations (Fountain boneyard /* ... */)
    out.append("/*")
    out.append("NOTES")
    if ad.hook:
        out.append(f"- Hook: {ad.hook}")
    if ad.strategy_rationale:
        out.append(f"- Strategy rationale: {ad.strategy_rationale}")
    if ad.brand_safety_flags:
        out.append(f"- Brand safety flags: {', '.join(ad.brand_safety_flags)}")
    if ad.citations:
        out.append("- Citations:")
        for c in ad.citations:
            ts = f" @{c.timestamp_seconds}s" if c.timestamp_seconds is not None else ""
            out.append(f"    - {c.title or '(untitled)'}{ts} — {c.url}")
    out.append("*/")
    out.append("")

    return "\n".join(out).rstrip() + "\n"


EXPORTERS = {"md": to_markdown, "fountain": to_fountain}
