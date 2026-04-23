from __future__ import annotations

from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: Literal["dev", "staging", "prod"] = "dev"
    log_level: str = "INFO"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    anthropic_api_key: str = ""
    anthropic_model_primary: str = "claude-sonnet-4-6"
    anthropic_model_premium: str = "claude-opus-4-7"
    anthropic_model_utility: str = "claude-haiku-4-5-20251001"

    voyage_api_key: str = ""
    voyage_model: str = "voyage-3"
    voyage_dim: int = 1024

    cohere_api_key: str = ""
    cohere_rerank_model: str = "rerank-3"

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    qdrant_collection: str = "tanmay_chunks"
    qdrant_exemplars_collection: str = "tanmay_exemplars"

    postgres_dsn: str = "postgresql+asyncpg://tanmay:tanmay@localhost:5432/tanmay"
    redis_url: str = "redis://localhost:6379/0"

    r2_endpoint: str = ""
    r2_bucket: str = "tanmay-raw"
    r2_access_key: str = ""
    r2_secret_key: str = ""

    deepgram_api_key: str = ""

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    retrieval_top_k_candidates: int = 50
    retrieval_top_k_final: int = 12
    retrieval_confidence_threshold: float = 0.45


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
