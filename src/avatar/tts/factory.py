# === Файл: src/avatar/tts/factory.py ===
"""Factory для создания TTS движков на основе конфига."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from avatar.interfaces.tts import ITTSEngine
from avatar.tts.silero_engine import SileroEngine
from avatar.tts.xtts_engine import XTTSEngine

if TYPE_CHECKING:
    from avatar.config.settings import TTSConfig


class TTSFactory:
    """Factory для создания TTS движков."""

    @staticmethod
    def create(config: TTSConfig) -> ITTSEngine:
        """Создать TTS движок на основе конфигурации.

        Args:
            config: Конфигурация TTS.

        Returns:
            ITTSEngine: Инстанс TTS движка.

        Raises:
            ValueError: Если движок не поддерживается.
        """
        engine = config.engine.lower()

        if engine == "xtts":
            logger.info(f"Creating XTTSEngine for language={config.language}")
            return XTTSEngine(
                language=config.language,
                speed=config.speed,
                speaker_wav=config.speaker_wav,
            )

        if engine == "silero":
            logger.info(f"Creating SileroEngine for language={config.language}")
            return SileroEngine(
                language=config.language,
                speaker="aidar",  # Можно добавить в config
                sample_rate=24000,
            )

        raise ValueError(
            f"Unsupported TTS engine: {engine}. " f"Supported: xtts, silero"
        )
