from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Platform(str, Enum):
    YOUTUBE = "youtube"
    X = "x"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    PODCAST = "podcast"
    EVENT = "event"
    OTHER = "other"


class ContentFormat(str, Enum):
    LONG_PODCAST = "long_podcast"
    REEL = "reel"
    TWEET = "tweet"
    THREAD = "thread"
    STAGE = "stage"
    AD = "ad"
    BRANDED = "branded"
    INTERVIEW = "interview"


class Register(str, Enum):
    ROAST = "roast"
    REFLECTIVE = "reflective"
    INFORMATIVE = "informative"
    COMEDIC = "comedic"
    SINCERE = "sincere"


class Citation(BaseModel):
    source_id: str
    url: str
    platform: Platform
    title: str | None = None
    timestamp_seconds: int | None = None
    excerpt: str


class ToneDial(BaseModel):
    roast_level: float = Field(default=0.5, ge=0.0, le=1.0)
    chaos: float = Field(default=0.5, ge=0.0, le=1.0)
    depth: float = Field(default=0.5, ge=0.0, le=1.0)
    hinglish_ratio: float = Field(default=0.5, ge=0.0, le=1.0)


class ContentGenerateRequest(BaseModel):
    idea: str = Field(min_length=3, max_length=2000)
    format: Literal[
        "reel",
        "youtube_short",
        "talking_head",
        "long_podcast",
        "thread",
        "stage",
        "monologue",
        "explainer",
        "interview",
        "reaction",
    ] = "reel"
    target_length_seconds: int = Field(default=60, ge=15, le=3600)
    tone: ToneDial = Field(default_factory=ToneDial)
    language: Literal["hinglish", "english", "hindi"] = "hinglish"


class ContentGenerateResponse(BaseModel):
    script: str
    description: str
    rationale: str
    citations: list[Citation]


class AdCast(BaseModel):
    name: str
    role: str | None = None


Industry = Literal[
    "fintech", "d2c", "saas_b2b", "fmcg", "beauty", "edtech",
    "auto", "realty", "ott_media", "telecom", "healthcare", "travel", "other",
]
CampaignGoal = Literal["awareness", "consideration", "conversion", "relaunch", "feature_drop"]
Placement = Literal["yt_preroll", "yt_bumper", "ig_reel", "ig_story", "tv_spot", "ooh", "audio", "other"]
ProductStage = Literal["launch", "relaunch", "feature", "seasonal", "always_on"]
BrandVoiceTag = Literal[
    "premium", "playful", "cant_do_humor", "family_safe_only",
    "no_celebrity_impersonation", "educational", "minimal",
]


class AdGenerateRequest(BaseModel):
    product_name: str
    product_description: str
    target_audience: str | None = None
    duration_seconds: int = Field(ge=6, le=180)
    language: Literal["hinglish", "english", "hindi"] = "hinglish"
    cast: list[AdCast] = Field(default_factory=list)
    celebrities: list[str] = Field(default_factory=list)
    notes: str | None = None
    tone: ToneDial = Field(default_factory=ToneDial)

    # New diversity/quality fields — all optional for backward compat.
    industry: Industry | None = None
    campaign_goal: CampaignGoal | None = None
    proof_point: str | None = Field(default=None, max_length=280)
    positioning: str | None = Field(default=None, max_length=280)
    competitor: str | None = Field(default=None, max_length=140)
    brand_voice_tags: list[BrandVoiceTag] = Field(default_factory=list)
    do_not_say: list[str] = Field(default_factory=list)
    placement: Placement | None = None
    product_stage: ProductStage | None = None


class AdScene(BaseModel):
    scene_number: int
    setting: str
    direction: str
    characters: list[str]
    lines: list[str]
    duration_seconds: int


class AdQualityScores(BaseModel):
    """Haiku-judged rubric scores, 1-5 on each dimension."""

    on_brand: int = Field(ge=1, le=5)
    proof_point_present: int = Field(ge=1, le=5)
    audience_match: int = Field(ge=1, le=5)
    hook_strength: int = Field(ge=1, le=5)
    no_tanmay_leak: int = Field(ge=1, le=5)
    notes: str = ""

    @property
    def total(self) -> int:
        return (
            self.on_brand + self.proof_point_present + self.audience_match
            + self.hook_strength + self.no_tanmay_leak
        )


class AdGenerateResponse(BaseModel):
    title: str
    hook: str
    scenes: list[AdScene]
    cta: str
    strategy_rationale: str
    brand_safety_flags: list[str] = Field(default_factory=list)
    citations: list[Citation]
    quality: AdQualityScores | None = None
    # Words/phrases from do_not_say that leaked into the output. Empty = clean.
    do_not_say_hits: list[str] = Field(default_factory=list)
    # True when the stated proof_point (or close paraphrase) was found in output.
    proof_point_found: bool | None = None


class QaRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


class QaConfidence(str, Enum):
    ANSWERED = "answered"
    REFUSED_LOW_CONFIDENCE = "refused_low_confidence"
    REFUSED_SENSITIVE = "refused_sensitive"


class VerifiedClaim(BaseModel):
    claim: str
    citation_indices: list[int] = Field(default_factory=list)
    supported: bool = False


class QaResponse(BaseModel):
    status: QaConfidence
    answer: str | None = None
    reason: str | None = None
    citations: list[Citation] = Field(default_factory=list)
    max_similarity: float | None = None
    verified_claims: list[VerifiedClaim] = Field(default_factory=list)
    n_supported: int = 0
    n_unsupported: int = 0
    paraphrases_used: list[str] = Field(default_factory=list)


class Chunk(BaseModel):
    chunk_id: str
    source_id: str
    platform: Platform
    format: ContentFormat
    text: str
    start_seconds: int | None = None
    end_seconds: int | None = None
    published_at: datetime | None = None
    topic_tags: list[str] = Field(default_factory=list)
    register: Register | None = None
    language_mix: dict[str, float] = Field(default_factory=dict)
    url: str
    score: float | None = None
