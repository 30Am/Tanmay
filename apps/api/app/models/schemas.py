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
    format: Literal["long_podcast", "reel", "thread", "stage"] = "reel"
    target_length_seconds: int = Field(default=60, ge=15, le=3600)
    tone: ToneDial = Field(default_factory=ToneDial)


class ContentGenerateResponse(BaseModel):
    script: str
    description: str
    rationale: str
    citations: list[Citation]


class AdCast(BaseModel):
    name: str
    role: str | None = None


class AdGenerateRequest(BaseModel):
    product_name: str
    product_description: str
    target_audience: str | None = None
    duration_seconds: int = Field(ge=10, le=180)
    language: Literal["hinglish", "english", "hindi"] = "hinglish"
    cast: list[AdCast] = Field(default_factory=list)
    celebrities: list[str] = Field(default_factory=list)
    notes: str | None = None


class AdScene(BaseModel):
    scene_number: int
    setting: str
    direction: str
    characters: list[str]
    lines: list[str]
    duration_seconds: int


class AdGenerateResponse(BaseModel):
    title: str
    hook: str
    scenes: list[AdScene]
    cta: str
    strategy_rationale: str
    brand_safety_flags: list[str] = Field(default_factory=list)
    citations: list[Citation]


class QaRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


class QaConfidence(str, Enum):
    ANSWERED = "answered"
    REFUSED_LOW_CONFIDENCE = "refused_low_confidence"
    REFUSED_SENSITIVE = "refused_sensitive"


class QaResponse(BaseModel):
    status: QaConfidence
    answer: str | None = None
    reason: str | None = None
    citations: list[Citation] = Field(default_factory=list)
    max_similarity: float | None = None


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
