from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load .env into os.environ before any service imports read it.
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

from app.core.config import get_settings  # noqa: E402
from app.core.logging import configure_logging, get_logger
from app.routers import ad, content, health, qa


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    log = get_logger("lifespan")
    log.info("startup", env=settings.env)
    yield
    log.info("shutdown")


settings = get_settings()
app = FastAPI(title="Create with Tanmay API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(content.router)
app.include_router(ad.router)
app.include_router(qa.router)
