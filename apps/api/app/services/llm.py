from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from anthropic import AsyncAnthropic

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)


class LLMService:
    def __init__(self) -> None:
        settings = get_settings()
        self.primary = settings.anthropic_model_primary
        self.premium = settings.anthropic_model_premium
        self.utility = settings.anthropic_model_utility
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None

    async def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        if self._client is None:
            log.warning("anthropic_api_key not set, returning stub")
            return "[stub: anthropic API key not configured]"
        response = await self._client.messages.create(
            model=model or self.primary,
            system=system,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        blocks = [b.text for b in response.content if b.type == "text"]
        return "".join(blocks)

    async def stream(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        if self._client is None:
            log.warning("anthropic_api_key not set, streaming stub")
            for token in "[stub: anthropic API key not configured]".split():
                yield token + " "
            return
        async with self._client.messages.stream(
            model=model or self.primary,
            system=system,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        ) as stream:
            async for text in stream.text_stream:
                yield text
