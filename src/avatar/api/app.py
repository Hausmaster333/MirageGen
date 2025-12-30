"""FastAPI application factory.

Создание и настройка FastAPI приложения с CORS, logging, routes.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel

from avatar.api.dependencies import get_pipeline, init_dependencies
from avatar.api.middleware import setup_logging_middleware
from avatar.api.routes import chat, stream
from avatar.config.settings import Settings
from avatar.lipsync.factory import LipSyncFactory
from avatar.llm.factory import LLMFactory
from avatar.motion.factory import MotionFactory
from avatar.motion.sentiment_analyzer import SentimentAnalyzer
from avatar.pipeline.avatar_pipeline import AvatarPipeline
from avatar.tts.factory import TTSFactory


class HealthResponse(BaseModel):
    """Response для healthcheck endpoint."""

    status: str
    components: dict[str, bool]
    vram_usage: dict[str, int] | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: RUF029
    """Lifecycle manager для FastAPI (startup/shutdown)."""
    logger.info("Starting Avatar Pipeline API...")
    yield
    logger.info("Shutting down Avatar Pipeline API...")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Создание FastAPI приложения.

    Args:
        settings: Опциональные настройки (по умолчанию загружаются из config).

    Returns:
        FastAPI: Настроенное приложение.
    """
    if settings is None:
        settings = Settings()

    # Создаём компоненты через фабрики
    llm_provider = LLMFactory.create(settings.llm)
    tts_engine = TTSFactory.create(settings.tts)
    lipsync_generator = LipSyncFactory.create(settings.lipsync)
    motion_generator = MotionFactory.create(settings.motion)
    sentiment_analyzer = SentimentAnalyzer()

    # Создаём глобальный пайплайн
    pipeline = AvatarPipeline(
        llm_provider=llm_provider,
        tts_engine=tts_engine,
        lipsync_generator=lipsync_generator,
        motion_generator=motion_generator,
        sentiment_analyzer=sentiment_analyzer,
    )

    # Инициализируем глобальные зависимости
    init_dependencies(pipeline=pipeline, settings=settings)
    logger.info("AvatarPipeline initialized successfully")

    app = FastAPI(
        title="Avatar PoC API",
        description="Real-time avatar animation pipeline (LLM + TTS + Lipsync + Motion)",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Logging middleware
    setup_logging_middleware(app)

    # Include routes
    app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
    app.include_router(stream.router, prefix="/api/v1", tags=["stream"])

    # Health endpoint
    @app.get("/api/v1/health", response_model=HealthResponse, tags=["health"])
    async def health_endpoint() -> HealthResponse:
        """GET /api/v1/health - healthcheck всех компонентов."""
        pipeline = get_pipeline()
        components = await pipeline.healthcheck()

        all_healthy = all(components.values())
        status = "healthy" if all_healthy else "unhealthy"

        vram = get_vram_usage()

        return HealthResponse(
            status=status,
            components=components,
            vram_usage=vram,
        )

    logger.info(f"FastAPI app created: host={settings.api.host}, port={settings.api.port}")
    return app


def get_vram_usage() -> dict[str, int] | None:
    """Получить VRAM usage через pynvml."""
    try:
        import pynvml  # noqa: PLC0415

        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        pynvml.nvmlShutdown()

        return {
            "used_mb": info.used // (1024**2),
            "total_mb": info.total // (1024**2),
        }
    except Exception:
        logger.debug("pynvml not available or no GPU detected")
        return None
