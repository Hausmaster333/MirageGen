"""Dependency injection для FastAPI endpoints.

Хранит глобальные зависимости (pipeline, settings) и предоставляет их через Depends().
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from avatar.config.settings import Settings
    from avatar.pipeline.avatar_pipeline import AvatarPipeline

# Глобальные зависимости (инициализируются в app.py при старте)
_global_pipeline: AvatarPipeline | None = None
_global_settings: Settings | None = None


def init_dependencies(pipeline: AvatarPipeline, settings: Settings) -> None:
    """Инициализировать глобальные зависимости.

    Вызывается из create_app() при старте приложения.

    Args:
        pipeline: Инстанс AvatarPipeline.
        settings: Глобальные настройки.
    """
    global _global_pipeline, _global_settings
    _global_pipeline = pipeline
    _global_settings = settings
    logger.info("Dependencies initialized")


def get_pipeline() -> AvatarPipeline:
    """Dependency injection для AvatarPipeline.

    Returns:
        AvatarPipeline: Инстанс пайплайна.

    Raises:
        RuntimeError: Если пайплайн не инициализирован.
    """
    if _global_pipeline is None:
        msg = "Pipeline not initialized. Call init_dependencies() first."
        raise RuntimeError(msg)
    return _global_pipeline


def get_settings() -> Settings:
    """Dependency injection для Settings.

    Returns:
        Settings: Глобальные настройки.

    Raises:
        RuntimeError: Если настройки не инициализированы.
    """
    if _global_settings is None:
        msg = "Settings not initialized. Call init_dependencies() first."
        raise RuntimeError(msg)
    return _global_settings
