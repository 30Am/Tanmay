"""Validate the structured ad response for duration/wordcount sanity."""
from __future__ import annotations

from dataclasses import dataclass

WORDS_PER_SECOND: dict[str, float] = {"hinglish": 2.3, "english": 2.6, "hindi": 2.0}
DURATION_TOLERANCE_S = 2
WORDCOUNT_TOLERANCE = 0.25  # ±25% of target word count is fine


@dataclass
class ValidationIssue:
    code: str
    message: str


@dataclass
class ValidationResult:
    ok: bool
    issues: list[ValidationIssue]
    total_scene_duration_s: int
    total_words: int
    target_duration_s: int
    target_words: int


def _count_words(lines: list[str]) -> int:
    return sum(len(line.split()) for line in lines if isinstance(line, str))


def validate_ad(
    *,
    scenes: list[dict],
    target_duration_s: int,
    language: str,
) -> ValidationResult:
    total_dur = sum(int(s.get("duration_seconds") or 0) for s in scenes)
    total_words = sum(_count_words(s.get("lines") or []) for s in scenes)
    wps = WORDS_PER_SECOND.get(language, WORDS_PER_SECOND["hinglish"])
    target_words = int(target_duration_s * wps)

    issues: list[ValidationIssue] = []

    if not scenes:
        issues.append(ValidationIssue("no_scenes", "Scenes list is empty."))

    dur_delta = total_dur - target_duration_s
    if abs(dur_delta) > DURATION_TOLERANCE_S:
        issues.append(
            ValidationIssue(
                "duration_mismatch",
                f"Total scene durations {total_dur}s vs target {target_duration_s}s "
                f"(delta {dur_delta:+d}s, tolerance ±{DURATION_TOLERANCE_S}s).",
            )
        )

    word_lo = int(target_words * (1 - WORDCOUNT_TOLERANCE))
    word_hi = int(target_words * (1 + WORDCOUNT_TOLERANCE))
    if not (word_lo <= total_words <= word_hi):
        issues.append(
            ValidationIssue(
                "wordcount_off",
                f"Total words {total_words} outside target range [{word_lo}-{word_hi}] "
                f"for {target_duration_s}s in {language} ({wps} wps).",
            )
        )

    # Each scene should have at least one line and a positive duration.
    for s in scenes:
        if not s.get("lines"):
            issues.append(ValidationIssue("empty_scene_lines", f"Scene {s.get('scene_number')} has no lines."))
        if (s.get("duration_seconds") or 0) <= 0:
            issues.append(ValidationIssue("scene_zero_duration", f"Scene {s.get('scene_number')} has non-positive duration."))

    return ValidationResult(
        ok=not issues,
        issues=issues,
        total_scene_duration_s=total_dur,
        total_words=total_words,
        target_duration_s=target_duration_s,
        target_words=target_words,
    )
