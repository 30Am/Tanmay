from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field


class Platform(str, Enum):
    YOUTUBE = "youtube"
    X = "x"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    PODCAST = "podcast"
    EVENT = "event"
    OTHER = "other"


class Source(BaseModel):
    source_id: str
    platform: Platform
    kind: Literal["channel", "profile", "rss", "video", "post", "manual"] | None = None
    url: str
    format: Literal[
        "long_podcast", "reel", "tweet", "thread", "stage", "ad", "branded", "interview"
    ]
    co_hosts: list[str] = Field(default_factory=list)
    sponsor: str | None = None
    apify_actor: str | None = None
    enabled: bool = True


class Defaults(BaseModel):
    checkpoint_every: int = 50
    retry_max: int = 3


class Registry(BaseModel):
    version: int
    defaults: Defaults = Field(default_factory=Defaults)
    sources: list[Source]

    def enabled_sources(self) -> list[Source]:
        return [s for s in self.sources if s.enabled]


def load_registry(path: str | Path) -> Registry:
    path = Path(path)
    with path.open("r") as fh:
        data = yaml.safe_load(fh)
    return Registry.model_validate(data)
