# === Файл: src/avatar/tts/silero_engine.py ===
"""Silero TTS Engine implementation (легковесный fallback для русского).

Нативная поддержка русского языка, быстрая генерация, малый VRAM-footprint.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, AsyncIterator

from loguru import logger

from avatar.interfaces.tts import ITTSEngine
from avatar.schemas.audio_types import AudioSegment

if TYPE_CHECKING:
    import torch


class SileroEngine(ITTSEngine):
    """Silero TTS Engine (русский, легковесный).

    Attributes:
        language: Язык синтеза (только "ru").
        speaker: Голос диктора ("aidar", "baya", "kseniya", "xenia", "random").
        sample_rate: Частота дискретизации (8000, 24000, 48000).
        model: Silero TTS model.
        device: Устройство (CPU или CUDA).
    """

    def __init__(
        self,
        language: str = "ru",
        speaker: str = "aidar",
        sample_rate: int = 24000,
    ) -> None:
        """Инициализация Silero Engine.

        Args:
            language: Язык синтеза (только "ru").
            speaker: Голос диктора.
            sample_rate: Частота дискретизации.

        Raises:
            ValueError: Если язык не "ru".
        """
        if language != "ru":
            msg = f"SileroEngine supports only 'ru', got '{language}'"
            raise ValueError(msg)
        self.language = language
        self.speaker = speaker
        self.sample_rate = sample_rate
        self._model: torch.nn.Module | None = None
        self._device: str | None = None
        logger.info(f"SileroEngine initialized: speaker={speaker}, sample_rate={sample_rate}")

    def _load_model(self) -> torch.nn.Module:
        """Загрузка Silero TTS модели.

        Returns:
            torch.nn.Module: Загруженная модель.

        Raises:
            RuntimeError: Если загрузка модели не удалась.
        """
        raise NotImplementedError("TODO: Implement _load_model")

    async def synthesize(
        self,
        text: str,
        language: str = "ru",
        speaker_wav: str | None = None,
    ) -> AudioSegment:
        """Синтез речи из текста (non-streaming).

        Args:
            text: Текст для озвучки.
            language: Язык синтеза (игнорируется, всегда "ru").
            speaker_wav: Игнорируется (Silero не поддерживает voice cloning).

        Returns:
            AudioSegment: Аудио-сегмент с метаданными.

        Raises:
            ValueError: Если текст пустой.
            RuntimeError: Если синтез завершился ошибкой.
        """
        raise NotImplementedError("TODO: Implement synthesize")

    async def synthesize_streaming(
        self,
        text: str,
        language: str = "ru",
    ) -> AsyncIterator[AudioSegment]:
        """Синтез речи (streaming).

        Args:
            text: Текст для озвучки.
            language: Язык синтеза (игнорируется, всегда "ru").

        Yields:
            AudioSegment: Аудио-чанки.

        Raises:
            ValueError: Если текст пустой.
            RuntimeError: Если синтез завершился ошибкой.
        """
        raise NotImplementedError("TODO: Implement synthesize_streaming")
        yield  # type: ignore[unreachable]

    def get_supported_languages(self) -> list[str]:
        """Список поддерживаемых языков.

        Returns:
            list[str]: Только ["ru"].
        """
        return ["ru"]
