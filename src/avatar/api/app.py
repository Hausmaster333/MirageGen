# === Файл: src/avatar/api/app.py ===
"""FastAPI application factory.

Создание и настройка FastAPI приложения с CORS, logging, routes.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel

from avatar.api.middleware import setup_logging_middleware
from avatar.api.routes import chat, stream
from avatar.config.settings import Settings


class HealthResponse(BaseModel):
    """Response для healthcheck endpoint.

    Attributes:
        status: Общий статус ("healthy" или "unhealthy").
        components: Статус каждого компонента.
        vram_usage: VRAM usage (опционально, если pynvml доступен).
    """

    status: str
    components: dict[str, bool]
    vram_usage: dict[str, int] | None = None


def create_app(settings: Settings | None = None) -> FastAPI:
    """Создание FastAPI приложения.

    Args:
        settings: Опциональные настройки (по умолчанию загружаются из config).

    Returns:
        FastAPI: Настроенное приложение.
    """
    if settings is None:
        settings = Settings()

    app = FastAPI(
        title="Avatar PoC API",
        description="Real-time avatar animation pipeline (LLM + TTS + Lipsync + Motion)",
        version="0.1.0",
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
        """GET /api/v1/health - healthcheck всех компонентов.

        Returns:
            HealthResponse: Статус компонентов и VRAM usage.
        """
        raise NotImplementedError("TODO: Implement health_endpoint")

    logger.info(f"FastAPI app created: host={settings.api.host}, port={settings.api.port}")
    return app


def get_vram_usage() -> dict[str, int] | None:
    """Получить VRAM usage через pynvml.

    Returns:
        dict[str, int] | None: {"used_mb": 7500, "total_mb": 12288} или None.
    """
    raise NotImplementedError("TODO: Implement get_vram_usage")
