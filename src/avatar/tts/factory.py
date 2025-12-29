"""Factory для создания TTS движков на основе конфига."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from avatar.interfaces.tts import ITTSEngine
from avatar.tts.silero_engine import SileroEngine

# XTTSEngine удален из импортов, так как библиотека исключена
# from avatar.tts.xtts_engine import XTTSEngine

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
        engine_type = config.engine.lower()

        if engine_type == "silero":
            logger.info(f"Creating SileroEngine (v5) for language={config.language}")

            # Извлекаем параметры из конфига или используем дефолты для V5
            # Pydantic модель TTSConfig может иметь поле extra_params или поля напрямую
            # Здесь предполагаем, что поля добавлены в TTSConfig (см. models_config.yaml)

            speaker = getattr(config, "speaker", "xenia")
            sample_rate = getattr(config, "sample_rate", 48000)
            device = getattr(config, "device", "cpu")

            return SileroEngine(
                language=config.language,
                speaker=speaker,
                sample_rate=sample_rate,
                device=device
            )

        # Если вдруг захотим вернуть XTTS, код будет здесь,
        # но сейчас мы не импортируем класс, чтобы не ломать сборку без пакета coqui-tts
        if engine_type == "xtts":
            raise NotImplementedError("XTTS engine is disabled in this build.")

        raise ValueError(
            f"Unsupported TTS engine: {engine_type}. "
            f"Supported: silero"
        )
