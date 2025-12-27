# === Файл: src/avatar/main.py ===
"""Entry point для запуска FastAPI сервера."""

from __future__ import annotations

import uvicorn
from loguru import logger

from avatar.api.app import create_app
from avatar.config import Settings
from avatar.lipsync.factory import LipSyncFactory
from avatar.llm.factory import LLMFactory
from avatar.motion.factory import MotionFactory
from avatar.motion.sentiment_analyzer import SentimentAnalyzer
from avatar.pipeline.avatar_pipeline import AvatarPipeline
from avatar.tts.factory import TTSFactory

# Глобальный pipeline (инициализируется один раз)
_pipeline: AvatarPipeline | None = None


def initialize_pipeline(settings: Settings) -> AvatarPipeline:
    """Инициализировать pipeline через фабрики.

    Args:
        settings: Настройки приложения.

    Returns:
        AvatarPipeline: Инициализированный pipeline.
    """
    logger.info("Initializing pipeline with factories...")

    # Создание компонентов через фабрики (как в ARCHITECTURE.md)
    llm = LLMFactory.create(settings.llm)
    tts = TTSFactory.create(settings.tts)
    lipsync = LipSyncFactory.create(settings.lipsync)
    motion = MotionFactory.create(settings.motion)
    sentiment = SentimentAnalyzer(model_name=settings.motion.sentiment_model)

    # Сборка pipeline
    pipeline = AvatarPipeline(
        llm_provider=llm,
        tts_engine=tts,
        lipsync_generator=lipsync,
        motion_generator=motion,
        sentiment_analyzer=sentiment,
    )

    logger.info("Pipeline initialized successfully!")
    return pipeline


def get_pipeline() -> AvatarPipeline:
    """Получить глобальный инстанс pipeline (Singleton).

    Returns:
        AvatarPipeline: Глобальный pipeline.
    """
    global _pipeline
    if _pipeline is None:
        settings = Settings()
        _pipeline = initialize_pipeline(settings)
    return _pipeline


def run_server() -> None:
    """Запустить FastAPI сервер."""
    settings = Settings()

    # Инициализировать pipeline до запуска сервера
    global _pipeline
    _pipeline = initialize_pipeline(settings)

    # Создать FastAPI app
    app = create_app(settings)

    logger.info(f"Starting server at {settings.api.host}:{settings.api.port}")

    uvicorn.run(
        app,
        host=settings.api.host,
        port=settings.api.port,
        log_level="info",
    )


if __name__ == "__main__":
    run_server()
