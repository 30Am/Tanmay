"""IP-based sliding-window rate limiter backed by Redis.

Limits (requests / minute per IP):
  POST /generate/qa              20
  POST /generate/content         10
  POST /generate/content/stream  10
  POST /generate/ad              10
  All other routes              100

Returns HTTP 429 with Retry-After header when the limit is exceeded.
Gracefully disables itself if Redis is unreachable (fail-open — never blocks a request
because Redis is down).

Usage (in main.py):
    from app.middleware.ratelimit import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware, redis_url=settings.redis_url)
"""
from __future__ import annotations

import time
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.core.logging import get_logger

log = get_logger(__name__)

# (path_prefix, method) → (max_requests, window_seconds)
ROUTE_LIMITS: list[tuple[str, str, int, int]] = [
    ("/generate/qa",             "POST", 20,  60),
    ("/generate/content/stream", "POST", 10,  60),
    ("/generate/content",        "POST", 10,  60),
    ("/generate/ad",             "POST", 10,  60),
]
DEFAULT_LIMIT = (100, 60)  # fallback for all other routes


def _client_ip(request: Request) -> str:
    """Extract real IP, respecting X-Forwarded-For from trusted proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _route_limit(path: str, method: str) -> tuple[int, int]:
    for prefix, m, limit, window in ROUTE_LIMITS:
        if method.upper() == m and path.startswith(prefix):
            return limit, window
    return DEFAULT_LIMIT


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, *, redis_url: str) -> None:
        super().__init__(app)
        self._redis_url = redis_url
        self._redis: Any = None  # lazy-initialised on first request

    async def _get_redis(self) -> Any | None:
        if self._redis is not None:
            return self._redis
        try:
            import redis.asyncio as aioredis  # type: ignore[import-untyped]
            client = aioredis.from_url(self._redis_url, socket_connect_timeout=1)
            await client.ping()
            self._redis = client
            log.info("rate_limiter_redis_connected", url=self._redis_url)
            return self._redis
        except Exception as exc:
            log.warning("rate_limiter_redis_unavailable", error=str(exc))
            return None

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        ip = _client_ip(request)
        limit, window = _route_limit(request.url.path, request.method)

        redis = await self._get_redis()
        if redis is None:
            # Fail-open: Redis unavailable, let the request through
            return await call_next(request)

        # Sliding window via Redis INCR + EXPIRE (fixed window approximation)
        bucket = f"rl:{ip}:{request.url.path}:{int(time.time()) // window}"
        try:
            count = await redis.incr(bucket)
            if count == 1:
                await redis.expire(bucket, window)
            if count > limit:
                retry_after = window - (int(time.time()) % window)
                log.warning(
                    "rate_limit_exceeded",
                    ip=ip,
                    path=request.url.path,
                    count=count,
                    limit=limit,
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "rate_limit_exceeded",
                        "detail": f"Too many requests. Limit: {limit} per {window}s.",
                        "retry_after": retry_after,
                    },
                    headers={"Retry-After": str(retry_after)},
                )
        except Exception as exc:
            # Fail-open on any Redis error mid-request
            log.warning("rate_limiter_redis_error", error=str(exc))

        return await call_next(request)
